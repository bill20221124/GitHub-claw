---
id: memory-write
triggers:
  commands: ["/memory-write"]
  labels:   []
inputs:
  issue_or_pr_body: string
  thread_comments: string
  args: string   # optional hint
outputs:
  format: markdown
  sections: [Proposed Patch, Rationale]
model_tier: simple
---

# Skill: memory-write

## Purpose
Propose an addition or change to `MEMORY.md` based on a concluded discussion.

## When to Use
`/memory-write` at the end of an issue thread, when a decision has been reached.

## Inputs
- Thread body + comments.
- Current `MEMORY.md`.

## Steps
1. Identify the single durable fact worth remembering.
2. Decide which section it belongs to:
   `Owner Preferences` / `Standing Context` / `Known Interconnections` / `Task Log`.
3. Produce a unified diff in the `Proposed Patch` section — do NOT commit.
4. Explain in `Rationale` why this fact is durable (vs. ephemeral / better in `memory/<date>.md`).

## Outputs

```markdown
**Proposed Patch.**
\`\`\`diff
--- a/MEMORY.md
+++ b/MEMORY.md
@@
- existing line
+ new line
\`\`\`

**Rationale.** One short paragraph.
```
