import sys
from pathlib import Path
from typing import Any

from app.errors import AppError
from app.settings import Settings


class BunqPaymentClient:
    """Real bunq sandbox adapter using the hackathon toolkit.

    This adapter is opt-in. FakePaymentClient remains the default for local M1
    development so the core loop works without credentials.
    """

    mode = "real"

    def __init__(self, settings: Settings):
        self.settings = settings
        if not settings.bunq_api_key:
            raise AppError("payment_failed", "BUNQ_API_KEY is not configured.", status_code=500)
        if not settings.bunq_parent_account_id or not settings.bunq_kid_account_id:
            raise AppError(
                "payment_failed",
                "BUNQ_PARENT_ACCOUNT_ID and BUNQ_KID_ACCOUNT_ID are required.",
                status_code=500,
            )
        self.parent_account_id = settings.bunq_parent_account_id
        self.kid_account_id = settings.bunq_kid_account_id
        self._client = None

    def create_parent_to_kid_payment(
        self,
        *,
        amount: str,
        currency: str,
        description: str,
        idempotency_key: str,
    ) -> dict:
        client = self._get_client()
        kid_alias = self._get_kid_account_iban(client)

        try:
            response = client.post(
                f"user/{client.user_id}/monetary-account/{self.parent_account_id}/payment",
                {
                    "amount": {"value": amount, "currency": currency},
                    "counterparty_alias": {
                        "type": "IBAN",
                        "value": kid_alias,
                        "name": "Bloom Kid",
                    },
                    "description": description,
                },
            )
        except Exception as exc:
            raise AppError(
                "payment_failed",
                "bunq sandbox payment failed.",
                status_code=502,
                retryable=True,
            ) from exc

        try:
            bunq_payment_id = str(response[0]["Id"]["id"])
        except (IndexError, KeyError, TypeError) as exc:
            raise AppError(
                "payment_state_unknown",
                "bunq sandbox payment response could not be parsed.",
                status_code=502,
                retryable=False,
            ) from exc

        return {
            "status": "succeeded",
            "amount": amount,
            "currency": currency,
            "bunq_payment_id": bunq_payment_id,
            "description": description,
            "idempotency_key": idempotency_key,
        }

    def get_kid_balance(self, state: dict | None = None) -> dict:
        client = self._get_client()
        kid_account = self._get_account(client, self.kid_account_id)
        balance = kid_account.get("balance", {})
        return {
            "amount": balance.get("value", "0.00"),
            "currency": balance.get("currency", "EUR"),
            "source": "bunq",
        }

    def _get_client(self) -> Any:
        if self._client:
            return self._client

        toolkit_path = self._resolve_toolkit_path()
        if str(toolkit_path) not in sys.path:
            sys.path.insert(0, str(toolkit_path))

        try:
            from bunq_client import BunqClient
        except ImportError as exc:
            raise AppError(
                "payment_failed",
                "bunq hackathon toolkit could not be imported.",
                status_code=500,
            ) from exc

        client = BunqClient(api_key=self.settings.bunq_api_key, sandbox=True)
        client.authenticate()
        self._client = client
        return client

    def _resolve_toolkit_path(self) -> Path:
        path = self.settings.resolved_bunq_toolkit_path()
        if not (path / "bunq_client.py").exists():
            raise AppError(
                "payment_failed",
                "bunq hackathon toolkit path is invalid.",
                status_code=500,
            )
        return path

    def _get_kid_account_iban(self, client: Any) -> str:
        account = self._get_account(client, self.kid_account_id)
        for alias in account.get("alias", []):
            if alias.get("type") == "IBAN" and alias.get("value"):
                return alias["value"]
        raise AppError(
            "payment_failed",
            "Kid bunq account does not expose an IBAN alias.",
            status_code=500,
        )

    def _get_account(self, client: Any, account_id: str | None) -> dict:
        accounts = client.get(f"user/{client.user_id}/monetary-account-bank")
        for item in accounts:
            account = item.get("MonetaryAccountBank", {})
            if str(account.get("id")) == str(account_id):
                return account
        raise AppError("payment_failed", "Configured bunq account was not found.", status_code=500)
