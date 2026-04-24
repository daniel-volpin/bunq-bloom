# GitHub Setup

GitHub CLI is installed, but authentication must be valid before remote setup can run.

## Re-authenticate

```bash
gh auth login -h github.com
```

## Create The Repository

From `/Users/pnl11e4o/Documents/Bunq`:

```bash
git init
git add .
git commit -m "Initialize bunq Bloom project docs"
gh repo create bunq-bloom --private --source=. --remote=origin --push
```

Use `--public` instead of `--private` only if the team explicitly wants the hackathon repo public.

## Create Labels

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

## Create Milestones

```bash
gh api repos/:owner/:repo/milestones -f title="M1 Core Loop Fake Adapters"
gh api repos/:owner/:repo/milestones -f title="M2 Real Claude + bunq"
gh api repos/:owner/:repo/milestones -f title="M3 Mobile Camera UX"
gh api repos/:owner/:repo/milestones -f title="M4 Demo Hardening"
```

## Create A GitHub Project

GitHub Projects v2 is easiest to create from the GitHub UI:

1. Open the repository on GitHub.
2. Go to `Projects`.
3. Create a new project named `bunq Bloom Build`.
4. Add fields and views from `docs/project-tracker.md`.
5. Convert the tracker items into issues and add them to the project.

The CLI can automate this later with `gh project`, but the owner scope and account type should be confirmed first.

