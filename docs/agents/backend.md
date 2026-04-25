# Backend Agent Guide

Use this guide for FastAPI, domain logic, local state, Claude, and bunq integration work.

## First Read

Before backend changes, read:

- `docs/domain-model.md`
- `docs/system-architecture.md`
- `docs/api-contracts.md`
- `docs/integrations/bunq-hackathon-toolkit.md`

## Architecture

Keep backend code layered:

```text
routes -> services -> repositories/integration clients
```

Recommended modules:

- `app/main.py`
- `app/routes/gigs.py`
- `app/routes/health.py`
- `app/models/api.py`
- `app/models/domain.py`
- `app/services/gig_service.py`
- `app/services/verification_service.py`
- `app/services/payment_service.py`
- `app/integrations/claude_client.py`
- `app/integrations/bunq_client.py`
- `app/repositories/state_repository.py`

## Rules

- Use typed Pydantic request and response models.
- Keep route handlers thin.
- Keep domain transitions in `GigService`.
- Keep AI and bunq behind interfaces with fake and real implementations.
- Do not read `.env` files. Use normal environment variable loading at runtime.
- Do not expose integration errors directly to the frontend.
- Return stable error codes the UI can handle.

## Core Loop

The backend owns this sequence:

```text
receive after photo
load gig and before photo
mark verifying
run verification
if rejected: mark rejected and return verdict
if approved: create bunq payment
fetch kid balance
mark paid
return verdict, payment, balance
```

## Collaboration Handoffs

Backend must publish stable contracts before frontend depends on behavior.

Before handing work to frontend, confirm:

- response shapes match `docs/api-contracts.md`
- stable error codes exist
- fallback modes are explicit
- idempotency behavior is documented
- fake response fixtures are available or easy to reproduce

Backend owns the contract for `POST /api/gigs/{gig_id}/complete`. Any change to this endpoint needs coordination with frontend and UI/UX because it affects camera flow, loading states, payment feedback, and completion copy.

## Testing Strategy

Start with local AI and fake bunq:

- gig state transition tests
- repository read/write tests
- completion endpoint tests
- duplicate completion/idempotency tests

Real Claude and bunq tests should be opt-in smoke tests because they require credentials and network.

## Failure Handling

Required backend failure states:

- invalid gig transition
- missing before photo
- AI unavailable
- AI rejected
- bunq payment failed
- duplicate completion request
- local state write failed

The frontend should always receive a recoverable response shape where possible.
