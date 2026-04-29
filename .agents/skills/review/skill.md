---
id: review
triggers:
  commands: ["/review"]
  labels:   []
inputs:
  pull_request_diff: string
outputs:
  format: markdown
  sections: [Summary, Findings, Suggestions, Blocking?]
model_tier: complex
cognitive_mode: deliberative   # reflexive | deliberative | reflective
collab_tier: suggest           # suggest | propose | execute
---

# Skill: review

## Purpose
Critical review of a pull request's diff with actionable feedback.

## When to Use
`/review` in a PR comment.

## Inputs
- `GITHUB_EVENT_PATH` payload → PR metadata.
- `gh pr diff <num>` output (fetched by `run_skill.py` before the LLM call).
- `AGENTS.md` Interconnection Map (for cascade detection).

## Steps
1. Read the diff and the Interconnection Map.
2. Summarize the changes in ≤ 4 bullets.
3. Emit `Findings`: each finding tagged `[correctness|style|security|interconnection]`.
4. Emit `Suggestions`: concrete diffs or file paths to change.
5. End with `Blocking?` = Yes / No and a one-line reason.

## Outputs

```markdown
**Summary.**
- ...

**Findings.**
- [correctness] ...
- [interconnection] ...

**Suggestions.**
- ...

**Blocking?** Yes/No — one-line reason.
```
