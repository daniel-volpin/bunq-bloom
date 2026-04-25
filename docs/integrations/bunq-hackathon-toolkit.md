# bunq Hackathon Toolkit Reference

This doc is the working guide for using bunq's local hackathon toolkit inside bunq Bloom.

Local path:

```text
hackathon_toolkit-main/
```

The toolkit is currently vendored as reference code in this repository. Treat it as an external dependency/reference unless Daniel explicitly asks to modify it.

## Toolkit Structure

Important files:

- `hackathon_toolkit-main/bunq_client.py`: lightweight bunq API client for auth, request signing, HTTP calls, and context caching.
- `hackathon_toolkit-main/01_authentication.py`: creates or uses a sandbox API key and authenticates.
- `hackathon_toolkit-main/02_create_monetary_account.py`: creates and lists bank accounts.
- `hackathon_toolkit-main/03_list_monetary_accounts.py`: lists monetary accounts and balances.
- `hackathon_toolkit-main/03_make_payment.py`: requests sandbox funds and creates a payment.
- `hackathon_toolkit-main/06_list_transactions.py`: lists recent payments.
- `hackathon_toolkit-main/docs/API_REFERENCE.md`: endpoint and header cheat sheet.
- `hackathon_toolkit-main/docs/TROUBLESHOOTING.md`: common failures and fixes.

## Agent Rules

- Do not read `.env`, credential, private key, or token files.
- Prefer wrapping toolkit calls in our own adapter instead of importing toolkit internals throughout the backend.
- Keep all bunq calls server-side. The Next.js frontend must never receive bunq API keys, private keys, installation tokens, or session data.
- Use bunq sandbox only unless explicitly instructed otherwise.
- Do not mark a gig as `paid` unless the bunq payment succeeds or the API response explicitly says `fallback_mode: true`.
- Do not run toolkit scripts that create users, accounts, payment requests, or payments unless that is the current task.
- Do not print or persist API keys in docs, code, logs, issues, or PRs.

## What The Toolkit Handles

`BunqClient` handles:

- sandbox base URL: `https://public-api.sandbox.bunq.com`
- production base URL: `https://api.bunq.com`
- RSA keypair generation
- `/installation`
- `/device-server`
- `/session-server`
- request body signing for POST/PUT
- session/context caching in `bunq_context.json`
- simple `get`, `post`, `put`, and `delete` helpers
- `get_primary_account_id()` convenience helper

Authentication flow:

```text
BUNQ_API_KEY
  -> POST /installation
  -> POST /device-server
  -> POST /session-server
  -> cached context in bunq_context.json
```

## Secret Handling

`bunq_client.py` writes `bunq_context.json`.

That file contains sensitive material:

- API key
- private RSA key
- installation token
- session token
- user id

Never commit or display this file. The root `.gitignore` excludes `**/bunq_context.json`, `*.key`, and `*.pem`.

## Integration Boundary

Our backend should expose a small payment interface independent of toolkit details:

```python
class PaymentClient:
    def create_parent_to_kid_payment(
        self,
        amount: str,
        currency: str,
        description: str,
        idempotency_key: str,
    ) -> PaymentResult:
        ...

    def get_kid_balance(self) -> Balance:
        ...
```

Implementation options:

- `FakePaymentClient` for local M1 development.
- `BunqSandboxPaymentClient` for real sandbox integration.

Do not let route handlers call the toolkit directly. Route handlers should call application services, and services should call the payment client interface.

## Required Operations

The core loop only needs three bunq capabilities:

- Resolve configured parent and kid monetary accounts.
- Create a payment from parent to kid after AI approval.
- Fetch the kid account balance after payment.

Anything beyond that is deferred unless required for the core loop.

## Bloom Account Model

Use one bunq sandbox user with two monetary accounts for MVP:

- parent account: source of gig reward payments
- kid account: destination for earned rewards

Configure:

- `BUNQ_PARENT_ACCOUNT_ID`
- `BUNQ_KID_ACCOUNT_ID`

Use the setup helper to select/create these accounts without printing secrets:

```bash
cd apps/api
python scripts/setup_bunq_sandbox.py
python scripts/setup_bunq_sandbox.py --create-missing-accounts --fund-parent 500.00
```

This avoids managing two API keys and two session contexts. If bunq sandbox rejects same-user account transfers, keep the Bloom `PaymentClient` interface and change only the bunq adapter internals to support two sandbox users.

## Endpoint Cheatsheet For Bloom

List bank accounts:

```text
GET /v1/user/{userId}/monetary-account-bank
```

List all monetary accounts:

```text
GET /v1/user/{userId}/monetary-account
```

Create EUR bank account:

```json
{
  "currency": "EUR",
  "description": "Bloom Kid Account"
}
```

Create payment:

```text
POST /v1/user/{userId}/monetary-account/{accountId}/payment
```

```json
{
  "amount": {
    "value": "5.00",
    "currency": "EUR"
  },
  "counterparty_alias": {
    "type": "IBAN",
    "value": "{kid_account_iban_from_bunq}",
    "name": "Bloom Kid"
  },
  "description": "bunq Bloom reward: Clean your room"
}
```

Use the kid account alias returned by bunq account listing. If the sandbox setup uses a separate kid user instead of a second monetary account, use that user's supported alias instead.

Request sandbox funds:

```text
POST /v1/user/{userId}/monetary-account/{accountId}/request-inquiry
```

```json
{
  "amount_inquired": {
    "value": "500.00",
    "currency": "EUR"
  },
  "counterparty_alias": {
    "type": "EMAIL",
    "value": "sugardaddy@bunq.com",
    "name": "Sugar Daddy"
  },
  "description": "Hackathon test funds",
  "allow_bunqme": false
}
```

List payments:

```text
GET /v1/user/{userId}/monetary-account/{accountId}/payment?count=20
```

## State And Files

Expected local files:

- `bunq_context.json`: toolkit session/cache file, never commit.
- `.env`: local credentials, never read or commit.
- `data/state.json`: our local MVP app state.

The app should store only the bunq payment id/reference and high-level status in local state.

Do not store:

- API keys
- private keys
- installation tokens
- session tokens
- full signed request data

## Rate Limits And Demo Safety

Toolkit docs list these limits:

- GET: 3 requests per 3 seconds
- POST: 5 requests per 3 seconds
- PUT: 2 requests per 3 seconds
- `/session-server`: 1 request per 30 seconds

Implications:

- Reuse `bunq_context.json` during local runs.
- Avoid repeated session creation in health checks.
- Cache account IDs after resolving them.
- Keep balance refreshes targeted.
- Add retry/backoff only around safe operations.

## Payment Safety

Payment flow rules:

- AI approval must happen before payment creation.
- Payment creation must be idempotent at the bunq adapter boundary.
- A gig can have at most one successful payment.
- Retrying after `payment_failed` must not re-run AI if verification already passed.
- The completion endpoint must return payment status clearly: `succeeded`, `failed`, or `fallback`.

## Backend Smoke Test Goal

Once credentials are configured, the minimum real bunq smoke test is:

```text
health check -> fetch kid balance -> create tiny sandbox payment -> fetch updated kid balance
```

This should be opt-in and never run by default in unit tests.

The tiny payment smoke test has a second explicit guard because it creates a sandbox transfer:

```bash
cd apps/api
BLOOM_RUN_SMOKE_TESTS=true BLOOM_RUN_BUNQ_PAYMENT_SMOKE=true pytest tests/test_integration_smoke.py::test_bunq_tiny_payment_smoke -q
```

## Troubleshooting Notes

- HTTP 401 usually means the session expired. Delete `bunq_context.json` and re-authenticate.
- HTTP 403 can mean device/IP registration mismatch. Re-authenticate.
- HTTP 429 means rate limit. Wait and avoid unnecessary session creation.
- HTTP 400 usually means a malformed body, especially amount or counterparty alias fields.
- "No active monetary account found" means an account must be created or selected explicitly.
