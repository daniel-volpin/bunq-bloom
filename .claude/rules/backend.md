---
paths:
  - "apps/api/**"
---

# Backend Rules

- Use typed Pydantic request and response models.
- Keep route handlers thin — business logic belongs in services.
- Keep integrations behind adapter interfaces with fake and real implementations.
- Do not expose integration errors directly to the frontend — return stable error codes.
- Validate image size and content type before sending to AI.
- Use idempotency keys for completion/payment flows.

## Layering

```
routes -> services -> repositories/integration clients
```

## Testing

```bash
cd apps/api && pytest tests
pytest tests/test_gig_service.py::test_name  # single test
```

Start with fake adapters. Real Claude and bunq tests must be opt-in.