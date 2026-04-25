# Runbook

This runbook covers the current local LM Studio AI plus fake bunq payment setup.

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

Backend `.env` defaults should be:

```text
BLOOM_AI_PROVIDER=lmstudio
BLOOM_LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
BLOOM_LMSTUDIO_MODEL=qwen3.5-9b-mlx
BLOOM_USE_FAKE_BUNQ=true
```

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
- `BUNQ_PARENT_ACCOUNT_ID` configured locally.
- `BUNQ_KID_ACCOUNT_ID` configured locally.
- `bunq_context.json` ignored and local only.

Expected smoke test:

```text
health reports bunq configured
backend fetches kid balance
backend creates tiny sandbox payment
backend fetches updated kid balance
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

## Current Environment Note

In the current Codex environment, backend tests pass. Node/npm are not installed in PATH, so frontend typecheck and lint could not be run here.
