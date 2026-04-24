# Frontend Agent Guide

Use this guide for Next.js, React, TypeScript, Tailwind, API calls, and client-side flow work.

## First Read

Before frontend changes, read:

- `docs/product-foundation.md`
- `docs/api-contracts.md`
- `docs/agents/ui-ux.md`

## Architecture

Recommended app areas:

- app shell and routing
- API client
- gig creation flow
- kid gig list
- camera capture flow
- completion verdict screen
- shared UI primitives

Keep the frontend focused on product interaction. The backend owns verification, payment, and domain truth.

## Rules

- Do not call Claude or bunq from the frontend.
- Use typed API client functions matching `docs/api-contracts.md`.
- Prefer simple state first. Do not introduce global state until prop/state flow becomes painful.
- Design and test at 390px width early.
- Use progressive loading states for long-running completion calls.
- Preserve recoverability: retake, retry, back, and clear error actions matter.

## Core Screens

Minimum frontend journey:

```text
parent creates gig
kid sees available gig
kid claims gig
kid captures before photo
kid captures after photo
kid waits through verification/payment
kid sees verdict and updated balance
```

## Camera Guidance

Start pragmatic:

- Use browser-supported capture input or MediaDevices depending on implementation speed.
- Always show preview before submit.
- Always allow retake.
- Compress/resize before upload if payloads become too large.
- Keep desktop file upload as fallback for development.

## API Handling

Completion states the UI must handle:

- approved and paid
- rejected with kid-friendly reason
- approved but payment failed
- AI fallback mode
- bunq fallback mode
- network failure

Do not collapse these into one generic error message.

