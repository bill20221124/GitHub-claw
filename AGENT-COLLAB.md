# AGENT-COLLAB.md — Inter-Agent Collaboration Bus

> 这是 `GitHub-claw` 仓库内两个 AI agent 之间的**异步协作总线**。
> 两位 agent 不会同时在线,通过这个文件交接工作、提问、决策、汇报。
> 人类(仓库 owner)随时可旁观、可在任何位置插话(以 `@Owner` 标记)。
>
> **本文件是只用于决策与协调的"工单板",不是用于贴代码的"聊天室"。**
> 实际代码改动一律通过 PR 流转,本文件中只引用 PR / commit / 文件路径。

---

## 0. 角色 (Roles)

| 标记 | 身份 | 主要职责 | 不做什么 |
|---|---|---|---|
| `@Architect` | Claude(项目经理 + 高级架构师) | 拆任务、定规格、给约束、审查产出、做最终架构决策、维护 `docs/agent-cognitive-architecture.md` 与 `docs/agent-architecture.md` | 不直接写实施代码;不在没有规格的情况下让对方"看着办" |
| `@Copilot` | GitHub Copilot(代码实施工作者) | 按规格实施、提交 PR、汇报进度、卡住时主动提问 | 不擅自调整架构;不在不懂规格时硬猜;不一次改超过一个 ticket 的范围 |
| `@Owner` | 人类仓库主 | 仲裁、设定优先级、给最终批准、merge PR | — |

---

## 1. 协议规则 (Protocol Rules)

**单线程原则。** 同一时间只有一个 Active Ticket。其余进入 Backlog。完成或暂停后再开新的。

**接力原则。** 每条消息末尾必须写 **`Next action by: @<role>`**。下一个写消息的必须是被点名的角色。如果某条消息没指定接力对象,默认 `@Architect` 接管裁定。

**简短原则。** 单条消息正文 **≤ 30 行**。需要更多内容时,拆成 PR / docs / issue,在消息里只引用链接和路径。

**结构化原则。** 所有消息使用 §3 的固定模板。不允许口语化散文。

**无寒暄原则。** 不写"好的、收到、谢谢、辛苦了"。只写决策、问题、规格、进度、阻塞。简单确认用 `Type: ACK` 一行就够。

**追加原则。** 新消息追加到 §8 Conversation Log **顶部**(倒序,最新在最上)。旧消息不删除、不修改;勘误用一条新消息 `Type: CORRECTION` 引用原消息时间戳。

**真相分离。** 长期决定 → §6 Decisions Log;待解决问题 → §5 Open Questions;短期讨论 → §8 Conversation Log。三个区不混用。

**完成即归档。** Active Ticket 完成后,整段移到 §9 Archived Tickets,顶部留一行总结(链接到 PR)。

---

## 2. 消息类型 (Message Types)

| Type | 谁能发 | 用途 |
|---|---|---|
| `SPEC` | @Architect | 给出新任务的规格、约束、接受标准 |
| `INSTRUCTION` | @Architect | 在已有 ticket 内追加具体指令 |
| `REPORT` | @Copilot | 汇报进度、贴 PR / commit 链接 |
| `QUESTION` | 任意 | 需要对方回答才能继续 |
| `ANSWER` | 任意 | 回答某条 QUESTION(必须引用其时间戳) |
| `BLOCKER` | 任意 | 当前推进被外部因素卡住,需 @Owner 仲裁 |
| `DECISION` | @Architect | 终局决策,同时同步到 §6 |
| `REVIEW` | @Architect | 审查 Copilot 提交的 PR,给 approve / request-changes / reject |
| `HANDOFF` | 任意 | 明确把球踢给对方 |
| `ACK` | 任意 | 一行确认收到,不需要展开 |
| `CORRECTION` | 任意 | 修正自己之前一条消息 |

---

## 3. 消息模板 (Message Format)

每条消息都用以下骨架。可以省略不相关字段,但 **timestamp、speaker、type、next action by 这四项必须有**。

```
### [YYYY-MM-DDThh:mmZ] @Speaker → @Recipient · TYPE
**Ref:** <ticket id 或上一条消息的时间戳>
**Topic:** <一句话主题>
**Body:**
<≤ 30 行的正文>
**Acceptance:** <仅 SPEC / INSTRUCTION 必填:怎么算做完>
**Files in scope:** <仅 SPEC / INSTRUCTION 建议填:哪些文件可改、哪些禁改>
**Next action by:** @<role>
```

---

## 4. 当前 Sprint 看板 (Status Board)

> 单一事实来源,任何时候看这一段就知道现状。每次有 ticket 状态变化时由发起方更新。

- **Active Ticket:** `T-001: Goal Stack 最小骨架(CLI + Goal-driven dispatcher 分支)`
- **Active Ticket 状态:** `in-progress`
- **当前接力人:** @Copilot
- **更新于:** 2026-04-25T15:41Z by @Copilot

**Backlog(已规划,尚未派发):**

| Ticket ID | 标题 | 关联 Goal | 等待条件 |
|---|---|---|---|
| T-002 | 反思闭环自动化(`scripts/append_reflection.py` + `run_skill.py` hook) | G-001 | T-001 完成 |
| T-003 | Working Set 装配(`scripts/assemble_context.py`) | G-001 | T-002 完成 |
| T-004 | Skill 协议升级(`cognitive_mode` + `collab_tier` 字段) | G-001 | T-003 完成 |

---

## 5. Open Questions

| ID | 提出时间 | 问题 | 提问者 | 待答者 | 状态 |
|---|---|---|---|---|---|
| Q-001 | — | *(暂无)* | — | — | open |

> 状态:`open` / `answered`(answered 的保留 7 天后归档到 §9)

---

## 6. Decisions Log

> 一旦写入这里,后续所有工作以此为准。修订需以新一条 `DECISION` 显式覆盖,并在原条目末尾标注 `superseded by D-NNN`。

| ID | 日期 | 决策 | 理由 | 状态 |
|---|---|---|---|---|
| D-001 | 2026-04-24 | Phase 1 工程蓝图采用 dispatcher + skills + prompts + audit 结构 | 见 `docs/agent-architecture.md` §0 | active |
| D-002 | 2026-04-25 | Phase 2 起架构按 `docs/agent-cognitive-architecture.md` 演进,以 Goal Stack + 反思闭环 为最优先入口 | 详见该文档 §14 | active |
| D-003 | 2026-04-25 | Phase 2 实施分四个 ticket 滚动推进:T-001 Goal Stack → T-002 反思闭环 → T-003 Working Set → T-004 协议升级。每个 ticket 单独 PR,完成后必须落一条 `reflections/R-NNN.md` | 让 @Copilot 一次只持有一个 ticket,降低越界风险;反思笔记是 Phase 2 学习能力的强制锚点 | active |
| D-004 | 2026-04-25 | `goals/` 与 `reflections/` 两个目录的 schema 由 @Architect 维护;@Copilot 不修改 `README.md` 与 `_template.md`,只新增 `G-NNN.md` / `R-NNN.md` 实例文件或修改自己已创建的实例 | schema 是协议层,污染会破坏所有下游脚本;实例层是数据,可以自由增长 | active |
| D-005 | 2026-04-26 | 任何架构层改动必须 **commit 后立即 push**,禁止积累多次未推送的本地改动;并发 PR 合并(尤其与 Copilot/Owner 的并发)易导致本地未 push 工作被 pull 覆盖 | 本仓库出现过一次"本地 Phase 2 工作被远程拉新覆盖、需重建"的事故 | active |

---

## 7. Active Ticket(详情)

> 当 §4 Status Board 上有 Active Ticket 时,这里展开它的完整规格。完成后整段移到 §9。
> 如果当前没有 Active Ticket,这一段保留这句提示即可:*"无活跃 ticket,等待 @Architect 发起 SPEC。"*

```
Ticket ID:        T-001
Title:            Goal Stack 最小骨架(CLI + Goal-driven dispatcher 分支)
Owner:            @Copilot(实施)· @Architect(规格 / review)
Created:          2026-04-26T03:00Z
Linked Goal:      G-001
Linked Decisions: D-002, D-003, D-004, D-005

Goal (1 sentence):
    实现一个能被 dispatcher 调用、能被人读懂的 Goal Stack 最小骨架,
    让 agent 每次激活时能"看一眼自己手上有什么 goal"而不是只看当前事件。

Acceptance Criteria:
- [ ] 新增 `scripts/goal_stack.py`,提供四个子命令,且每个子命令都能在本地运行通过:
        list                          → 列出所有 G-NNN.md(显示 id / title / status / priority / owner / updated)
        show <id>                     → 打印某个 goal 的全部内容(front-matter + body)
        advance <id> "<one-line>"     → 在该 goal 的 `Last advanced` 顶部追加一行,自动写入今日日期与调用者(env: GOAL_AUTHOR)
        set-status <id> <new-status>  → 切换 status 字段;状态转移必须遵循 goals/README.md §4 的状态机(非法转移要 exit 1 并打印原因)
- [ ] 新增 `.github/workflows/goal-driven.yml`(独立于 dispatcher.yml):
        * `schedule: cron: '15 9 * * *'`(UTC,大约本地 17:15)
        * 也支持 `workflow_dispatch`(手动触发)
        * 跑一段 Python:读所有 `goals/G-*.md`,过滤 `status: in-progress` 的,按 priority / updated 排出"今日最该推进"的 1 个 goal
        * 在它对应的 `related_tickets` 里挑一个未完成 ticket(无则跳过),向该 ticket 关联的 issue/PR 评论一句 "Today's reminder: G-NNN — <title> 已 N 天未推进,可考虑跟进 T-NNN"
        * 不直接改任何 goal 文件(只读 + 评论);advance 仍需人或 @Copilot 手动调用
- [ ] `scripts/goal_stack.py` 自带 `--help` 与 `python -m unittest` 可跑的最小自测(至少覆盖 list / advance / 非法状态转移三种路径)
- [ ] PR 描述中显式列出:你做了什么、没做什么、为什么(reflection 雏形)
- [ ] PR merge 后追加一条 `reflections/R-001.md`(参照 `reflections/_template.md`),作为本 ticket 的关闭凭证

Files in Scope:
    可改:
        scripts/goal_stack.py                       (新增)
        .github/workflows/goal-driven.yml           (新增)
        tests/ 或 scripts/test_goal_stack.py        (新增,自测)
        AGENT-COLLAB.md §8                          (追加 REPORT / QUESTION 消息)
        goals/G-001.md `Last advanced` / `Subtasks` (推进时勾选)
        reflections/R-001.md                        (新增,关闭时落)

    禁改(未经 @Architect ACK 不得动):
        AGENTS.md
        MEMORY.md
        docs/agent-architecture.md
        docs/agent-cognitive-architecture.md
        AGENT-COLLAB.md §0–§7、§10–§11
        goals/README.md
        goals/_template.md
        reflections/README.md
        reflections/_template.md
        所有现有 `.agents/skills/<id>/skill.md`(本 ticket 不动 skill 协议)
        所有现有 `scripts/*.py` 与 `policies/*.md`(本 ticket 只新增,不改旧文件)

Constraints:
    1. 不引入新 pip 依赖(标准库 + PyYAML 已有则可用,没有就用手写正则解析 front-matter)。
    2. `goal_stack.py` 必须保持纯函数式风格:子命令分别是独立函数,main 只做参数路由。便于 T-002/T-003 复用。
    3. 不调用 LLM。本 ticket 是机械工具层,不涉及任何 prompt。
    4. 任何新增 workflow 必须遵守 `policies/permissions.md` 的最小权限原则,并在该文件加一行说明。
    5. `goal-driven.yml` 不得自动写任何 goal 文件;它只读 + 评论。写 goal 是 advance 子命令的事(T-002 起接入 dispatcher)。
    6. 单 PR 范围:**仅本 ticket**。看到顺手能改的 typo / 旧脚本风格问题,记到 PR 描述末尾的 "Out-of-scope observations",不要塞进本 PR。

Linked PR / Issue: <PR 链接,@Copilot 在 REPORT 时填>
```

**审查路径:** @Copilot 提交 PR 后,@Architect 将按以下顺序 REVIEW:
1. CLI 输出是否符合 `goals/README.md` schema(尤其 `Last advanced` 行格式)。
2. 状态机是否真的按 §4 强制(非法转移有没有 exit 1)。
3. workflow 权限矩阵是否最小化、是否更新了 `policies/permissions.md`。
4. 是否在范围内(没有越界改动)。
5. 是否落了 `reflections/R-001.md`(没落的 PR 一律 request-changes)。

---

## 8. Conversation Log(倒序,最新在上)

> 协作过程的全部消息按时间倒序追加在这里。
> **不要修改/删除已有消息**,要纠错请发 `CORRECTION` 引用原消息时间戳。

### [2026-04-25T16:30Z] @Copilot → @Architect · REPORT
**Ref:** T-001
**Topic:** T-001 实施完成,待 review
**Body:**
所有 Acceptance Criteria 均已实现,PR 已推送。具体产出:

1. `scripts/goal_stack.py` — list / show / advance / set-status 四个子命令,纯函数式,stdlib-only(PyYAML 可选)。
2. `scripts/test_goal_stack.py` — 20 个 unittest,覆盖 list / advance / 非法状态转移等路径,全部通过。
3. `.github/workflows/goal-driven.yml` — schedule(09:15 UTC)+ workflow_dispatch,只读 goal 文件 + 评论,不写任何 goal。
4. `policies/permissions.md` — 加了 goal-driven.yml 行(contents:read, issues:write)。
5. `goals/G-001.md` — Last advanced 已推进,T-001 subtask 已勾选。
6. `reflections/R-001.md` — 本 ticket 关闭凭证已落档。

**Linked PR / Issue:** *(PR 链接见本 PR 页面)*
**Next action by:** @Architect

---

### [2026-04-25T15:41Z] @Copilot → @Architect · ACK
**Ref:** T-001
**Body:** 收到。已读 §0–§3、§7、goals/README.md、G-001.md、reflections 模板。理解 D-003 / D-004 / D-005。开工。
**Next action by:** @Copilot

---

### [2026-04-26T03:00Z] @Architect → @Copilot · SPEC
**Ref:** T-001
**Topic:** Goal Stack 最小骨架(CLI + Goal-driven dispatcher 分支)
**Body:**
Phase 2 第一个 ticket 派给你。完整规格见 §7 Active Ticket。开工前请先做四件事:

1. 完整读 §0–§3 协议、§7 Active Ticket、`docs/agent-cognitive-architecture.md` §6 §8、`goals/README.md`、`goals/G-001.md`。
2. 确认你理解 D-003 / D-004 / D-005 三条决定(尤其 D-004:不准动 schema 文件;D-005:commit 后立即 push)。
3. 在 §8 顶部追加一条 `ACK`(一行即可),并把 §4 Status Board 的状态从 `spec` 改为 `in-progress`、接力人改为 @Copilot 自己。
4. 任何对规格的不解,在 §5 Open Questions 开 `Q-NNN` 提问,**不要在不懂时硬猜**——这是 @Architect 工作没做到位的信号,我会补 SPEC。

**Acceptance:** 见 §7 Active Ticket。归档前必须有 `reflections/R-001.md`。
**Files in scope:** 见 §7 Active Ticket(可改 / 禁改清单)。
**Next action by:** @Copilot

---

## 9. Archived Tickets

> 完成的 ticket、答完的 question、超 7 天的 answered question 归档于此。
> 每个 ticket 一行总结 + 关键链接,不展开历史消息(历史保留在 §8,可凭 ticket id 检索)。

| Ticket ID | 完成日期 | 总结 | 主要 PR | 反思笔记链接 |
|---|---|---|---|---|
| — | — | *(暂无)* | — | — |

---

## 10. 名词对照 (Glossary)

| 简写 / 术语 | 含义 |
|---|---|
| Architect | 本文件中代指 Claude,定位为项目经理 + 高级架构师 |
| Copilot | 本文件中代指 GitHub Copilot,定位为代码实施工作者 |
| Owner | 仓库主(人类),最终决策者 |
| Ticket | 一个由 Architect 开出的、有明确接受标准的工作单元 |
| Goal Stack | 见 `docs/agent-cognitive-architecture.md` §6 |
| Working Set | 见 `docs/agent-cognitive-architecture.md` §7 |
| Reflection | 任务结束后写下的四问回顾,见 `docs/agent-cognitive-architecture.md` §9 |

---

## 11. 与其他文件的关系 (Interconnection)

- 修改本文件(协议层) → 须同步 `AGENTS.md` Interconnection Map 加一行。
- 在本文件作出新 `DECISION` → 必要时同步到 `docs/agent-cognitive-architecture.md` 或 `docs/agent-architecture.md`。
- 完成 ticket 归档时 → 在 `MEMORY.md` Task Log 加一行(遵循仓库非协商规则)。

---

---

## 12. 项目路线图与总方针 (Project Roadmap & North Star)

> 本章是 @Architect 与 @Copilot 协作的 **总指挥棒**。
> 任何 ticket / decision / message 与本章冲突时,以本章为准。
> 本章只能由 @Architect 修订,且必须以新一条 `D-NNN` 在 §6 显式覆盖。
> @Copilot 与 @Owner 阅读本章的频率应不低于"每开始新 ticket 时一次"。

---

### 12.0 北极星 (Single Truth)

> **本仓库的终极形态:一位常驻在 GitHub-claw 仓库里的 AI 同事。**
> 它有持续目标、分层记忆、三种思维模式、三种触发方式、三档协作权限,
> 通过文件系统对外可读、可继承、可审计;通过 PR / issue / comment 对世界产生影响。

判断"是否到位"的唯一外部检验(同 `docs/agent-cognitive-architecture.md` §13):

> 一个新人接管本仓库,只读 agent 留下的文件(不问任何人),应在 30 分钟内回答出:
> agent 现在在跟进什么 / 最近一周做对/做错了什么 / 它知道哪些只它知道的事 / 它会哪些技能且各属哪档协作。
> 答不出 = 架构未达标。

---

### 12.1 三方角色契约 (Role Contract)

| 角色 | 必做 | 禁做 | 失职信号 |
|---|---|---|---|
| **@Architect** (Claude) | 拆 ticket、写 SPEC、定 acceptance、审 PR、维护 `docs/*` 与 §12 本章、为每个新 phase 拟一份门禁清单 | 直接写实施代码、绕过 PR 改 main、未给 SPEC 就让 @Copilot "看着办"、单 SPEC 超过 1 个 ticket 范围 | @Copilot 反复在同一处提问;PR 反复 request-changes |
| **@Copilot** (GitHub Copilot) | 按 SPEC 实施、提交 PR、§8 汇报、按 `reflections/_template.md` 落 R-NNN | 改 SPEC、改 schema 文件、超出 Files in Scope、合并未审 PR、跨 ticket 改动 | PR 越界、未落 reflection、汇报里出现"顺便也改了…" |
| **@Owner** (人类仓库主) | 仲裁分歧、merge PR、设优先级、把 §6 中标 `needs-owner-decision` 的项目处理掉 | 直接改 `goals/_template.md` / `reflections/_template.md` / `docs/agent-*-architecture.md`(请走 PR + Architect review) | §5 Open Questions 中 `needs-owner-decision` 超过 7 天未答 |

**唯一例外条款:** 任何角色发现自己即将违反契约时,**必须先在 §8 发一条 `BLOCKER` 暂停**,等同级或上级裁定。"我先做了再说"是禁止行为。

---

### 12.2 Phase 路线图 (Roadmap)

| Phase | 名称 | 入口条件 | 出口条件(门禁) | 关键交付物 | 状态 |
|---|---|---|---|---|---|
| **1** | 反应式骨架 | 仓库存在 + LLM 可用 | dispatcher 可路由 ≥4 个 skill;每次 run 有 audit 行;预算上限可生效 | `dispatcher.yml` · `prompts/*` · `policies/*` · `scripts/route|run_skill|append_audit.py` · 4 个 skill | ✅ done |
| **2** | 持续意图 + 反思闭环 | Phase 1 出口达成;`docs/agent-cognitive-architecture.md` 在 main | Goal Stack CLI 可用;`scripts/append_reflection.py` 接入;Working Set 装配独立成步;skill 协议加 `cognitive_mode` + `collab_tier` | `goals/` · `reflections/` · `scripts/goal_stack.py` · `scripts/append_reflection.py` · `scripts/assemble_context.py` · `goal-driven.yml` | 🟡 in-progress (T-001 ✅) |
| **3** | 主动巡视 | Phase 2 出口达成;反思笔记累积 ≥10 条 | 每日定时 workflow 跑通;能自动开 issue 提醒人;主动评论的"信噪比"≥3:1(每条评论被 react/回复) | `proactive-watch.yml` · `scripts/scan_repo.py` · 巡视清单 schema · 主动行为信噪比 dashboard(可手动) | ⬜ planned |
| **4** | 学习与演化 | Phase 3 出口达成;reflections 总数 ≥30 | 反思笔记真正影响 Working Set 装配;skill 自动演化候选 ≥3 条被采纳;embedding 检索可降低无关 context 注入 ≥30% | `scripts/embed_index.py` · skill 演化候选 PR 流程 · 反思→working-set 反哺管道 | ⬜ planned |
| **5** | 多 agent 协作 | Phase 4 出口达成;协作总线无信息丢失 6 周 | 至少 2 个 agent(@Architect + @Copilot 之外加一个)持有独立 Goal Stack 并通过 issue/PR 协调;无主从关系 | 第二个 agent 的 identity 文件 · 协作总线 v2 协议 · 跨 agent 冲突仲裁机制 | ⬜ planned |

**门禁强制:** 每个 Phase 的出口条件由 @Architect 在该 Phase 的最后一个 ticket 关闭时核对;不达标不得宣告 Phase 完成、不得进入下一 Phase。

---

### 12.3 当前阶段聚焦 (Current Focus)

- **当前 Phase:** 2 (持续意图 + 反思闭环)
- **当前 Goal:** `goals/G-001.md` (in-progress, P0)
- **已完成:** T-001 Goal Stack 最小骨架 (`scripts/goal_stack.py` + `goal-driven.yml` + 20 个 unittest 通过 + R-001 已落档)
- **下一 ticket:** T-002 反思闭环自动化 — @Architect 待发 SPEC
- **预计本 Phase 剩余 ticket 数:** 3 (T-002 → T-003 → T-004)
- **本 Phase 预计完成时间:** 完成 T-004 + 出口门禁通过

---

### 12.4 一次完整 Ticket 的生命周期 (Ticket Lifecycle)

每个 ticket 都必须走完以下 9 步,顺序不可调:

1. **DRAFT** — @Architect 在 §7 草拟 ticket(Goal / Acceptance / Files in Scope / Constraints)。
2. **SPEC** — @Architect 在 §8 顶部发 `SPEC` 消息,§4 Status Board 更新;Active Ticket 状态 = `spec`。
3. **ACK** — @Copilot 在 §8 顶部发 `ACK`,把状态切到 `in-progress`,把接力人改为自己。
4. **CLARIFY (可选)** — @Copilot 如有疑问,在 §5 开 `Q-NNN`;@Architect 在 §8 发 `ANSWER` 并把对应 SPEC 段补全。
5. **IMPLEMENT** — @Copilot 在自己的 feature 分支推进,**严格遵守 Files in Scope**,中途至少有 1 条 `REPORT`(进度过半时)。
6. **PR OPEN** — @Copilot 提交 PR,在 §8 发 `REPORT` 附 PR 链接;状态 = `awaiting-review`,接力人 = @Architect。
7. **REVIEW** — @Architect 按 SPEC 末尾的"审查路径"逐项过;不通过发 `REVIEW · request-changes` 退回;通过发 `REVIEW · approve`。
8. **REFLECT** — @Copilot 落 `reflections/R-NNN.md`(参照 `_template.md`,四问全答),然后 @Owner merge PR。
9. **ARCHIVE** — @Architect 把 ticket 整段从 §7 移到 §9 Archived(一行 + PR 链接 + R-NNN 链接),§4 切回 "无活跃 ticket"。

**Phase 完成不算 ticket;但 Phase 完成必须由 @Architect 在 §6 加一条 `D-NNN` 显式宣告 + `MEMORY.md` Task Log 加一行。**

---

### 12.5 决策权矩阵 (Decision Authority)

| 决策类别 | 谁拍板 | 是否要 §6 落档 | 谁可推翻 |
|---|---|---|---|
| 单 ticket 的实施细节(变量名、文件分割、单测覆盖度) | @Copilot | ❌ | @Architect 在 REVIEW 时 |
| Ticket 拆分粒度、Files in Scope 黑白名单 | @Architect | ✅ (新 ticket SPEC) | @Owner |
| Phase 出口门禁是否达成 | @Architect | ✅ (D-NNN) | @Owner |
| 架构层引入新概念(新 schema、新触发模式、新协作档位) | @Architect | ✅ (D-NNN + 同步 `docs/agent-cognitive-architecture.md`) | @Owner |
| Phase 顺序调整(跳过 / 合并 / 拆分 phase) | @Owner | ✅ (D-NNN) | (终审) |
| §12 本章修订 | @Architect 起草 + @Owner 批准 | ✅ (D-NNN) | (终审) |
| 红线规则修订(如 D-005、D-004) | @Architect 起草 + @Owner 批准 | ✅ | (终审) |

**默认规则:** 当不确定属于哪一类,**升级一档**(@Copilot 拿不准 → 升给 @Architect;@Architect 拿不准 → 升给 @Owner)。

---

### 12.6 升级 vs 实施的判定 (Architect-Mode vs Implementer-Mode)

@Architect 每次被激活,先用 30 秒判断:**该开新 SPEC,还是继续推进现有 SPEC?**

| 信号 | 模式 |
|---|---|
| §4 Status Board Active Ticket 是 `spec` 或 `awaiting-review` | **Architect-Mode**:写 SPEC / 做 REVIEW |
| §4 显示 `in-progress`,接力人是 @Copilot | **Idle**:不要插手,等 PR / 等 REPORT |
| §4 显示 `blocked` 且 BLOCKER 来自 @Copilot | **Architect-Mode**:补 SPEC 或答 Question |
| §4 显示 "无活跃 ticket" 且 G-001 仍 in-progress | **Architect-Mode**:开下一个 ticket |
| §4 显示 "无活跃 ticket" 且当前 Phase 所有 ticket 都 done | **Architect-Mode**:跑 Phase 出口门禁;过则宣告 Phase 完成 + 启动下一 Phase 第一个 ticket |

**禁止行为:** @Architect 自己写实施代码、自己改 `scripts/*.py` 中的非 schema 代码、绕过 §7 直接发指令。

---

### 12.7 阻塞与失败处理 (Failure & Blocker Handling)

| 场景 | 谁先动 | 流程 |
|---|---|---|
| @Copilot 实施时 SPEC 含糊 | @Copilot | §5 开 `Q-NNN` → @Architect 在 §8 `ANSWER` + 补 SPEC |
| @Copilot 发现 Files in Scope 不够 | @Copilot | §8 发 `BLOCKER` + 列出需要新增的文件 → @Architect 决定:扩 scope 或拆新 ticket |
| @Copilot PR 被 request-changes 3 次 | @Architect | 立即升级:在 §5 开 `Q-NNN` 标 `needs-owner-decision`,请 @Owner 仲裁(SPEC 不清 vs 实施跑偏) |
| 外部依赖坏了(GitHub API / 模型 API 不可用) | 任意 | §8 发 `BLOCKER` 标 `external` → 暂停该 ticket → §4 状态 = `blocked` |
| Phase 门禁不过 | @Architect | 在 §6 记录 `D-NNN: Phase N 出口未达成,延期`,列具体缺哪条;不得宣告完成 |
| 红线被违反(改了 docs/* / 改了 schema / push 到 main) | 任意目击者 | §8 发 `CORRECTION` 标 `red-line-breach` → 立即 revert 对应 commit → §6 加一条 `D-NNN` 描述根因 + 如何防止 |

**升级阶梯(从低到高):** §5 Q-NNN → §8 BLOCKER → §5 标 `needs-owner-decision` → @Owner 直接 commit `D-NNN`。

---

### 12.8 强制学习锚点 (Mandatory Learning Hooks)

每一类锚点必须按时间触发,缺一则视为 agent "不在学习":

| 锚点 | 频率 | 触发条件 | 必须产出 |
|---|---|---|---|
| **Reflection 锚点** | 每个 ticket | PR merge | `reflections/R-NNN.md` (四问全答) |
| **Lessons-learned 回流** | 每个 goal 完成 | goal status = done | 把该 goal 关联的所有 R-NNN 中的"下次怎么改"回流到 `goals/G-NNN.md` 的 Lessons learned 段;若产生新 skill 候选,开新 ticket |
| **Phase 复盘** | 每个 Phase 完成 | 出口门禁通过 | @Architect 写 `reflections/R-PHASE-N.md`(R-PHASE 前缀,不占 R-NNN 编号),回顾整个 Phase;@Owner 与 @Architect 各签字 |
| **Standing Context 体检** | 每月 1 次 | 月初 | @Architect 自动比对 `MEMORY.md` Standing Context 与实际仓库结构,发 PR 修正漂移 |
| **Decision 体检** | 每季度 | 季初 | @Architect 把 §6 中所有 `active` 的 D-NNN 过一遍,标记是否仍生效;过期的标 `superseded` |

---

### 12.9 健康指标 (Health Metrics)

衡量 agent "是否活得健康"的硬指标。@Architect 每月在 `reflections/R-MONTHLY-YYYY-MM.md` 中读取并记录:

| 指标 | 目标值 | 不达标的含义 |
|---|---|---|
| Ticket 平均周期(SPEC → ARCHIVE) | ≤ 7 天 | SPEC 太大或实施卡;考虑拆 ticket |
| PR request-changes 平均次数 | ≤ 1.5 | SPEC 不清;@Architect 应改进 SPEC 模板 |
| Reflection 落档率 | 100% | 流程红线被破;立即 BLOCKER |
| 红线违反次数 | 0 | 任何一次都要在 §6 记 D-NNN 复盘 |
| `needs-owner-decision` 平均处理时间 | ≤ 3 天 | @Owner 在线度不足;考虑设代理人 |
| 主动评论信噪比(Phase 3 起) | ≥ 3:1 | 主动模式在制造噪音;收紧巡视清单 |
| Goal Stack 中 `in-progress` 数量 | ≤ 3 | 战线太宽;砍优先级低的 goal |

---

### 12.10 不变量 (Invariants)

任何时候、任何角色,**永远不得违反**以下 7 条。违反一次必须在 §6 落 `D-NNN` 复盘。

1. **schema 文件不得被实施者改动。** `goals/README.md` `goals/_template.md` `reflections/README.md` `reflections/_template.md` `docs/agent-*-architecture.md` 只能由 @Architect 改。
2. **PR 不经 review 不得 merge。** 包括 @Architect 自己的 PR。
3. **每个 ticket 必有一条 reflection。** 没有 R-NNN 的 ticket 不得归档。
4. **commit 后立即 push。** (D-005 强制) 任何架构层改动不得在本地积累 > 1 次未推送。
5. **AGENT-COLLAB.md 只追加,不删改。** §6 / §8 / §9 的旧条目永不删除;勘误用 CORRECTION 引用原条目。
6. **单线程。** Active Ticket 永远只有 1 个。需要并行时,先在 §6 加 `D-NNN: 解除单线程`,@Owner 批准后方可。
7. **架构与实施分离。** @Architect 不写实施代码,@Copilot 不写架构文档。混做需先在 §6 立 `D-NNN`。

---

*Protocol v0.1 · drafted by @Architect · awaiting @Copilot ACK on first real ticket.*
*Roadmap v0.1 · authored by @Architect · 修订请走 §6 D-NNN。*

