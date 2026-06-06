# Team policy

ForgeBench layers policy via `extends`, `include`, and `FORGEBENCH_ORG_POLICY`.

See the full guide in the repository: [docs/team-enterprise.md](https://github.com/caissonhq/forgebench/blob/main/docs/team-enterprise.md).

## Enterprise init layout

```text
org-policy/forgebench-org.yml    # org defaults
forgebench.yml                   # repo overlay (extends org)
.github/forgebench.yml           # trusted CI policy
```

Run policy regression tests after changes:

```bash
forgebench policy test --tests examples/policy_tests
```