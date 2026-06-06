# New user checklist

ForgeBench `doctor` includes these onboarding checks:

- [ ] **Python 3.10+** and package import
- [ ] **git** available (for PR worktree checkout)
- [ ] **gh** authenticated (for `review-pr`)
- [ ] Writable **forgebench-output/**
- [ ] Run **`forgebench demo`**
- [ ] **`forgebench.yml`** or `.github/forgebench.yml` present
- [ ] **CI workflow** at `.github/workflows/forgebench.yml` (teams)
- [ ] **Team onboarding doc** at `docs/forgebench-onboarding.md` (enterprise init)

## Recommended first hour

1. `forgebench doctor`
2. `forgebench demo`
3. `forgebench status`
4. Install VS Code or JetBrains extension
5. `forgebench init` or `forgebench init --enterprise`
6. `forgebench policy test --tests examples/policy_tests`
7. `forgebench review-pr` on a real PR (dry run first)