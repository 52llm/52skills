# changes — 在途变更

> 每个变更一个文件夹（`forge new <slug>` 创建），彼此并行互不冲突；完成后归档进 `archive/YYYY-MM-DD-<slug>/`。
> in-flight（这里）与 settled truth（../specs/）物理分离：评审只看 delta，归档才合并。

## 生命周期

1. `forge new <slug>`（small：proposal+tasks；`--full` 大变更再加 spec+plan）
2. forge-spec 对齐 WHAT → forge-plan 定 HOW → `forge check <slug>` 过机械门
3. forge-build 执行（progress.md 记台账）→ forge-review 评审
4. forge-compound 复盘沉淀 → `forge merge <slug>` 合并 delta → `forge archive <slug>`（会校验已合并）
