# Delta 规格完整语法

> 为什么用 delta 而非全量重写：改动一目了然（不用心算 diff）、多变更并行改同一 capability 的不同需求不冲突、评审只看变化、天然适配存量项目（brownfield）。

## 四种 delta 段

```markdown
## ADDED Requirements      ← 新行为（归档时追加进 specs/）
## MODIFIED Requirements   ← 改行为（归档时整块替换）
## REMOVED Requirements    ← 废弃（归档时删除；必须写 Reason 与 Migration）
## RENAMED Requirements    ← 仅改名（用 FROM: / TO: 两行）
```

## Requirement 块格式

```markdown
### Requirement: 用户可以用邮箱登录 (P1)

系统 MUST 允许已注册用户使用邮箱 + 密码登录，连续失败 5 次后锁定 15 分钟。

#### Scenario: 正常登录

- **WHEN** 用户提交正确的邮箱与密码
- **THEN** 返回会话凭证并跳转到首页

#### Scenario: 连续失败锁定

- **WHEN** 同一账号 15 分钟内第 5 次提交错误密码
- **THEN** 拒绝登录并提示锁定剩余时间，期间正确密码也 MUST 被拒绝
```

要点：

- 描述用 **MUST / SHALL / 必须**，避免 should/may/尽量——规格是承诺不是愿望。
- 写**可观察行为**（用户/调用方能看到什么），不写实现（用什么库、什么表结构）。
- 优先级标在 Requirement 上：**(P1) = 只实现它也是可交付的 MVP**；P2/P3 可砍可延期。
- 每条 Requirement **至少一个 Scenario**；边界与失败路径值得单独 Scenario。

## 硬约束（`forge check` 机械验证）

| 规则 | 违反后果 |
| --- | --- |
| Scenario 标题**恰好 4 个 #**（`#### Scenario:`） | 层级错误会让归档合并静默丢内容 |
| 每条 Requirement ≥1 个 Scenario | 无场景 = 不可验收 = FAIL |
| MODIFIED 必须复制**整块**（`### Requirement:` 到最后一个 Scenario）再修改 | 只写片段 → 归档替换时丢掉未写的细节 |
| Requirement 标题与旧 spec 匹配（空白与尾部 (Pn) 不敏感） | 匹配不上 → `forge check` FAIL、`forge merge` 拒绝执行 |
| REMOVED 必须含 **Reason**（为什么废弃）与 **Migration**（存量怎么办） | 缺失 = 评审打回 |

## 归档合并语义（`forge merge <slug>` 机械执行，forge-compound 第 5 步调用）

```
specs/ 描述现状 → change 写 delta → 实现+验证 → 归档时合并：
  ADDED    追加到 specs/<capability>/spec.md 的 Requirements 下
  MODIFIED 按标题定位，整块替换
  REMOVED  按标题定位，整块删除
  RENAMED  按 FROM 定位改标题
→ specs/ 描述新现状 → 下一个 change 站在更新后的真相上
```

merge 幂等可重跑、支持 `--dry-run` 预览；ADDED 的目标 capability 唯一时自动推断，否则用
`--capability` 指明；`forge archive` 会校验合并已完成，未合并会拒绝归档。

## 常见坑

- 把"怎么实现"写进 Requirement（出现库名/表名/函数名 = 走味了，挪去 plan.md）。
- Scenario 写成测试用例代码（这里是行为语言，代码在 build 阶段）。
- 一条 Requirement 塞多个行为（拆开，否则优先级和验收都糊）。
- 忘了给失败路径写 Scenario（happy path 之外才是质量所在）。
