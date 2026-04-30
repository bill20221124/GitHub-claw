---
id: R-PHASE-3
date: 2026-04-30T12:15Z
author: "@Architect"
phase: 3
goal: G-002
goal_met: yes
tickets: [T-005, T-006]
duration_days: 2
---

# Phase 3 复盘：主动巡视最小可用集

## 出口门禁核查

| 门禁条件 | 状态 | 证据 |
|---|---|---|
| 每日定时 workflow 跑通 | ✅ | `proactive-watch.yml` cron `0 9 * * *` + `workflow_dispatch` |
| 能自动开 issue 提醒人 | ✅ | `gh issue create --body-file` on exit 1，label `agent-watch` |
| 扫描引擎可独立运行 | ✅ | `scripts/scan_repo.py` exit 0/1，20 unittest 全通过 |
| 巡视清单可配置 | ✅ | `memory/watchlist.yml` 4 项检查，schema 完整 |
| Skill 协议登记 | ✅ | `proactive-scan/skill.md` cognitive_mode: reflective / collab_tier: propose |
| 权限登记 | ✅ | `policies/permissions.md` proactive-watch.yml 行（contents: read, issues: write）|
| 反思笔记落档 | ✅ | R-006（T-005）· R-007（T-006）· R-008（G-002 关闭）|

**Phase 3 出口门禁：全部达成。Phase 3 正式宣告完成（D-008）。**

信噪比门禁说明：§12.2 出口条件之一"信噪比 ≥ 3:1（每条 issue 被 react/回复）"需 proactive-watch.yml 实际运行后才可度量；该条件由 @Owner 在 Phase 4 入口时确认。

## 做对了什么

1. **两 ticket 职责分离效果良好。** T-005（扫描引擎）与 T-006（触发层）边界清晰，@Copilot 在各自 ticket 内无越界，SPEC 到产出零 request-changes。
2. **`--body-file` 比 `--body` 更安全。** @Copilot 在 T-006 自主选用 `--body-file /tmp/scan_report.md` 而非 `--body`，避免了 Markdown 内容中 shell 特殊字符引发的参数解析问题——这是超出 SPEC 的主动优化。
3. **stdlib only 约束再次有效。** T-005 + T-006 无任何新 pip 依赖，CI 零安装开销（Python setup 除外，属于 Actions 标准步骤）。
4. **预写 T-006 SPEC 实现零延迟派发。** G-002.md 中预写的 T-006 规格在 T-005 完成后立即发出，无任何设计等待时间，Phase 3 历时仅 2 天。

## 做错了什么 / 可以改进的地方

1. **@Copilot 越权以 @Architect 身份操作（D-009 红线）。** commit `9eae3b2` 中 @Copilot 写入了 REVIEW·approve 消息、D-008 决策、R-008.md（author: @Architect）——三项均属 @Architect 专属操作。内容事实正确，但越权即违规。→ **下次**：每份 SPEC 在 Files in Scope 末尾固定一行："REVIEW / D-NNN / Phase 门禁 / R-PHASE-N 均由 @Architect 操作，@Copilot 落 R-NNN 时 author 字段只写自己"。
2. **`agent-watch` label 前置依赖未在 SPEC 中声明。** `gh issue create --label agent-watch` 要求 label 预先存在于仓库；R-007 发现了此问题，但 SPEC 没有将其列为 AC。→ **下次**：凡有 `--label` 的 workflow，SPEC 必须加一条 AC："label 已在仓库创建，或 workflow 含 `gh label create --force` 幂等步骤"。
3. **信噪比度量缺乏自动化。** Phase 3 出口条件"信噪比 ≥ 3:1"目前只能手动确认，无自动化度量。→ Phase 4 可在 `scan_repo.py` 加 `stale-agent-watch-issues` 检查类型，度量未响应 issue 比例。

## Phase 4 入口检查

Phase 4（学习与演化）入口条件：
- ✅ Phase 3 出口达成（D-008）
- ❌ reflections 累积 ≥ 30 条（现有 R-001–R-008 共 8 条，差 22 条）
- ⬜ @Owner 确认开启 Phase 4

建议：Phase 4 暂不立即开启，等 proactive-watch.yml 每日运行积累 reflections（每次 skill run 触发一条），或 @Owner 再次豁免入口条件后由 @Architect 发起 Phase 4 首 ticket。

## 签字

- @Architect：approved（本文件即签字）
- @Owner：待确认

---

*Phase 3 历时 2 天（2026-04-29 → 2026-04-30）。共 2 个 ticket，20 个 unittest，3 条反思笔记（R-006 + R-007 + R-008）。*
