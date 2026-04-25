from typing import Any

from app.errors import AppError
from app.models.domain import new_id, now_iso
from app.models.verification import VerificationResultModel
from app.repositories.photo_repository import PhotoRepository
from app.repositories.state_repository import StateRepository
from app.services.payment_service import PaymentService


_AI_NOT_CONFIGURED_ERROR_CODES = {"analysis_not_configured", "report_generation_not_configured", "verification_not_configured"}


class GigService:
    def __init__(
        self,
        *,
        state_repository: StateRepository,
        photo_repository: PhotoRepository,
        verification_client: Any,
        payment_service: PaymentService,
        allow_ai_fallback: bool = False,
    ):
        self.state_repository = state_repository
        self.photo_repository = photo_repository
        self.verification_client = verification_client
        self.payment_service = payment_service
        self.allow_ai_fallback = allow_ai_fallback

    def list_gigs(self) -> dict:
        state = self.state_repository.load()
        return {"gigs": list(state["gigs"].values())}

    def create_gig(self, payload) -> dict:
        if payload.currency != "EUR":
            raise AppError("invalid_currency", "Only EUR is supported for the MVP.")
        gig_id = new_id("gig")
        now = now_iso()
        gig = {
            "id": gig_id,
            "family_id": "family_001",
            "title": payload.title,
            "description": payload.description,
            "reward_amount": payload.reward_amount,
            "currency": payload.currency,
            "status": "open",
            "created_by_user_id": "parent_001",
            "claimed_by_user_id": None,
            "verification_checklist": payload.verification_checklist,
            "before_photo_id": None,
            "after_photo_id": None,
            "verification_result_id": None,
            "payment_id": None,
            "created_at": now,
            "updated_at": now,
        }
        with self.state_repository.transaction() as state:
            state["gigs"][gig_id] = gig
            return {"gig": gig}

    def claim_gig(self, gig_id: str) -> dict:
        with self.state_repository.transaction() as state:
            gig = self._get_gig(state, gig_id)
            if gig["status"] != "open":
                raise AppError("invalid_gig_state", "Only open gigs can be claimed.")
            gig["status"] = "claimed"
            gig["claimed_by_user_id"] = "kid_001"
            gig["updated_at"] = now_iso()
            return {"gig": gig}

    def add_before_photo(self, gig_id: str, image_base64: str) -> dict:
        with self.state_repository.transaction() as state:
            gig = self._get_gig(state, gig_id)
            if gig["status"] not in {"claimed", "rejected"}:
                raise AppError("invalid_gig_state", "Before photo can only be added after claiming.")

            photo = self.photo_repository.save_data_url(image_base64, gig_id=gig_id, kind="before")
            photo["created_at"] = now_iso()
            state["photos"][photo["id"]] = photo
            gig["before_photo_id"] = photo["id"]
            gig["status"] = "awaiting_after_photo"
            gig["updated_at"] = now_iso()
            return {"gig": gig}

    def complete_gig(self, gig_id: str, *, after_image_base64: str, idempotency_key: str) -> dict:
        attempt_id = f"{gig_id}:{idempotency_key}"
        with self.state_repository.transaction() as state:
            if attempt_id in state["completion_attempts"]:
                return state["completion_attempts"][attempt_id]["response"]

            gig = self._get_gig(state, gig_id)
            if gig["status"] == "paid":
                return self._paid_response(state, gig)
            if gig["status"] not in {"awaiting_after_photo", "payment_failed"}:
                raise AppError("invalid_gig_state", "Gig is not ready for completion.")
            if not gig.get("before_photo_id"):
                raise AppError("missing_before_photo", "Add a before photo before completing the gig.")
            if gig["status"] == "payment_failed":
                self._ensure_payment_retryable(state, gig)

            after_photo_id = None
            if gig["status"] == "payment_failed" and gig.get("verification_result_id"):
                verification = state["verification_results"][gig["verification_result_id"]]
                if not verification.get("approved"):
                    raise AppError("invalid_gig_state", "Rejected gigs need a new after photo before retry.")
            else:
                before_photo = state["photos"][gig["before_photo_id"]]
                after_photo = self.photo_repository.save_data_url(after_image_base64, gig_id=gig_id, kind="after")
                after_photo["created_at"] = now_iso()
                state["photos"][after_photo["id"]] = after_photo
                after_photo_id = after_photo["id"]
                gig["after_photo_id"] = after_photo["id"]
                gig["status"] = "verifying"
                gig["updated_at"] = now_iso()

                verification = self._verify_or_fallback(
                    gig=gig,
                    before_photo=before_photo,
                    after_photo=after_photo,
                )
                verification["created_at"] = now_iso()
                state["verification_results"][verification["id"]] = verification
                gig["verification_result_id"] = verification["id"]

            if not verification["approved"]:
                gig["status"] = "rejected"
                gig["updated_at"] = now_iso()
                response = self._completion_response(gig, verification, None, None)
                self._store_attempt(state, attempt_id, response, verification["id"], None, after_photo_id)
                return response

            return self._complete_approved_gig_payment(
                state=state,
                gig=gig,
                verification=verification,
                attempt_id=attempt_id,
                after_photo_id=after_photo_id,
            )

    def retry_payment(self, gig_id: str, *, idempotency_key: str) -> dict:
        attempt_id = f"{gig_id}:retry-payment:{idempotency_key}"
        with self.state_repository.transaction() as state:
            if attempt_id in state["completion_attempts"]:
                return state["completion_attempts"][attempt_id]["response"]

            gig = self._get_gig(state, gig_id)
            if gig["status"] == "paid":
                return self._paid_response(state, gig)
            if gig["status"] != "payment_failed":
                raise AppError("invalid_gig_state", "Only payment_failed gigs can retry payment.")
            self._ensure_payment_retryable(state, gig)

            verification_id = gig.get("verification_result_id")
            if not verification_id:
                raise AppError("invalid_gig_state", "Payment retry requires an approved verification result.")

            verification = state["verification_results"][verification_id]
            if not verification.get("approved"):
                raise AppError("invalid_gig_state", "Payment retry requires an approved verification result.")

            return self._complete_approved_gig_payment(
                state=state,
                gig=gig,
                verification=verification,
                attempt_id=attempt_id,
                after_photo_id=None,
            )

    def get_kid_balance(self) -> dict:
        with self.state_repository.transaction() as state:
            balance = self.payment_service.get_kid_balance(state)
            mode = getattr(self.payment_service.payment_client, "mode", "fake_local")
            return {
                "balance": balance,
                "mode": mode,
                "fallback_mode": mode in ("bunq_fallback",),
            }

    def _get_gig(self, state: dict, gig_id: str) -> dict:
        try:
            return state["gigs"][gig_id]
        except KeyError as exc:
            raise AppError("gig_not_found", "Gig was not found.", status_code=404) from exc

    def _ensure_payment_retryable(self, state: dict, gig: dict) -> None:
        payment = state["payments"].get(gig.get("payment_id"))
        if payment and payment.get("status") == "failed" and not payment.get("retryable", True):
            raise AppError(
                "payment_not_retryable",
                "Payment state is unknown. Check bunq before retrying to avoid a duplicate payment.",
                status_code=409,
            )

    def _store_attempt(
        self,
        state: dict,
        attempt_id: str,
        response: dict,
        verification_id: str | None,
        payment_id: str | None,
        after_photo_id: str | None,
    ) -> None:
        state["completion_attempts"][attempt_id] = {
            "id": attempt_id,
            "verification_result_id": verification_id,
            "payment_id": payment_id,
            "after_photo_id": after_photo_id,
            "response": response,
            "created_at": now_iso(),
        }

    def _complete_approved_gig_payment(
        self,
        *,
        state: dict,
        gig: dict,
        verification: dict,
        attempt_id: str,
        after_photo_id: str | None,
    ) -> dict:
        gig["status"] = "approved"
        try:
            payment, kid_balance = self.payment_service.pay_for_gig(
                state=state,
                gig=gig,
                idempotency_key=attempt_id,
            )
        except AppError as exc:
            payment = self.payment_service.record_failed_payment(
                state=state,
                gig=gig,
                error_code=exc.code,
                retryable=exc.retryable,
            )
            gig["payment_id"] = payment["id"]
            gig["status"] = "payment_failed"
            gig["updated_at"] = now_iso()
            response = self._completion_response(gig, verification, payment, None)
            self._store_attempt(state, attempt_id, response, verification["id"], payment["id"], after_photo_id)
            return response

        gig["payment_id"] = payment["id"]
        gig["status"] = "paid"
        gig["updated_at"] = now_iso()
        if kid_balance is None:
            kid_balance = state["balances"]["kid_001"]
            response = self._completion_response(gig, verification, payment, kid_balance)
            response["balance_refresh_status"] = "pending"
            self._store_attempt(state, attempt_id, response, verification["id"], payment["id"], after_photo_id)
            self.state_repository.save(state)

            try:
                kid_balance = self.payment_service.get_kid_balance(state)
                response = self._completion_response(gig, verification, payment, kid_balance)
                response["balance_refresh_status"] = "ok"
            except AppError as exc:
                response = self._completion_response(gig, verification, payment, kid_balance)
                response["balance_refresh_status"] = "failed"
                response["balance_refresh_error"] = exc.code
            except Exception:
                response = self._completion_response(gig, verification, payment, kid_balance)
                response["balance_refresh_status"] = "failed"
                response["balance_refresh_error"] = "balance_refresh_failed"
            self._store_attempt(state, attempt_id, response, verification["id"], payment["id"], after_photo_id)
            return response

        response = self._completion_response(gig, verification, payment, kid_balance)
        self._store_attempt(state, attempt_id, response, verification["id"], payment["id"], after_photo_id)
        return response

    def _verify_or_fallback(self, *, gig: dict, before_photo: dict, after_photo: dict) -> dict:
        try:
            raw_verification = self.verification_client.verify(
                gig=gig,
                before_photo=before_photo,
                after_photo=after_photo,
            )
            return VerificationResultModel.model_validate(raw_verification).model_dump()
        except AppError as exc:
            if not self.allow_ai_fallback or exc.code not in _AI_NOT_CONFIGURED_ERROR_CODES:
                raise
        except Exception as exc:
            if not self.allow_ai_fallback:
                raise AppError(
                    "verification_failed",
                    "AI verification failed. Try again.",
                    status_code=502,
                    retryable=True,
                ) from exc
            return VerificationResultModel(
                id=new_id("verif"),
                gig_id=gig["id"],
                approved=True,
                confidence=0,
                tags=["demo fallback"],
                message_for_kid="Demo fallback approved this task because AI verification is unavailable.",
                reasoning_summary="AI verification failed and explicit demo fallback was enabled.",
                raw_provider="fallback",
                raw_model="ai-fallback-v1",
            ).model_dump()

        return VerificationResultModel(
            id=new_id("verif"),
            gig_id=gig["id"],
            approved=True,
            confidence=0,
            tags=["demo fallback"],
            message_for_kid="Demo fallback approved this task because AI verification is unavailable.",
            reasoning_summary="AI verification failed and explicit demo fallback was enabled.",
            raw_provider="fallback",
            raw_model="ai-fallback-v1",
        ).model_dump()

    def _completion_response(
        self,
        gig: dict,
        verification: dict | None,
        payment: dict | None,
        kid_balance: dict | None,
    ) -> dict:
        ai_mode = self._ai_response_mode(verification)
        payment_mode = getattr(self.payment_service.payment_client, "mode", "fake_local")
        mode = self._response_mode(ai_mode, payment_mode)
        return {
            "gig": gig,
            "verification": self._public_verification(verification) if verification else None,
            "payment": self._public_payment(payment) if payment else None,
            "kid_balance": kid_balance,
            "mode": mode,
            "ai_mode": ai_mode,
            "payment_mode": payment_mode,
            "fallback_mode": mode in ("ai_fallback", "bunq_fallback"),
        }

    def _ai_response_mode(self, verification: dict | None) -> str:
        verification_provider = (verification or {}).get("raw_provider")
        if verification_provider == "fallback":
            return "fallback"
        if verification_provider == "fake":
            return "fake"
        return "real"

    def _response_mode(self, ai_mode: str, payment_mode: str) -> str:
        if ai_mode == "fallback":
            return "ai_fallback"
        if payment_mode == "bunq_fallback":
            return "bunq_fallback"
        if payment_mode == "fake_local":
            return "fake_local"
        if ai_mode == "fake":
            return "fake_ai"
        return "real"

    def _paid_response(self, state: dict, gig: dict) -> dict:
        verification = state["verification_results"].get(gig.get("verification_result_id"))
        payment = state["payments"].get(gig.get("payment_id"))
        return self._completion_response(
            gig,
            verification,
            payment,
            state["balances"]["kid_001"],
        )

    def _public_verification(self, verification: dict) -> dict:
        return {
            "approved": verification["approved"],
            "confidence": verification["confidence"],
            "tags": verification["tags"],
            "message_for_kid": verification["message_for_kid"],
        }

    def _public_payment(self, payment: dict) -> dict:
        public_payment = {
            "status": payment["status"],
            "amount": payment["amount"],
            "currency": payment["currency"],
            "bunq_payment_id": payment.get("bunq_payment_id"),
            "retryable": payment.get("retryable", payment["status"] == "failed"),
        }
        if payment.get("error_code"):
            public_payment["error_code"] = payment["error_code"]
        return public_payment
