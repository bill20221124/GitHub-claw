# Goal Stack — 目标层记忆

> 本目录是 agent 的 **目标层记忆 (Goal Stack)**,对应 `docs/agent-cognitive-architecture.md` §6。
> 每个进行中的目标是一个独立的 markdown 文件,文件名 `G-NNN.md`(NNN 从 001 起,顺序分配)。

---

## 0. 为什么独立成目录

Phase 1 没有"目标"的概念,所有 agent 行为都被动响应单条命令。引入 Goal Stack 之后,agent 每次激活的第一件事不再是"看这条命令是什么",而是 **"看看我手上这堆目标里,哪个最该推进、哪一步"**。

被点名的命令只是输入之一,不是唯一驱动。这是从"机器人"升级为"智能体"的关键。

---

## 1. 文件命名 & 编号

- 文件名:`G-NNN.md`,如 `G-001.md`、`G-002.md`。
- 编号一旦分配 **永不复用**,目标完成或废弃后文件保留(状态字段更新),不删除。
- 索引可由 `ls goals/G-*.md` 列出;后续可加 `goals/INDEX.md` 自动生成的清单(Phase 4)。

---

## 2. 文件结构(Schema)

每个 `G-NNN.md` 必须以 YAML front-matter 开头,后接固定章节顺序:

```yaml
---
id: G-NNN                              # 必须与文件名一致
title: <短标题,≤ 60 字符>
status: backlog | in-progress | blocked | done | abandoned
priority: P0 | P1 | P2 | P3            # P0 最高
owner: "@Architect" | "@Copilot" | "@Owner"   # 当前主要推进者
created: YYYY-MM-DD
updated: YYYY-MM-DD                    # 最近一次推进的日期
related_decisions: [D-NNN, D-NNN]      # 关联的 AGENT-COLLAB.md Decision id
related_tickets:   [T-NNN, T-NNN]      # 关联的 AGENT-COLLAB.md Ticket id
related_prs:       [#NN, #NN]
---
```

后接的固定章节(顺序不可调):

| 章节 | 必填 | 内容 |
|---|---|---|
| `## One-sentence statement` | ✅ | 这个目标用一句话讲清楚 |
| `## Acceptance Criteria` | ✅ | checkbox 列表,每条独立可验证 |
| `## Subtasks` | ✅ | checkbox 列表;允许嵌套 ≤ 2 层 |
| `## Blockers` | ✅ | 当前阻塞项;无则写 `(none)` |
| `## Last advanced` | ✅ | 时间倒序的推进记录,每条一行,格式 `YYYY-MM-DD by @<role>: <一句话>` |
| `## Lessons learned` | ⭕ | 推进过程中的非显然的洞察;留空可省 |

**示例:** 见 `goals/G-001.md`(本仓库的第一个真实 goal)。**模板:** 见 `goals/_template.md`。

---

## 3. 谁能写、什么时候写

| 字段 / 区域 | 写入方 | 触发时机 |
|---|---|---|
| 创建新文件 | `@Architect` | 决策需要拆出一个跨多个 ticket 的目标时 |
| `status` 字段 | `@Architect` 或 `@Owner` | 状态切换时(in-progress → blocked → done 等) |
| `Subtasks` 勾选 | 任意 agent | 完成具体子任务后,在自己的 PR 里同步勾选 |
| `Last advanced` 追加 | 任意 agent | 每次有实质推进就追加一行 |
| `Lessons learned` 追加 | 任意 agent | 反思笔记 (`reflections/`) 沉淀出值得长期保留的洞察时 |
| `Blockers` 增删 | 任意 agent | 出现/解除阻塞时立即更新 |
| 删除字段 / 删除文件 | **禁止** | goals 是 append-mostly;状态改 `abandoned` 即可 |

---

## 4. 状态机

```
                ┌─────────┐
                │ backlog │
                └────┬────┘
                     │ (Architect 选中开始)
                     ▼
   ┌────────────► in-progress ◄────────────┐
   │                  │                     │
   │    (出现阻塞)    │   (推完)           │ (阻塞解除)
   │                  ▼                     │
   │              ┌─────┐               ┌──────┐
   └──────────────│ done│               │blocked│
                  └─────┘               └──────┘
                                            │
                                  (放弃推进) │
                                            ▼
                                       ┌──────────┐
                                       │ abandoned│
                                       └──────────┘
```

`done` 和 `abandoned` 是终态。终态文件保留,不删除——它们是情景记忆。

---

## 5. 与其他文件的关系 (Interconnection)

- 新增/状态切换 goal → 在 `AGENT-COLLAB.md` §6 Decisions Log 记一条 `D-NNN`(若是架构级目标)。
- goal 状态变 `done` → 反思笔记 `reflections/R-NNN.md` 中必须引用本 goal 的 id。
- goal 推进时跨多个文件 → 在 goal 的 `related_prs` 字段累加 PR 编号。
- 修改本 README(schema 变更) → 必须同步 `AGENTS.md` Interconnection Map 与 `MEMORY.md` Standing Context。

---

## 6. 反模式(明令禁止)

- ❌ **把日常 ticket 写成 goal**。Ticket 是"一次性的工作单",写在 `AGENT-COLLAB.md`;Goal 是"跨 ticket、跨 session 的持续意图"。判断标准:这件事如果不在文件里持续提醒,会不会被忘记?如果会,才是 goal。
- ❌ **一个 goal 没有 acceptance criteria**。没有验收标准的 goal 永远完不成。
- ❌ **删 goal 文件**。状态改 `abandoned` 并在 `Last advanced` 追加放弃理由。
