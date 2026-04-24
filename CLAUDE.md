@AGENTS.md

# Claude Code

## Project Status

M1 (Core Loop Fake Adapters) is complete. Current priority is **M2 (Real Claude + bunq)**.
Critical missing piece: `apps/api/app/integrations/claude_client.py`.

## Verify After Changes

```bash
# Backend
cd apps/api && pytest tests

# Frontend
cd apps/web && npm run typecheck && npm run lint
```

Always run the relevant checks before considering a task done.

## State Management

```bash
# Reset local state
rm -rf apps/api/data

# Inspect state
cat apps/api/data/state.json | python3 -m json.tool
```

## Critical Rules

- NEVER commit, push, reset, or make destructive git changes without explicit instruction.
- NEVER read `.env`, `bunq_context.json`, `*.key`, or `*.pem` files.
- NEVER print, log, or persist API keys, tokens, or private keys.
- NEVER run bunq toolkit scripts unless that is the explicit current task.
- NEVER call real Claude or bunq APIs in default test runs.
- NEVER modify files in `hackathon_toolkit-main/` — it is vendored reference code.
- Frontend must NEVER call Claude or bunq directly.
- A gig must NEVER be paid twice.
- A gig must NEVER be marked `paid` unless payment succeeded or `fallback_mode: true`.

## Key Contract

`POST /api/gigs/{gig_id}/complete` joins camera upload, AI verification, bunq payment, idempotency, and balance. Changes require cross-stack coordination. See `docs/api-contracts.md`.

## Source of Truth

Read these in order when in doubt:

1. `docs/api-contracts.md` — API shapes
2. `docs/domain-model.md` — entities and state transitions
3. `docs/system-architecture.md` — boundaries and flow
4. `docs/engineering-priorities.md` — build order
5. `docs/pre-implementation-decisions.md` — resolved design questions

## Dependencies

```bash
# Backend: add to pyproject.toml then reinstall
cd apps/api && pip install -e ".[dev]"

# Frontend
cd apps/web && npm install <package>
```