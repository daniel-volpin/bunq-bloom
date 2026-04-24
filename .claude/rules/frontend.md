---
paths:
  - "apps/web/**"
---

# Frontend Rules

- Do not call Claude or bunq from the frontend.
- Use typed API client functions matching `docs/api-contracts.md`.
- Design and test at 390px mobile viewport first.
- Tap targets must be at least 44px.
- Use progressive loading states for long-running completion calls.
- Keep camera capture as the primary interaction, not a file-upload afterthought.

## Testing

```bash
cd apps/web && npm run typecheck && npm run lint
```

## Completion States to Handle

- approved and paid
- rejected with kid-friendly reason
- approved but payment failed (retryable)
- AI fallback mode
- bunq fallback mode
- network failure

Do not collapse these into one generic error message.