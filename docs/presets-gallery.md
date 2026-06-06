# ForgeBench Presets Gallery

Curated starter guardrails for common stacks. Install with one command — no copy-paste from docs.

## Browse presets

```bash
forgebench presets list
```

## Install a preset

```bash
forgebench presets install python
forgebench presets install nextjs --force
```

Bundled presets live in `examples/presets/` in the ForgeBench repository.

| Preset | Stack | Best for |
|--------|-------|----------|
| `python` | Python | `pyproject.toml` / unittest services |
| `node` | Node.js | npm packages and APIs |
| `nextjs` | Next.js | App Router full-stack apps |

After install, edit `protected_behavior` and `forbidden_patterns` for your team.

## Export your own preset

Share a tuned policy with another repo or team:

```bash
forgebench presets export --file forgebench.yml --out ./my-team-preset
```

Copy the output directory into `examples/presets/<name>/` or attach to GitHub Discussions.

## Related

- [Install methods](install-methods.md)
- [Team init wizard](team-enterprise.md)
- [forgebench.yml schema](forgebench-yml-schema.md)