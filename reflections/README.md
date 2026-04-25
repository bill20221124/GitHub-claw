# Reflections — 反思层记忆

> 本目录是 agent 的 **反思层记忆 (Reflection Log)**,对应 `docs/agent-cognitive-architecture.md` §9。
> 每次任务结束后,agent 必须写一条 `reflections/R-NNN.md`,回答四个固定问题。
> 这是 agent 真正"学习"的入口——不需要 fine-tuning,纯靠文件就能积累经验。

---

## 0. 为什么独立成目录

Phase 1 的 `memory/audit/YYYY-MM-DD.md` 只是"留痕"——记录何时谁跑了哪个 skill、消耗多少 token。它回答不了三个真正重要的问题:**这次做对了吗?为什么对/错?下次该怎么改?** 反思层就是为这三个问题存在。

反思笔记会反过来影响后续的 Working Set 装配:同一类任务,**之前反思过的、关联高的笔记会优先被纳入 ContextPack**。这是 agent 跨 session 学习的具体机制。

---

## 1. 文件命名 & 编号

- 文件名:`R-NNN.md`,编号顺序分配,永不复用。
- 一次任务对应一条反思;批量反思(每日总结)用单独前缀 `R-DAILY-YYYY-MM-DD.md`(Phase 4 起启用)。

---

## 2. 文件结构(Schema)

每个 `R-NNN.md` 必须以 YAML front-matter 开头,后接四个固定章节:

```yaml
---
id: R-NNN
date: YYYY-MM-DDThh:mmZ              # UTC,任务结束的时刻
author: "@Architect" | "@Copilot"    # 谁跑的任务谁写
ticket: T-NNN | null                 # 关联 AGENT-COLLAB.md 的 ticket id
goal: G-NNN | null                   # 关联 goals/ 的 goal id
skill: <skill-id> | null             # 关联 .agents/skills/ 的 skill id
goal_met: yes | partial | no
duration_minutes: <int>              # 大致耗时,可估
memories_used: [<file-path>, ...]    # 哪些记忆文件进入了 ContextPack
memories_missing: [<short-desc>, ...] # 想用但没有的记忆,是 memory-write 候选
---
```

后接的固定章节(顺序与命名不可调):

| 章节 | 必填 | 内容 |
|---|---|---|
| `## 1. Did the task meet its acceptance criteria?` | ✅ | 对照 ticket / goal 的 acceptance,逐条说明达成度 |
| `## 2. Which memories did I rely on?` | ✅ | 列出实际用到的记忆文件;附一句话说明各自帮到了什么 |
| `## 3. What memory was missing?` | ✅ | 想用却没有的记忆;每条标 `→ memory-write candidate` 表示要进 `MEMORY.md` |
| `## 4. What would I change next time?` | ✅ | 给未来同类任务的具体建议;每条标 `→ skill update` / `→ doc update` / `→ workflow change` 中的一种 |

**示例:** 待 T-001 完成后由 @Copilot 写第一条 `R-001.md`(本 ticket 的 acceptance 之一)。**模板:** 见 `reflections/_template.md`。

---

## 3. 谁能写、什么时候写

| 场景 | 写入方 | 触发时机 |
|---|---|---|
| Skill 调用结束 | 跑该 skill 的 agent(通常 @Copilot 通过 `scripts/append_reflection.py`) | `scripts/run_skill.py` 末尾自动触发(T-002 实现) |
| 架构决策结束 | @Architect | 一个跨多个 ticket 的目标完成时,手动追加一条 |
| 失败/refused 也要写 | 任意 | 即使任务失败,反思更值钱;`goal_met: no` + 详细第 3、4 条 |
| 修改已写笔记 | **禁止** | 反思是 append-only;勘误用一条新 reflection 引用旧 id |

---

## 4. 反思笔记如何反哺(Phase 2 → Phase 4 的演进)

| Phase | 反思的用法 |
|---|---|
| **Phase 2** | 仅作为 episodic memory 落档。人类可读;Working Set 装配时按文件路径做朴素关键词匹配。 |
| **Phase 3** | `scripts/assemble_context.py` 在装配 ContextPack 时,优先纳入与当前任务 skill / goal 相同的最近 N 条反思。 |
| **Phase 4** | 引入 embedding 检索;反思笔记的 `memories_missing` 字段触发 `/memory-write` skill 生成候选 PR;`What would I change` 字段触发 skill 演化候选。 |

---

## 5. 与其他文件的关系 (Interconnection)

- `R-NNN.md` 标 `→ memory-write candidate` → 触发 `/memory-write` skill,产出 `MEMORY.md` 候选 patch。
- `R-NNN.md` 标 `→ skill update` → 在 `AGENT-COLLAB.md` 开新 ticket 修改对应 `.agents/skills/<id>/skill.md`。
- `R-NNN.md` 关联 `goal: G-NNN` → 该 goal 的 `Lessons learned` 章节追加一行(由 @Architect 在 PR review 时同步)。
- 修改本 README(schema 变更) → 必须同步 `AGENTS.md` Interconnection Map 与 `scripts/append_reflection.py` 的写入逻辑。

---

## 6. 反模式(明令禁止)

- ❌ **反思变成寒暄或自我表扬**。"很顺利、做得很好" 不是反思,是噪音。每条反思必须给出可操作的"下次改进"。
- ❌ **省略失败案例**。失败的反思价值远高于成功的反思;`goal_met: no` 的反思必须最详细。
- ❌ **第 3 条留空**。"没有缺记忆" 几乎不可能,真没缺就明确写 `(none — knowledge graph already complete for this task class)` 并解释为什么。
- ❌ **改动旧反思**。反思是历史,改史就没法学习。
