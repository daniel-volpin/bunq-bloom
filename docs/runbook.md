# Runbook

This runbook covers the current backend posture: real AI is expected when AI-backed flows are exercised, while bunq can still run in fake mode during integration hardening.

## Local LM Studio Mode

Backend:

```bash
cd apps/api
cp .env.example .env
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend `.env` values for local frontend integration should be:

```text
BLOOM_AI_PROVIDER=lmstudio
BLOOM_LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
BLOOM_LMSTUDIO_MODEL=<your-vision-model-id>
BLOOM_USE_FAKE_BUNQ=true
```

Notes:

- LM Studio is now a real readiness dependency for AI-backed flows.
- The configured LM Studio model must be vision-capable for before/after verification and Snap & Learn.
- If `BLOOM_LMSTUDIO_MODEL` is missing, `/api/health` reports AI as `not_configured` and backend readiness as `not_ready`.
- `BLOOM_USE_FAKE_BUNQ=true` still keeps bunq in fake mode while the real bunq sandbox path is hardened.

Frontend:

```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

The frontend calls relative `/api/*` routes. Next.js proxies those requests to FastAPI through `API_BASE_URL`.

Open:

```text
http://localhost:3000/gigs
```

Expected smoke test:

```text
health ok
gig list loads
kid claims seeded gig
before photo accepted
after photo accepted
LM Studio verification returns a structured result
fake payment succeeds
verdict screen shows updated fake balance
response shows `mode=fake_local`, `ai_mode=real`, and `payment_mode=fake_local`
```

Health expectations in this mode:

```text
ai configured
bunq configured in fake mode
readiness ready
```

Backend test command:

```bash
cd apps/api
pytest tests
```

Frontend check commands:

```bash
cd apps/web
npm run typecheck
npm run lint
```

## Real bunq Smoke Test

Only run when explicitly working on bunq integration.

Preconditions:

- `BUNQ_API_KEY` configured locally.
- `bunq_context.json` ignored and local only.

Prepare sandbox accounts:

```bash
cd apps/api
python scripts/setup_bunq_sandbox.py
```

If you need the helper to create Bloom accounts and request sandbox funds:

```bash
cd apps/api
python scripts/setup_bunq_sandbox.py --create-missing-accounts --fund-parent 500.00
```

The setup helper prints only non-secret account IDs. Add those values to `apps/api/.env`:

```text
BLOOM_USE_FAKE_BUNQ=false
BUNQ_PARENT_ACCOUNT_ID=...
BUNQ_KID_ACCOUNT_ID=...
BUNQ_KID_ACCOUNT_IBAN=...
```

Expected smoke test:

```text
health reports bunq configured
backend fetches kid balance
backend creates tiny sandbox payment
backend fetches updated kid balance
```

The tiny payment smoke is intentionally behind a second flag because it creates a real sandbox transfer:

```bash
cd apps/api
export BLOOM_RUN_SMOKE_TESTS=true
export BLOOM_RUN_BUNQ_PAYMENT_SMOKE=true
export BLOOM_BUNQ_SMOKE_PAYMENT_AMOUNT=0.01
pytest tests/test_integration_smoke.py::test_bunq_tiny_payment_smoke -q
```

## Opt-In Real Provider Smoke Tests

These smoke checks are excluded from default test runs.

Enable them explicitly:

```bash
cd apps/api
export BLOOM_RUN_SMOKE_TESTS=true
pytest tests/test_integration_smoke.py -q
```

LM Studio smoke test requires:

```text
BLOOM_LMSTUDIO_BASE_URL
BLOOM_LMSTUDIO_MODEL
```

Optional:

```text
BLOOM_LMSTUDIO_API_KEY
```

bunq smoke test requires:

```text
BUNQ_API_KEY
BUNQ_PARENT_ACCOUNT_ID
BUNQ_KID_ACCOUNT_ID
BLOOM_BUNQ_TOOLKIT_PATH
```

Recommended:

```text
BUNQ_KID_ACCOUNT_IBAN
```

`BUNQ_PARENT_ACCOUNT_ID`, `BUNQ_KID_ACCOUNT_ID`, and `BUNQ_KID_ACCOUNT_IBAN` can be selected by `python scripts/setup_bunq_sandbox.py`. Keeping the kid IBAN in local config avoids one bunq account-list request before every payment.

Tiny bunq payment smoke test additionally requires:

```text
BLOOM_RUN_BUNQ_PAYMENT_SMOKE=true
```

Expected default result without configuration:

```text
3 skipped
```

## Reset Local State

Local state lives under `apps/api/data/` by default.

Reset app state:

```bash
rm -rf apps/api/data
```

Only delete `bunq_context.json` when re-authentication is needed. Never commit or display that file.

## Troubleshooting

Known categories to document during implementation:

- backend dependency install failure
- frontend dependency install failure
- CORS/proxy mismatch
- image too large
- invalid image type
- AI unavailable
- bunq 401/403/429/400
- duplicate completion attempt
- payment succeeded but balance refresh failed
- payment response shape unknown
- payment rate limit or network failure
- payment reconciliation by bunq payment id or merchant reference

## Current Environment Note

In the current Codex environment, backend tests pass. Node/npm are not installed in PATH, so frontend typecheck and lint could not be run here.
