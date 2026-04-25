# Project Tracker

This document is the local source for GitHub issues and project cards.

## Milestones

### M1 Core Loop Local AI + Fake bunq

Goal: prove the full product journey without external dependencies.

Issues:

- `backend` Create FastAPI app skeleton.
- `backend` Add local JSON state repository.
- `backend` Add gig domain service and state transitions.
- `backend` Add LM Studio verification adapter.
- `backend` Add fake payment adapter.
- `backend` Implement `GET /api/gigs`.
- `backend` Implement `POST /api/gigs`.
- `backend` Implement `POST /api/gigs/{gig_id}/claim`.
- `backend` Implement `POST /api/gigs/{gig_id}/before-photo`.
- `backend` Implement `POST /api/gigs/{gig_id}/complete`.
- `frontend` Create Next.js app shell.
- `frontend` Add mobile bottom navigation.
- `frontend` Add parent gig creation flow.
- `frontend` Add kid gig list and claim flow.
- `frontend` Add before/after camera capture with retake.
- `frontend` Add completion verdict screen.

Exit criteria:

- One gig can move from open to paid using LM Studio AI and fake bunq.
- The UI works on a 390px mobile viewport.
- Refreshing the page does not lose gig state.

### M2 Real Claude + bunq

Goal: replace local payment simulation with real bunq and switch AI to hosted Claude when ready.

Issues:

- `ai` Add Claude Vision client.
- `ai` Design verification prompt and response schema.
- `ai` Add AI failure fallback mode.
- `bunq` Add bunq sandbox client wrapper.
- `bunq` Add parent-to-kid payment creation.
- `bunq` Add kid balance retrieval.
- `backend` Add integration configuration and health checks.
- `backend` Add real-adapter smoke tests where credentials are available.

Exit criteria:

- Approved gig triggers a real bunq sandbox payment.
- Completion response returns kid balance from bunq.
- Claude failure and bunq failure are handled without crashing the flow.

### M3 Mobile Camera UX

Goal: make the photo journey feel like a product, not a form.

Issues:

- `frontend` Use browser camera capture for before and after photos.
- `frontend` Add image preview and retake.
- `frontend` Add upload progress and verification loading state.
- `frontend` Add completion animation for money earned.
- `frontend` Add accessible and kid-friendly status copy.
- `frontend` Add desktop fallback upload path.

Exit criteria:

- The camera path works on a modern mobile browser.
- The kid understands what to do without explanation.
- Long-running verification/payment calls have clear progress states.

### M4 Demo Hardening

Goal: reduce live-demo failure risk.

Issues:

- `backend` Add idempotency key handling for completion.
- `backend` Prevent duplicate payments for one gig.
- `backend` Add payment retry path.
- `backend` Add seeded demo data.
- `backend` Add health endpoint for Claude, bunq, and state.
- `frontend` Add recoverable error screens.
- `frontend` Add visible fallback-mode copy.
- `docs` Add runbook for local startup and smoke test.

Exit criteria:

- Re-clicking completion cannot double-pay.
- Known integration failures produce controlled UI states.
- The app can be started and smoke-tested from docs.

## Initial GitHub Project Views

Recommended project fields:

- Status: `Backlog`, `Ready`, `In Progress`, `In Review`, `Done`
- Milestone: `M1`, `M2`, `M3`, `M4`
- Area: `frontend`, `backend`, `ai`, `bunq`, `docs`
- Priority: `critical`, `high`, `medium`
- Demo Risk: `yes`, `no`

Recommended views:

- `Core Loop Board`: grouped by Status, filtered to M1 and M2.
- `Demo Risks`: filtered to `demo-risk`.
- `Frontend`: filtered to `frontend`.
- `Backend + Integrations`: filtered to `backend`, `ai`, and `bunq`.

