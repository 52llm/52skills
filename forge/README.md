# forge — 工程流水线技能套件

一组互相衔接的 Claude Code / Codex skills：把一个想法带上 **spec → plan → build → review → compound** 的完整流水线。既有思想（各阶段方法论），也有功能（真实 CLI + 落盘产物 + 机械质量门）。

融合了 14 个项目之所长：superpowers、spec-kit、OpenSpec、agent-os、compound-engineering-plugin、gstack、ECC (everything-claude-code)、andrej-karpathy-skills、mattpocock-skills、agency-agents、scientific-agent-skills、BMAD-METHOD、gsd-core、claude-code-templates。与本仓库 `careful`（通用工作纪律层）互补，**一轻一重**：careful 轻、零产物，日常任何任务都可用；forge 重、产物落盘，只在功能级/复杂变更时启用。careful 管怎么干活，forge 管干什么活、按什么顺序、落什么盘、如何复利；两者同载时的仪式承接映射见 `forge/SKILL.md`。forge 各阶段内联的 Iron Law / 借口拦截节选是**最小纪律锚点**（保证单独加载也安全）：锚点只是 careful 条款的节选，随 careful 演进同步，但不得出现 careful 没有的纪律。

## 套件结构

| 目录 | 职责 | 一句话 |
| --- | --- | --- |
| `forge/` | 枢纽 + CLI | 分级路由（trivial/small/large）、`.forge/` 工程记忆、`scripts/forge`（init/new/list/check/merge/recall/archive/status） |
| `forge-spec/` | 定 WHAT | 逼问对齐 → proposal → delta 规格 → 澄清分类法（≤5 问） |
| `forge-plan/` | 定 HOW | 前提挑战、最小可行 vs 理想架构同权、宪法门、tracer-bullet 拆任务、六道一致性体检 |
| `forge-build/` | 执行 | 先红后绿、外科手术纪律、progress 台账、卡住熔断、验证铁律 |
| `forge-review/` | 评审 | 双轴分离（规格符合 vs 代码质量）、镜头阵容（security 永不跳过）、默认 NEEDS WORK |
| `forge-debug/` | 排障 | 能变红的复现回路 → 竞争假设 → 根因回溯 → 回归测试 |
| `forge-compound/` | 复利 | lesson 双轨沉淀、升级 standard、术语表、Discoverability、delta 合并归档 |

## 落盘产物（在目标项目里）

```
.forge/
├── constitution.md   宪法（plan 阶段逐条对照）
├── standards/        规范库 + index.md
├── glossary.md       术语表
├── lessons/          经验库（frontmatter + 双轨）
├── deferred-work.md  评审挂账（存量问题，首次挂账时创建）
├── specs/            结算真相（当前行为规格）
└── changes/          在途变更 → archive/
```

## 安装与起步

```bash
cd <本仓库根目录>
for s in forge forge-spec forge-plan forge-build forge-review forge-debug forge-compound; do
  ln -s "$PWD/forge/$s" ~/.claude/skills/$s
done
cd <你的项目> && bash ~/.claude/skills/forge/scripts/forge init
```

## 主要设计的出处

- **superpowers**：铁律 + 借口拦截表的表述范式；两段评审防污染；file-handoff 与 progress 台账；收尾菜单（discard 要打字确认）；description 只写触发条件不写流程摘要。
- **spec-kit**：澄清覆盖分类法（≤5 问带推荐项）；analyze 六道一致性检查与严重度分级；宪法 + Constitution Check 门；成功标准可度量且技术无关；`[NEEDS CLARIFICATION]` ≤3。
- **OpenSpec**：changes/（在途）与 specs/（结算真相）物理分离；delta 规格（ADDED/MODIFIED/REMOVED/RENAMED + 4 个 # 的 Scenario）；归档合并的良性循环；分级仪式感（fluid not rigid）。
- **agent-os**：standards 作为可注入上下文（规则先行 + 正反例 + index 检索层）。上游 clone 2026-07 已删（star 太少）；已吸收条款保留，后续与新证据冲突时逐步剔除。
- **compound-engineering**：复利飞轮世界观与回流箭头；lesson 双轨 frontmatter schema；查重五维（更新不新建）；Discoverability Check；80/20（价值在规划与评审）。
- **gstack**：ETHOS（完整胜过捷径 / 先搜后造三层 / 用户主权）；决策简报格式（含完整度 n/10）；User Challenge 永不自动决定；评审阵容的 NEVER_GATE；验证 Iron Law 台词。
- **ECC**：确定性质量门思想（`forge check` 即机械 delivery-gate）；lesson 的 confidence 字段与升级管线（instinct → standard/hook）；silent-failure 猎物清单；外部数据不可信基线。
- **karpathy**：外科手术改动（孤儿分治、每行可追溯）；简单性四禁；强成功标准 → 才能自主循环。
- **mattpocock**：grilling 逼问原语；tracer-bullet 垂直切片与 seam 最少化；评审双轴不合并重排；删除测试；同义反复/实现耦合测试反模式；ADR 三条件；glossary 纪律；写 skill 的元工艺（no-op 测试、触发词前置）。v1.1.0 增量（2026-07 第六轮）：事实/决策分治与用户确认门（grilling）；expand–contract 宽改造（爆炸半径分批、批批 CI 绿）；测试只落约定接缝；Fowler 异味基线两约束（仓库规范压过基线、永为 judgement call）；正向表述（"别想大象"，禁令须配替代动作）；雾/工单精确性判据；[HITL] 任务契约。其 wayfinder 地图机制未采纳（目的地先行/地图即索引/雾出界分离已被成功标准、台账写引用、NEEDS CLARIFICATION vs Out of Scope 覆盖）；红绿循环剔除重构（重构归评审）未采纳——forge-build 的「边走边简化」是有界的 Phase 末尾动作，与评审端不冲突。
- **agency-agents**：逐任务 Dev↔QA 环（retry≤3、逐级门禁）；默认 NEEDS WORK + AUTOMATIC FAIL 触发；镜头派遣卡的角色骨架。
- **scientific-agent-skills**：「结构性错误只能在前置阶段修」框架；竞争假设 + 可证伪 + 区分性观察；反自欺纪律（确认性 vs 探索性、不许为绿改标准）；分层反馈结构；复现率放大。
- **BMAD-METHOD**（v6，2026-07 第四轮对照）：拍板门的深化菜单（编号深化循环，卡组正本在 careful thinking-tools）；任务简报装配职责（将改文件先读、隐式需求也是需求、经验回传）；中途变卦三路线（就地调整/回滚/砍范围）；评审 finding 主会话重定级 + deferred-work 挂账；零 finding=评审失效；analyze 新鲜上下文；评审换模型去相关。其具名人格 agent、customize 三层覆盖、微文件步骤机未采纳（与轻量/跨 harness 约束冲突）。
- **GSD-core**（2026-07 第五轮对照）：目标倒推验证（任务完成≠目标达成；评审四层实存检查 存在→有实质→被接线→数据流真通；行为断言静态不充分）；计划外发现协议（顺手修正确性要件/停下问架构级/挂账存量，slopsquat 守卫正本在 careful）；假设先行澄清模式（clarify-taxonomy）；决策覆盖验证；~50% 上下文规划锚；编排方不碰源文件；逐文件 stage；结构测试（tests/test_structure.py，把行数预算与承重标记机械化）。其能力注册表、16 运行时适配、变异测试基建未采纳（分发管道与过重基建）。
- **claude-code-templates**（2026-07 第六轮对照）：仅取基建理念两条——评审阅读策略随 diff 规模缩放（<20 文件全读 / 20–100 先 diff 再深读高危 / >100 缩范围）；硬护栏阻断/警告分级（阻断只给判定准确的规则，会误伤的门迟早被绕过）。目录内容（423 agents / 341 commands / 3135 skills）为关键词样板与拼贴，未采纳。

## 设计约束（改动时保持）

- description 只写触发条件，不写流程摘要——写了摘要，模型会以为读过正文而不加载。
- 纪律锚点政策：forge 内联的 Iron Law / 借口表是 careful 条款的**节选**，随 careful 同步；
  不得出现 careful 没有的纪律。careful 新增硬规则时，检查 forge-build / forge-debug 的节选要不要跟。
- 模板即规格：`forge check` 的模板残留检查从 `references/templates/` **动态推导**占位符——
  改模板不用改代码，但新增占位符必须用 `[方括号]` 且不放进引导行（`>` / `<!--`），否则查不到。
- hub（forge/SKILL.md）≤110 行、各阶段 SKILL ≤80 行；CLI 仅标准库；
  改 `forge.py` 必须过 `forge/tests/` 回归套件。

## 本地校验

```bash
python3 -m py_compile forge/forge/scripts/forge.py
python3 -m unittest discover -s forge/tests -v
bash forge/forge/scripts/forge --help
mkdir -p tmp/forge-smoke
cd tmp/forge-smoke && bash ../../forge/forge/scripts/forge init && bash ../../forge/forge/scripts/forge new demo --full && bash ../../forge/forge/scripts/forge check demo && bash ../../forge/forge/scripts/forge merge demo --capability demo --dry-run
```
