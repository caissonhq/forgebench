# Air-Gapped and Self-Hosted Deployment

ForgeBench is designed for **offline-first** operation. No network calls are made unless you explicitly enable optional features.

## Offline by default

| Feature | Network required |
|---------|------------------|
| `forgebench review` | No |
| `forgebench policy test/simulate` | No |
| `forgebench policy serve` | No (local HTTP only) |
| `forgebench github-app serve` | No (local webhook receiver) |
| Telemetry | No (local JSONL only) |
| Feedback | No |
| `--llm-provider openai` | Yes (explicit opt-in) |
| `--llm-provider command` | No |
| `forgebench policy verify --grok` | Yes (explicit opt-in) |

Disable external calls in enterprise environments by omitting `FORGEBENCH_LLM_API_KEY`, `FORGEBENCH_GROK_API_KEY`, and LLM flags.

## Docker Compose

```bash
export FORGEBENCH_GITHUB_WEBHOOK_SECRET="$(openssl rand -hex 32)"
export FORGEBENCH_POLICY_ADMIN_TOKEN="$(openssl rand -hex 32)"
docker compose -f deployments/docker-compose.yml up --build
```

Mount your policy workspace read-only at `/workspace`.

## Helm (skeleton)

```bash
helm install forgebench deployments/helm/forgebench \
  --set image.repository=your-registry/forgebench \
  --set image.tag=0.9.0
```

Create Kubernetes secrets for `FORGEBENCH_POLICY_ADMIN_TOKEN` and `FORGEBENCH_GITHUB_WEBHOOK_SECRET` before deploying.

## Air-gapped install

1. Build wheel on a connected build host: `python -m build`
2. Transfer `dist/forgebench-*.whl` and `requirements-lock.txt` to the air-gapped host
3. Install: `pip install --no-index forgebench-*.whl -r requirements-lock.txt`
4. Verify: `forgebench doctor`
5. Run reviews locally with no outbound connectivity

## Security tokens

- `FORGEBENCH_GITHUB_WEBHOOK_SECRET` — required for GitHub App webhook service
- `FORGEBENCH_POLICY_ADMIN_TOKEN` / `FORGEBENCH_POLICY_READONLY_TOKEN` — policy service RBAC
- `FORGEBENCH_ALLOW_INSECURE_BIND=1` — only when binding beyond loopback in controlled networks

See [docs/security/soc2-readiness.md](security/soc2-readiness.md) for compliance mapping.