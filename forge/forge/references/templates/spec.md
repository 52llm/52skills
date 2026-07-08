# Spec Delta: {{SLUG}}

> delta 规格：只写"改什么"，不重述全量。归档时按段合并进 `.forge/specs/<capability>/spec.md`：
> ADDED 追加 / MODIFIED 整块替换 / REMOVED 删除 / RENAMED 改名。
> 硬约束（`forge check` 会验）：
> - 每条需求 `### Requirement: 名称`，描述用 MUST/SHALL/必须 句式，每条至少一个 Scenario
> - Scenario 标题**恰好 4 个 #**（`#### Scenario:`），层级错了归档合并会静默丢失
> - MODIFIED 必须从旧 spec 复制整块（含全部 Scenario）后修改，只写片段=归档时丢细节
> - REMOVED 必须写 **Reason** 与 **Migration**

## ADDED Requirements

### Requirement: [能力名] (P1)

系统 MUST [可观察的行为]。

#### Scenario: [场景名]

- **WHEN** [触发条件]
- **THEN** [可验证的结果]
