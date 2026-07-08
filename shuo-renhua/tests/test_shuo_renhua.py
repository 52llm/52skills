"""shuo-renhua 机械层回归测试（离线）。运行：
python3 -m unittest discover -s shuo-renhua/tests   （从仓库根目录）
"""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import shuo_renhua as sr  # noqa: E402


def rules(text):
  return {(r, s) for _, r, s, _ in sr.scan_text(text)[0]}


ZH_SLOP = """随着人工智能的不断发展，我们致力于打造一站式、全方位、多维度的数字化平台，
赋能千行百业，以科技为抓手构建业务闭环——这不仅是一次升级——更是一场革命。
在这片璀璨的时代画卷上，我们扬帆起航，共同谱写属于这个时代的华章。
详情见 https://example.com/?utm_source=chatgpt.com ，地址：XX路100号。
希望对您有帮助! 未来可期,让我们拭目以待。"""

ZH_HUMAN = """前天晚上我妈给我打电话，说家里的洗衣机坏了，修一次要两百多。
她犹豫了半天，最后还是没修，说凑合用甩干桶也行。我心里有点酸，说不上来是哪一种。
我说下个月给她买台新的，她说别乱花钱。就这样吧。"""

EN_SLOP = """Let's dive into this vibrant tapestry of innovation. This groundbreaking
platform serves as a testament to our commitment, showcasing intricate capabilities
that underscore our pivotal role — a seamless experience — truly transformative.
It's not just a product, it's a movement. I hope this helps!"""


class TestZhRules(unittest.TestCase):
  def test_slop_triggers(self):
    got = rules(ZH_SLOP)
    for rid, sev in [("gaopin-cluster", "major"), ("huali-cluster", "major"),
                     ("dash-density", "major"), ("ai-url", "critical"),
                     ("placeholder", "critical"), ("assistant-zh", "critical"),
                     ("shidai-opening", "minor"), ("kong-jiewei", "minor"),
                     ("halfwidth-punct", "major")]:
      self.assertIn((rid, sev), got, rid)

  def test_human_text_clean(self):
    self.assertEqual(rules(ZH_HUMAN), set())

  def test_halfwidth_not_fooled_by_code_and_numbers(self):
    ok = "版本 v3.5 发布了，见 file.md 和 https://a.b/c?x=1，性能提升 12.5%。"
    self.assertNotIn(("halfwidth-period", "major"), rules(ok))
    self.assertNotIn(("halfwidth-punct", "major"), rules(ok))

  def test_dead_slang_and_emoji_block(self):
    t = "这家店 yyds！绝绝子！\n✅ 必点招牌\n📍 地址在老街\n⏰ 营业到十点\n"
    got = rules(t)
    self.assertIn(("dead-slang", "major"), got)
    self.assertIn(("emoji-infoblock", "major"), got)

  def test_ascii_ellipsis(self):
    self.assertIn(("ascii-ellipsis", "minor"), rules("他说不出话来...就走了。"))

  def test_code_fence_lines_skipped(self):
    t = "```python\nprint('希望对您有帮助!')\n```\n正文没有问题。"
    # fence 开关行被跳过；围栏内首行以 ``` 开头之后的行仍可能命中——
    # 这里断言至少 fence 行本身不报（粗略跳过策略的下限）
    fs, _ = sr.scan_text(t)
    self.assertTrue(all(line != 1 for line, *_ in fs))


class TestEnRules(unittest.TestCase):
  def test_en_slop_triggers(self):
    got = rules(EN_SLOP)
    self.assertIn(("en-vocab-cluster", "major"), got)
    self.assertIn(("em-dash-en", "major"), got)
    self.assertIn(("signposting", "major"), got)
    self.assertIn(("assistant-en", "critical"), got)
    self.assertIn(("negative-parallelism", "minor"), got)

  def test_lang_detection(self):
    self.assertEqual(sr._lang_of(ZH_SLOP), {"zh"})
    self.assertEqual(sr._lang_of(EN_SLOP), {"en"})


class TestStats(unittest.TestCase):
  def test_counts(self):
    t = "我试了三次，花了 45 分钟。他说：「行，你看着办。」\n\n最后我们放弃了。"
    s = sr.text_stats(t)
    self.assertEqual(s["paragraphs"], 2)
    self.assertEqual(s["quoted_speech"], 1)
    self.assertGreaterEqual(s["first_person_zh"], 2)
    self.assertGreaterEqual(s["numbers"], 2)
    self.assertEqual(s["dashes"], 0)

  def test_gaopin_hits_listed(self):
    s = sr.text_stats("我们要赋能业务，打造闭环。")
    self.assertIn("赋能", s["zh_gaopin_hits"])
    self.assertIn("闭环", s["zh_gaopin_hits"])


if __name__ == "__main__":
  unittest.main()
