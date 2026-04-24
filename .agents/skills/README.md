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
| [summarize](./summarize/skill.md) | Summarize a file, PR, or issue into a concise set of bullet points. |
| [ui-ux-pro-max](./ui-ux-pro-max/skill.md) | AI-powered design intelligence: 67 styles, 161 color palettes, 57 font pairings, 99 UX guidelines, 25 chart types across 16 stacks. Installed via `uipro-cli`. |
