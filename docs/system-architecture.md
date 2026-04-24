# System Architecture

## Overview

bunq Bloom uses a Next.js mobile-first frontend and a FastAPI backend. The backend owns integrations with Claude Vision and bunq sandbox. The frontend should not call external AI or banking APIs directly.

```text
Next.js app
  -> /api proxy
  -> FastAPI backend
    -> Claude Vision
    -> bunq sandbox API
    -> local JSON state
```

## Frontend

Technology:

- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Lucide icons

Responsibilities:

- Render parent and kid flows.
- Capture before and after photos from the mobile camera.
- Submit gig completion requests.
- Render verification and payment outcomes.
- Keep the interface fast and resilient during long-running backend calls.

Frontend should not:

- Store bunq API credentials.
- Store Anthropic API credentials.
- Decide whether a gig deserves payment.
- Simulate successful payment unless the backend explicitly returns fallback mode.

## Backend

Technology:

- Python
- FastAPI
- bunq official hackathon toolkit
- Anthropic Claude API
- Local JSON state for MVP persistence

Responsibilities:

- Own all domain state.
- Validate request payloads.
- Run AI before/after verification.
- Trigger bunq sandbox payments.
- Fetch current balances from bunq sandbox.
- Provide fallback responses that keep demos recoverable.

Backend should expose JSON APIs only. Binary image upload can start as base64 for speed, but the boundary should allow multipart upload later.

## Integration Boundaries

### Claude Vision

Used for before/after gig verification.

Input:

- Gig title
- Gig description
- Verification checklist
- Before photo
- After photo

Output:

- Approved boolean
- Confidence
- Specific completion tags
- Short kid-friendly message
- Short reasoning summary for the parent/backend logs

Fallback:

- If Claude is unavailable during a demo, backend may approve with `fallback_mode: true`.
- The response must make fallback mode explicit so the UI can avoid pretending AI succeeded.

### bunq Sandbox

Used for real sandbox money movement and balance retrieval.

Operations:

- Get parent monetary account.
- Get kid monetary account.
- Create payment from parent to kid after approved gig.
- Fetch kid balance after payment.

Fallback:

- If bunq payment fails, do not mark the gig as paid.
- Return `payment_failed` with a retry-safe identifier.
- For demo-only mode, backend may return a simulated balance with `fallback_mode: true`.

## Local State

For the MVP, local JSON state is acceptable because it is inspectable and fast to iterate on.

Recommended files:

- `data/state.json` for families, users, gigs, verification results, and payments.
- `data/photos/` for local photo files if base64 is moved out of JSON.
- `bunq_context.json` for bunq toolkit session cache, excluded from commits.

Do not store secrets in committed files.

## End-to-End Completion Flow

```text
1. Frontend captures before photo.
2. Backend stores before photo and moves gig to awaiting_after_photo.
3. Frontend captures after photo.
4. Frontend POSTs completion request.
5. Backend marks gig verifying.
6. Backend sends before and after images to Claude Vision.
7. Backend stores verification result.
8. If approved, backend creates bunq payment.
9. Backend fetches updated kid balance.
10. Backend marks gig paid.
11. Frontend renders verdict, payment status, and updated balance.
```

## Security Notes For MVP

- Never expose external API keys to the frontend.
- Never read or commit `.env` files.
- Treat local JSON as development state only.
- Validate image size and content type before sending to Claude.
- Add idempotency around payment creation before public demos.

