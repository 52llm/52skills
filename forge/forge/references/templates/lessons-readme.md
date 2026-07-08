# lessons — 经验库

> 存放格式：`lessons/<category>/<slug>.md`，文件名不带日期（frontmatter 的 `date` 才是权威）。
> category 常用：debugging / architecture / conventions / performance / integration / tooling。
> 写入前先查重（`forge recall <关键词>`）：**高度重合就更新旧文档，不新建**——同一问题两份文档必然漂移。
> 消费方式：规划/评审/排障开工前 `forge recall`；旧经验与当前证据冲突时，标日期摆出来，不许静默压过现场证据。

## 条目格式（frontmatter + 双轨正文）

```markdown
---
date: YYYY-MM-DD
category: debugging
module: [受影响模块/子系统]
severity: low | medium | high
confidence: 0.3-0.9        # 这条经验的把握度；被再次印证后调高
tags: [关键词, 便于 grep]
---

# 一句话可检索的标题

（bug 轨）Problem / Symptoms / What Didn't Work / Solution / Why This Works / Prevention
（知识轨）Context / Guidance / Why This Matters / When to Apply / Examples
```

同类 lesson 出现 2 次以上，或某规则每次都要人提醒 → 升级为 `standards/` 里的正式标准。
