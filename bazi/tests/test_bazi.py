"""bazi 回归测试：全部离线锚点，无网络。运行：
python3 -m unittest discover -s bazi/tests   （从仓库根目录）
"""

import pathlib
import sys
import unittest
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import bazi  # noqa: E402


class TestSolarTerms(unittest.TestCase):
  # 紫金山天文台发布值（北京时间）；允许 ±60 秒（ΔT 模型误差远小于此）
  KNOWN = {
    "立春": "2024-02-04 16:26:53",
    "春分": "2024-03-20 11:06:12",
    "夏至": "2024-06-21 04:50:46",
    "冬至": "2024-12-21 17:20:20",
  }

  def test_terms_2024(self):
    for name, jde, _ in bazi.terms_of_year(2024):
      if name in self.KNOWN:
        got = bazi.jd_ut_to_datetime(bazi.jde_to_jd_ut(jde), 8)
        want = datetime.fromisoformat(self.KNOWN[name])
        self.assertLess(abs((got - want).total_seconds()), 60, name)


class TestLunar(unittest.TestCase):
  CNY = {2020: (1, 25), 2021: (2, 12), 2022: (2, 1), 2023: (1, 22),
         2024: (2, 10), 2025: (1, 29), 2026: (2, 17), 2000: (2, 5), 1990: (1, 27)}
  LEAPS = {2004: 2, 2009: 5, 2012: 4, 2014: 9, 2017: 6, 2020: 4, 2023: 2, 2025: 6, 2033: 11}

  def test_chinese_new_year(self):
    for y, (m, d) in self.CNY.items():
      lu = bazi.solar_to_lunar(y, m, d)
      self.assertEqual((lu["month"], lu["day"], lu["leap"]), (1, 1, False), f"{y} 春节")

  def test_leap_months(self):
    for y, lm in self.LEAPS.items():
      leaps = [n for n, leap, _, _ in bazi.build_lunar_year(y) if leap]
      self.assertEqual(leaps, [lm], f"农历{y}年闰月")

  def test_no_false_leap(self):
    for y in (2021, 2022, 2024, 2026):
      leaps = [n for n, leap, _, _ in bazi.build_lunar_year(y) if leap]
      self.assertEqual(leaps, [], f"农历{y}年不应有闰月")

  def test_roundtrip(self):
    self.assertEqual(bazi.lunar_to_solar(2024, 1, 1), (2024, 2, 10))
    self.assertEqual(bazi.lunar_to_solar(2020, 4, 10, leap=True), (2020, 6, 1))


class TestPillars(unittest.TestCase):
  def test_day_ganzhi_anchors(self):
    for (y, m, d), want in [((2000, 1, 7), "甲子"), ((2000, 1, 1), "戊午"),
                            ((1900, 1, 1), "甲戌"), ((1949, 10, 1), "甲子")]:
      self.assertEqual(bazi.ganzhi_name(bazi.day_ganzhi_index(y, m, d)), want)

  def test_year_boundary_lichun(self):
    tz = bazi.parse_tz("Asia/Shanghai")
    for dstr, want in [("1984-02-03 12:00", "癸亥"), ("1984-02-05 12:00", "甲子"),
                       ("1984-02-04 23:00", "癸亥"), ("1984-02-04 23:30", "甲子")]:
      c = bazi.compute_chart(datetime.fromisoformat(dstr), tz)
      self.assertEqual(c["pillars"]["year"]["ganzhi"], want, dstr)

  def test_known_chart(self):
    tz = bazi.parse_tz("Asia/Shanghai")
    c = bazi.compute_chart(datetime.fromisoformat("1988-08-08 08:08"), tz, gender="female")
    self.assertEqual(c["bazi"], "戊辰 庚申 乙未 庚辰")
    self.assertEqual(c["dayun"]["female"]["direction"], "逆行")

  def test_late_zi_schools(self):
    tz = bazi.parse_tz("Asia/Shanghai")
    dt = datetime.fromisoformat("2001-01-10 23:40")
    nxt = bazi.compute_chart(dt, tz, zishi="next")
    spl = bazi.compute_chart(dt, tz, zishi="split")
    self.assertEqual(nxt["pillars"]["day"]["ganzhi"], "甲戌")   # 23 点起算次日
    self.assertEqual(spl["pillars"]["day"]["ganzhi"], "癸酉")   # 早晚子时派：日柱当天
    self.assertEqual(spl["pillars"]["hour"]["ganzhi"], "甲子")  # 时柱按次日日干遁


class TestEquationOfTime(unittest.TestCase):
  def test_extremes(self):
    for (y, m, d), want in [((2024, 11, 3), 16.4), ((2024, 2, 11), -14.2)]:
      jde = bazi.jd_ut_to_jde(bazi.gregorian_to_jd(y, m, d + 0.5))
      self.assertLess(abs(bazi.equation_of_time_minutes(jde) - want), 0.6)


if __name__ == "__main__":
  unittest.main()
