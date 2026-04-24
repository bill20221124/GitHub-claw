# MEMORY.md — Long-Term Memory

> Updated by the AI assistant at the end of tasks that produce a lasting outcome.  
> This file is read at the start of every new session to restore context.

---

## Owner Preferences

- Prefer concise, practical files over elaborate documentation.
- Keep the workspace lightweight and scalable.
- Separate long-term memories from temporary task notes.

---

## Repository Purpose

This repository is a persistent personal AI workspace used with GitHub Copilot.  
It stores role definitions, memories, and working artifacts so that context survives across sessions.

---

## Standing Context

- Project-level skills live in `.agents/skills/<skill-name>/skill.md`.
- New skills follow the template in `.agents/skills/README.md`.
- `validate-skills` workflow enforces that every skill directory has a `skill.md`.

---

## Task Log

| Date | Summary |
|---|---|
| 2026-04-24 | Added `.agents/skills/` skill system: discovery index, `summarize` example skill, `validate-skills` workflow, and Skills section in AGENTS.md. |
| 2026-04-24 | Installed `ui-ux-pro-max` skill via `npx uipro-cli init --ai copilot` (source: github.com/nextlevelbuilder/ui-ux-pro-max-skill). Files at `.github/prompts/ui-ux-pro-max/`. Applied skill to optimize `index.html`: added Plus Jakarta Sans font, skip link, focus-visible styles, active nav scroll spy, CSS-class-driven mobile menu, and prefers-reduced-motion support. |
