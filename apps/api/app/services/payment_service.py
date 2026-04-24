from app.models.domain import money_add, new_id, now_iso


class PaymentService:
    def __init__(self, payment_client):
        self.payment_client = payment_client

    def pay_for_gig(self, *, state: dict, gig: dict, idempotency_key: str) -> tuple[dict, dict]:
        payment_result = self.payment_client.create_parent_to_kid_payment(
            amount=gig["reward_amount"],
            currency=gig["currency"],
            description=f"bunq Bloom reward: {gig['title']}",
            idempotency_key=idempotency_key,
        )
        payment_id = new_id("payment")
        now = now_iso()
        payment = {
            "id": payment_id,
            "gig_id": gig["id"],
            "amount": gig["reward_amount"],
            "currency": gig["currency"],
            "from_monetary_account_id": getattr(self.payment_client, "parent_account_id", "unknown"),
            "to_monetary_account_id": getattr(self.payment_client, "kid_account_id", "unknown"),
            "bunq_payment_id": payment_result["bunq_payment_id"],
            "status": payment_result["status"],
            "created_at": now,
            "updated_at": now,
        }
        state["payments"][payment_id] = payment

        if getattr(self.payment_client, "mode", "fake_local") == "fake_local":
            kid_balance = state["balances"]["kid_001"]
            kid_balance["amount"] = money_add(kid_balance["amount"], gig["reward_amount"])
            kid_balance["source"] = "fake"
        else:
            kid_balance = self.payment_client.get_kid_balance(state)
            state["balances"]["kid_001"] = kid_balance
        return payment, kid_balance

    def record_failed_payment(self, *, state: dict, gig: dict, error_code: str) -> dict:
        payment_id = new_id("payment")
        now = now_iso()
        payment = {
            "id": payment_id,
            "gig_id": gig["id"],
            "amount": gig["reward_amount"],
            "currency": gig["currency"],
            "from_monetary_account_id": getattr(self.payment_client, "parent_account_id", "unknown"),
            "to_monetary_account_id": getattr(self.payment_client, "kid_account_id", "unknown"),
            "bunq_payment_id": None,
            "status": "failed",
            "error_code": error_code,
            "created_at": now,
            "updated_at": now,
        }
        state["payments"][payment_id] = payment
        return payment

    def get_kid_balance(self, state: dict) -> dict:
        if getattr(self.payment_client, "mode", "fake_local") == "fake_local":
            return state["balances"]["kid_001"]
        balance = self.payment_client.get_kid_balance(state)
        state["balances"]["kid_001"] = balance
        return balance
