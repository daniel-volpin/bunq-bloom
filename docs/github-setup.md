# GitHub Setup

GitHub is configured for this project.

Repository:

- `https://github.com/daniel-volpin/bunq-bloom`

Project board:

- `https://github.com/users/daniel-volpin/projects/6`

## Current Setup

- Private repository created and pushed.
- Local `main` tracks `origin/main`.
- Issue templates and PR template are committed.
- Labels are created.
- Milestones are created.
- Backlog issues from `docs/project-tracker.md` are created.
- GitHub Project `bunq Bloom Build` is created, linked to the repository, and populated with issues.
- Custom project fields are created: `Area`, `Priority`, `Demo Risk`.

## Label Setup

These labels are already created. Re-run with `--force` only if they need to be repaired.

```bash
gh label create frontend --color 1D76DB
gh label create backend --color 0E8A16
gh label create ai --color 5319E7
gh label create bunq --color F9D0C4
gh label create docs --color 0075CA
gh label create priority:critical --color B60205
gh label create priority:high --color D93F0B
gh label create priority:medium --color FBCA04
gh label create demo-risk --color E11D21
```

## Milestone Setup

These milestones are already created.

```bash
gh api repos/:owner/:repo/milestones -f title="M1 Core Loop Fake Adapters"
gh api repos/:owner/:repo/milestones -f title="M2 Real Claude + bunq"
gh api repos/:owner/:repo/milestones -f title="M3 Mobile Camera UX"
gh api repos/:owner/:repo/milestones -f title="M4 Demo Hardening"
```

## Project Setup

Project fields:

- Status: default GitHub field
- Milestone: default GitHub field
- Labels: default GitHub field
- Area: custom single-select field
- Priority: custom single-select field
- Demo Risk: custom single-select field

Recommended manual views to add in the GitHub UI:

- `Core Loop Board`: grouped by Status, filtered to M1 and M2.
- `Demo Risks`: filtered to `demo-risk`.
- `Frontend`: filtered to `frontend`.
- `Backend + Integrations`: filtered to `backend`, `ai`, and `bunq`.
