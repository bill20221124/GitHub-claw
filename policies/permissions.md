# Workflow Permissions

| Workflow              | contents | issues | pull-requests | models | id-token | notes |
|-----------------------|----------|--------|---------------|--------|----------|-------|
| dispatcher.yml        | read     | write  | write         | read   | none     | main entry |
| summary.yml           | read     | write  | none          | read   | none     | legacy; retire in Phase 2 |
| validate-skills.yml   | read     | none   | none          | none   | none     | static check |
| jekyll-gh-pages.yml   | read     | none   | none          | none   | write*   | * only for Pages deploy |
| static.yml            | read     | none   | none          | none   | write*   | * only for Pages deploy |

## External Domain Allowlist

- `api.github.com`
- `models.github.ai` (GitHub Models)
- `api.anthropic.com` (only when `ANTHROPIC_API_KEY` is configured)

Any call outside this list must be rejected by the skill.

## Principle
Each workflow should request the minimum permissions it needs. If a workflow needs an
elevated permission for a single step, prefer splitting it into a dedicated workflow with
the narrower scope rather than widening the entire file.
