# Product Foundation

## Product Promise

bunq Bloom teaches kids that money is earned, limited, and connected to real choices.

The first product experience is not a passive bank balance. It is an earning loop where a child completes a household gig, proves the result with photos, receives money instantly, and sees their balance grow.

## Primary Users

### Parent

The parent wants less nagging, a simple reward system, and a better way to teach money habits.

Core needs:

- Create household gigs with clear expectations and rewards.
- Trust that completion is verified without manually inspecting every task.
- Move money safely from parent to kid account.
- See progress without turning the app into another admin chore.

### Kid

The kid wants clear ways to earn, fast feedback, and visible progress toward things they want.

Core needs:

- See available gigs.
- Claim a gig and understand what "done" means.
- Use the camera naturally.
- Receive money immediately after approval.
- Understand how the earned money changes what they can afford.

## Core Learning Journey

```text
Parent posts gig
Kid claims gig
Kid takes before photo
Kid completes work
Kid takes after photo
AI verifies improvement
Backend triggers bunq sandbox payment
Kid sees earned money and updated balance
```

## MVP Scope

The MVP should prove one complete earning loop with real integrations.

Included:

- Parent can create a gig with title, description, reward, and optional verification checklist.
- Kid can view, claim, and complete a gig.
- Mobile camera capture supports before and after photos.
- Backend compares images with Claude Vision.
- Approved completion triggers a bunq sandbox payment from parent to kid.
- Frontend shows verdict, earned amount, and updated kid balance.
- Local state persists enough to survive refreshes during development and demo.

Deferred:

- Multi-family accounts.
- Real authentication and authorization.
- Production-grade database.
- Advanced parental controls.
- Recurring gigs.
- Dispute flows.
- App store packaging.
- Full weekly report implementation.
- Full Snap & Learn implementation.

## Non-Negotiable Product Qualities

- The core flow must be understandable without explanation.
- The AI verdict must feel specific, not generic.
- Payment success must be visually obvious.
- Failure states must keep the demo recoverable.
- The app must feel native on a 390px mobile viewport.

