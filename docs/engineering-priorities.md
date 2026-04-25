# Engineering Priorities

## Priority 1: Prove The Core Loop

Build the smallest reliable path that demonstrates the product:

```text
create gig -> claim gig -> before photo -> after photo -> AI verification -> bunq payment -> updated balance
```

Success criteria:

- The flow works end-to-end on a mobile viewport.
- The backend controls verification and payment.
- The payment is real in bunq sandbox.
- The UI clearly shows verification outcome and earned money.
- The flow has recoverable errors.

## Priority 2: Make The Camera Feel Native

The camera is the main interaction, not an implementation detail.

Requirements:

- Use mobile camera capture from the browser.
- Support retake before submission.
- Compress or resize images before upload if needed.
- Show clear progress while verification and payment are running.
- Avoid desktop-first file-upload UX unless used as a fallback.

## Priority 3: Make The Backend Idempotent And Demo-Safe

The backend must prevent duplicate payments and survive retries.

Requirements:

- Accept an `idempotency_key` on completion.
- Store verification and payment state before returning.
- Do not create a second bunq payment for the same approved completion.
- Allow payment retry if verification already passed but payment failed.
- Make fallback mode explicit in responses.

## Priority 4: Build Clear Integration Adapters

Keep integrations isolated so the app can be tested without external services.

Recommended backend modules:

- `services/gig_service.py`
- `services/verification_service.py`
- `services/payment_service.py`
- `integrations/claude_client.py`
- `integrations/bunq_client.py`
- `repositories/state_repository.py`

Each adapter should have a simple interface and a fake implementation for local development.

## Priority 5: Add Product Polish After The Loop Works

Polish should reinforce the learning journey.

Useful polish:

- Animated money-earned moment.
- Specific AI verdict tags.
- Kid-friendly copy.
- Parent confidence summary.
- Balance delta display.
- Bottom navigation and camera-first mobile shell.

Defer until the core loop works:

- Weekly Bloom Report.
- Snap & Learn.
- Multi-user authentication.
- Production database.
- Complex analytics.
- Advanced visual design system.

## First Implementation Milestone

The first coding milestone should produce:

- A Next.js app shell with parent and kid paths stubbed.
- A FastAPI app with the documented endpoints.
- Local JSON state.
- LM Studio verification and fake bunq adapters.
- One end-to-end flow using local AI and fake bunq.

After that, switch to hosted Claude and real bunq sandbox clients behind the same interfaces.

