---
name: new-screen
description: Add a new page or screen to the Next.js frontend
---

Add a new frontend screen: $ARGUMENTS

1. Read `docs/api-contracts.md` and `docs/agents/ui-ux.md`
2. Add types to `apps/web/lib/types.ts` if the API shape is new
3. Add API client method to `apps/web/lib/api-client.ts`
4. Create the page under `apps/web/app/`
5. Create components under `apps/web/components/`
6. Add navigation in `apps/web/components/bottom-nav.tsx` if needed
7. Run `cd apps/web && npm run typecheck && npm run lint`
8. Test at 390px viewport width