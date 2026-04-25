# Pre-Implementation Decisions

These decisions remove ambiguity before scaffolding code. Revisit only when a real constraint invalidates them.

## Decision 1: bunq Sandbox Account Model

Use one bunq sandbox user with two monetary accounts:

- parent monetary account
- kid monetary account

Rationale:

- Simplest setup for a hackathon MVP.
- Avoids managing two sandbox API keys and two session contexts.
- Still demonstrates real money movement between accounts.
- Easier to seed, inspect, reset, and explain to developers.

Implementation notes:

- Store `BUNQ_PARENT_ACCOUNT_ID` and `BUNQ_KID_ACCOUNT_ID` in backend environment.
- Resolve the kid account IBAN/alias from bunq account listing before creating payments.
- Do not create a second sandbox user unless bunq constraints force it.

Open risk:

- If bunq sandbox does not allow payment between two accounts under the same user, switch to two sandbox users while preserving the same `PaymentClient` interface.

## Decision 2: Idempotency

Completion idempotency is mandatory before real bunq payments.

Rule:

```text
completion_attempt_id = gig_id + idempotency_key
```

Behavior:

- Repeating the same `gig_id + idempotency_key` returns the same logical completion result.
- A gig can have many failed/rejected attempts, but only one successful payment.
- If a gig is already `paid`, completion returns the paid result and does not call bunq again.
- If a gig is `payment_failed`, retry payment without re-running AI when verification already passed.
- If a different idempotency key is sent for a paid gig, reject or return paid result without creating payment.

Persistence:

- Store completion attempts in local state.
- Store request idempotency key, verification result id, payment id, and final status.

## Decision 3: Photo Storage

Store uploaded photos as files under `data/uploads/`, not inline in JSON.

Accepted content types:

- `image/jpeg`
- `image/png`
- `image/webp`

Limits:

- Max original upload size: 8 MB.
- Backend should reject larger payloads with stable error code `image_too_large`.
- Frontend should resize/compress before upload when possible.

State:

- Store only `photo_id`, `kind`, `content_type`, `storage_ref`, and timestamps in JSON.
- Do not commit `data/` or uploaded photos.

Rationale:

- Keeps JSON state inspectable.
- Avoids huge local state files.
- Makes it easier to send photos to AI as files or base64 later.

## Decision 4: AI Verification Schema

Claude output must be parsed into a strict backend-owned schema.

Required fields:

```json
{
  "approved": true,
  "confidence": 0.91,
  "tags": ["bed made", "floor clear"],
  "message_for_kid": "Nice work. Your bed is made and the floor is clear.",
  "reasoning_summary": "The after photo shows visible improvement against the checklist."
}
```

Validation:

- `approved`: boolean
- `confidence`: number from 0 to 1
- `tags`: list of short strings
- `message_for_kid`: short kid-readable sentence
- `reasoning_summary`: short parent/backend-readable explanation

Failure handling:

- If Claude returns invalid JSON, treat as AI failure.
- Do not expose raw model output to the frontend.
- Store raw provider/model metadata only if useful and non-sensitive.

## Decision 5: Fallback Honesty

The product can use LM Studio locally for AI, fake bunq locally for payment if needed, and demo fallbacks when explicitly enabled, but the UI must be honest.

Modes:

- `fake_local`: local fake payment mode, not a production claim.
- `real`: real AI verification succeeded, and bunq may be real or fake depending on environment.
- `ai_fallback`: Claude failed and backend used fallback behavior.
- `bunq_fallback`: bunq failed and backend used simulated behavior.

Rules:

- Fake local mode may show "Local payment demo mode" in developer-facing areas.
- Real mode may say "AI verified" and "Paid with bunq sandbox".
- AI fallback must not say AI verified the chore.
- bunq fallback must not say bunq payment succeeded.
- A gig must not be marked `paid` for real bunq mode unless real bunq payment succeeded.

## Decision 6: First Vertical Slice

The first implementation slice is not "backend scaffold" or "frontend scaffold" in isolation. It is a full local product loop.

Slice:

```text
seeded gig
  -> kid claims
  -> before/after upload
  -> local AI verification approved
  -> fake payment succeeds
  -> verdict screen shows updated fake balance
```

Acceptance:

- Runs locally without external credentials.
- Uses the same API endpoints planned for real integrations.
- Has at least one backend test around completion.
- Can be manually tested from a runbook.

## Decision 7: CI Baseline

Add CI after the first backend/frontend scaffolds exist.

Minimum checks:

- backend test suite
- backend formatting/linting if configured
- frontend typecheck
- frontend lint if configured

Do not block early scaffolding on perfect CI. Add it once commands exist and stabilize.

## Decision 8: Runbook

Maintain `docs/runbook.md` once the app has runnable commands.

It must include:

- install dependencies
- start backend
- start frontend
- fake mode smoke test
- real bunq smoke test
- troubleshooting
- reset local state

Until code exists, `docs/runbook.md` should remain a placeholder checklist rather than fake commands.

