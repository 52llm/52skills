"""forge CLI 回归测试（仅标准库，黑盒 subprocess 调用）。

运行: python3 -m unittest discover -s forge/tests -v
覆盖: init 幂等 / 脚手架残留告警 / check 违规捕获 / merge 四段语义与幂等 /
幻影 REMOVED 回归 / 未合并归档拦截 / 台账对账 / 跨变更撞名 / recall 目录计分 / list 去重。

临时目录按仓库约定建在仓库根的 tmp/ 下，用例结束自动清理。
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FORGE_PY = REPO_ROOT / "forge" / "forge" / "scripts" / "forge.py"
REPO_TMP = REPO_ROOT / "tmp"

REAL_SPEC = """\
## ADDED Requirements

### Requirement: 邮箱登录 (P1)

系统 MUST 允许已注册用户用邮箱+密码登录，连续失败 5 次锁定 15 分钟。

#### Scenario: 正常登录

- **WHEN** 提交正确邮箱与密码
- **THEN** 返回会话凭证
"""

MOD_SPEC = """\
## MODIFIED Requirements

### Requirement: 邮箱登录

系统 MUST 允许已注册用户用邮箱+密码登录，连续失败 3 次锁定 30 分钟。

#### Scenario: 连续失败锁定

- **WHEN** 第 3 次密码错误
- **THEN** 拒绝并提示锁定剩余时间
"""

DONE_TASKS = """\
- [x] T01 建登录骨架 → 验证: curl 返回 400
- [x] T02 实现锁定 → 验证: pytest -k lockout
"""

FULL_PROGRESS = """\
| T01 | done | abc | curl 400 |
| T02 | done | def | pytest 绿 |
"""


class ForgeCliTest(unittest.TestCase):
  def setUp(self):
    REPO_TMP.mkdir(exist_ok=True)
    self._tmp = tempfile.TemporaryDirectory(dir=str(REPO_TMP), prefix="forge-test-")
    self.addCleanup(self._tmp.cleanup)
    self.proj = Path(self._tmp.name)
    self.run_ok("init")

  def forge(self, *args: str):
    return subprocess.run(
      [sys.executable, str(FORGE_PY), *args],
      cwd=self.proj, capture_output=True, text=True,
    )

  def run_ok(self, *args: str) -> str:
    r = self.forge(*args)
    self.assertEqual(r.returncode, 0, msg=f"forge {' '.join(args)} 失败:\n{r.stdout}\n{r.stderr}")
    return r.stdout

  def write(self, rel: str, content: str):
    p = self.proj / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

  def new_change(self, slug: str, spec: str | None = None,
                 tasks: str = DONE_TASKS, progress: str = FULL_PROGRESS):
    self.run_ok("new", slug, "--full")
    if spec is not None:
      self.write(f".forge/changes/{slug}/spec.md", spec)
    self.write(f".forge/changes/{slug}/tasks.md", tasks)
    self.write(f".forge/changes/{slug}/progress.md", progress)

  def settle_login(self):
    """建立结算真相：specs/auth 里有「邮箱登录 (P1)」。"""
    self.new_change("base", spec=REAL_SPEC)
    self.run_ok("merge", "base", "--capability", "auth")
    self.run_ok("archive", "base")

  def settled_text(self) -> str:
    return (self.proj / ".forge/specs/auth/spec.md").read_text(encoding="utf-8")

  # ---------------------------------------------------------- init / 脚手架

  def test_init_idempotent(self):
    out = self.run_ok("init")
    self.assertIn("已有", out)
    self.assertNotIn("新建 .forge/constitution.md", out)

  def test_fresh_scaffold_warns_but_passes(self):
    self.run_ok("new", "demo", "--full")
    r = self.forge("check", "demo")
    self.assertEqual(r.returncode, 0)
    self.assertIn("模板占位符未替换", r.stdout)
    self.assertIn("候选方案不足", r.stdout)
    self.assertNotEqual(self.forge("check", "demo", "--strict").returncode, 0)

  # ---------------------------------------------------------- check 违规捕获

  def test_check_catches_violations(self):
    bad_spec = REAL_SPEC + (
      "\n### Requirement: 没场景的需求 (P2)\n\n系统尽量处理。\n"
      "\n#### Scenario\n- x\n\n####  Scenario: 双空格\n- x\n\n##### Scenario: 层级\n- x\n"
    )
    self.new_change(
      "bad", spec=bad_spec,
      tasks="- [ ] 没编号没验证的任务\n- [x] T09 有验证 → 验证: make test\n",
      progress="| 空 |",
    )
    self.write(
      ".forge/changes/bad/proposal.md",
      "# bad\n\n## Why\n因为。\n\n成功标准: 有\n\nOut of Scope: 无\n\n"
      "范围 TBD [NEEDS CLARIFICATION: p99?]\n",
    )
    r = self.forge("check", "bad")
    self.assertEqual(r.returncode, 1)
    self.assertEqual(r.stdout.count("Scenario 标题格式/层级错误"), 3)
    self.assertIn("没有任何 #### Scenario", r.stdout)
    self.assertIn("缺「→ 验证:」", r.stdout)
    self.assertIn("残留 [NEEDS CLARIFICATION]", r.stdout)
    self.assertIn("占位符", r.stdout)
    self.assertIn("台账证据行", r.stdout)  # T09 勾了但 progress 没记

  # ---------------------------------------------------------- merge 主链路

  def test_merge_added_flow_and_idempotency(self):
    self.new_change("demo", spec=REAL_SPEC)
    self.assertNotEqual(self.forge("merge", "demo").returncode, 0)  # specs 空须指明 capability
    out = self.run_ok("merge", "demo", "--capability", "auth", "--dry-run")
    self.assertIn("ADDED", out)
    self.assertFalse((self.proj / ".forge/specs/auth/spec.md").exists())
    self.run_ok("merge", "demo", "--capability", "auth")
    self.assertIn("### Requirement: 邮箱登录 (P1)", self.settled_text())
    out = self.run_ok("merge", "demo", "--capability", "auth")
    self.assertIn("跳过 ADDED", out)  # 幂等
    self.assertIn("delta 已合并", self.run_ok("check", "demo"))
    self.run_ok("archive", "demo")
    self.assertTrue(list((self.proj / ".forge/changes/archive").glob("*-demo")))

  def test_modified_replace_and_renamed(self):
    self.settle_login()
    self.new_change("mod", spec=MOD_SPEC)
    self.assertEqual(self.forge("check", "mod").returncode, 0)
    self.run_ok("merge", "mod")  # 唯一 capability 自动推断
    self.assertIn("3 次锁定 30 分钟", self.settled_text())
    self.assertNotIn("5 次锁定 15 分钟", self.settled_text())
    self.run_ok("archive", "mod")
    ren = ("## RENAMED Requirements\n\n"
           "- FROM: `### Requirement: 邮箱登录`\n- TO: `### Requirement: 账号密码登录`\n")
    self.new_change("ren", spec=ren)
    self.run_ok("merge", "ren")
    self.assertIn("### Requirement: 账号密码登录", self.settled_text())
    self.assertNotIn("### Requirement: 邮箱登录", self.settled_text())
    self.run_ok("archive", "ren")

  def test_phantom_removed_fails_check(self):
    """回归：REMOVED 指向从未存在的需求，不得被误判成「已合并」而放行。"""
    self.settle_login()
    phantom_tail = (
      "\n## REMOVED Requirements\n\n### Requirement: 不存在的需求\n\n"
      "系统 MUST 无。Reason: 试验。Migration: 无。\n\n"
      "#### Scenario: 无\n\n- **WHEN** x\n- **THEN** y\n"
    )
    self.new_change("phantom", spec=MOD_SPEC + phantom_tail)
    r = self.forge("check", "phantom")
    self.assertEqual(r.returncode, 1)
    self.assertIn("REMOVED「不存在的需求」在 specs/ 找不到", r.stdout)
    # 纯幻影（只有 REMOVED）同样必须 FAIL，且不得出现「delta 已合并」的 OK 判定
    self.write(".forge/changes/phantom/spec.md", phantom_tail.lstrip())
    r = self.forge("check", "phantom")
    self.assertEqual(r.returncode, 1)
    self.assertNotIn("delta 已合并", r.stdout)

  def test_merge_duplicate_op_guard(self):
    self.settle_login()
    dup = MOD_SPEC + (
      "\n## RENAMED Requirements\n\n"
      "- FROM: `### Requirement: 邮箱登录`\n- TO: `### Requirement: 登录`\n"
    )
    self.new_change("dup", spec=dup)
    r = self.forge("merge", "dup", "--dry-run")
    self.assertNotEqual(r.returncode, 0)
    self.assertIn("多个 delta 操作", r.stderr)

  # ---------------------------------------------------------- archive 门

  def test_archive_blocks_unmerged_delta(self):
    self.new_change("gate", spec=REAL_SPEC)  # 任务全勾但 delta 未合并
    r = self.forge("archive", "gate")
    self.assertNotEqual(r.returncode, 0)
    self.assertIn("尚未合并", r.stderr)
    out = self.run_ok("archive", "gate", "--force")
    self.assertIn("注意", out)

  # ---------------------------------------------------------- 协同告警

  def test_cross_change_collision_warn(self):
    self.settle_login()
    self.new_change("c-a", spec=MOD_SPEC)
    self.new_change("c-b", spec=MOD_SPEC)
    out = self.run_ok("check", "c-a")
    self.assertIn("在途变更「c-b」", out)

  def test_recall_scores_directory_name(self):
    self.settle_login()
    out = self.run_ok("recall", "auth")
    self.assertIn("specs/auth", out)

  def test_list_title_dedup(self):
    self.run_ok("new", "demo", "--full")
    out = self.run_ok("list")
    self.assertRegex(out, r"(?m)^demo\s+large\s+0/4$")


if __name__ == "__main__":
  unittest.main()
