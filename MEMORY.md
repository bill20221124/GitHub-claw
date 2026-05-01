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
- Phase 1 architecture blueprint: `docs/agent-architecture.md` (engineering-layer source of truth).
- Phase 2+ cognitive architecture: `docs/agent-cognitive-architecture.md` (cognitive-layer source of truth — Goal Stack, layered memory, reflection loop, working set, three trigger modes, three cognitive modes, three collaboration tiers).
- Goal Stack lives in `goals/G-NNN.md`; schema in `goals/README.md`; first concrete goal is `goals/G-001.md` (implement Phase 2 minimum viable set).
- Reflection log lives in `reflections/R-NNN.md`; schema in `reflections/README.md`; written after every skill run (post T-002).
- Inter-agent collaboration protocol: `AGENT-COLLAB.md`. @Architect (Claude) 负责规格 / 决策 / 审查;@Copilot (GitHub Copilot) 负责按规格实施。Ticket / Decision / Question 三类信息严格分区。
- Project roadmap & North Star: `AGENT-COLLAB.md` §12. 任何 ticket / decision / message 与 §12 冲突时,以 §12 为准。

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
| `AGENT-COLLAB.md` | `AGENTS.md` Interconnection Map · `MEMORY.md` Standing Context |
| `goals/README.md` 或 `_template.md` (schema) | `scripts/goal_stack.py` · `MEMORY.md` Standing Context |
| `goals/G-NNN.md` (实例) | `AGENT-COLLAB.md` §6 (若架构级决策) · 关联 ticket |
| `reflections/README.md` 或 `_template.md` (schema) | `scripts/append_reflection.py` · `MEMORY.md` Standing Context |
| `reflections/R-NNN.md` 标 `memory-write candidate` | `MEMORY.md` (经 `/memory-write` 候选 PR) |
| `scripts/assemble_context.py` | `scripts/run_skill.py`(调用点) · `prompts/skill-wrapper.md`(memory_excerpt 占位符) · `MEMORY.md` Standing Context |
| `.agents/skills/<id>/skill.md` (cognitive_mode/collab_tier) | `.github/workflows/validate-skills.yml` 枚举校验 · `MEMORY.md` Standing Context |
| `AGENT-COLLAB.md` §12 (Roadmap) | `docs/agent-cognitive-architecture.md` (Phase 定义需对齐) · `MEMORY.md` Standing Context |

---

## Task Log

| Date | Summary |
|---|---|
| 2026-04-24 | Added `.agents/skills/` skill system: discovery index, `summarize` example skill, `validate-skills` workflow, and Skills section in AGENTS.md. |
| 2026-04-24 | Installed `ui-ux-pro-max` skill via `npx uipro-cli init --ai copilot` (source: github.com/nextlevelbuilder/ui-ux-pro-max-skill). Files at `.github/prompts/ui-ux-pro-max/`. Applied skill to optimize `index.html`: added Plus Jakarta Sans font, skip link, focus-visible styles, active nav scroll spy, CSS-class-driven mobile menu, and prefers-reduced-motion support. |
| 2026-04-24 | Systemic fix: added Non-Negotiable Rules + Interconnection Map to `AGENTS.md`; added Known Interconnections section and owner preference for mandatory memory updates to `MEMORY.md`. Enforces that every future task updates memory and cascades changes. |
| 2026-04-24 | Wrote Phase 1 architecture blueprint: `docs/agent-architecture.md`. Defines dispatcher single-entry, three-part prompt, four core skills (`summarize`/`plan`/`review`/`memory-write`), policies, and audit log. |
| 2026-04-25 | Implemented Phase 1 blueprint end-to-end: created `prompts/`, `policies/`, `scripts/route.py`, `scripts/run_skill.py`, `scripts/append_audit.py`, `.github/workflows/dispatcher.yml`, `memory/audit/README.md`; added `_template/`, `plan/`, `review/`, `memory-write/` skills; upgraded `summarize` and `.agents/skills/README.md` to the new YAML-front-matter protocol; extended `validate-skills.yml` to enforce required keys; updated `AGENTS.md` with Dispatcher and Policies sections and extended both Interconnection Maps. |
| 2026-04-25 | Transformed `index.html` from static "AI Guide" knowledge base to a fully functional AI interactive chat website. Features: OpenAI-compatible streaming chat, localStorage API Key/BaseURL/model/system-prompt config, Markdown+code-highlight rendering, settings panel, multi-model support (OpenAI/DeepSeek/Qwen), responsive dark UI. Used ui-ux-pro-max skill for design guidance. |
| 2026-04-25 | Drafted Phase 2 cognitive architecture (`docs/agent-cognitive-architecture.md`) — Goal Stack, layered memory, reflection loop, working-set assembly, three cognitive modes, three trigger modes, three collaboration tiers. |
| 2026-04-25 | Created multi-agent collaboration bus (`AGENT-COLLAB.md`) — protocol for @Architect (Claude) ↔ @Copilot (GitHub Copilot) async handoff with strict message schema, single-threaded ticket flow, and append-only conversation log. |
| 2026-04-30 | **Phase 3 完成**：G-002 关闭(status→done)。T-006 REVIEW 通过（@Architect 正式审查），D-008 落档，D-009 红线修正（@Copilot 越权冒充 @Architect 写 REVIEW/D-008/R-008，不 revert，SPEC 模板补强制约束）。R-PHASE-3.md 落档。 |
| 2026-04-30 | T-007 REVIEW 通过：embed_index.py TF-IDF 索引 + assemble_context Layer 3 升级(fallback 正确) + 20 unittest + R-009 落档。T-008 SPEC 派发：scan_repo.py skill-evolution 检查 + watchlist.yml 新增项 + ≥5 unittest。D-010 落档(Phase 4 入口豁免)。 |
| 2026-05-01 | **T-009 实施完成 + G-003 全部 AC 达成**：`assemble_context.py` 新增 Layer 3 source 日志（stderr）；3 新增 unittest（19 个全部通过）；R-011.md 落档；G-003 status→done（Phase 4 全部 AC 勾选）。待 @Architect REVIEW + Phase 4 出口门禁。 |
| 2026-04-30 | **T-008 实施完成**：`memory/watchlist.yml` 新增 `skill-evolution` 项；`scripts/scan_repo.py` 新增 `check_skill_evolution()`（只扫 §4，大小写不敏感，静默跳过）；6 新增 unittest，26 个全部通过；`reflections/R-010.md` 落档。待 @Architect REVIEW。 |
| 2026-04-30 | **Phase 4 开始**：@Owner 授权豁免 reflections≥30 入口条件。T-007 实施完成：`scripts/embed_index.py`(TF-IDF 反思索引 + CLI + JSON 缓存)、`scripts/assemble_context.py` Layer 3 升级(相关反思优先/fallback 近期审计)、20 unittest 全通过。G-003 建立，R-009 落档。待 @Architect REVIEW。 |
| 2026-04-29 | T-006 实施完成：proactive-watch.yml（定时巡视 + gh issue create）、proactive-scan skill.md（reflective/propose）、policies/permissions.md 追加行、R-007.md 落档。待 @Architect REVIEW。 |
| 2026-04-29 | T-005 REVIEW 通过：memory/watchlist.yml + scripts/scan_repo.py 4 类检查 + 20 unittest + R-006.md 落档。T-006 SPEC 派发：proactive-watch.yml + proactive-scan skill.md + policies/permissions.md。 |
| 2026-04-29 | T-005 实施完成：memory/watchlist.yml（4 项检查）、scripts/scan_repo.py（4 类检查 + CLI exit 0/1）、scripts/test_scan_repo.py（20 unittest 全通过）、reflections/R-006.md 落档。G-002 Last advanced 更新，AGENT-COLLAB.md §4 状态更新至 pending review。 |
| 2026-04-29 | **Phase 2 完成**：G-001 关闭(status→done)。T-001–T-004 全部 REVIEW 通过，出口门禁达成。R-001–R-005 落档，R-PHASE-2.md 落档。 |
| 2026-04-29 | T-004 REVIEW 通过：5 个 skill.md + _template 新增 cognitive_mode/collab_tier 字段，validate-skills.yml 枚举校验，R-004.md 落档。Phase 2 出口门禁全部达成。 |
| 2026-04-29 | T-003 REVIEW 通过：scripts/assemble_context.py 四层 ContextPack(Standing Context/Active Goal/Recent Audit/Event Hint)；run_skill.py 替换 memory_excerpt()，fallback 保留；16 unittest 全通过；R-003.md 落档。 |
| 2026-04-26 | T-001 REVIEW 通过：scripts/goal_stack.py(list/show/advance/set-status)、goal-driven.yml(schedule 09:15 UTC)、20 unittest 全通过、R-001.md 落档。 |
| 2026-04-26 | T-002 实施:创建 scripts/append_reflection.py(幂等反思骨架 CLI)、修改 scripts/run_skill.py 加 --reflect 双模式 hook、18 个 unittest 全通过,reflections/R-002.md 落档。 |
| 2026-04-26 | Phase 2 起步(重建):built `goals/` and `reflections/` skeletons (README + _template); created `goals/G-001.md` (Phase 2 MVP goal); dispatched T-001 (Goal Stack CLI + goal-driven dispatcher branch) to @Copilot via `AGENT-COLLAB.md` §7. Implementation work delegated; @Architect role is now spec + review only. Lesson: a previous attempt was lost when local changes were overwritten by a remote pull — D-005 added to `AGENT-COLLAB.md` mandating commit-then-push immediately. |
