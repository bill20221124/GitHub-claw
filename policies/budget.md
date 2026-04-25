# Daily Budget

daily_tokens: 200000
per_skill_tokens: 40000
max_runs_per_hour: 30

## Rationale
Phase 1 uses GitHub Models (free tier) by default. The cap exists to catch runaway loops,
not to control spend. Tighten when Anthropic API is enabled for complex skills.

## How it is enforced
`scripts/append_audit.py --phase check` parses the `daily_tokens:` line above and compares
against the sum of `Tokens` columns in today's `memory/audit/YYYY-MM-DD.md`. If the cap is
reached, the script exits with code 78 (GitHub Actions "neutral") and the dispatcher posts
a "today's quota is exhausted" comment instead of invoking the skill.

## Future (Phase 2)
- Add `monthly_usd` line once the Anthropic API is wired in.
- Add per-skill caps that override `per_skill_tokens` for specific skills.
