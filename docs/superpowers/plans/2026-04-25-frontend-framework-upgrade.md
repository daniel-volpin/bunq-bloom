# Frontend Framework Upgrade Implementation Plan

**Goal:** Upgrade the Next.js frontend to Next 16 and React 19 while preserving current application behavior and keeping Tailwind on v3.
**Architecture:** This change is a bounded framework/tooling upgrade inside `apps/web`. Package versions and minimal config/scripts will be updated first, then validated with typecheck, lint, and build, with only compatibility fixes added if the upgraded toolchain requires them.
**Tech Stack:** Next.js, React, TypeScript, ESLint, Tailwind CSS, npm

---

### Task 1: Upgrade Core Frontend Packages

**Files:**
- Modify: `apps/web/package.json`
- Modify: `apps/web/package-lock.json`

- [ ] Update `next`, `react`, `react-dom`, and `eslint-config-next` to the target compatible versions.
- [ ] Run `cd apps/web && npm install` to regenerate the lockfile.
- [ ] Run `cd apps/web && npm run typecheck`.
- [ ] Commit.

### Task 2: Fix Tooling Compatibility

**Files:**
- Modify: `apps/web/package.json`
- Modify if needed: `apps/web/next.config.mjs`
- Modify if needed: `apps/web/tsconfig.json`

- [ ] Run `cd apps/web && npm run lint` and capture the first concrete breakage.
- [ ] Apply the smallest compatibility fix required by the upgraded toolchain.
- [ ] Re-run `cd apps/web && npm run lint`.
- [ ] Commit.

### Task 3: Validate Production Build

**Files:**
- Modify only if build requires a compatibility fix.

- [ ] Run `cd apps/web && npm run build`.
- [ ] If build fails, apply the smallest build-specific compatibility fix.
- [ ] Re-run `cd apps/web && npm run build`.
- [ ] Summarize remaining dependency risk, if any.
- [ ] Commit.