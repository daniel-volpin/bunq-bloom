---
name: build-claude-client
description: Build the Claude Vision verification client for M2
disable-model-invocation: true
---

Build the real Claude Vision verification client.

1. Read `docs/pre-implementation-decisions.md` (Decision 4: AI Verification Schema)
2. Read `apps/api/app/integrations/fake_verification_client.py` for the interface
3. Read `apps/api/app/models/verification.py` for the output schema
4. Create `apps/api/app/integrations/claude_client.py`
5. Accept `gig`, `before_photo`, `after_photo` dicts
6. Build a prompt with gig title, description, checklist, and both images (base64)
7. Call the Anthropic API with Claude Vision
8. Parse response into `VerificationResultModel` schema
9. Handle invalid/missing model output as AI failure — do not pass raw output through
10. Wire into `apps/api/app/dependencies.py`: use when `BLOOM_USE_FAKE_AI=false` and `ANTHROPIC_API_KEY` is set
11. Add tests with a mocked Anthropic client
12. Run `cd apps/api && pytest tests`