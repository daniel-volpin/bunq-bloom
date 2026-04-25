import pytest
from requests import ConnectionError, HTTPError, Response

import app.integrations.bunq_payment_client as bunq_module
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
        self.get_calls = 0

    def get(self, endpoint: str):
        assert endpoint == "user/42/monetary-account-bank"
        self.get_calls += 1
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


class HttpErrorBunqToolkitClient(FakeBunqToolkitClient):
    def __init__(self, status_code: int):
        super().__init__()
        self.status_code = status_code

    def post(self, endpoint: str, body: dict):
        response = Response()
        response.status_code = self.status_code
        error = HTTPError(f"{self.status_code} error")
        error.response = response
        raise error


class FlakyGetBunqToolkitClient(FakeBunqToolkitClient):
    def get(self, endpoint: str):
        if self.get_calls == 0:
            self.get_calls += 1
            response = Response()
            response.status_code = 429
            error = HTTPError("429 error")
            error.response = response
            raise error
        return super().get(endpoint)


def make_client(fake_toolkit_client: FakeBunqToolkitClient) -> BunqPaymentClient:
    settings = Settings(
        BUNQ_API_KEY="sandbox-api-key",
        BUNQ_PARENT_ACCOUNT_ID="100",
        BUNQ_KID_ACCOUNT_ID="200",
        BUNQ_KID_ACCOUNT_IBAN="",
    )
    client = BunqPaymentClient(settings)
    client._client = fake_toolkit_client
    return client


def make_client_with_kid_iban(fake_toolkit_client: FakeBunqToolkitClient) -> BunqPaymentClient:
    settings = Settings(
        BUNQ_API_KEY="sandbox-api-key",
        BUNQ_PARENT_ACCOUNT_ID="100",
        BUNQ_KID_ACCOUNT_ID="200",
        BUNQ_KID_ACCOUNT_IBAN="NL00BUNQCONFIGUREDIBAN",
    )
    client = BunqPaymentClient(settings)
    client._client = fake_toolkit_client
    return client


class FailingAuthBunqClient:
    def __init__(self, *, api_key: str, sandbox: bool):
        self.api_key = api_key
        self.sandbox = sandbox

    def authenticate(self):
        raise ConnectionError("DNS unavailable")


class ImportableFailingAuthPaymentClient(BunqPaymentClient):
    def _resolve_toolkit_path(self):
        return self.settings.resolved_bunq_toolkit_path()


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


def test_bunq_payment_client_uses_configured_kid_iban_without_account_lookup():
    fake_toolkit_client = FakeBunqToolkitClient(include_iban=False)
    client = make_client_with_kid_iban(fake_toolkit_client)

    result = client.create_parent_to_kid_payment(
        amount="5.00",
        currency="EUR",
        description="bunq Bloom reward: Clean your room",
        idempotency_key="gig_001:attempt-001",
    )

    assert result["status"] == "succeeded"
    assert fake_toolkit_client.get_calls == 0
    assert fake_toolkit_client.posts[0][1]["counterparty_alias"]["value"] == "NL00BUNQCONFIGUREDIBAN"


def test_bunq_payment_client_gets_kid_balance():
    client = make_client(FakeBunqToolkitClient())

    assert client.get_kid_balance() == {
        "amount": "27.50",
        "currency": "EUR",
        "source": "bunq",
    }


def test_bunq_payment_client_retries_safe_account_reads(monkeypatch):
    monkeypatch.setattr(bunq_module, "SAFE_READ_RETRY_DELAYS_SECONDS", (0,))
    fake_toolkit_client = FlakyGetBunqToolkitClient()
    client = make_client(fake_toolkit_client)

    assert client.get_kid_balance()["amount"] == "27.50"
    assert fake_toolkit_client.get_calls == 2


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


def test_bunq_payment_client_maps_auth_network_failure_to_retryable_error(monkeypatch, tmp_path):
    toolkit_path = tmp_path / "toolkit"
    toolkit_path.mkdir()
    (toolkit_path / "bunq_client.py").write_text(
        "from tests.test_bunq_payment_client import FailingAuthBunqClient as BunqClient\n",
        encoding="utf-8",
    )
    settings = Settings(
        BUNQ_API_KEY="sandbox-api-key",
        BUNQ_PARENT_ACCOUNT_ID="100",
        BUNQ_KID_ACCOUNT_ID="200",
        BLOOM_BUNQ_TOOLKIT_PATH=toolkit_path,
    )
    client = BunqPaymentClient(settings)

    with pytest.raises(AppError) as exc:
        client.create_parent_to_kid_payment(
            amount="5.00",
            currency="EUR",
            description="bunq Bloom reward: Clean your room",
            idempotency_key="gig_001:attempt-001",
        )

    assert exc.value.code == "payment_network_failed"
    assert exc.value.status_code == 502
    assert exc.value.retryable is True


@pytest.mark.parametrize(
    ("status_code", "expected_code", "retryable"),
    [
        (400, "payment_bad_request", False),
        (401, "payment_auth_failed", True),
        (403, "payment_auth_failed", True),
        (429, "payment_rate_limited", True),
        (500, "payment_failed", True),
    ],
)
def test_bunq_payment_client_maps_payment_http_errors(status_code, expected_code, retryable):
    client = make_client(HttpErrorBunqToolkitClient(status_code))

    with pytest.raises(AppError) as exc:
        client.create_parent_to_kid_payment(
            amount="5.00",
            currency="EUR",
            description="bunq Bloom reward: Clean your room",
            idempotency_key="gig_001:attempt-001",
        )

    assert exc.value.code == expected_code
    assert exc.value.retryable is retryable
