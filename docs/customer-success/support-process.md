# Support Process

## Channels

1. **GitHub Discussions** — community + Team tier (public, searchable)
2. **Email** — hello@forgebench.dev (include license ID for Team/Enterprise)
3. **GitHub Issues** — bugs and feature requests with repro templates

## Intake template (email)

```
Subject: [Team|Enterprise] <org> — <short summary>

License ID: (from forgebench license status)
ForgeBench version: (forgebench --version)
OS:
Command:
Expected:
Actual:
```

## Triage

| Label | Owner | SLA |
|-------|-------|-----|
| `bug` | Engineering | per SLA |
| `docs` | DX | 3 days |
| `license` | CS | 1 day |
| `enterprise` | CSM + Eng | per contract |

## Self-serve first

Direct customers to:

```bash
forgebench doctor
forgebench status
forgebench license status
forgebench --explain   # on errors
```

Docs: site-docs/troubleshooting.md