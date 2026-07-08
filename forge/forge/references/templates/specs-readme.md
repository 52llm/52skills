# specs — 现行为规格（结算真相）

> 这里描述系统**当前**的行为，按能力（capability）组织：`specs/<capability>/spec.md`。
> 在途改动不直接改这里——先在 `changes/<slug>/spec.md` 写 delta，实现并验证后归档时合并：
> ADDED 追加 / MODIFIED 整块替换 / REMOVED 删除。
> 良性循环：specs 描述现状 → change 提 delta → 实现 → 归档合并 → specs 描述新现状 → 下一个 change 站在更新后的真相上。

## 条目格式

```markdown
# <capability>

## Requirements

### Requirement: 名称
系统 MUST [可观察行为]。

#### Scenario: 场景名（恰好 4 个 #）
- **WHEN** 触发条件
- **THEN** 可验证结果
```
