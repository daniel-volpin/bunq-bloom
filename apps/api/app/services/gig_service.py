from app.errors import AppError
from app.integrations.fake_verification_client import FakeVerificationClient
from app.models.domain import new_id, now_iso
from app.repositories.photo_repository import PhotoRepository
from app.repositories.state_repository import StateRepository
from app.services.payment_service import PaymentService


class GigService:
    def __init__(
        self,
        *,
        state_repository: StateRepository,
        photo_repository: PhotoRepository,
        verification_client: FakeVerificationClient,
        payment_service: PaymentService,
    ):
        self.state_repository = state_repository
        self.photo_repository = photo_repository
        self.verification_client = verification_client
        self.payment_service = payment_service

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
        state = self.state_repository.load()
        state["gigs"][gig_id] = gig
        self.state_repository.save(state)
        return {"gig": gig}

    def claim_gig(self, gig_id: str) -> dict:
        state = self.state_repository.load()
        gig = self._get_gig(state, gig_id)
        if gig["status"] != "open":
            raise AppError("invalid_gig_state", "Only open gigs can be claimed.")
        gig["status"] = "claimed"
        gig["claimed_by_user_id"] = "kid_001"
        gig["updated_at"] = now_iso()
        self.state_repository.save(state)
        return {"gig": gig}

    def add_before_photo(self, gig_id: str, image_base64: str) -> dict:
        state = self.state_repository.load()
        gig = self._get_gig(state, gig_id)
        if gig["status"] not in {"claimed", "rejected"}:
            raise AppError("invalid_gig_state", "Before photo can only be added after claiming.")

        photo = self.photo_repository.save_data_url(image_base64, gig_id=gig_id, kind="before")
        photo["created_at"] = now_iso()
        state["photos"][photo["id"]] = photo
        gig["before_photo_id"] = photo["id"]
        gig["status"] = "awaiting_after_photo"
        gig["updated_at"] = now_iso()
        self.state_repository.save(state)
        return {"gig": gig}

    def complete_gig(self, gig_id: str, *, after_image_base64: str, idempotency_key: str) -> dict:
        attempt_id = f"{gig_id}:{idempotency_key}"
        state = self.state_repository.load()
        if attempt_id in state["completion_attempts"]:
            return state["completion_attempts"][attempt_id]["response"]

        gig = self._get_gig(state, gig_id)
        if gig["status"] == "paid":
            return self._paid_response(state, gig)
        if gig["status"] not in {"awaiting_after_photo", "payment_failed"}:
            raise AppError("invalid_gig_state", "Gig is not ready for completion.")
        if not gig.get("before_photo_id"):
            raise AppError("missing_before_photo", "Add a before photo before completing the gig.")

        before_photo = state["photos"][gig["before_photo_id"]]
        after_photo = self.photo_repository.save_data_url(after_image_base64, gig_id=gig_id, kind="after")
        after_photo["created_at"] = now_iso()
        state["photos"][after_photo["id"]] = after_photo
        gig["after_photo_id"] = after_photo["id"]
        gig["status"] = "verifying"
        gig["updated_at"] = now_iso()

        verification = self.verification_client.verify(
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
            response = self._completion_response(gig, verification, None, None, mode="fake_local")
            self._store_attempt(state, attempt_id, response, verification["id"], None, after_photo["id"])
            self.state_repository.save(state)
            return response

        gig["status"] = "approved"
        payment, kid_balance = self.payment_service.pay_for_gig(
            state=state,
            gig=gig,
            idempotency_key=attempt_id,
        )
        gig["payment_id"] = payment["id"]
        gig["status"] = "paid"
        gig["updated_at"] = now_iso()
        response = self._completion_response(
            gig,
            verification,
            payment,
            kid_balance,
            mode=getattr(self.payment_service.payment_client, "mode", "fake_local"),
        )
        self._store_attempt(state, attempt_id, response, verification["id"], payment["id"], after_photo["id"])
        self.state_repository.save(state)
        return response

    def get_kid_balance(self) -> dict:
        state = self.state_repository.load()
        balance = self.payment_service.get_kid_balance(state)
        self.state_repository.save(state)
        return {
            "balance": balance,
            "mode": getattr(self.payment_service.payment_client, "mode", "fake_local"),
            "fallback_mode": False,
        }

    def _get_gig(self, state: dict, gig_id: str) -> dict:
        try:
            return state["gigs"][gig_id]
        except KeyError as exc:
            raise AppError("gig_not_found", "Gig was not found.", status_code=404) from exc

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

    def _completion_response(
        self,
        gig: dict,
        verification: dict | None,
        payment: dict | None,
        kid_balance: dict | None,
        *,
        mode: str,
    ) -> dict:
        return {
            "gig": gig,
            "verification": self._public_verification(verification) if verification else None,
            "payment": self._public_payment(payment) if payment else None,
            "kid_balance": kid_balance,
            "mode": mode,
            "fallback_mode": False,
        }

    def _paid_response(self, state: dict, gig: dict) -> dict:
        verification = state["verification_results"].get(gig.get("verification_result_id"))
        payment = state["payments"].get(gig.get("payment_id"))
        return self._completion_response(
            gig,
            verification,
            payment,
            state["balances"]["kid_001"],
            mode=getattr(self.payment_service.payment_client, "mode", "fake_local"),
        )

    def _public_verification(self, verification: dict) -> dict:
        return {
            "approved": verification["approved"],
            "confidence": verification["confidence"],
            "tags": verification["tags"],
            "message_for_kid": verification["message_for_kid"],
        }

    def _public_payment(self, payment: dict) -> dict:
        return {
            "status": payment["status"],
            "amount": payment["amount"],
            "currency": payment["currency"],
            "bunq_payment_id": payment["bunq_payment_id"],
        }
