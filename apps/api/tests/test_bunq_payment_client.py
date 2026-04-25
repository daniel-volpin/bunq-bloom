import pytest

from app.errors import AppError
from app.integrations.bunq_payment_client import BunqPaymentClient
from app.settings import Settings


class FakeBunqToolkitClient:
    user_id = 42

    def __init__(self, *, fail_post: bool = False, include_iban: bool = True, malformed_post_response: bool = False):
        self.fail_post = fail_post
        self.include_iban = include_iban
        self.malformed_post_response = malformed_post_response
        self.posts = []

    def get(self, endpoint: str):
        assert endpoint == "user/42/monetary-account-bank"
        kid_aliases = []
        if self.include_iban:
            kid_aliases.append({"type": "IBAN", "value": "NL00BUNQ0123456789"})
        return [
            {
                "MonetaryAccountBank": {
                    "id": 100,
                    "alias": [{"type": "IBAN", "value": "NL00BUNQ0000000001"}],
                    "balance": {"value": "100.00", "currency": "EUR"},
                }
            },
            {
                "MonetaryAccountBank": {
                    "id": 200,
                    "alias": kid_aliases,
                    "balance": {"value": "27.50", "currency": "EUR"},
                }
            },
        ]

    def post(self, endpoint: str, body: dict):
        if self.fail_post:
            raise RuntimeError("sandbox unavailable")
        self.posts.append((endpoint, body))
        if self.malformed_post_response:
            return [{"Unexpected": {"id": 12345}}]
        return [{"Id": {"id": 12345}}]


def make_client(fake_toolkit_client: FakeBunqToolkitClient) -> BunqPaymentClient:
    settings = Settings(
        BUNQ_API_KEY="sandbox-api-key",
        BUNQ_PARENT_ACCOUNT_ID="100",
        BUNQ_KID_ACCOUNT_ID="200",
    )
    client = BunqPaymentClient(settings)
    client._client = fake_toolkit_client
    return client


def test_bunq_payment_client_creates_parent_to_kid_payment():
    fake_toolkit_client = FakeBunqToolkitClient()
    client = make_client(fake_toolkit_client)

    result = client.create_parent_to_kid_payment(
        amount="5.00",
        currency="EUR",
        description="bunq Bloom reward: Clean your room",
        idempotency_key="gig_001:attempt-001",
    )

    assert result["status"] == "succeeded"
    assert result["bunq_payment_id"] == "12345"
    assert fake_toolkit_client.posts == [
        (
            "user/42/monetary-account/100/payment",
            {
                "amount": {"value": "5.00", "currency": "EUR"},
                "counterparty_alias": {
                    "type": "IBAN",
                    "value": "NL00BUNQ0123456789",
                    "name": "Bloom Kid",
                },
                "description": "bunq Bloom reward: Clean your room",
            },
        )
    ]


def test_bunq_payment_client_gets_kid_balance():
    client = make_client(FakeBunqToolkitClient())

    assert client.get_kid_balance() == {
        "amount": "27.50",
        "currency": "EUR",
        "source": "bunq",
    }


def test_bunq_payment_client_requires_kid_iban_alias():
    client = make_client(FakeBunqToolkitClient(include_iban=False))

    with pytest.raises(AppError) as exc:
        client.create_parent_to_kid_payment(
            amount="5.00",
            currency="EUR",
            description="bunq Bloom reward: Clean your room",
            idempotency_key="gig_001:attempt-001",
        )

    assert exc.value.code == "payment_failed"
    assert exc.value.status_code == 500


def test_bunq_payment_client_maps_payment_failure_to_retryable_error():
    client = make_client(FakeBunqToolkitClient(fail_post=True))

    with pytest.raises(AppError) as exc:
        client.create_parent_to_kid_payment(
            amount="5.00",
            currency="EUR",
            description="bunq Bloom reward: Clean your room",
            idempotency_key="gig_001:attempt-001",
        )

    assert exc.value.code == "payment_failed"
    assert exc.value.status_code == 502
    assert exc.value.retryable is True


def test_bunq_payment_client_maps_malformed_payment_response_to_non_retryable_unknown_state():
    client = make_client(FakeBunqToolkitClient(malformed_post_response=True))

    with pytest.raises(AppError) as exc:
        client.create_parent_to_kid_payment(
            amount="5.00",
            currency="EUR",
            description="bunq Bloom reward: Clean your room",
            idempotency_key="gig_001:attempt-001",
        )

    assert exc.value.code == "payment_state_unknown"
    assert exc.value.status_code == 502
    assert exc.value.retryable is False
