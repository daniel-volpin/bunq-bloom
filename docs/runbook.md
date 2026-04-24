# Runbook

This runbook is a placeholder until the frontend and backend are scaffolded. Do not invent commands before code exists.

## Local Fake Mode

To be filled after scaffolding:

- install backend dependencies
- install frontend dependencies
- create local `.env` files from `.env.example`
- start FastAPI backend with fake AI and fake bunq
- start Next.js frontend
- complete the seeded fake gig loop

Expected smoke test:

```text
health ok
gig list loads
kid claims seeded gig
before photo accepted
after photo accepted
fake verification approves
fake payment succeeds
verdict screen shows updated fake balance
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

To be filled after storage paths are implemented.

Expected reset scope:

- delete local app state under `data/`
- optionally delete `bunq_context.json` only when re-authentication is needed
- never delete real source files

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

