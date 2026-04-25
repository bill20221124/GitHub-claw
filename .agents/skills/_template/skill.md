---
id: _template
triggers:
  commands: []
  labels: []
inputs:
  issue_or_pr_body: string
outputs:
  format: markdown
  sections: [Summary]
model_tier: simple
---

# Skill: _template

## Purpose
One sentence describing what the skill does.

## When to Use
One-line trigger description (slash command, label, or situation).

## Inputs
List inputs the skill expects.

## Steps
1. ...
2. ...

## Outputs
Markdown with the sections listed in the front-matter `outputs.sections`.
