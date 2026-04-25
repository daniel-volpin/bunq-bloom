# Technical Implementation Plan

This plan records the implementation shape for bunq Bloom and the constraints to preserve while hardening the codebase.

## Goal

Build one reliable end-to-end learning journey:

```text
parent creates gig -> kid claims gig -> kid submits before/after photos -> backend verifies -> backend pays -> kid sees updated balance
```

## Repository Layout

Use a simple monorepo:

```text
apps/
  api/
    app/
      integrations/
      models/
      repositories/
      routes/
      services/
    tests/
  web/
    app/
    components/
    lib/
    public/
docs/
hackathon_toolkit-main/
```

Rationale:

- Keeps frontend and backend independently runnable.
- Keeps shared docs at repo root.
- Keeps bunq toolkit available as reference code without mixing it into app logic.

## Tooling Decisions

Backend:

- Python 3.10+.
- FastAPI.
- Pydantic models.
- `pytest` for tests.
- `uv` preferred for dependency and command execution if available.

Frontend:

- Next.js 16.
- React 19.
- TypeScript.
- Tailwind CSS.
- Lucide icons.
- `npm` with a committed lockfile.

Shared:

- Add root `Makefile` only if it reduces repeated command friction.
- Add `.env.example` files, never real `.env` files.
- Use LM Studio for local AI by default and fake bunq locally so the app works without hosted AI or banking credentials.
- Keep real bunq sandbox available through explicit local env and opt-in smoke tests.
- Build the first vertical slice across backend and frontend instead of completing one side in isolation.
- Use `docs/agents/orchestration.md` when splitting work across multiple coding agents.

## Environment Contract

Backend `.env.example`:

```text
BLOOM_AI_PROVIDER=lmstudio
BLOOM_LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
BLOOM_LMSTUDIO_MODEL=qwen3.5-9b-mlx
BLOOM_USE_FAKE_BUNQ=true
BLOOM_STATE_PATH=data/state.json
BLOOM_UPLOAD_DIR=data/uploads
ANTHROPIC_API_KEY=
BUNQ_API_KEY=
BUNQ_PARENT_ACCOUNT_ID=
BUNQ_KID_ACCOUNT_ID=
BUNQ_KID_ACCOUNT_IBAN=
BLOOM_DEMO_ALLOW_AI_FALLBACK=false
BLOOM_DEMO_ALLOW_BUNQ_FALLBACK=false
```

Frontend `.env.example`:

```text
API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_API_BASE_URL=
```

Rules:

- The frontend must not receive `ANTHROPIC_API_KEY`, `BUNQ_API_KEY`, session tokens, or bunq context data.
- Real integrations are opt-in with explicit env flags.
- Default local development must use LM Studio for AI and fake bunq for payment.

## Backend Design

Recommended modules:

```text
apps/api/app/main.py
apps/api/app/routes/health.py
apps/api/app/routes/gigs.py
apps/api/app/routes/balance.py
apps/api/app/models/domain.py
apps/api/app/models/api.py
apps/api/app/repositories/state_repository.py
apps/api/app/repositories/photo_repository.py
apps/api/app/services/gig_service.py
apps/api/app/services/payment_service.py
apps/api/app/services/snap_and_learn_service.py
apps/api/app/services/bloom_report_service.py
apps/api/app/integrations/fake_verification_client.py
apps/api/app/integrations/claude_client.py
apps/api/app/integrations/lmstudio_client.py
apps/api/app/integrations/fake_payment_client.py
apps/api/app/integrations/bunq_payment_client.py
apps/api/app/settings.py
```

Layering:

```text
FastAPI routes -> services -> repositories/integration clients
```

Route handlers should validate requests and return responses. They should not own domain transitions, AI prompts, payment logic, or file persistence details.

## Frontend Design

Recommended modules:

```text
apps/web/app/page.tsx
apps/web/app/gigs/page.tsx
apps/web/app/gigs/[gigId]/page.tsx
apps/web/app/parent/gigs/new/page.tsx
apps/web/components/app-shell.tsx
apps/web/components/bottom-nav.tsx
apps/web/components/camera-capture.tsx
apps/web/components/gig-card.tsx
apps/web/components/verdict-screen.tsx
apps/web/lib/api-client.ts
apps/web/lib/types.ts
```

The first frontend should be small:

- Parent gig creation.
- Kid gig list.
- Gig detail with claim and camera steps.
- Completion loading state.
- Verdict/payment/balance result screen.

Avoid adding global state until the flow proves it needs it.

## Adapter Strategy

Start with local-friendly adapters:

- `LMStudioVisionClient` handles local AI verification.
- `FakePaymentClient` simulates payment id and balance.

Then add real adapters behind the same interfaces:

- `ClaudeVerificationClient`.
- `BunqPaymentClient`.

This lets the team test product flow before credentials, rate limits, and network failures become blockers.

## Local State Strategy

Use local JSON for MVP:

```text
data/state.json
data/uploads/
```

Rules:

- `data/` is ignored by git.
- State writes should be atomic enough for local demo usage.
- Store photo files in `data/uploads/` and references in JSON.
- Do not store secrets or bunq context in app state.

Photo rules:

- Accept `image/jpeg`, `image/png`, and `image/webp`.
- Reject original uploads larger than 8 MB.
- Return stable error code `image_too_large` for oversized images.
- Keep uploaded photos local and uncommitted.

## bunq Account Model

Use one bunq sandbox user with two monetary accounts for MVP:

- parent monetary account
- kid monetary account

Configure both account ids in backend environment. If bunq sandbox does not support the required transfer between accounts owned by one user, switch the adapter internals to two sandbox users without changing the frontend API or service interface.

## AI Verification Contract

Verification clients must return this normalized schema:

```json
{
  "approved": true,
  "confidence": 0.91,
  "tags": ["bed made", "floor clear"],
  "message_for_kid": "Nice work. Your bed is made and the floor is clear.",
  "reasoning_summary": "The after photo shows visible improvement against the checklist."
}
```

Invalid Claude output is an AI failure and should not be passed through to the frontend.

## Idempotency Contract

The completion idempotency key is scoped to the gig:

```text
completion_attempt_id = gig_id + idempotency_key
```

Rules:

- Same key returns the same logical result.
- Paid gigs cannot create another payment.
- Payment retry after `payment_failed` must not re-run AI when verification already passed.
- Real bunq payment creation must not happen until this behavior is implemented.

## First Coding Sequence

First vertical slice:

```text
seeded gig -> claim -> before/after upload -> LM Studio verification -> fake payment -> verdict screen
```

Sequence:

1. Scaffold backend app with health route and settings.
2. Add domain/API models.
3. Add local JSON repository, photo repository, and seed data.
4. Add gig service state transitions and idempotency storage.
5. Add LM Studio verification and fake payment clients.
6. Implement gig and balance endpoints.
7. Scaffold frontend app shell.
8. Add typed API client.
9. Build kid gig list and claim flow against seeded data.
10. Build camera capture/upload fallback.
11. Build completion call and verdict screen.
12. Add parent gig creation after seeded kid flow works.
13. Add tests around backend state transitions and completion idempotency.

## Parallel Work Guidance

Safe parallel tracks after the API contract is agreed:

- Backend agent: local-AI endpoints, domain service, local state, idempotency tests.
- Frontend agent: app shell, typed API client, gig list, camera flow against documented local response fixtures.
- UI/UX agent: camera state design, completion screen hierarchy, fallback/retry copy.

Do not parallelize real bunq payment work with completion endpoint contract changes unless file ownership and response shapes are already stable.

The orchestrating agent should integrate these tracks and run the smallest relevant verification before moving to real integrations.

## Real Integration Sequence

After local LM Studio end-to-end flow works:

1. Add Claude Vision client and structured response parsing.
2. Add bunq sandbox payment client using `hackathon_toolkit-main/bunq_client.py` as reference.
3. Add integration health checks.
4. Add opt-in smoke tests.
5. Test with real sandbox account IDs.
6. Harden retries and fallback modes.

## CI Baseline

Add GitHub Actions after scaffold commands exist.

Minimum checks:

- backend tests
- frontend typecheck
- frontend lint if configured

CI should verify the local LM Studio path and fake bunq path first. Real Claude and bunq smoke tests must remain opt-in.

## Done Criteria Before Polish

The first implementation phase is done when:

- A teammate can start backend and frontend locally from docs.
- The core loop works with LM Studio AI, fake bunq, and seeded data.
- A created gig can reach `paid`.
- The UI shows verdict, payment status, and updated balance.
- Backend tests cover core state transitions.
- No frontend code knows about Claude or bunq credentials.
- `docs/runbook.md` has real local startup and smoke-test commands.
