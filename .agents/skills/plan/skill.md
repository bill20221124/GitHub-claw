---
id: plan
triggers:
  commands: ["/plan"]
  labels:   []
inputs:
  issue_or_pr_body: string
  args: string   # the goal
outputs:
  format: markdown
  sections: [Goal, Assumptions, Checklist, Risks]
model_tier: complex
---

# Skill: plan

## Purpose
Decompose a coarse goal into a reviewable, ordered checklist.

## When to Use
`/plan <goal>` in an issue comment.

## Inputs
- `args`: the goal statement (everything after `/plan`).
- Standing memory: `MEMORY.md`, `AGENTS.md` Interconnection Map.

## Steps
1. Restate the goal in one sentence; list explicit assumptions.
2. Produce a 5–12 item checklist; each item is a ≤ 1-day task.
3. Attach a Risks section noting files that will be touched and the
   Interconnection-Map cascades they imply.
4. Do NOT modify any file; this skill only proposes a plan.

## Outputs

```markdown
**Goal.** One sentence.

**Assumptions.**
- ...

**Checklist.**
- [ ] ...
- [ ] ...

**Risks.**
- Files touched: `...`
- Cascades: `...`
```
