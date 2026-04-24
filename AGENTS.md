# bunq Bloom Agent Instructions

## Project

bunq Bloom is a kid economy engine for the bunq Hackathon 7.0.

The product priority is the core learning journey:

```text
parent posts gig -> kid takes before/after photos -> AI verifies -> bunq sandbox payment lands instantly -> kid sees money earned
```

Everything should support making this loop reliable, understandable, and demo-safe before expanding into secondary features.

## User Context

Read `~/Documents/DevAI/Shared/profile.md` for Daniel's working style and environment context.

Important local rules:

- Keep work scoped and high-signal.
- Prefer MVP/POC progress over broad abstraction.
- Plan before non-trivial implementation.
- Do not read `.env` files or expose secrets.
- Do not commit, push, reset, or make destructive changes without explicit instruction.
- Prefer auditable local workflows.
- Use Podman, not Docker.

## Stack

Frontend:

- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Lucide icons
- Mobile-first UI, optimized for a 390px phone viewport

Backend:

- Python
- FastAPI
- bunq official hackathon toolkit
- Anthropic Claude Vision/Text
- Local JSON state for MVP persistence

Integrations:

- bunq sandbox API for real sandbox payments and balances
- Claude Vision for before/after photo verification

## Source Of Truth

Start with these docs before making product or architecture decisions:

- `docs/product-foundation.md`
- `docs/domain-model.md`
- `docs/system-architecture.md`
- `docs/api-contracts.md`
- `docs/technical-implementation-plan.md`
- `docs/mvp-spec.md`
- `docs/pre-implementation-decisions.md`
- `docs/runbook.md`
- `docs/engineering-priorities.md`
- `docs/project-tracker.md`
- `docs/integrations/bunq-hackathon-toolkit.md`
- `docs/agents/backend.md`
- `docs/agents/frontend.md`
- `docs/agents/ui-ux.md`

Do not add pitch, demo-script, or marketing work unless explicitly requested.

## Role-Specific Guidance

When working in a specific area, read the relevant specialization first:

- Backend/API/integrations: `docs/agents/backend.md`
- Frontend/Next.js/client state: `docs/agents/frontend.md`
- Visual design/copy/mobile UX: `docs/agents/ui-ux.md`
- bunq sandbox/toolkit usage: `docs/integrations/bunq-hackathon-toolkit.md`

## Build Priorities

1. Build the end-to-end gig completion loop with fake adapters.
2. Swap fake adapters for real Claude and bunq sandbox clients behind stable interfaces.
3. Make browser camera capture feel native on mobile.
4. Add idempotency and retry safety around verification and payment.
5. Polish only after the core flow is reliable.

Defer:

- Weekly Bloom Report
- Snap & Learn
- Production authentication
- Production database
- Multi-family support
- Advanced analytics

## Architecture Rules

- The frontend must not call Claude or bunq directly.
- The backend owns verification, payment, and domain state.
- External integrations must sit behind adapters so local fake implementations can be used.
- The core completion endpoint is `POST /api/gigs/{gig_id}/complete`.
- A gig must never be paid twice.
- A gig must never be marked paid unless bunq payment succeeded or the response explicitly says fallback mode.
- Fallback mode must be explicit in API responses and UI copy.

## Frontend Rules

- Design mobile-first.
- Keep tap targets at least 44px.
- Treat camera capture as the primary interaction, not a file-upload afterthought.
- Show clear progress while AI verification and payment are running.
- Render verdict, earned amount, payment status, and updated balance in one clear completion screen.
- Avoid dark-mode-first or generic SaaS UI. Use a bright bunq-inspired light theme.

## Backend Rules

- Use typed request/response models.
- Keep business logic outside route handlers.
- Keep integrations isolated under clear service/client modules.
- Validate image size and content type before sending to AI.
- Use idempotency keys for completion/payment flows.
- Make payment retry possible when verification already passed.
- Store enough local state to inspect and recover demo flows.

## GitHub Tracking

Use GitHub issues/milestones/project items to track implementation work.

Recommended milestones:

- `M1 Core Loop Fake Adapters`
- `M2 Real Claude + bunq`
- `M3 Mobile Camera UX`
- `M4 Demo Hardening`

Issue labels:

- `frontend`
- `backend`
- `ai`
- `bunq`
- `docs`
- `priority:critical`
- `priority:high`
- `priority:medium`
- `demo-risk`

## Verification Expectations

For code changes, run the smallest relevant checks first.

Examples:

- Frontend: typecheck, lint, targeted component tests if available.
- Backend: unit tests for services/adapters, FastAPI route tests.
- Integration: fake adapters first, then real sandbox smoke tests when credentials are configured.

If checks cannot run because dependencies or credentials are missing, state that clearly.
