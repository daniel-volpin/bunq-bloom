---
name: fix-completion-bug
description: Debug and fix issues in the gig completion flow
---

Fix a completion flow bug: $ARGUMENTS

1. Read `apps/api/app/services/gig_service.py` — the `complete_gig` method is the core
2. Read `apps/api/tests/test_gig_service.py` — understand existing test coverage
3. Write a failing test that reproduces the bug
4. Fix the issue in the service layer (not in routes)
5. Run `cd apps/api && pytest tests` — all tests pass including the new one
6. Check if the fix changes any response shape — if so, update `docs/api-contracts.md`