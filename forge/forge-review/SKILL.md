---
name: forge-review
description: >-
  双轴多镜头代码评审（也含接收评审的纪律）。当用户要 review 代码/diff/PR/一个在途变更，
  说「帮我看看这段代码」「提交前检查一下」「挑挑毛病」，或 forge 流水线 build 完成进入评审时使用；
  也用于收到他人评审意见后的处理；合并任何非琐碎改动前使用。Dual-axis multi-lens code review;
  use before merging any nontrivial change and when receiving review feedback.
---

# forge-review — 双轴多镜头评审

> 评审的两问永远分开答：**①符合规格吗？②代码质量过关吗？** 两轴各自出结论，
> 禁止合并重排成一张"总分表"——重排正是分离要防的掩盖。

## 评审方（给别人/给自己的 diff 挑毛病）

**第 0 步**：`forge recall <关键词>`——过往同类翻车 lesson 就是本次的检查项；读 change 的 proposal/spec/tasks（无 forge 上下文时，先向用户要"这次改动想达成什么"，没有意图就没有评审基准）。评审基于 diff 与产物，**不基于作者自述**——自述里的理由不能降低任何 finding 的严重度。

**轴 A：规格符合度**。对照 Requirement/Scenario 逐条过：Missing（承诺了没做）/ Extra（没承诺却做了，夹带按未授权处理）/ Misunderstood（做拧了）。diff 看不出来的标「无法验证」并说要什么证据，不许猜。
每条「已实现」再过**四层实存检查**——任务完成 ≠ 目标达成，占位符也能让任务"完成"：
①存在（文件/符号在）→ ②有实质（非 stub，无 TODO/PLACEHOLDER，行数与导出对得上承诺）→
③被接线（有真实 import 与调用点，不是孤岛）→ ④数据流真通（上游喂的不是空值/硬编码）。
行为类断言（状态迁移/清理时序/并发）静态四层全过也只算「无法验证」——要跑起来看。
另对照 plan.md 的 **Decisions 逐条查落地**：需求都覆盖了、决策被无视，同样是返工。

**轴 B：代码质量**，按镜头阵容过（详表见 `references/lenses.md`）：

| 镜头 | 何时启用 |
| --- | --- |
| correctness / testing / simplicity | **常驻** |
| security | 涉输入解析、权限、密钥、外部数据 → 启用；**NEVER_GATE：静默多轮也不许跳过** |
| data-migration | 动 schema/存量数据 → 启用，同为 NEVER_GATE |
| performance | 热路径、循环里 IO、N+1 |
| silent-failure | 错误处理多处 → 空 catch、吞错兜底、丢 stack、无超时 |
| adversarial | 常驻收尾一遍：像攻击者+混乱工程师那样想，只挑刺不夸 |

有子代理 → 每镜头独立新鲜上下文并行跑（互不知晓，防互相附和），跨镜头互证的 finding 严重度升一级；主会话汇总时逐条读 finding 周边源码后**重新定级**——严重度 = 真实调用点上的真实后果，子代理自评仅作参考。无子代理 → 逐镜头串行，切换镜头时刻意清空上一镜头的立场。

**输出（分层，不平铺）**：

```
Summary: 一段话（改动做了什么 + 总体判断）
Critical: 会造成错误行为/数据损坏/安全洞——逐条 file:line + 问题 + 为何 + 修法
Important: 该修但不阻塞——同上
Minor: 品味与打磨
Deferred: 存量问题（非本变更引入）——真实但现在不修，挂账 .forge/deferred-work.md
          （日期 + file:line + 一句话 + 为何缓；首次挂账时创建该文件）
Questions: 需要作者回答才能裁决的
Verdict: NEEDS WORK（默认）/ READY WITH FIXES / READY
```

- **默认 NEEDS WORK**，要压倒性证据才给 READY——首次实现通常要 2-3 轮修订，直接满分是失职信号。
- **零 finding = 评审失效信号**，不是通过：换镜头/换角度重跑一遍，第二遍仍为零才可作为通过证据，并写明跑了两遍。
- **AUTOMATIC FAIL**：上游宣称"零问题"、无证据的满分/自夸（"98/100"）、验证输出缺失。
- 评判方法论不评判立场：不许因为"结论我喜欢"而放宽标准；工具已强制的（lint/类型）不重复报。

## 接收方（收到评审意见时）

1. **禁表演式附和**：「您说得对！」「好问题！」——写出来就删掉，用修复本身回应。
2. 每条 finding **技术核实**后再动：复现它、读相关代码。成立 → 修；不成立 → 拿证据反驳。评审是待验证的输入，不是命令——哪怕两个评审都这么说，一致是信号不是授权。
3. YAGNI 反查：被建议"加灵活性/加配置"时先 grep 使用方——没人用就拒绝，附证据。
4. 全部处理完复跑验证 + `forge check`，**Critical 清零**才算过 Residual 门。

## 下一步

评审清零 → 回 forge-build 收尾菜单（合并/PR）。评审里挖出的通用教训（同类问题第二次出现、踩了没人写过的坑）→ **forge-compound** 沉淀成 lesson/standard。
