"""结构测试：把 careful/forge 文档的设计约束机械化（测契约，不测措辞）。

思想来自 GSD 的 prompt structure tests（第五轮对照，见 forge/README.md 出处表）：
prompt 的"代码"是散文，能锁住的是行数预算、承重标记与 frontmatter 完整性——
任何一轮吸收把预算撑爆或删掉承重机制，这里直接红。
预算出处：careful/references/design.md 设计约束、forge/README.md 设计约束。
运行：python3 -m unittest discover -s forge/tests
"""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent  # skills 仓库根

CAREFUL_PLAYBOOKS = ["decide", "diagnose", "build", "research", "review",
                     "plan", "write", "transform", "ideate", "retro"]
FORGE_STAGES = ["forge-spec", "forge-plan", "forge-build",
                "forge-review", "forge-debug", "forge-compound"]


def _lines(rel):
  return len((ROOT / rel).read_text(encoding="utf-8").splitlines())


def _text(rel):
  return (ROOT / rel).read_text(encoding="utf-8")


class TestLineBudgets(unittest.TestCase):
  """行数预算：指令越长遵循率越低，预算是设计约束不是建议。"""

  def test_careful_hub_within_140(self):
    self.assertLessEqual(_lines("careful/SKILL.md"), 140)

  def test_careful_playbooks_within_45(self):
    for name in CAREFUL_PLAYBOOKS:
      self.assertLessEqual(_lines(f"careful/references/{name}.md"), 45, name)

  def test_thinking_tools_within_45(self):
    self.assertLessEqual(_lines("careful/references/thinking-tools.md"), 45)

  def test_forge_hub_within_110(self):
    self.assertLessEqual(_lines("forge/forge/SKILL.md"), 110)

  def test_forge_stage_skills_within_80(self):
    for stage in FORGE_STAGES:
      self.assertLessEqual(_lines(f"forge/{stage}/SKILL.md"), 80, stage)


class TestLoadBearing(unittest.TestCase):
  """承重标记：这些机制被删掉/改名，纪律就静默失效。"""

  def test_careful_rituals_present(self):
    t = _text("careful/SKILL.md")
    for marker in ("[PLAN]", "[FINAL]", "借口拦截", "硬规则", "任务形状"):
      self.assertIn(marker, t, marker)

  def test_forge_hub_mechanisms_present(self):
    t = _text("forge/forge/SKILL.md")
    for marker in ("trivial", "forge check", "forge recall", "仪式承接", ".forge/"):
      self.assertIn(marker, t, marker)

  def test_build_discipline_anchors_present(self):
    t = _text("forge/forge-build/SKILL.md")
    for marker in ("Iron Law", "借口拦截表", "progress.md", "先写会失败的验证"):
      self.assertIn(marker, t, marker)

  def test_review_dual_axis_present(self):
    t = _text("forge/forge-review/SKILL.md")
    for marker in ("轴 A", "轴 B", "四层实存检查", "NEEDS WORK"):
      self.assertIn(marker, t, marker)

  def test_anchor_policy_declared_both_sides(self):
    # 锚点政策：forge 的纪律节选随 careful 演进，声明必须同时在两处存在
    self.assertIn("节选", _text("forge/README.md"))
    self.assertIn("节选", _text("careful/references/design.md"))


class TestFrontmatter(unittest.TestCase):
  """每个 SKILL.md 必须有合法 frontmatter（name + description），description 不空。"""

  def _check(self, rel):
    t = _text(rel)
    self.assertTrue(t.startswith("---"), rel)
    m = re.match(r"^---\n(.*?)\n---", t, re.DOTALL)
    self.assertIsNotNone(m, rel)
    fm = m.group(1)
    self.assertIn("name:", fm, rel)
    self.assertIn("description:", fm, rel)

  def test_all_careful_forge_skills(self):
    self._check("careful/SKILL.md")
    self._check("forge/forge/SKILL.md")
    for stage in FORGE_STAGES:
      self._check(f"forge/{stage}/SKILL.md")


if __name__ == "__main__":
  unittest.main()
