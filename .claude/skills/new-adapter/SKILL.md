---
name: new-adapter
description: Add a new integration adapter (Claude, bunq, or other external service)
---

Add a new integration adapter: $ARGUMENTS

1. Read `docs/agents/backend.md` and the relevant integration doc
2. Read the existing fake adapter to understand the interface
3. Create a new client file under `apps/api/app/integrations/`
4. Match the interface of the fake adapter (same method signatures)
5. Wire it into `apps/api/app/dependencies.py` behind the appropriate env flag
6. Add env vars to `apps/api/.env.example` and `apps/api/app/settings.py`
7. Add tests using a test double for the external dependency
8. Update `apps/api/app/routes/health.py` if the integration needs health reporting
9. Run `cd apps/api && pytest tests`