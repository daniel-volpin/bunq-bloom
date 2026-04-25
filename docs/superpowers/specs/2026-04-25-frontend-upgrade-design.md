# Frontend Upgrade Design

**Goal:** Upgrade the web app to a production-safer modern stack by moving to Next 16 and React 19 while keeping the existing app behavior and avoiding a Tailwind migration in the same change.

**Recommended Approach:** Perform a bounded framework upgrade: bump `next`, `react`, `react-dom`, and matching Next ESLint tooling together; keep Tailwind 3 and the existing app/router structure unchanged; then fix only the minimum config or script breakages exposed by validation.

**Why This Approach:** It removes the highest-risk outdated framework packages without coupling the work to a separate styling-system migration. The main expected compatibility surface is package versions, lint command behavior, and small config changes rather than broad UI rewrites.

**Success Criteria:**
- `apps/web` installs cleanly with a regenerated lockfile.
- `npm run typecheck` passes.
- `npm run lint` passes.
- `npm run build` passes.
- No frontend API contract or UI behavior changes are introduced intentionally.