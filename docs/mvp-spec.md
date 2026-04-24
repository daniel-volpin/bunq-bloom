# MVP Spec

This spec defines the first buildable product scope for bunq Bloom.

## MVP Outcome

A parent can create a paid household gig. A kid can complete it with before/after photos. The backend verifies the result and pays the kid. The kid sees that they earned money.

## Personas

Parent:

- Wants to create clear tasks with rewards.
- Wants verification without manual nagging.
- Wants money movement to be safe.

Kid:

- Wants to know what gigs are available.
- Wants to complete a task and get fast feedback.
- Wants to see money earned immediately.

## Core User Journey

```text
1. Parent creates a gig.
2. Kid sees the gig.
3. Kid claims the gig.
4. Kid takes a before photo.
5. Kid does the work.
6. Kid takes an after photo.
7. Backend compares the photos.
8. If approved, backend pays the kid.
9. Kid sees verdict, reward, payment status, and updated balance.
```

## Functional Requirements

### Gig Creation

Parent can create a gig with:

- title
- description
- reward amount
- currency
- verification checklist

Validation:

- title is required
- reward amount must be positive
- currency is `EUR` for MVP
- checklist can be empty, but the default demo gig should include checklist items

Acceptance:

- Created gig appears in the kid gig list.
- New gig starts with status `open`.

### Claim Gig

Kid can claim an open gig.

Acceptance:

- Gig moves from `open` to `claimed`.
- Claimed gig shows the next action: take before photo.
- Already claimed/completed gigs cannot be claimed again.

### Before Photo

Kid can submit a before photo.

Acceptance:

- Photo preview is shown before submit.
- Kid can retake before submit.
- Accepted types are `image/jpeg`, `image/png`, and `image/webp`.
- Original upload size must be at most 8 MB.
- Backend stores photo reference.
- Gig moves to `awaiting_after_photo`.

### After Photo And Completion

Kid can submit an after photo to complete the gig.

Acceptance:

- Photo preview is shown before submit.
- Kid can retake before submit.
- Frontend sends `after_image_base64` and `idempotency_key`.
- Accepted types are `image/jpeg`, `image/png`, and `image/webp`.
- Original upload size must be at most 8 MB.
- Backend owns verification and payment.
- Frontend shows loading/progress while backend works.

### AI Verification

Backend compares before and after photos using the configured verification client.

Output must include:

- `approved`
- `confidence`
- `tags`
- `message_for_kid`
- `reasoning_summary`

Normalized schema:

```json
{
  "approved": true,
  "confidence": 0.91,
  "tags": ["bed made", "floor clear"],
  "message_for_kid": "Nice work. Your bed is made and the floor is clear.",
  "reasoning_summary": "The after photo shows visible improvement against the checklist."
}
```

Acceptance:

- Approved result can proceed to payment.
- Rejected result does not create payment.
- Rejected result gives a specific kid-readable reason.
- AI failure returns explicit fallback mode if fallback is enabled.
- Invalid model output is treated as AI failure.

### Payment

Backend pays the kid only after approval.

Acceptance:

- Payment amount equals gig reward.
- Payment description references bunq Bloom and the gig title.
- Successful payment marks gig `paid`.
- Failed payment marks gig `payment_failed`.
- One gig cannot create more than one successful payment.
- For MVP bunq sandbox, use one sandbox user with two monetary accounts unless sandbox constraints force two users.

### Balance

After successful payment, backend returns the kid balance.

Acceptance:

- If bunq is configured, balance source is `bunq`.
- If fake bunq is used, balance source is `fake`.
- If balance retrieval fails after payment, payment result should still be visible and the balance failure should be recoverable.

## Required Screens

### Parent Gig Creation

Fields:

- title
- description
- reward amount
- checklist items

Primary action:

- create gig

### Kid Gig List

Shows:

- gig title
- reward
- status
- short description
- next action

### Gig Detail / Camera Flow

States:

- claim gig
- take before photo
- confirm before photo
- take after photo
- confirm after photo
- verifying and paying

### Completion Result

Shows:

- approved or rejected verdict
- AI tags
- message for kid
- reward amount
- payment status
- updated balance if available
- next action

## Required API Behavior

Use `docs/api-contracts.md` as the source of truth for endpoint shapes.

Required endpoints:

- `GET /api/health`
- `GET /api/gigs`
- `POST /api/gigs`
- `POST /api/gigs/{gig_id}/claim`
- `POST /api/gigs/{gig_id}/before-photo`
- `POST /api/gigs/{gig_id}/complete`
- `GET /api/balance/kid`

## State Rules

Allowed status flow:

```text
open -> claimed -> awaiting_after_photo -> verifying -> approved -> paid
```

Failure flows:

```text
verifying -> rejected
approved -> payment_failed
payment_failed -> paid
rejected -> awaiting_after_photo
```

Invariants:

- A gig cannot be paid before approval.
- A gig cannot be paid twice.
- A gig must have a before photo before completion.
- A payment must belong to one gig.
- Fallback mode must be explicit.
- `gig_id + idempotency_key` identifies one completion attempt.
- Repeating the same completion attempt returns the same logical result.

## Fallback Modes

### Fake Local Mode

Default for local development.

Behavior:

- Fake AI can approve or reject deterministically.
- Fake bunq can return simulated payment and balance.
- API response uses `fallback_mode: false` if fake mode is intentionally configured for local development.
- UI may show source as `fake`.
- UI should indicate local demo mode in developer-facing areas.

### AI Failure Fallback

Used when real Claude is configured but unavailable.

Behavior:

- Backend may auto-approve only if demo fallback is enabled.
- Response must include `fallback_mode: true`.
- UI must not say real AI verified the chore.
- Suggested copy: "Demo fallback approved this task because AI verification is unavailable."

### bunq Failure Fallback

Used when real bunq is configured but unavailable.

Behavior:

- Backend must not mark gig `paid` unless real payment succeeded.
- If demo simulation is used, response must include `fallback_mode: true`.
- UI must distinguish simulated payment from real bunq payment.
- Suggested copy: "Payment is simulated because bunq sandbox is unavailable."

## Non-Functional Requirements

- Mobile-first at 390px width.
- Tap targets at least 44px.
- Backend returns stable JSON error codes.
- Local app works without external credentials.
- Real integrations are opt-in.
- Secrets are never committed or exposed to frontend.
- Long-running operations have visible progress.
- CI should cover fake backend tests and frontend typecheck once code exists.

## Out Of Scope For MVP

- Snap & Learn.
- Weekly Bloom Report.
- Real authentication.
- Production database.
- Multi-family support.
- Recurring gigs.
- Parent approval override.
- App store/native packaging.

## MVP Acceptance Checklist

- Parent can create a gig.
- Kid can claim it.
- Kid can submit before and after photos.
- Backend verifies with fake AI.
- Backend pays with fake bunq.
- Frontend shows paid result and updated fake balance.
- Real Claude and bunq can later replace fake adapters without changing frontend API contracts.
- Duplicate completion attempts cannot create duplicate payments.
- Uploaded photos are stored under ignored local storage, not committed.
