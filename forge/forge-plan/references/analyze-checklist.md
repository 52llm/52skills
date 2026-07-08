# analyze — 跨产物一致性体检（六道只读检查）

> 对象：proposal.md + spec.md + plan.md + tasks.md（+ constitution）。
> 特性：**只读**（发现问题回对应阶段改，本检查不动产物）；结果可复现（同输入同结论）；输出上限 50 条。

## 六道检查

| # | 检查 | 找什么 |
| --- | --- | --- |
| A | Duplication 重复 | 近似重复的需求/任务；两处描述同一行为且措辞漂移 |
| B | Ambiguity 含混 | 无量化的形容词（fast/robust/直观/无缝）；未定义的代词与术语；TODO/TBD/??? 残留 |
| C | Underspecification 欠说明 | 有动词无对象、有目标无验收；任务引用了 spec/plan 里不存在的组件或概念 |
| D | Constitution 违宪 | 与宪法 MUST 原则冲突的方案/任务——**一律 CRITICAL，不可降级** |
| E | Coverage 覆盖缺口 | 零任务对应的 Requirement；对不上任何 Requirement 的任务（要么补需求要么删任务）；P1 没有 Checkpoint |
| F | Inconsistency 矛盾 | 术语与 glossary 不一致；数据实体只在一边出现；任务顺序与依赖矛盾；技术选型互斥（plan 说 A、任务用 B） |

## 严重度

- **CRITICAL**：违宪 / 核心产物缺失 / P1 需求零覆盖 —— 不清零不准进 build。
- **HIGH**：需求冲突或重复 / 安全性能属性无法验证 / 验收标准不可测。
- **MEDIUM**：术语漂移 / 边界欠说明 / 非 P1 覆盖缺口。
- **LOW**：措辞与格式。

## 输出格式

```
| ID | 类别 | 严重度 | 位置 | 摘要 | 建议 |
```

末尾附覆盖率小结：Requirement 总数 / 有任务覆盖的数量 / 无覆盖清单。

## 纪律

- 发现问题**指回具体文件与行**，不泛泛说"需要完善"。
- 不许因为"是自己刚写的"而放水——用方法论评判，不用感情评判。
- 修完 CRITICAL/HIGH 后重跑一遍确认清零，再交用户拍板。
