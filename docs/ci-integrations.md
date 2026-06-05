# CI Integrations

ForgeBench is CLI-first. These recipes run the same local review flow in common CI systems.

## GitHub Actions

Primary integration: [action/README.md](../action/README.md)

```yaml
- uses: caissonhq/forgebench@v0.9.0
  with:
    guardrails-path: forgebench.yml
    run-checks: "true"
    post-check-run: "true"
```

## GitLab CI

Example: [integrations/gitlab-ci/.gitlab-ci.yml](../integrations/gitlab-ci/.gitlab-ci.yml)

```yaml
forgebench:
  image: python:3.12-slim
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  script:
    - pip install forgebench
    - forgebench doctor
    - forgebench review-pr "$CI_MERGE_REQUEST_PROJECT_URL/-/merge_requests/$CI_MERGE_REQUEST_IID"
      --guardrails forgebench.yml
      --checkout-pr
      --run-checks
  artifacts:
    paths:
      - forgebench-output/
```

Set org policy when needed:

```yaml
variables:
  FORGEBENCH_ORG_POLICY: /builds/platform-policy/forgebench-org.yml
```

## CircleCI

Example: [integrations/circleci/config.yml](../integrations/circleci/config.yml)

```yaml
jobs:
  forgebench:
    docker:
      - image: cimg/python:3.12
    steps:
      - checkout
      - run: pip install forgebench
      - run: forgebench doctor
      - run: |
          forgebench review-pr "$CIRCLE_PULL_REQUEST" \
            --guardrails forgebench.yml \
            --checkout-pr \
            --run-checks
      - store_artifacts:
          path: forgebench-output
```

## Jenkins

Example: [integrations/jenkins/Jenkinsfile](../integrations/jenkins/Jenkinsfile)

```groovy
stage('ForgeBench') {
  steps {
    sh 'pip install forgebench'
    sh 'forgebench doctor'
    sh '''
      forgebench review-pr "${CHANGE_URL}" \
        --guardrails forgebench.yml \
        --checkout-pr \
        --run-checks
    '''
    archiveArtifacts artifacts: 'forgebench-output/**', allowEmptyArchive: true
  }
}
```

## Shared policy in CI

1. Check out or mount a trusted org policy file.
2. Export `FORGEBENCH_ORG_POLICY` before `forgebench review` or `review-pr`.
3. Validate shared files in a separate job:

```bash
forgebench validate --file org-policy/forgebench-org.yml --strict
forgebench dashboard --repo . --guardrails forgebench.yml
```

## SARIF and annotations

- GitHub Check Runs: `forgebench review-pr ... --check-run`
- SARIF artifact: `forgebench-output/forgebench-report.sarif.json`

## Repair workflow

Download CI artifacts and run:

```bash
forgebench repair --out forgebench-output
```

Paste the repair prompt into Cursor, Codex, or Claude Code. See [cursor-integration.md](cursor-integration.md).