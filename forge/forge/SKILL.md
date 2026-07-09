---
name: forge
description: >-
  工程流水线枢纽 + forge CLI。当用户要开工一个新功能/新项目/较大改动，说「走 forge 流程」
  「按规范开发」「先立个规格」，要初始化项目工程记忆（.forge 目录），要查在途变更进度/工程记忆状态，
  或不确定该用哪个 forge-* 子技能时使用。重量级、产物落盘；琐事（改一行、查个事实）与
  不建产物的日常任务不必加载（那是 careful 纪律层的场合）。Engineering pipeline hub:
  sizing router, .forge project memory, scaffolding CLI and mechanical gates.
---

# forge — 工程流水线枢纽

一套「spec → plan → build → review → compound」的具体工程流水线：既有方法（各阶段子技能），也有功能（真实 CLI + 落盘产物）。融合十余个项目之所长（完整清单与出处见套件 README.md）。

## 世界观（三句话）

1. **规格是主产物，代码是它的表达。** 规格与实现脱节的地方，就是返工发生的地方。
2. **结构性错误只能在前置阶段修。** 需求含混、无验收标准、选错架构——这类错误上线后无解，分析和补救救不了设计。所以价值的 80% 在规划与评审，20% 在敲代码。
3. **每单位工作要让下一单位更容易。** 复盘沉淀回流到下一次规划——这根回流箭头是整套流程存在的意义（First time: research 30min → document 5min；Next time: lookup 2min）。

## ETHOS（贯穿所有阶段）

- **完整胜过捷径**：当完整实现只比捷径多几分钟，永远做完整的。烂尾、半吊子、"以后再补"的复利是负的。
- **先搜后造**：动手造之前查三层——成熟先例（别重造）、新兴方案（要批判）、第一性原理（最珍贵）。项目内先例 > 生态现成 > 自造。
- **用户主权**：AI 负责建议与分析，用户负责决定。想改变用户已定的方向属于 User Challenge——**永远不许自动决定**，必须摆出理由交用户拍板；机械小事自决，品味类决定自决但要在收尾时明示。
- **证据高于宣称**：没有新鲜验证证据，不下"完成/能用"的结论。整条流水线的每道门都是这句话的具体化。

## 第一步：分级（先认大小，再开工）

| 级别 | 判据 | 流程 |
| --- | --- | --- |
| trivial | 改一行 / 查询 / 纯格式 | 直接做并验证。不建变更，不走流水线 |
| small | 单模块、≤半天、无破坏性 | `forge new <slug>` → proposal+tasks → build → review 轻审 → compound |
| large | 新能力 / 跨模块 / 动 schema / 安全敏感 / 迁移 / 歧义大 | `forge new <slug> --full` → 全流程（spec → clarify → plan → analyze → build → review → compound） |

拿不准算 small 还是 large → 按 large。做着做着发现升级了（越改越多、影响面扩散）→ 停下补齐上一级产物再继续。从裸会话 / careful 会话中途升级进来：`forge new` 补 proposal 与 tasks，把已做的事实补记进 progress.md，再继续走流水线。

## 流水线与子技能

| 阶段 | 子技能 | 产出 |
| --- | --- | --- |
| 定 WHAT | forge-spec | proposal.md（+ 大变更 spec.md delta 规格）、澄清记录 |
| 定 HOW | forge-plan | plan.md（候选方案/决策/风险）、tasks.md（可验证任务）|
| 执行 | forge-build | 代码 + progress.md 台账 + checkpoint commits |
| 评审 | forge-review | 双轴分层 findings → 修复 → Residual 清零 |
| 排障 | forge-debug | 根因 + 回归测试（随时可进入，修完回原阶段）|
| 复盘沉淀 | forge-compound | lessons / standards / glossary 更新 + 归档合并 |

每个子技能开头都会先做**复利检索**（查 lessons/standards），结尾都写明**下一步交棒**。

## .forge/ 工程记忆（落盘在目标项目里）

```
.forge/
├── constitution.md   宪法：3-7 条不可协商原则（plan 阶段逐条对照）
├── standards/        规范库：<域>.md + index.md（规则先行、正反代码例）
├── glossary.md       术语表：领域词唯一定义处（自立成篇，不写路径/类名）
├── lessons/          经验库：<category>/<slug>.md（frontmatter + bug/知识双轨）
├── deferred-work.md  评审挂账：存量问题台账（forge-review 首次挂账时创建）
├── specs/            结算真相：<capability>/spec.md（当前行为，归档时才更新）
└── changes/          在途变更：<slug>/{proposal,spec,plan,tasks,progress}.md → archive/
```

## forge CLI（功能层）

脚本在本 skill 目录 `scripts/forge`（bash 包装 + Python 实现，仅标准库；在目标项目目录里运行）：

```bash
bash <本skill目录>/scripts/forge init            # 在当前目录建 .forge/ 骨架（幂等，不覆盖已有）
bash <本skill目录>/scripts/forge init --git-root # 在当前仓库根目录建 .forge/ 骨架
bash <本skill目录>/scripts/forge new <slug> [--full]   # 建在途变更（--full 附 spec/plan）
bash <本skill目录>/scripts/forge list            # 在途变更与任务进度
bash <本skill目录>/scripts/forge check <slug>    # 机械质量门：delta 语法与 specs 对照/任务格式/台账对账/澄清残留/占位符
bash <本skill目录>/scripts/forge merge <slug>    # spec delta 合并进 specs/（幂等；--dry-run 预览，--capability 指 ADDED 目标）
bash <本skill目录>/scripts/forge recall <关键词>…  # 检索工程记忆（复利闭环的读端）
bash <本skill目录>/scripts/forge archive <slug>  # 归档（任务未全勾需 --force）
bash <本skill目录>/scripts/forge status          # 工程记忆总览与健康提示
```

`check` 是**确定性门**（机器可验，不靠自觉）：spec 每条 Requirement 至少一个 `#### Scenario`（恰好 4 个 #）、delta 标题与 specs/ 对照（MODIFIED/REMOVED 必须存在、ADDED 不得撞名、跨在途变更撞名告警）、tasks 每条带「→ 验证:」、已勾任务与 progress.md 台账对账、`[NEEDS CLARIFICATION]` 清零、占位符与模板残留报警。进 build 前和交评审前各跑一次。

## 复利闭环（回流箭头）

- **读端**：spec/plan/build/review/debug 开工前先 `forge recall <关键词>`，把命中的 lesson/standard 当作约束带进产物；旧经验与现场证据冲突时标日期摆出来，不许静默压过现场。
- **写端**：收工走 forge-compound——lesson 落盘、重复 2 次的教训升级 standard、新词进 glossary、delta 用 `forge merge` 合并进 specs（archive 会校验）、变更归档。
- **最后一公里**：项目 CLAUDE.md/AGENTS.md 必须有一行指向 `.forge/`（`forge init` 会给出建议文案）。没有指针，记忆就是死档案。

## 与 careful 同时加载（仪式承接映射）

careful 的**铁律 / 硬规则 / 借口拦截表原样生效**——纪律层不被流水线替代。仪式由流水线产物承接，禁止双写：

| careful 仪式 | 流水线内由谁承接 |
| --- | --- |
| [PLAN] 块 | proposal.md（WHAT）+ plan.md / tasks.md（HOW） |
| 做 → 验 → 记 小步循环 | forge-build 任务五拍（读/红/绿/验/记） |
| careful-notes.md 台账 | progress.md（唯一台账，禁止记两本） |
| [FINAL] 门 | forge-build 收尾门 + `forge check` + forge-review |
| 收工状态四选一 | 收尾门通过后照常陈述（完成/有保留/受阻/需要信息）——收尾菜单只管下一步动作，不代替状态陈述 |
| 提问纪律（≤3 问） | spec 阶段由 forge-spec 澄清循环（≤5 问）承接 |
| 复盘 playbook（retro） | forge-compound（沉淀进 `.forge/`） |

「PLAN 不是回复」与 spec/plan 阶段的用户拍板门不冲突：拍板门是带着完整产物请求决策，不是只交计划就烂尾。

## 起步

新项目：进项目目录跑 `forge init` → 立宪 → 从第一个变更开始走流水线（安装接线见套件 README.md）。
