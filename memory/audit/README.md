# Audit Log

One markdown file per UTC date, written by `scripts/append_audit.py`.

## Row schema

| Column | Meaning |
|---|---|
| Time   | ISO-8601 UTC timestamp |
| Phase  | `check` (budget pre-flight) or `finish` |
| Skill  | skill id |
| Status | `success` / `failure` / `refused` / `budget-exceeded` |
| Tokens | total tokens consumed for this run |
| Run    | GitHub Actions run id (link via `https://github.com/<owner>/<repo>/actions/runs/<id>`) |

## Retention
Files older than 90 days may be archived into `memory/audit/archive/YYYY-MM.md`
(aggregated counts only) by a Phase 2 cleanup workflow.

## Why audit lives under `memory/`
Audit rows are durable evidence of what the agent did. Treating them as memory keeps
"what the agent decided" and "what the agent ran" in one place, so future maintainers
can reconstruct context from a single tree.
