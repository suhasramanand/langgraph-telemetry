# Contributing

Thanks for helping improve LangGraph-Telemetry.

## Workflow

- Open an issue for bugs or feature discussion when the change is non-trivial.
- Keep pull requests focused; avoid drive-by refactors.
- Follow **Build, test, and unblock** (see `docs/development.md`): run **ruff** + **pytest** after Python edits, **npm run lint** / **npm run build** after dashboard edits. If two distinct fixes fail, search official docs or GitHub issues before continuing.

## Project layout

| Path | Purpose |
| ---- | ------- |
| `packages/langgraph-telemetry` | PyPI package (`langgraph_telemetry`) |
| `dashboard` | Next.js UI |
| `examples/basic_agent` | Metrics + Compose demo |
| `docs` | Extra documentation |
| `.cursor/rules` | Cursor project rules |

## Code of Conduct

This project adopts the Contributor Covenant (see `CODE_OF_CONDUCT.md`).
