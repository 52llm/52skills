---
name: forge-compound
description: >-
  复盘沉淀与归档——把本次工作的教训变成下次的起点（复利飞轮）。当一个变更/排障/评审收尾，
  用户说「复盘一下」「这个坑记下来」「总结沉淀」「retro」，要把 lesson 升级成规范、更新术语表，
  或要归档在途变更（合并 delta 进 specs）时使用；被用户纠正过的会话收尾时也应主动使用。
  Retro and capture at the end of a change: lessons, standards, glossary, spec-delta merge, archive.
---

# forge-compound — 复利飞轮

> 每单位工作要让下一单位更容易——**这根回流箭头是整条流水线存在的意义**。
> 第一次：调研 30 分钟 → 写下来 5 分钟；下一次：查 2 分钟。不写，就永远是 30 分钟。

本技能是 careful「复盘/沉淀」形状在 `.forge/` 工程记忆上的具体化：forge 项目里沉淀一律走这里；散文式经验库（CLAUDE.md、独立笔记）才用 careful 的 retro playbook。

## 触发时机

变更收尾 / 排障出坑（查了 >30 分钟、反直觉、会再踩）/ **被用户纠正后**（纠正 = 最高价值的学习源）/ 评审发现同类问题第二次出现 / 周期性 retro。

## 第 1 步：提取候选学习

从本次会话里扫三类信号（这三类的沉淀价值最高）：

1. **用户纠正**：用户说"不对/不是这样/换成 X"的每一处 → 背后的规则是什么？
2. **错误解决**：走了弯路才修好的问题 → 弯路（What Didn't Work）与根因一样值钱。
3. **重复工作流**：这次又手工做了一遍的流程 → 值得固化。

每条候选先做 **reuse / compose / novel** 三态判定：

- **reuse**：`forge recall` 查到已有 lesson 覆盖 → **更新旧文档**（补案例、调 confidence），不新建——同一问题两份文档必然漂移。
- **compose**：是既有能力/技能的组合 → 写"薄配方"（frontmatter + 按序调用哪些东西），不重复正文。
- **novel**：全新 → 走第 2 步写新 lesson。

## 第 2 步：写 lesson

落盘 `.forge/lessons/<category>/<slug>.md`（格式与字段详见 `references/lesson-schema.md`）：

- 双轨选一：**bug 轨**（Problem / Symptoms / What Didn't Work / Solution / Why This Works / Prevention）或**知识轨**（Context / Guidance / Why This Matters / When to Apply / Examples）。
- frontmatter 必填 date/category/module/severity/confidence/tags；**标题一句话可检索**（未来的你只会看到标题和 tags）。
- 一次复盘的主产出是**一个文件**——贪多会稀释；真有多条独立教训才分多个。
- 写完自问 no-op 测试：这条 lesson 会改变下次的行为吗？不会就删——正确但不改变行为的话是沉积物。

## 第 3 步：升级判定（lesson 不是终点）

- **升级成 standard**：同类 lesson 第 2 次出现，或某规则每次都要人提醒 → 写进 `.forge/standards/<域>.md`（**规则先行**：H2 标题即规则本身 + 正反代码例 + bullet），并更新 `standards/index.md` 一行描述。
- **升级成硬护栏**：违反代价大且机器可判定的规则（如"禁止改 lint 配置降标准""改文件前必须先读"）→ 建议用户配 hook/CI 检查，给出可粘贴的建议；纪律交给确定性机制，比每次靠自觉便宜。
- **收进 glossary**：讨论中被误解过的词、新领域名词 → `.forge/glossary.md` 一句话定义+边界。铁律：自立成篇，不写文件路径/类名/具体阈值。
- **记决策**：满足三条件之一的决策（难回退 / 缺上下文会觉得奇怪 / 真实取舍的产物）→ 知识轨 lesson；决策被推翻时**写 supersede 标注**，不删旧文（推翻的理由也是知识）。

## 第 4 步：Discoverability Check（最后一公里，每次都跑）

检查项目 CLAUDE.md / AGENTS.md 是否有指向 `.forge/` 的指针行；没有就补一行（信息式语气，不命令式）：

```
- `.forge/` 是本项目的工程记忆（宪法/规范/术语/经验/规格）。规划、评审、排障前先检索 lessons 与 standards。
```

**没有指针，知识库就是死档案**——写得再好也不会被下一个会话读到。

## 第 5 步：归档变更

1. tasks.md 全勾、评审 Residual 清零。
2. 合并 delta：`forge merge <slug>`（机械执行 ADDED 追加 / MODIFIED 整块替换 / REMOVED 删除 / RENAMED 改名，幂等；先 `--dry-run` 预览；ADDED 目标 capability 不唯一时用 `--capability` 指明。语义见 forge-spec 的 spec-format）。合完抽查 `.forge/specs/` 对应文件。
3. `forge archive <slug>`（会校验 delta 确已合并，未合并会拒绝；全套产物进 `archive/YYYY-MM-DD-<slug>/` 留审计）。
4. `forge status` 看一眼健康提示收尾。

## 检索协议（读端——其他阶段怎么消费这里写的东西）

- 开工先 `forge recall <关键词>`（grep 优先：先命中 frontmatter/标题缩小候选，再读强匹配全文），把命中蒸馏成三样带走：**约束 / 要避免的失败路 / 要跟的模式**。
- **旧经验不许静默压过现场证据**：冲突时标日期摆出来（"2025-03 的 lesson 说 X，但当前代码已是 Y"），让证据裁决。
- confidence 随印证调整：再次踩中 +0.1，被推翻就 supersede。

## 下一步

飞轮回到起点：下一个变更的 forge-spec 第 0 步，会读到你刚写下的东西。
