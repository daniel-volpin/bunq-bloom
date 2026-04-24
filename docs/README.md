# bunq Bloom Docs

This folder is the product and engineering source of truth for building the first version of bunq Bloom.

The current priority is the core kid learning journey:

```text
parent posts gig -> kid takes before/after photos -> AI verifies -> bunq sandbox payment lands instantly -> kid sees money earned
```

## Docs

- [Product Foundation](./product-foundation.md) defines the user problem, product promise, first user journey, and MVP scope.
- [Domain Model](./domain-model.md) defines the core entities and state transitions.
- [System Architecture](./system-architecture.md) defines the Next.js, FastAPI, Claude, and bunq sandbox boundaries.
- [API Contracts](./api-contracts.md) defines the initial REST surface between frontend and backend.
- [Technical Implementation Plan](./technical-implementation-plan.md) defines repo layout, tooling, adapters, and build sequence.
- [MVP Spec](./mvp-spec.md) defines the exact first product behavior and acceptance criteria.
- [Pre-Implementation Decisions](./pre-implementation-decisions.md) records account model, idempotency, photo storage, fallback, CI, and runbook decisions.
- [Runbook](./runbook.md) will define local startup and smoke-test steps once code exists.
- [Engineering Priorities](./engineering-priorities.md) defines what should be built first and what should be deferred.
- [bunq Hackathon Toolkit Reference](./integrations/bunq-hackathon-toolkit.md) defines how to use the local toolkit safely.
- [Backend Agent Guide](./agents/backend.md) defines backend/API implementation guidance.
- [Frontend Agent Guide](./agents/frontend.md) defines Next.js implementation guidance.
- [UI/UX Agent Guide](./agents/ui-ux.md) defines mobile product and visual guidance.
- [Agent Orchestration Guide](./agents/orchestration.md) defines when and how to use multiple coding agents.

## Working Principles

- Optimize for one convincing end-to-end loop before broad feature coverage.
- Keep the demo resilient: AI and bunq calls need explicit fallback or retry behavior.
- Treat real money movement, even in sandbox, as the product-defining proof.
- Keep state simple and inspectable until the core flow is stable.
- Prefer mobile-first implementation decisions because the product is camera-led.
