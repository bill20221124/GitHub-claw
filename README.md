# Agent Cognitive Architecture

> 本文件定义 `GitHub-claw` 仓库 AI 智能体的 **认知架构**——agent 作为"智能体"而非"事件路由器"的逻辑设计。
> 与 `docs/agent-architecture.md`(Phase 1 工程蓝图,已落地)互补:那份文档回答"如何安全地接入 LLM",本文件回答"agent 如何思考"。
>
> 适用范围:Phase 2 起 · 维护者:AI Agent · 日期:2026-04-25

---

## 0. 为什么需要这份文档

Phase 1 解决了"如何让 LLM 在仓库里被安全调用"的问题——它建出了一个 dispatcher、一组 skills、一套 prompts、一份 audit log。它工作得很好,但它本质上是一个 **事件驱动的脚本调度器**,对应的隐喻是"客服工单系统":人发请求、机器人回复、留个工单。

但本仓库的长期目标不是建一个 chatbot,而是把仓库本身打造为一个 **长期住在这里的 AI 同事**。同事的特点是:有自己持续的目标、有跨会话的记忆、会自己安排事情、做完事会反思。要让 agent 真的"像同事",就必须从认知层面重新设计,而不能只在工程层面继续加脚本。

---

## 1. 核心隐喻

> **Agent = 一位常驻在这个仓库里的同事。**

这条隐喻是后续所有设计决策的源头。它隐含了四个推论:

1. 同事 **有持续身份**——不是每次会话都重新认识自己。
2. 同事 **有自己的待办清单**——不是只做被指派的事。
3. 同事 **会主动巡视**——不是只在被点名时才出现。
4. 同事 **做完事会反思**——不是 commit 完就忘了。

这条隐喻的反面是要避免的:**Agent ≠ 一个被触发的脚本**。任何把 agent 设计成"事件 → 路由 → 回复"线性流水线的方案,本质上都还是 chatbot。

---

## 2. 不可或缺的三个特征

任何架构决策都必须服务于以下三个属性。缺一个,agent 就退化为 chatbot。

**持续目标 (Persistent Goals).** Agent 必须有跨 session 存在的"我想推动什么"。没有这个,它永远是被动响应。

**自洽记忆 (Coherent Memory).** 不是一个 MEMORY.md 文件,是一个 **分层的认知系统**:身份 / 长期事实 / 工作上下文 / 情景回忆 / 程序技能 / 反思笔记,各司其职、写入规则不同、半衰期不同。

**自主循环 (Autonomous Loop).** Agent 的核心不是"事件 → 路由 → LLM → 回帖"的流水线,而是 **"感知 → 唤起记忆 → 决策 → 行动 → 反思 → 更新记忆"** 的闭环。每一次激活都走完这个循环。

---

## 3. 五层认知架构

| 层 | 它回答的问题 | 在仓库里对应什么 |
|---|---|---|
| 感知层 (Perception) | "现在世界是什么样?" | GitHub events + 仓库快照(git tree、open issues、PR 队列、Goal Stack) |
| 记忆层 (Memory) | "我知道什么?" | 见 §5 分层记忆 |
| 认知层 (Cognition) | "我应该做什么?怎么做?" | LLM 调用 + planner + 反思 |
| 行动层 (Action) | "我对世界做了什么?" | PR / comment / label / workflow_dispatch / 文件提议 |
| 治理层 (Governance) | "什么我不能做?" | 权限矩阵 + 预算 + 红线 + 人类否决权 |

这五层是 **纵向** 的。横向上,认知层内部进一步分为三种思维模式(§4)。

---

## 4. 三种思维模式

一个真正的 agent 不应该只用一种方式思考。三种模式的成本、速度、典型场景各不相同:

| 模式 | 描述 | 典型场景 | 模型选型 |
|---|---|---|---|
| 反射式 (Reflexive) | 模式匹配 → 直接执行 | `/summarize` 一段固定文本 | 小模型甚至无模型 |
| 思辨式 (Deliberative) | 拿到目标 → 拆解 → 排序 → 逐步执行 → 中途可重新规划 | `/plan` 一个跨周的任务 | 强模型 |
| 反思式 (Reflective) | 任务结束后回看:做对了吗?哪里浪费了?哪条记忆该更新? | 每日定时 / 每次任务完成后 | 中等模型,可批量 |

Phase 1 的 `model_tier: simple|complex` 字段只区分了"贵不贵",没区分"思维方式不同"。Phase 2 起,每个 skill 应同时声明 `cognitive_mode: reflexive|deliberative|reflective`。

---

## 5. 分层记忆

把现有的 MEMORY.md 拆成六类记忆,各类对应不同的写入规则、读取规则、半衰期。

| 记忆类型 | 内容 | 谁写 | 半衰期 |
|---|---|---|---|
| **身份记忆 (Identity)** | "我是谁、我的工作方式" | 极少改,人类把关 | 永久 |
| **语义记忆 (Semantic)** | 关于这个仓库的领域知识、约定、决策依据 | agent 提议 + 人类批准 | 长期(月/年) |
| **程序记忆 (Procedural)** | 我会哪些技能、每个技能怎么做 | agent 自己积累 + 人类 review | 长期 |
| **情景记忆 (Episodic)** | 我什么时候做过什么、结果如何 | agent 自动写,append-only | 中期(90 天后归档) |
| **工作记忆 (Working)** | 当前任务的上下文、相关文件、相关历史 | 临时,任务结束即清理 | 短期(单次激活) |
| **目标记忆 (Goal Stack)** ⭐ | 当前所有进行中的目标、状态、阻塞项 | agent 持续维护 | 直到目标完成 |

最后一类是 Phase 1 完全没有的,是从"机器人"升级为"智能体"的关键。详见 §6。

---

## 6. Goal Stack:让 agent 真的"有事可做"

每个进行中的目标是一个独立文件,内容包括:

- 目标的一句话陈述
- 接受标准(怎么算"完成")
- 当前状态(在哪一步、谁是阻塞方)
- 子任务清单及进度
- 关联的 issue / PR / commit
- 上次推进的时间和当时学到的东西

**有了 Goal Stack,agent 每次被激活的第一件事不再是"看这条命令是什么",而是"看看我手上这堆目标里,哪个最该推进、推进哪一步"。** 被点名的命令只是输入之一,不是唯一驱动。

这一个概念同时解锁了两个新能力:

- **跨 session 的连贯性**——你今天让它推进 A,明天它来上班还记得 A 没做完。
- **主动模式的种子**——定时触发时,它能问自己"上次推 A 是 5 天前了,该跟进了"。

---

## 7. Working Set:不要把整个脑子塞给 LLM

Phase 1 是把整个 MEMORY.md 截断后塞进 prompt——粗暴、随记忆增长会撑爆 context、且大部分内容跟当前任务无关。

Phase 2 起,在感知层之后、认知层之前,**必须有一个明确的"工作集装配"步骤**:

> 基于"现在要做什么",从所有记忆里挑出相关的部分,组装成一个临时的 ContextPack,只把这个 ContextPack 喂给 LLM。

Phase 2 的过渡方案足够朴素——根据当前 issue/PR 涉及的文件路径,反查 Interconnection Map、反查 Goal Stack、反查最近 7 天的 audit;Phase 4 起再考虑 embedding 检索。

把"装配工作集"独立成一个明确的步骤,比把所有记忆一股脑塞进 prompt 重要得多。

---

## 8. 三种触发模式

| 模式 | 触发源 | 隐喻 | 计划 Phase |
|---|---|---|---|
| 反应式 (Reactive) | 人类 issue / PR / comment | "工单到了我处理" | Phase 1 已实现 |
| 目标驱动 (Goal-driven) | Goal Stack 中有未完成项,且满足某个推进条件 | "我手上有事在跟进,该往前走一步" | Phase 2 |
| 主动式 (Proactive) | 定时巡视 + 状态扫描 | "我自己看看有没有事要做" | Phase 3 |

后两种才是"智能体"和"chatbot"的真正分界线。

主动式不需要复杂——一个每天跑一次的 workflow,让 agent 跑一遍"巡视清单"(stale PR / 文档与代码漂移 / Goal Stack 中超过 N 天没动的项目),如果发现可做的事,就开 issue 或评论提醒人——就够了。

---

## 9. 反思闭环

Phase 1 的 audit log 只是"留痕",没有"反思"。真正的反思应在每次任务结束后由 agent 自己写下,回答四个问题:

1. **目标是否达成?** —— 与 skill 输出的接受标准比对。
2. **过程中我用了哪些记忆?** —— 帮助下次知道哪些记忆是"高价值"的。
3. **过程中我缺哪些记忆?** —— 产生新的 memory-write 候选。
4. **下次遇到同类任务,有什么我应该改的?** —— 产生 skill 演化候选。

这些反思笔记本身就是新的记忆(归类为情景 + 反思),会反过来影响后续的工作集装配。**这是 agent 真正"学习"的入口**——不需要任何 fine-tuning,纯靠文件就能积累。

---

## 10. 人机协作的三档

每个 skill 必须显式声明它属于哪一档协作:

- **Suggest 档** —— 只产出文字建议,人类自己决定。例:`/plan`、`/review`。
- **Propose 档** —— 产出 PR / draft,人类 merge 决定。例:`/memory-write`、文档改动、配置调整。
- **Execute 档** —— 直接 commit 到 main。**仅限低风险、高确定性、有 schema 校验** 的事。例:格式化、修 typo、归档过期 audit 日志。

权限矩阵应改为 **"skill × 协作档位"** 的二维结构,而不是 Phase 1 的 workflow 级粗粒度。

---

## 11. 完整运行循环

每次 agent 被激活——无论是被 comment、被定时器、还是被 Goal Stack 触发——都走以下 6 步:

1. **PERCEIVE** — 读事件 / 读仓库快照 / 读 Goal Stack
2. **RECALL** — 装配 Working Set(从分层记忆里挑相关片段)
3. **DECIDE** — 选择思维模式 + 选择 skill + 选择协作档位
4. **ACT** — 执行,产出 PR / comment / 文件 / 新的 Goal
5. **REFLECT** — 写反思笔记,标注用了什么记忆、缺什么记忆
6. **CONSOLIDATE** — 更新分层记忆(Goal 状态 / 反思 / memory-write 候选)

这才是一次"agent 行为"的完整形态。Phase 1 只做了 1 → 3 → 4 的一条线。

---

## 12. Phase 演进路线(按能力解锁,而非按文件数)

| Phase | 解锁的能力 | 关键改动 |
|---|---|---|
| **1** ✅ | 安全地接 LLM,反应式响应命令 | dispatcher + skills + audit |
| **2** | 拥有"持续意图" | 引入 Goal Stack;反思闭环;Working Set 装配 |
| **3** | 主动巡视 | 定时 workflow + 巡视清单;能开 issue 提醒人 |
| **4** | 学习与演化 | 反思笔记影响 Working Set;skill 的自动演化建议;embedding 检索 |
| **5** | 多 agent 协作 | 不同 agent 持有不同 Goal Stack,通过 issue/PR 相互协调 |

每个 Phase 的判断标准都是 **一句话能讲清的能力提升**,而不是"加了几个目录"。

---

## 13. 北极星(验收)

> **如果一个新人从零接管这个仓库,只通过读 agent 留下的文件(不问任何人),Ta 应当能在 30 分钟内回答:**
>
> - 这个 agent 现在手上在跟进什么?(Goal Stack)
> - 它最近一周做对了什么、做错了什么?(Reflections)
> - 它知道哪些只有它知道的事?(Semantic Memory)
> - 它会哪些技能、每个技能在什么协作档位?(Procedural Memory + Tier)
>
> **如果任何一个回答不出,说明 agent 的内心世界还是不可见、不可继承、不真正"长期"的——架构尚未达标。**

---

## 14. 与 Phase 1 的关系

本文件不否定 `docs/agent-architecture.md`(Phase 1 工程蓝图)。**Phase 1 是骨骼,本文件是大脑。**

| 维度 | Phase 1(工程层) | Phase 2+(认知层) |
|---|---|---|
| 解决的问题 | "怎么安全地接 LLM" | "agent 怎么思考" |
| 中心概念 | dispatcher / skills / prompts / audit | goals / memory layers / reflection / working set |
| 触发模型 | 反应式 | 反应式 + 目标驱动 + 主动式 |
| 记忆模型 | 一个扁平的 MEMORY.md | 分层(身份 / 语义 / 程序 / 情景 / 工作 / 目标) |
| 学习模型 | 无 | 反思闭环 + memory-write 候选 + skill 演化候选 |

**实施顺序建议:** 在 Phase 1 已落地的基础上,**先实现 Goal Stack 与反思闭环(§6 + §9)**——这两个是最少改动、最大杠杆的入口,做完之后 agent 才真正"活"起来。

---

## ✨ 访问交互网址

**[https://bill20221124.github.io/GitHub-claw/](https://bill20221124.github.io/GitHub-claw/)**

## 🛠️ 部署方式

本项目通过 **GitHub Pages** 部署，访问地址：  
`https://bill20221124.github.io/GitHub-claw/`

在仓库 Settings → Pages 中，将 Source 设置为 `main` 分支根目录即可。

*End of Cognitive Architecture · v0.1*
