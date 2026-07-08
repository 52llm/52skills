"""astro-chart 回归测试：全部离线锚点，无网络。运行：
python3 -m unittest discover -s astro-chart/tests   （从仓库根目录）
"""

import math
import pathlib
import random
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import astro_chart as ac  # noqa: E402


class TestSunMoon(unittest.TestCase):
  def test_equinox_2024(self):
    # 2024-03-20 03:06:20 UTC 春分，太阳视黄经应为 0°
    jde = ac.jd_ut_to_jde(ac.gregorian_to_jd(2024, 3, 20 + (3 + 6 / 60 + 20 / 3600) / 24))
    err = ((ac.sun_apparent_lon(jde) + 180) % 360) - 180
    self.assertLess(abs(err), 0.01)

  def test_full_moon_opposition(self):
    # 2024-01-25 17:54 UTC 满月：月亮黄经 = 太阳 + 180
    jde = ac.jd_ut_to_jde(ac.gregorian_to_jd(2024, 1, 25 + (17 + 54 / 60) / 24))
    d = (ac.moon_position(jde)[0] - ac.sun_apparent_lon(jde) - 180) % 360
    self.assertLess(abs(((d + 180) % 360) - 180), 0.1)


class TestPlanets(unittest.TestCase):
  def test_signs_2024_06_15(self):
    jde = ac.jd_ut_to_jde(ac.gregorian_to_jd(2024, 6, 15.0))
    expect = {"Jupiter": "双子", "Saturn": "双鱼", "Uranus": "金牛",
              "Neptune": "双鱼", "Pluto": "水瓶", "Mars": "金牛"}
    for en, sign in expect.items():
      lon, _, _ = ac.planet_position(en, jde)
      self.assertEqual(ac.SIGNS[ac.sign_of(lon)], sign, en)

  def test_saturn_station_2024(self):
    # 2024-06-29 土星留（转逆）于双鱼 19°25′
    jde = ac.jd_ut_to_jde(ac.gregorian_to_jd(2024, 6, 29.8))
    lon, _, _ = ac.planet_position("Saturn", jde)
    self.assertLess(abs(lon - (330 + 19 + 25 / 60)), 0.2)

  def test_true_node_eclipse_2024(self):
    # 2024-04-08 日全食，真交点在白羊 15° 附近
    jde = ac.jd_ut_to_jde(ac.gregorian_to_jd(2024, 4, 8.5))
    self.assertLess(abs(ac.lunar_node_lon(jde) - 15), 2.5)


class TestHouses(unittest.TestCase):
  def test_asc_on_horizon_east(self):
    rng = random.Random(7)
    eps_deg = ac.true_obliquity_deg(0.24)
    eps = math.radians(eps_deg)
    for _ in range(30):
      ramc = rng.uniform(0, 360)
      lat = rng.uniform(-60, 60)
      asc = ac.asc_lon(ramc, lat, eps)
      ra, dec = ac._ecl_to_equ(asc, eps)
      h = ((ramc - ra) + 180) % 360 - 180
      alt = (math.sin(math.radians(lat)) * math.sin(math.radians(dec))
             + math.cos(math.radians(lat)) * math.cos(math.radians(dec))
             * math.cos(math.radians(h)))
      self.assertLess(abs(alt), 1e-6)
      self.assertLess(h, 0)

  def test_placidus_equation(self):
    rng = random.Random(3)
    eps_deg = ac.true_obliquity_deg(0.24)
    for _ in range(20):
      ramc = rng.uniform(0, 360)
      lat = rng.uniform(-60, 60)
      cusps = ac.placidus_cusps(ramc, lat, eps_deg)
      if cusps is None:
        continue
      for idx, offset, frac in ((10, 30, 1 / 3), (11, 60, 2 / 3)):
        ra, dec = ac._ecl_to_equ(cusps[idx], math.radians(eps_deg))
        ad = math.degrees(math.asin(math.tan(math.radians(lat)) * math.tan(math.radians(dec))))
        want_ra = (ramc + offset + ad * frac) % 360
        self.assertLess(abs(((ra - want_ra + 180) % 360) - 180), 0.01)


if __name__ == "__main__":
  unittest.main()
