---
name: forge-spec
description: >-
  把模糊想法磨成可测规格（定 WHAT）。当用户要开始一个新功能/新变更需要对齐需求，要写需求文档、
  规格、PRD、用户故事、验收标准，说「先把需求定清楚」「把这个想法写成 spec」「帮我理清要做什么」，
  或 forge 流水线进入定 WHAT 阶段时使用。只产文档不写代码。Grill vague ideas into testable specs:
  proposal, delta spec, clarification loop with taxonomy.
---

# forge-spec — 把想法磨成可测规格

> **硬门：本阶段只对齐 WHAT。禁止写实现代码、脚手架、或"顺手先搭起来"。你唯一的产出是文档。**
> 「这个太简单不需要对齐」正是最常翻车的念头——AI 最贵的失败模式是自信地造出错的东西。

## 第 0 步：复利检索（开工必做）

- `forge recall <关键词>`：命中的 lesson/standard 作为约束带入本次规格。
- 改现有行为 → 先读 `.forge/specs/` 里相关 capability 的现状；用 `.forge/glossary.md` 的统一词汇。
- 还没有 `.forge/` → 先 `forge init`；还没有变更文件夹 → `forge new <slug>`（大变更 `--full`）。

## 第 1 步：Grilling（逼问对齐）

苏格拉底式访谈，把想法逼成可判定的东西。**收敛以用户确认共识为准，不是你宣布对齐**：

- **一次只问一个问题**；优先单选题，并先给出你的推荐项和理由。
- **事实自己查**（代码/文档能答的不许烦用户）；**决策交用户并等答复**——在工单/自主框架里替用户答决策 = 破坏对齐。
- **具体性是唯一硬通货**："支持导出"→ 什么格式、多大数据量、谁在什么场景用。
- **兴趣不等于需求**："挺有意思/可以有"不算数，行为才算数（真的会用、真的在付钱）。
- 反谄媚：禁说「这个方案很有意思」「应该可行」——直接表态行不行、为什么。
- 收敛前先摆 **2-3 个竞争方案**，至少一个来自非显然角度（反转 / 去掉某个约束 / 类比别的领域）。
- 用户的方向被你挑战时（User Challenge）：摆出理由与你可能缺的上下文，交用户拍板，**永不自动改**。

需要用户拍板的决策用简报格式：

```
D1 <决策名>：大白话一句说清这在决定什么
风险：选错的代价是什么
推荐：选 X，因为 …（完整度 n/10：10=完整方案 7=happy path 3=走捷径）
选项：A ✅优点 ✅优点 ❌代价 ｜ B ✅ ❌❌
```

## 第 2 步：写 proposal（所有级别都要）

填 `changes/<slug>/proposal.md`：

- **Why**：为什么做、为什么是现在。写不出 Why 的变更不开工。
- **What Changes**：按优先级列要点；**P1 = 砍到只剩它也独立成立的 MVP**；破坏性标 BREAKING。
- **Out of Scope**：明确不做什么，和做什么同样重要。
- **成功标准**：可度量、技术无关。好例「95% 的搜索 1 秒内出结果」；坏例「API 响应 <200ms」（那是实现细节）。
- 拿不准的内联 `[NEEDS CLARIFICATION: 具体问题]`：**全文最多 3 个**，优先留给 范围 > 安全/数据 > 体验 > 技术；其余取合理默认写进「假设」。挂它的门槛是**问题已能精确陈述**（只是还没答案）；连问题都说不清的雾，先逼问到能陈述。

## 第 3 步：写 spec delta（仅 large）

`changes/<slug>/spec.md` 只写"改什么"，完整语法与坑见 `references/spec-format.md`：

- 四段：`## ADDED / MODIFIED / REMOVED / RENAMED Requirements`。
- 每条 `### Requirement: 名称 (P1)`：MUST/SHALL 句式写**可观察行为**（不写实现），至少一个 `#### Scenario:`（**恰好 4 个 #**）+ WHEN/THEN。
- MODIFIED 必须从旧 spec **复制整块**再改；REMOVED 必须写 Reason 与 Migration。

## 第 4 步：Clarify（澄清循环）

对照 `references/clarify-taxonomy.md` 十类覆盖扫描（成熟代码库优先用其中的**假设先行**模式：先读码出带证据的假设清单让用户纠正，少问），挑 **影响 × 不确定度** 最高的问：

- 最多 5 问，一次一问，每问带 Recommended 选项。
- 每得到一个答案：立即回写 proposal 的 `## Clarifications`（`### Session YYYY-MM-DD` 下 `- Q: … → A: …`），同步更新正文对应处、删掉对应 `[NEEDS CLARIFICATION]`。
- 禁用无量化的模糊形容词：fast / robust / 直观 / 优雅 → 换成可度量表述。

## 质量门

自检清单：无实现细节 / 每条需求可测试 / 成功标准可度量 / 边界与失败路径列了 / Out of Scope 明确 / `[NEEDS CLARIFICATION]` 清零。
然后跑机械门：`forge check <slug>`，**FAIL 清零才准交棒**。
最后把 proposal（+spec）给用户过目拍板——**用户批准是进入下一阶段的硬门，不是礼貌**。
拍板附**深化菜单**（别只给「同意/提意见」两个出口）：智选 3-5 件思维工具编号列出，用户回编号 → 对指定章节深化一轮、展示增强稿、回菜单，回「过」才算批准（直接批准也合法）。
内置候选：事前验尸 / 红队反驳 / 钢人法 / 相关方圆桌 / 十倍简化；机制与全套卡组见 careful 的 thinking-tools。

## 下一步

- large → **forge-plan**（定 HOW）。
- small → 在 tasks.md 补上可验证任务，直接 **forge-build**。
- 中途发现比预想大（影响面扩散/出现迁移/安全面）→ 升级补 spec.md 与 plan.md 再继续。
