# lesson 格式与字段（.forge/lessons/）

## 存放

`lessons/<category>/<slug>.md`。文件名 kebab-case、**不带日期**（frontmatter 的 date 才是权威创建日）。
category 常用集：`debugging` / `architecture` / `conventions` / `performance` / `integration` / `tooling` / `process`。

## frontmatter（必填）

```yaml
---
date: 2026-07-05          # 创建日；重大更新时另加 updated:
category: debugging
module: <受影响模块/子系统，如 auth、任务队列>
severity: low | medium | high     # 再踩一次的代价
confidence: 0.3-0.9       # 把握度；0.3=一次观察 0.6=已印证 0.9=多次印证成规律
tags: [关键词, 便于, grep]  # recall 靠它命中，写全同义词
---
```

## bug 轨（排障出坑用）

```markdown
# 一句话可检索的标题（症状或规律，不要写"记一次排查"）

## Problem
出了什么事、影响什么。

## Symptoms
可观察症状（报错原文、日志特征）——未来的检索入口，尽量原文。

## What Didn't Work
试过但无效的路（和解法一样值钱：帮下次跳过弯路）。

## Solution
最终修法（关键 diff 或命令）。

## Why This Works
根因解释——为什么这个修法成立。

## Prevention
怎么让这类问题结构性不再发生（校验/断言/规范/hook）。
```

## 知识轨（模式/约定/决策用）

```markdown
# 一句话可检索的标题

## Context
什么背景下得出的（含当时的约束）。

## Guidance
规则本身，可判定的表述。

## Why This Matters
不遵守的代价。

## When to Apply
适用边界与例外（没有例外就写"无已知例外"）。

## Examples
正例/反例（代码或场景）。
```

## 查重（写入前必做）

`forge recall <标题关键词>`，对命中项按五维估重合：同一问题？同一根因？同一模块？同一解法？同一边界？
**高度重合 → 更新旧文档**（补案例、调 confidence、必要时改标题），不新建。

## supersede（推翻不删除）

结论被推翻时，旧 lesson 顶部加：

```markdown
> **SUPERSEDED (2026-07-05)**: 本条已被 <新slug> 取代，原因：<一句话>。
```

推翻的理由也是知识；删档会让同样的错误论证再来一遍。

## 质量自检

- 标题只看一眼能判断"与我现在的问题相关吗"？
- tags 覆盖了未来会用的搜索词（含英文/中文同义词）？
- 有 no-op 风险吗——这条会真的改变下次行为吗？「聪明但不可执行」的诊断也是 no-op。
- 是正向动作吗——「别做 Y」改写成「要做 X」；禁令只留给无法正向表述的硬护栏，且配替代动作。
- 正文自立成篇（不依赖"见上次会话"这类死链接）？
