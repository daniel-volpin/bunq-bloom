from app.models.domain import new_id


class FakePaymentClient:
    mode = "fake_local"
    parent_account_id = "fake_parent_account"
    kid_account_id = "fake_kid_account"

    def create_parent_to_kid_payment(
        self,
        *,
        amount: str,
        currency: str,
        description: str,
        idempotency_key: str,
    ) -> dict:
        return {
            "status": "succeeded",
            "amount": amount,
            "currency": currency,
            "bunq_payment_id": f"fake_{new_id('payment')}",
            "description": description,
            "idempotency_key": idempotency_key,
        }

    def get_kid_balance(self, state: dict | None = None) -> dict:
        if state:
            return state["balances"]["kid_001"]
        return {"amount": "22.50", "currency": "EUR", "source": "fake"}
