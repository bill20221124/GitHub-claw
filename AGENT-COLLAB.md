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

- **Active Ticket:** *(无)* / `T-NNN: <短标题>`
- **Active Ticket 状态:** `spec` / `in-progress` / `awaiting-review` / `awaiting-answer` / `blocked` / `done`
- **当前接力人:** @Architect / @Copilot / @Owner
- **更新于:** 2026-04-25T00:00Z by @Architect

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

---

## 7. Active Ticket(详情)

> 当 §4 Status Board 上有 Active Ticket 时,这里展开它的完整规格。完成后整段移到 §9。
> 如果当前没有 Active Ticket,这一段保留这句提示即可:*"无活跃 ticket,等待 @Architect 发起 SPEC。"*

```
Ticket ID:        T-NNN
Title:            <短标题>
Owner:            @Copilot(实施)/ @Architect(规格)
Created:          YYYY-MM-DDThh:mmZ
Goal (1 sentence): <一句话目标>

Acceptance Criteria:
- [ ] ...
- [ ] ...
- [ ] 反思笔记已追加(归档时填)

Files in Scope:
- 可改:`...`
- 禁改:`AGENTS.md`、`docs/agent-architecture.md`、`docs/agent-cognitive-architecture.md` 未经 @Architect 同意不得动

Constraints:
- ...

Linked PR / Issue: <链接>
Linked Decisions:  D-NNN, D-NNN
```

---

## 8. Conversation Log(倒序,最新在上)

> 协作过程的全部消息按时间倒序追加在这里。
> **不要修改/删除已有消息**,要纠错请发 `CORRECTION` 引用原消息时间戳。

### [2026-04-25T00:00Z] @Architect → @Copilot · SPEC
**Ref:** T-000(范例,首条真实 SPEC 进来后可删)
**Topic:** 协议格式示例
**Body:**
本条仅为模板示例。@Copilot 接手新任务前请先完整读 §0–§3,确认你能遵守:
单线程、接力、简短、结构化、无寒暄、追加、真相分离、完成即归档。
读完后请用一条 `ACK` 回复,正文一句话即可。
**Acceptance:** N/A(示例)
**Files in scope:** N/A
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

*Protocol v0.1 · drafted by @Architect · awaiting @Copilot ACK on first real ticket.*