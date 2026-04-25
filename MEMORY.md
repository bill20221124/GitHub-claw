# MEMORY.md — Long-Term Memory

> Updated by the AI assistant at the end of tasks that produce a lasting outcome.  
> This file is read at the start of every new session to restore context.

---

## Owner Preferences

- Prefer concise, practical files over elaborate documentation.
- Keep the workspace lightweight and scalable.
- Separate long-term memories from temporary task notes.
- **Always update `MEMORY.md` and check the Interconnection Map after every task — no exceptions.** Failure to do so is a critical workflow error.

---

## Repository Purpose

This repository is a persistent personal AI workspace used with GitHub Copilot.  
It stores role definitions, memories, and working artifacts so that context survives across sessions.

---

## Standing Context

- Project-level skills live in `.agents/skills/<skill-name>/skill.md`.
- New skills follow the template in `.agents/skills/README.md` (front-matter required: `id`, `triggers`, `outputs`, `model_tier`).
- `validate-skills` workflow enforces that every skill directory has a `skill.md` AND the required front-matter keys.
- Dispatcher entry point: `.github/workflows/dispatcher.yml`; slash commands routed via `scripts/route.py`.
- Prompt templates live in `prompts/` (`system.md` / `safety.md` / `skill-wrapper.md`).
- Policies in `policies/` define safety, budget, and the workflow permission matrix.
- Audit logs in `memory/audit/YYYY-MM-DD.md` (row schema in `memory/audit/README.md`).
- Phase 1 architecture blueprint: `docs/agent-architecture.md` (single source of truth for the agent design).

---

## Known Interconnections

The following files are linked — changing one requires checking the others:

| Changed | Must also check |
|---|---|
| `.agents/skills/<name>/skill.md` (add/remove/rename) | `.agents/skills/README.md` Skill Index · `MEMORY.md` Standing Context |
| `.agents/skills/README.md` | `AGENTS.md` Skills section · `MEMORY.md` Standing Context |
| `AGENTS.md` (workflow or structure) | `MEMORY.md` (if it references those conventions) |
| `MEMORY.md` (structure change) | `AGENTS.md` Memory Structure table |
| `.github/workflows/*.yml` (add/remove) | `MEMORY.md` Standing Context · `policies/permissions.md` |
| `index.html` (significant UI change) | `MEMORY.md` Task Log |
| `prompts/*` | `scripts/run_skill.py` · skill files that depend on the wrapper format |
| `policies/*` | `.github/workflows/dispatcher.yml` · `scripts/append_audit.py` |
| `scripts/*` | `docs/agent-architecture.md` · `.github/workflows/dispatcher.yml` |
| `docs/agent-architecture.md` | `AGENTS.md` Interconnection Map · `MEMORY.md` Standing Context |
| `memory/audit/README.md` | `scripts/append_audit.py` (row schema must match) |
| Any task completed | `MEMORY.md` Task Log |
| `docs/agent-cognitive-architecture.md` | `MEMORY.md` Standing Context `docs/agent-architecture.md`(交叉引用) |

---

## Task Log

| Date | Summary |
|---|---|
| 2026-04-24 | Added `.agents/skills/` skill system: discovery index, `summarize` example skill, `validate-skills` workflow, and Skills section in AGENTS.md. |
| 2026-04-24 | Installed `ui-ux-pro-max` skill via `npx uipro-cli init --ai copilot` (source: github.com/nextlevelbuilder/ui-ux-pro-max-skill). Files at `.github/prompts/ui-ux-pro-max/`. Applied skill to optimize `index.html`: added Plus Jakarta Sans font, skip link, focus-visible styles, active nav scroll spy, CSS-class-driven mobile menu, and prefers-reduced-motion support. |
| 2026-04-24 | Systemic fix: added Non-Negotiable Rules + Interconnection Map to `AGENTS.md`; added Known Interconnections section and owner preference for mandatory memory updates to `MEMORY.md`. Enforces that every future task updates memory and cascades changes. |
| 2026-04-24 | Wrote Phase 1 architecture blueprint: `docs/agent-architecture.md`. Defines dispatcher single-entry, three-part prompt, four core skills (`summarize`/`plan`/`review`/`memory-write`), policies, and audit log. |
| 2026-04-25 | Implemented Phase 1 blueprint end-to-end: created `prompts/`, `policies/`, `scripts/route.py`, `scripts/run_skill.py`, `scripts/append_audit.py`, `.github/workflows/dispatcher.yml`, `memory/audit/README.md`; added `_template/`, `plan/`, `review/`, `memory-write/` skills; upgraded `summarize` and `.agents/skills/README.md` to the new YAML-front-matter protocol; extended `validate-skills.yml` to enforce required keys; updated `AGENTS.md` with Dispatcher and Policies sections and extended both Interconnection Maps. |
