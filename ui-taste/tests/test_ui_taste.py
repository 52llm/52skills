"""ui-taste 机械层回归测试。运行：
python3 -m unittest discover -s ui-taste/tests   （从仓库根目录）
"""

import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import ui_taste  # noqa: E402


def scan_snippet(content, suffix=".tsx"):
  with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8") as f:
    f.write(content)
    path = f.name
  try:
    return {(r, s) for _, r, s, _ in ui_taste.scan_file(path)}
  finally:
    pathlib.Path(path).unlink()


class TestCheckRules(unittest.TestCase):
  def test_critical_rules_fire(self):
    hits = scan_snippet("""
      <div onClick={go} style={{transition: 'all 0.3s'}}>
        <img src="/a.png" />
      </div>
      window.addEventListener('scroll', onScroll);
    """)
    for rule in ("div-onclick", "transition-all", "img-no-alt", "scroll-listener"):
      self.assertIn((rule, "critical"), hits, rule)

  def test_viewport_and_paste_criticals_fire(self):
    hits = scan_snippet("""
      <meta name="viewport" content="width=device-width, user-scalable=no" />
      <input onPaste={(e) => e.preventDefault()} />
    """, suffix=".html")
    self.assertIn(("user-scalable", "critical"), hits)
    self.assertIn(("block-paste", "critical"), hits)

  def test_filler_words_extended(self):
    hits = scan_snippet('<p>In the world of AI, we Delve into Seamless workflows.</p>')
    self.assertIn(("filler-words", "minor"), hits)

  def test_em_dash_english_critical_chinese_minor(self):
    en = scan_snippet('<p>Fast — reliable — beautiful</p>')
    zh = scan_snippet('<p>快——而且好看</p>')
    self.assertIn(("em-dash", "critical"), en)
    self.assertIn(("em-dash", "minor"), zh)
    self.assertNotIn(("em-dash", "critical"), zh)

  def test_major_rules_fire(self):
    hits = scan_snippet("""
      <section className="h-screen bg-gradient-to-r from-purple-500 to-violet-600">
        <h1 className="bg-clip-text">Acme</h1>
        <aside style={{zIndex: 9999}} className="z-[9999] border-l-4">x</aside>
      </section>
    """)
    for rule in ("h-screen", "ai-gradient", "gradient-text", "arbitrary-z",
                 "side-stripe", "placeholder-copy"):
      self.assertIn((rule, "major"), hits, rule)

  def test_outline_none_needs_focus_visible(self):
    bad = scan_snippet('<button className="outline-none">x</button>')
    ok = scan_snippet('<button className="outline-none focus-visible:ring-2">x</button>')
    self.assertIn(("outline-none", "major"), bad)
    self.assertNotIn(("outline-none", "major"), ok)

  def test_reduced_motion_hint(self):
    bad = scan_snippet('import { motion } from "motion/react";')
    ok = scan_snippet('import { motion, useReducedMotion } from "motion/react";')
    self.assertIn(("no-reduced-motion", "minor"), bad)
    self.assertNotIn(("no-reduced-motion", "minor"), ok)

  def test_eyebrow_density(self):
    line = '<span className="uppercase tracking-widest">A</span>\n'
    hits = scan_snippet(line * 5)
    self.assertIn(("eyebrow-density", "major"), hits)
    hits2 = scan_snippet(line * 2)
    self.assertNotIn(("eyebrow-density", "major"), hits2)

  def test_clean_file_has_no_findings(self):
    hits = scan_snippet("""
      export function Card({ title }: { title: string }) {
        return <button aria-label="open" className="rounded-lg focus-visible:ring-2">{title}</button>;
      }
    """)
    self.assertEqual(hits, set())

  def test_css_rules(self):
    hits = scan_snippet(".hero { height: 100vh; border-left: 4px solid red; }", suffix=".css")
    self.assertIn(("h-screen", "major"), hits)
    self.assertIn(("side-stripe", "major"), hits)


class TestContrast(unittest.TestCase):
  def test_black_on_white_is_21(self):
    self.assertAlmostEqual(ui_taste.contrast_ratio("#000", "#fff"), 21.0, places=1)

  def test_known_aa_boundary(self):
    # #767676 on #ffffff ≈ 4.54:1，恰过 AA
    r = ui_taste.contrast_ratio("#767676", "#ffffff")
    self.assertGreater(r, 4.5)
    self.assertLess(r, 4.6)

  def test_muted_gray_fails_aa(self):
    self.assertLess(ui_taste.contrast_ratio("#aaaaaa", "#ffffff"), 4.5)

  def test_rgb_syntax(self):
    self.assertAlmostEqual(
      ui_taste.contrast_ratio("rgb(0,0,0)", "rgb(255,255,255)"), 21.0, places=1)


if __name__ == "__main__":
  unittest.main()
