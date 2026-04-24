---
name: new-endpoint
description: Add a new API endpoint to the FastAPI backend
---

Add a new API endpoint: $ARGUMENTS

1. Read `docs/api-contracts.md` and `docs/domain-model.md`
2. Add request/response models in `apps/api/app/models/api.py`
3. Add business logic in the relevant service under `apps/api/app/services/`
4. Add the route in the relevant file under `apps/api/app/routes/`
5. Register the router in `apps/api/app/main.py` if it is a new route module
6. Add tests in `apps/api/tests/`
7. Update `docs/api-contracts.md` with the new endpoint shape
8. Run `cd apps/api && pytest tests`