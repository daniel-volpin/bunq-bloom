# Agent Orchestration Guide

Use this guide when multiple coding agents or specialized assistants are available.

The goal is faster, safer delivery of the core loop, not process for its own sake.

## Principles

- Start simple. Use one agent for small, tightly coupled changes.
- Delegate only when work can proceed in parallel without blocking the main path.
- Keep ownership explicit: each agent needs a clear scope, files, and expected output.
- Use contracts as handoff boundaries. For this repo, `docs/api-contracts.md` is the primary backend/frontend boundary.
- Prefer workflows over open-ended autonomy for predictable tasks.
- Verify outputs with tests, diffs, screenshots, or smoke checks.
- Keep the orchestrating agent responsible for integration quality.

## When To Use Multiple Agents

Use multiple agents for:

- independent backend and frontend slices with a stable API contract
- parallel research on separate integration risks
- UI/UX review while backend implementation continues
- test or review passes that can run while implementation proceeds
- large changes with disjoint file ownership

Do not use multiple agents for:

- tiny changes where coordination costs exceed benefit
- tasks where the next local step depends on the delegated answer
- changes that require editing the same files in parallel
- unclear requirements where the first step should be a decision, not implementation

## Recommended Roles

Backend agent owns:

- domain truth
- FastAPI contracts
- local state
- idempotency
- photo storage
- Claude adapter
- bunq adapter
- payment safety

Frontend agent owns:

- typed API consumption
- client flow state
- camera interaction
- loading and retry states
- completion result rendering
- mobile app shell

UI/UX agent owns:

- mobile-first interaction quality
- kid and parent copy
- fallback honesty
- completion clarity
- camera-step friction
- visual hierarchy

Integrator/orchestrator owns:

- keeping the core loop coherent
- merging work
- resolving contract mismatches
- running verification
- deciding when to stop expanding scope

## Contract-First Handoff

For cross-stack work, agree on:

- endpoint path and method
- request shape
- success response shape
- error shape and stable error codes
- fallback mode values
- loading and retry expectations
- test fixtures or fake responses

The critical contract is:

```text
POST /api/gigs/{gig_id}/complete
```

This endpoint joins camera upload, AI verification, bunq payment, idempotency, balance, and completion UI. Changes to it should be coordinated across backend, frontend, and UI/UX.

## Safe Parallel Tracks

Good first parallel split:

- Backend: fake-adapter FastAPI endpoints, state transitions, tests.
- Frontend: app shell, typed API client, screens against documented fixtures.
- UI/UX: camera flow, completion state copy, fallback-mode copy.

Avoid real Claude and real bunq work until the fake vertical slice works.

## Delegation Prompt Checklist

When assigning a sub-agent, include:

- task goal
- files or modules owned by that agent
- files or modules they must not edit
- relevant docs to read
- expected output
- verification required
- known constraints or risks

Example:

```text
Implement fake payment adapter only.
Own files under apps/api/app/integrations/fake_payment_client.py and related tests.
Do not edit routes or frontend.
Read docs/pre-implementation-decisions.md and docs/api-contracts.md.
Return changed files and test command results.
```

## Review Gates

Require review or explicit integration check when:

- `docs/api-contracts.md` changes
- payment/idempotency logic changes
- fallback mode behavior changes
- camera capture flow changes
- completion screen behavior changes
- real bunq or Claude integration is enabled

## External Reference Principles

This guide follows public guidance from OpenAI and Anthropic:

- OpenAI Agents SDK: use code-first agent workflows when the application owns orchestration, tools, approvals, and state.
- OpenAI agent evals: inspect traces first, then move to repeatable evals when behavior stabilizes.
- Anthropic building effective agents: start with simple composable workflows, add agent complexity only when useful, keep tools and interfaces clear, and test in sandboxed environments.

