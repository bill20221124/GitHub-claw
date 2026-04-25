# Skills — Discovery, Installation & Usage

> Project-level skills for this AI workspace.  
> Every session reads this file to discover what capabilities are available.

---

## Directory Convention

```
.agents/skills/
├── README.md          ← this file (skill index)
└── <skill-name>/
    └── skill.md       ← skill definition (required)
    └── ...            ← optional helper scripts / prompts
```

Rules:
- Each skill lives in its own sub-directory under `.agents/skills/`.
- The directory name is the **skill ID** (lowercase, hyphen-separated).
- Every skill directory **must** contain a `skill.md` that describes the skill.

---

## Discovering Skills

At the start of a session, list available skills:

```bash
ls .agents/skills/
```

Then read the `skill.md` of any skill you want to use:

```bash
cat .agents/skills/<skill-name>/skill.md
```

---

## Installing a Skill

1. Create a new directory: `.agents/skills/<skill-name>/`
2. Add a `skill.md` following the template below.
3. Commit the directory.

### `skill.md` Template

Every skill file MUST start with a YAML front-matter block:

```yaml
---
id: <kebab-case-skill-id>         # must match directory name
triggers:                         # slash commands or labels that activate
  commands: ["/<name>"]
  labels:   []
inputs:                           # JSON-schema-ish, documentation only in Phase 1
  issue_or_pr_body: string
  args: string
outputs:
  format: markdown
  sections: [Summary, Details]
model_tier: simple                # simple | complex
---
```

Followed by the prose sections:

```markdown
# Skill: <Name>

## Purpose
One-sentence description of what this skill does.

## When to Use
Describe the situations or trigger phrases that should activate this skill.

## Inputs
List any required context or parameters.

## Steps
Numbered procedure the agent follows when executing this skill.

## Outputs
What the agent produces or returns after running this skill.
```

A ready-made starter lives at `.agents/skills/_template/skill.md` — copy that
directory and rename it to your new skill ID.

---

## Using a Skill

1. Identify the relevant skill from the index above.
2. Read its `skill.md`.
3. Follow the **Steps** section precisely.
4. Record any significant outputs per the skill's **Outputs** section.

---

## Skill Index

| Skill ID   | Purpose |
|------------|---------|
| [summarize](./summarize/skill.md) | Summarize a file, PR, or issue into TL;DR + Key Points + Open Questions. |
| [plan](./plan/skill.md) | Decompose a coarse goal into a reviewable, ordered checklist. |
| [review](./review/skill.md) | Critical review of a pull request's diff with actionable feedback. |
| [memory-write](./memory-write/skill.md) | Propose a `MEMORY.md` patch that fossilises a concluded discussion. |
| [ui-ux-pro-max](./ui-ux-pro-max/skill.md) | AI-powered design intelligence: 67 styles, 161 color palettes, 57 font pairings, 99 UX guidelines, 25 chart types across 16 stacks. Installed via `uipro-cli`. |

> Directory names beginning with `_` (e.g. `_template`) are scaffolding, not real skills,
> and are excluded from the dispatcher's whitelist.
