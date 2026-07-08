#!/usr/bin/env python3
"""astro_chart — 西方占星排盘（本命/当下天象/行运/合盘），纯标准库、离线天文算法。

行星位置：太阳用截断 VSOP87（角秒级）；月亮用 Meeus 第 47 章截断级数（约 10″级）；
水星到冥王星用 JPL 近似开普勒根数（1800–2050 适用，角分级，占星足够），含光行时、
光行差、岁差（J2000→当日春分点）与章动。北交点默认真交点（含摄动修正项）。
宫位：Placidus（迭代法）/ 整宫 / 等宫；上升点用黄道-地平圈数值求根，天顶用闭式解。
时区/夏令时由 IANA zoneinfo 处理。精度与边界情形见 references/algorithms.md。
"""

import argparse
import json
import math
from datetime import datetime, timedelta, timezone

try:
  from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
  ZoneInfo = None

SIGNS = ["白羊", "金牛", "双子", "巨蟹", "狮子", "处女",
         "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼"]
SIGN_EN = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir",
           "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
MODE_NAMES = ["基本", "固定", "变动"]
PLANETS = ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星"]
PLANET_EN = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter",
             "Saturn", "Uranus", "Neptune", "Pluto"]
ASPECTS = [(0, "合", "☌"), (60, "六合", "✶"), (90, "刑", "□"), (120, "拱", "△"), (180, "冲", "☍")]
NATAL_ORBS = {0: 8.0, 60: 5.0, 90: 7.0, 120: 8.0, 180: 8.0}
TRANSIT_ORBS = {0: 3.0, 60: 2.0, 90: 3.0, 120: 3.0, 180: 3.0}
SYNASTRY_ORBS = {0: 6.0, 60: 4.0, 90: 5.0, 120: 6.0, 180: 6.0}


def sign_of(lon):
  return int(lon % 360 // 30)


def fmt_lon(lon):
  lon %= 360
  d = lon % 30
  mnt = (d - int(d)) * 60
  return f"{SIGNS[sign_of(lon)]} {int(d):02d}°{int(mnt):02d}′"


def element_of_sign(s):
  return ["火", "土", "风", "水"][s % 4]


def mode_of_sign(s):
  return MODE_NAMES[s % 3]


def norm360(x):
  return x % 360


def angdiff(a, b):
  """a-b 归一化到 (-180, 180]。"""
  return ((a - b + 180) % 360) - 180


# ---------------------------------------------------------------- 时间基础 ---
def gregorian_to_jd(y, m, d):
  if m <= 2:
    y -= 1
    m += 12
  a = y // 100
  b = 2 - a + a // 4
  return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5


def jd_to_gregorian(jd):
  jd += 0.5
  z = math.floor(jd)
  f = jd - z
  if z < 2299161:
    a = z
  else:
    alpha = math.floor((z - 1867216.25) / 36524.25)
    a = z + 1 + alpha - math.floor(alpha / 4)
  b = a + 1524
  c = math.floor((b - 122.1) / 365.25)
  d0 = math.floor(365.25 * c)
  e = math.floor((b - d0) / 30.6001)
  day = b - d0 - math.floor(30.6001 * e) + f
  month = e - 1 if e < 14 else e - 13
  year = c - 4716 if month > 2 else c - 4715
  return int(year), int(month), day


def datetime_to_jd_ut(dt_utc):
  d = (dt_utc.day + dt_utc.hour / 24 + dt_utc.minute / 1440
       + (dt_utc.second + dt_utc.microsecond / 1e6) / 86400)
  return gregorian_to_jd(dt_utc.year, dt_utc.month, d)


def delta_t_seconds(year_frac):
  y = year_frac
  if y >= 2150 or y < 1700:
    u = (y - 1820) / 100
    return -20 + 32 * u * u
  if y >= 2050:
    u = (y - 1820) / 100
    return -20 + 32 * u * u - 0.5628 * (2150 - y)
  if y >= 2005:
    t = y - 2000
    return 62.92 + 0.32217 * t + 0.005589 * t * t
  if y >= 1986:
    t = y - 2000
    return (63.86 + 0.3345 * t - 0.060374 * t**2 + 0.0017275 * t**3
            + 0.000651814 * t**4 + 0.00002373599 * t**5)
  if y >= 1961:
    t = y - 1975
    return 45.45 + 1.067 * t - t * t / 260 - t**3 / 718
  if y >= 1941:
    t = y - 1950
    return 29.07 + 0.407 * t - t * t / 233 + t**3 / 2547
  if y >= 1920:
    t = y - 1920
    return 21.20 + 0.84493 * t - 0.076100 * t * t + 0.0020936 * t**3
  if y >= 1900:
    t = y - 1900
    return -2.79 + 1.494119 * t - 0.0598939 * t * t + 0.0061966 * t**3 - 0.000197 * t**4
  if y >= 1860:
    t = y - 1860
    return (7.62 + 0.5737 * t - 0.251754 * t * t + 0.01680668 * t**3
            - 0.0004473624 * t**4 + t**5 / 233174)
  if y >= 1800:
    t = y - 1800
    return (13.72 - 0.332447 * t + 0.0068612 * t * t + 0.0041116 * t**3 - 0.00037436 * t**4
            + 0.0000121272 * t**5 - 0.0000001699 * t**6 + 0.000000000875 * t**7)
  t = y - 1700
  return 8.83 + 0.1603 * t - 0.0059285 * t * t + 0.00013336 * t**3 - t**4 / 1174000


def jd_ut_to_jde(jd_ut):
  y, m, _ = jd_to_gregorian(jd_ut)
  return jd_ut + delta_t_seconds(y + (m - 0.5) / 12) / 86400


# --------------------------------------------- 章动/黄赤交角/太阳（VSOP87） ---
def nutation_lon_arcsec(t):
  om = math.radians((125.04452 - 1934.136261 * t) % 360)
  ls = math.radians((280.4665 + 36000.7698 * t) % 360)
  lm = math.radians((218.3165 + 481267.8813 * t) % 360)
  return (-17.20 * math.sin(om) - 1.32 * math.sin(2 * ls)
          - 0.23 * math.sin(2 * lm) + 0.21 * math.sin(2 * om))


def nutation_obl_arcsec(t):
  om = math.radians((125.04452 - 1934.136261 * t) % 360)
  ls = math.radians((280.4665 + 36000.7698 * t) % 360)
  lm = math.radians((218.3165 + 481267.8813 * t) % 360)
  return (9.20 * math.cos(om) + 0.57 * math.cos(2 * ls)
          + 0.10 * math.cos(2 * lm) - 0.09 * math.cos(2 * om))


def true_obliquity_deg(t):
  eps0 = 23.4392911111 - (46.8150 * t + 0.00059 * t * t - 0.001813 * t**3) / 3600
  return eps0 + nutation_obl_arcsec(t) / 3600


_L0 = (
  (175347046, 0.0000000, 0.00000000), (3341656, 4.6692568, 6283.07585000),
  (34894, 4.62610, 12566.15170), (3497, 2.7441, 5753.3849), (3418, 2.8289, 3.5231),
  (3136, 3.6277, 77713.7715), (2676, 4.4181, 7860.4194), (2343, 6.1352, 3930.2097),
  (1324, 0.7425, 11506.7698), (1273, 2.0371, 529.6910), (1199, 1.1096, 1577.3435),
  (990, 5.233, 5884.927), (902, 2.045, 26.298), (857, 3.508, 398.149),
  (780, 1.179, 5223.694), (753, 2.533, 5507.553), (505, 4.583, 18849.228),
  (492, 4.205, 775.523), (357, 2.920, 0.067), (317, 5.849, 11790.629),
  (284, 1.899, 796.298), (271, 0.315, 10977.079), (243, 0.345, 5486.778),
  (206, 4.806, 2544.314), (205, 1.869, 5573.143), (202, 2.458, 6069.777),
  (156, 0.833, 213.299), (132, 3.411, 2942.463), (126, 1.083, 20.775),
  (115, 0.645, 0.980), (103, 0.636, 4694.003), (102, 0.976, 15720.839),
  (102, 4.267, 7.114), (99, 6.21, 2146.17), (98, 0.68, 155.42),
  (86, 5.98, 161000.69), (85, 1.30, 6275.96), (85, 3.67, 71430.70),
  (80, 1.81, 17260.15), (79, 3.04, 12036.46), (75, 1.76, 5088.63),
  (74, 3.50, 3154.69), (74, 4.68, 801.82), (70, 0.83, 9437.76),
  (62, 3.98, 8827.39), (61, 1.82, 7084.90), (57, 2.78, 6286.60),
  (56, 4.39, 14143.50), (56, 3.47, 6279.55), (52, 0.19, 12139.55),
  (52, 1.33, 1748.02), (51, 0.28, 5856.48), (49, 0.49, 1194.45),
  (41, 5.37, 8429.24), (41, 2.40, 19651.05), (39, 6.17, 10447.39),
  (37, 6.04, 10213.29), (37, 2.57, 1059.38), (36, 1.71, 2352.87),
  (36, 1.78, 6812.77), (33, 0.59, 17789.85), (30, 0.44, 83996.85),
  (30, 2.74, 1349.87), (25, 3.16, 4690.48),
)
_L1 = (
  (628331966747, 0.000000, 0.00000000), (206059, 2.678235, 6283.075850),
  (4303, 2.6351, 12566.1517), (425, 1.590, 3.523), (119, 5.796, 26.298),
  (109, 2.966, 1577.344), (93, 2.59, 18849.23), (72, 1.14, 529.69),
  (68, 1.87, 398.15), (67, 4.41, 5507.55), (59, 2.89, 5223.69),
  (56, 2.17, 155.42), (45, 0.40, 796.30), (36, 0.47, 775.52),
  (29, 2.65, 7.11), (21, 5.34, 0.98), (19, 1.85, 5486.78),
  (19, 4.97, 213.30), (17, 2.99, 6275.96), (16, 0.03, 2544.31),
  (16, 1.43, 2146.17), (15, 1.21, 10977.08), (12, 2.83, 1748.02),
  (12, 3.26, 5088.63), (12, 5.27, 1194.45), (12, 2.08, 4694.00),
  (11, 0.77, 553.57), (10, 1.30, 6286.60), (10, 4.24, 1349.87),
  (9, 2.70, 242.73), (9, 5.64, 951.72), (8, 5.30, 2352.87),
  (6, 2.65, 9437.76), (6, 4.67, 4690.48),
)
_L2 = (
  (52919, 0.0000, 0.00000), (8720, 1.0721, 6283.0758), (309, 0.867, 12566.152),
  (27, 0.05, 3.52), (16, 5.19, 26.30), (16, 3.68, 155.42), (10, 0.76, 18849.23),
  (9, 2.06, 77713.77), (7, 0.83, 775.52), (5, 4.66, 1577.34), (4, 1.03, 7.11),
  (4, 3.44, 5573.14), (3, 5.14, 796.30), (3, 6.05, 5507.55), (3, 1.19, 242.73),
  (3, 6.12, 529.69), (3, 0.31, 398.15), (3, 2.28, 553.57), (2, 4.38, 5223.69),
  (2, 3.75, 0.98),
)
_L3 = (
  (289, 5.844, 6283.076), (35, 0.00, 0.00), (17, 5.49, 12566.15),
  (3, 5.20, 155.42), (1, 4.72, 3.52), (1, 5.30, 18849.23), (1, 5.97, 242.73),
)
_L4 = ((114, 3.142, 0.00), (8, 4.13, 6283.08), (1, 3.84, 12566.15))
_L5 = ((1, 3.14, 0.00),)


def _series(terms, tau):
  return sum(a * math.cos(b + c * tau) for a, b, c in terms)


def sun_radius_au(t):
  m = math.radians((357.52911 + 35999.05029 * t - 0.0001537 * t * t) % 360)
  e = 0.016708634 - 0.000042037 * t - 0.0000001267 * t * t
  c = ((1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(m)
       + (0.019993 - 0.000101 * t) * math.sin(2 * m) + 0.000289 * math.sin(3 * m))
  nu = m + math.radians(c)
  return 1.000001018 * (1 - e * e) / (1 + e * math.cos(nu))


def sun_apparent_lon(jde):
  tau = (jde - 2451545.0) / 365250.0
  t = tau * 10
  l = (_series(_L0, tau) + _series(_L1, tau) * tau + _series(_L2, tau) * tau**2
       + _series(_L3, tau) * tau**3 + _series(_L4, tau) * tau**4
       + _series(_L5, tau) * tau**5) * 1e-8
  lon = (math.degrees(l) + 180) % 360
  lon -= 0.09033 / 3600
  lon += nutation_lon_arcsec(t) / 3600
  lon -= 20.4898 / 3600 / sun_radius_au(t)
  return lon % 360


# ----------------------------------------------- 月亮（Meeus 第 47 章截断） ---
# (D, M, M', F, Σl 1e-6°, Σr 1e-3 km)
_MOON_LR = (
  (0, 0, 1, 0, 6288774, -20905355), (2, 0, -1, 0, 1274027, -3699111),
  (2, 0, 0, 0, 658314, -2955968), (0, 0, 2, 0, 213618, -569925),
  (0, 1, 0, 0, -185116, 48888), (0, 0, 0, 2, -114332, -3149),
  (2, 0, -2, 0, 58793, 246158), (2, -1, -1, 0, 57066, -152138),
  (2, 0, 1, 0, 53322, -170733), (2, -1, 0, 0, 45758, -204586),
  (0, 1, -1, 0, -40923, -129620), (1, 0, 0, 0, -34720, 108743),
  (0, 1, 1, 0, -30383, 104755), (2, 0, 0, -2, 15327, 10321),
  (0, 0, 1, 2, -12528, 0), (0, 0, 1, -2, 10980, 79661),
  (4, 0, -1, 0, 10675, -34782), (0, 0, 3, 0, 10034, -23210),
  (4, 0, -2, 0, 8548, -21636), (2, 1, -1, 0, -7888, 24208),
  (2, 1, 0, 0, -6766, 30824), (1, 0, -1, 0, -5163, -8379),
  (1, 1, 0, 0, 4987, -16675), (2, -1, 1, 0, 4036, -12831),
  (2, 0, 2, 0, 3994, -10445), (4, 0, 0, 0, 3861, -11650),
  (2, 0, -3, 0, 3665, 14403), (0, 1, -2, 0, -2689, -7003),
  (2, 0, -1, 2, -2602, 0), (2, -1, -2, 0, 2390, 10056),
  (1, 0, 1, 0, -2348, 6322), (2, -2, 0, 0, 2236, -9884),
  (0, 1, 2, 0, -2120, 5751), (0, 2, 0, 0, -2069, 0),
  (2, -2, -1, 0, 2048, -4950), (2, 0, 1, -2, -1773, 4130),
  (2, 0, 0, 2, -1595, 0), (4, -1, -1, 0, 1215, -3958),
  (0, 0, 2, 2, -1110, 0), (3, 0, -1, 0, -892, 3258),
  (2, 1, 1, 0, -810, 2616), (4, -1, -2, 0, 759, -1897),
  (0, 2, -1, 0, -713, -2117), (2, 2, -1, 0, -700, 2354),
  (2, 1, -2, 0, 691, 0), (2, -1, 0, -2, 596, 0),
  (4, 0, 1, 0, 549, -1423), (0, 0, 4, 0, 537, -1117),
  (4, -1, 0, 0, 520, -1571), (1, 0, -2, 0, -487, -1739),
  (2, 1, 0, -2, -399, 0), (0, 0, 2, -2, -381, -4421),
  (1, 1, 1, 0, 351, 0), (3, 0, -2, 0, -340, 0),
  (4, 0, -3, 0, 330, 0), (2, -1, 2, 0, 327, 0),
  (0, 2, 1, 0, -323, 1165), (1, 1, -1, 0, 299, 0),
  (2, 0, 3, 0, 294, 0), (2, 0, -1, -2, 0, 8752),
)
# (D, M, M', F, Σb 1e-6°)
_MOON_B = (
  (0, 0, 0, 1, 5128122), (0, 0, 1, 1, 280602), (0, 0, 1, -1, 277693),
  (2, 0, 0, -1, 173237), (2, 0, -1, 1, 55413), (2, 0, -1, -1, 46271),
  (2, 0, 0, 1, 32573), (0, 0, 2, 1, 17198), (2, 0, 1, -1, 9266),
  (0, 0, 2, -1, 8822), (2, -1, 0, -1, 8216), (2, 0, -2, -1, 4324),
  (2, 0, 1, 1, 4200), (2, 1, 0, -1, -3359), (2, -1, -1, 1, 2463),
  (2, -1, 0, 1, 2211), (2, -1, -1, -1, 2065), (0, 1, -1, -1, -1870),
  (4, 0, -1, -1, 1828), (0, 1, 0, 1, -1794), (0, 0, 0, 3, -1749),
  (0, 1, -1, 1, -1565), (1, 0, 0, 1, -1491), (0, 1, 1, 1, -1475),
  (0, 1, 1, -1, -1410), (0, 1, 0, -1, -1344), (1, 0, 0, -1, -1335),
  (0, 0, 3, 1, 1107), (4, 0, 0, -1, 1021), (4, 0, -1, 1, 833),
)


def _moon_args(t):
  lp = (218.3164477 + 481267.88123421 * t - 0.0015786 * t * t
        + t**3 / 538841 - t**4 / 65194000) % 360
  d = (297.8501921 + 445267.1114034 * t - 0.0018819 * t * t
       + t**3 / 545868 - t**4 / 113065000) % 360
  m = (357.5291092 + 35999.0502909 * t - 0.0001536 * t * t + t**3 / 24490000) % 360
  mp = (134.9633964 + 477198.8675055 * t + 0.0087414 * t * t
        + t**3 / 69699 - t**4 / 14712000) % 360
  f = (93.2720950 + 483202.0175233 * t - 0.0036539 * t * t
       - t**3 / 3526000 + t**4 / 863310000) % 360
  return lp, d, m, mp, f


def moon_position(jde):
  """月亮地心视黄经/黄纬（度）与距离（km）。"""
  t = (jde - 2451545.0) / 36525.0
  lp, d, m, mp, f = _moon_args(t)
  e = 1 - 0.002516 * t - 0.0000074 * t * t
  a1 = (119.75 + 131.849 * t) % 360
  a2 = (53.09 + 479264.290 * t) % 360
  a3 = (313.45 + 481266.484 * t) % 360
  sl = sr = 0.0
  for cd, cm, cmp, cf, l_coef, r_coef in _MOON_LR:
    arg = math.radians(cd * d + cm * m + cmp * mp + cf * f)
    ef = e if abs(cm) == 1 else (e * e if abs(cm) == 2 else 1.0)
    sl += l_coef * ef * math.sin(arg)
    sr += r_coef * ef * math.cos(arg)
  sl += (3958 * math.sin(math.radians(a1)) + 1962 * math.sin(math.radians(lp - f))
         + 318 * math.sin(math.radians(a2)))
  sb = 0.0
  for cd, cm, cmp, cf, b_coef in _MOON_B:
    arg = math.radians(cd * d + cm * m + cmp * mp + cf * f)
    ef = e if abs(cm) == 1 else (e * e if abs(cm) == 2 else 1.0)
    sb += b_coef * ef * math.sin(arg)
  sb += (-2235 * math.sin(math.radians(lp)) + 382 * math.sin(math.radians(a3))
         + 175 * math.sin(math.radians(a1 - f)) + 175 * math.sin(math.radians(a1 + f))
         + 127 * math.sin(math.radians(lp - mp)) - 115 * math.sin(math.radians(lp + mp)))
  lon = (lp + sl / 1e6 + nutation_lon_arcsec(t) / 3600) % 360
  lat = sb / 1e6
  dist = 385000.56 + sr / 1000
  return lon, lat, dist


def lunar_node_lon(jde, true_node=True):
  t = (jde - 2451545.0) / 36525.0
  om = (125.0445479 - 1934.1362891 * t + 0.0020754 * t * t + t**3 / 467441) % 360
  if true_node:
    _, d, m, mp, f = _moon_args(t)
    om += (-1.4979 * math.sin(math.radians(2 * (d - f))) - 0.1500 * math.sin(math.radians(m))
           - 0.1226 * math.sin(math.radians(2 * d)) + 0.1176 * math.sin(math.radians(2 * f))
           - 0.0801 * math.sin(math.radians(2 * (mp - f))))
  return om % 360


# ------------------------------------- 行星（JPL 近似开普勒根数 1800–2050） ---
# a(AU), e, I, L, 长期近点角 ϖ, 升交点 Ω；各自带每儒略世纪变率
_KEPLER = {
  "Mercury": (0.38709927, 0.00000037, 0.20563593, 0.00001906, 7.00497902, -0.00594749,
              252.25032350, 149472.67411175, 77.45779628, 0.16047689, 48.33076593, -0.12534081),
  "Venus": (0.72333566, 0.00000390, 0.00677672, -0.00004107, 3.39467605, -0.00078890,
            181.97909950, 58517.81538729, 131.60246718, 0.00268329, 76.67984255, -0.27769418),
  "EMB": (1.00000261, 0.00000562, 0.01671123, -0.00004392, -0.00001531, -0.01294668,
          100.46457166, 35999.37244981, 102.93768193, 0.32327364, 0.0, 0.0),
  "Mars": (1.52371034, 0.00001847, 0.09339410, 0.00007882, 1.84969142, -0.00813131,
           -4.55343205, 19140.30268499, -23.94362959, 0.44441088, 49.55953891, -0.29257343),
  "Jupiter": (5.20288700, -0.00011607, 0.04838624, -0.00013253, 1.30439695, -0.00183714,
              34.39644051, 3034.74612775, 14.72847983, 0.21252668, 100.47390909, 0.20469106),
  "Saturn": (9.53667594, -0.00125060, 0.05386179, -0.00050991, 2.48599187, 0.00193609,
             49.95424423, 1222.49362201, 92.59887831, -0.41897216, 113.66242448, -0.28867794),
  "Uranus": (19.18916464, -0.00196176, 0.04725744, -0.00004397, 0.77263783, -0.00242939,
             313.23810451, 428.48202785, 170.95427630, 0.40805281, 74.01692503, 0.04240589),
  "Neptune": (30.06992276, 0.00026291, 0.00859048, 0.00005105, 1.77004347, 0.00035372,
              -55.12002969, 218.45945325, 44.96476227, -0.32241464, 131.78422574, -0.00508664),
  "Pluto": (39.48211675, -0.00031596, 0.24882730, 0.00005170, 17.14001206, 0.00004818,
            238.92903833, 145.20780515, 224.06891629, -0.04062942, 110.30393684, -0.01183482),
}
LIGHT_DAY_PER_AU = 0.0057755183


def _helio_xyz(name, t_cent):
  """行星日心黄道直角坐标（J2000 分点），AU。"""
  a0, ad, e0, ed, i0, idot, l0, ld, p0, pd, n0, nd = _KEPLER[name]
  a = a0 + ad * t_cent
  e = e0 + ed * t_cent
  inc = math.radians(i0 + idot * t_cent)
  ll = l0 + ld * t_cent
  peri = p0 + pd * t_cent
  node = n0 + nd * t_cent
  m = math.radians(((ll - peri + 180) % 360) - 180)
  ecc = m + e * math.sin(m)
  for _ in range(12):
    ecc -= (ecc - e * math.sin(ecc) - m) / (1 - e * math.cos(ecc))
  xp = a * (math.cos(ecc) - e)
  yp = a * math.sqrt(1 - e * e) * math.sin(ecc)
  w = math.radians(peri - node)
  om = math.radians(node)
  cw, sw, co, so, ci, si = (math.cos(w), math.sin(w), math.cos(om),
                            math.sin(om), math.cos(inc), math.sin(inc))
  x = (cw * co - sw * so * ci) * xp + (-sw * co - cw * so * ci) * yp
  y = (cw * so + sw * co * ci) * xp + (-sw * so + cw * co * ci) * yp
  z = (sw * si) * xp + (cw * si) * yp
  return x, y, z


def _earth_xyz(t_cent, jde):
  """地球（EMB 修正到地心）日心坐标，J2000。"""
  ex, ey, ez = _helio_xyz("EMB", t_cent)
  mlon, mlat, mdist = moon_position(jde)
  # 地月质心 -> 地心：减去月亮方向的 1/82.30
  r = mdist / 1.495978707e8 * 0.0121505  # AU
  lr, br = math.radians(mlon), math.radians(mlat)
  ex -= r * math.cos(br) * math.cos(lr)
  ey -= r * math.cos(br) * math.sin(lr)
  ez -= r * math.sin(br)
  return ex, ey, ez


def planet_position(name, jde):
  """行星地心视黄经/黄纬（当日分点，含岁差/章动/光行时/光行差）。"""
  t = (jde - 2451545.0) / 36525.0
  ex, ey, ez = _earth_xyz(t, jde)
  px, py, pz = _helio_xyz(name, t)
  for _ in range(2):  # 光行时迭代
    dist = math.dist((px, py, pz), (ex, ey, ez))
    t2 = (jde - dist * LIGHT_DAY_PER_AU - 2451545.0) / 36525.0
    px, py, pz = _helio_xyz(name, t2)
  gx, gy, gz = px - ex, py - ey, pz - ez
  lon = math.degrees(math.atan2(gy, gx)) % 360
  lat = math.degrees(math.atan2(gz, math.hypot(gx, gy)))
  dist = math.sqrt(gx * gx + gy * gy + gz * gz)
  # 岁差 J2000 -> 当日分点
  lon += (5029.0966 * t + 1.11113 * t * t) / 3600
  # 章动
  lon += nutation_lon_arcsec(t) / 3600
  # 周年光行差（近似）
  slon = sun_apparent_lon(jde)
  lon -= 20.4898 / 3600 * math.cos(math.radians(slon - lon)) / max(math.cos(math.radians(lat)), 0.05)
  return lon % 360, lat, dist


def body_lon(body, jde, true_node=True):
  if body == "太阳":
    return sun_apparent_lon(jde)
  if body == "月亮":
    return moon_position(jde)[0]
  if body == "北交点":
    return lunar_node_lon(jde, true_node)
  return planet_position(PLANET_EN[PLANETS.index(body)], jde)[0]


# ------------------------------------------------------------ 恒星时与宫位 ---
def sidereal_deg(jd_ut, jde):
  t = (jde - 2451545.0) / 36525.0
  gmst = (280.46061837 + 360.98564736629 * (jd_ut - 2451545.0)
          + 0.000387933 * t * t - t**3 / 38710000) % 360
  eps = math.radians(true_obliquity_deg(t))
  return (gmst + nutation_lon_arcsec(t) / 3600 * math.cos(eps)) % 360


def _ecl_to_equ(lon, eps):
  """黄道上一点（β=0）的赤经/赤纬（度）。"""
  lr = math.radians(lon)
  ra = math.degrees(math.atan2(math.sin(lr) * math.cos(eps), math.cos(lr))) % 360
  dec = math.degrees(math.asin(math.sin(lr) * math.sin(eps)))
  return ra, dec


def mc_lon(ramc, eps):
  lam = math.degrees(math.atan2(math.sin(math.radians(ramc)),
                                math.cos(math.radians(ramc)) * math.cos(eps))) % 360
  return lam


def asc_lon(ramc, lat_deg, eps):
  """上升点：黄道与东方地平的交点（数值求根，稳）。"""
  phi = math.radians(lat_deg)

  def sin_alt(lam):
    ra, dec = _ecl_to_equ(lam, eps)
    h = math.radians(((ramc - ra) + 180) % 360 - 180)
    dr = math.radians(dec)
    return math.sin(phi) * math.sin(dr) + math.cos(phi) * math.cos(dr) * math.cos(h)

  roots = []
  step = 2.0
  prev = sin_alt(0.0)
  x = step
  while x <= 360.0 + 1e-9:
    cur = sin_alt(x % 360)
    if prev == 0 or (prev < 0) != (cur < 0):
      lo, hi = x - step, x
      flo = sin_alt(lo % 360)
      for _ in range(60):
        mid = (lo + hi) / 2
        fm = sin_alt(mid % 360)
        if fm == 0:
          lo = hi = mid
          break
        if (flo < 0) != (fm < 0):
          hi = mid
        else:
          lo, flo = mid, fm
      roots.append(((lo + hi) / 2) % 360)
    prev = cur
    x += step
  east = []
  for r in roots:
    ra, _ = _ecl_to_equ(r, eps)
    h = ((ramc - ra) + 180) % 360 - 180
    if h < 0:  # 时角为负 = 在东边（未过中天）
      east.append(r)
  if not east:
    return None
  return east[0]


def placidus_cusps(ramc, lat_deg, eps_deg):
  """Placidus 宫头（1..12），失败（极地）返回 None。"""
  eps = math.radians(eps_deg)
  phi = math.radians(lat_deg)
  if abs(lat_deg) > 66.0:
    return None
  asc = asc_lon(ramc, lat_deg, eps)
  if asc is None:
    return None
  mc = mc_lon(ramc, eps)

  def iterate(offset, frac):
    ra = (ramc + offset) % 360
    for _ in range(60):
      lam = math.degrees(math.atan2(math.sin(math.radians(ra)),
                                    math.cos(math.radians(ra)) * math.cos(eps))) % 360
      dec = math.asin(math.sin(math.radians(lam)) * math.sin(eps))
      x = math.tan(phi) * math.tan(dec)
      if abs(x) >= 1:  # 拱极，Placidus 失效
        return None
      ad = math.degrees(math.asin(x))
      ra_new = (ramc + offset + ad * frac) % 360
      if abs(angdiff(ra_new, ra)) < 1e-7:
        ra = ra_new
        break
      ra = ra_new
    return math.degrees(math.atan2(math.sin(math.radians(ra)),
                                   math.cos(math.radians(ra)) * math.cos(eps))) % 360

  c11 = iterate(30, 1 / 3)
  c12 = iterate(60, 2 / 3)
  c2 = iterate(120, 2 / 3)
  c3 = iterate(150, 1 / 3)
  if None in (c11, c12, c2, c3):
    return None
  cusps = {1: asc, 2: c2, 3: c3, 4: (mc + 180) % 360, 5: (c11 + 180) % 360,
           6: (c12 + 180) % 360, 7: (asc + 180) % 360, 8: (c2 + 180) % 360,
           9: (c3 + 180) % 360, 10: mc, 11: c11, 12: c12}
  return [cusps[i] for i in range(1, 13)]


def whole_sign_cusps(asc):
  start = sign_of(asc) * 30
  return [(start + 30 * i) % 360 for i in range(12)]


def equal_cusps(asc):
  return [(asc + 30 * i) % 360 for i in range(12)]


def house_of(lon, cusps):
  for i in range(12):
    a, b = cusps[i], cusps[(i + 1) % 12]
    if (lon - a) % 360 < (b - a) % 360:
      return i + 1
  return 12


# ------------------------------------------------------------------ 排盘 ---
def parse_tz(s):
  if "/" in s:
    if ZoneInfo is None:
      raise SystemExit("当前 Python 无 zoneinfo，请用数字时区如 --tz +8")
    return ZoneInfo(s)
  return timezone(timedelta(hours=float(s)))


def compute_positions(jde, true_node=True):
  out = {}
  slon = sun_apparent_lon(jde)
  out["太阳"] = {"lon": slon, "lat": 0.0}
  mlon, mlat, mdist = moon_position(jde)
  out["月亮"] = {"lon": mlon, "lat": mlat, "dist_km": round(mdist)}
  for cn, en in zip(PLANETS[2:], PLANET_EN[2:]):
    lon, lat, dist = planet_position(en, jde)
    out[cn] = {"lon": lon, "lat": lat, "dist_au": round(dist, 4)}
  out["北交点"] = {"lon": lunar_node_lon(jde, true_node), "lat": 0.0}
  # 速度（度/日）与逆行
  for name in list(out.keys()):
    l1 = body_lon(name, jde - 0.5, true_node)
    l2 = body_lon(name, jde + 0.5, true_node)
    speed = angdiff(l2, l1)
    out[name]["speed"] = round(speed, 4)
    out[name]["retrograde"] = speed < 0
  for name, d in out.items():
    d["sign"] = SIGNS[sign_of(d["lon"])]
    d["pos"] = fmt_lon(d["lon"])
    d["lon"] = round(d["lon"], 4)
    d["lat"] = round(d.get("lat", 0.0), 3)
    edge = min(d["lon"] % 30, 30 - d["lon"] % 30)
    if edge < 0.25:
      d["near_sign_boundary"] = True
  return out


def find_aspects(pos_a, pos_b=None, orbs=None, scale=1.0, cross_label=("", "")):
  """pos_b 为 None 时算盘内互相位，否则算 A 对 B 的跨盘相位。"""
  orbs = orbs or NATAL_ORBS
  names_a = list(pos_a.keys())
  res = []
  if pos_b is None:
    pairs = [(names_a[i], names_a[j]) for i in range(len(names_a))
             for j in range(i + 1, len(names_a))]
  else:
    pairs = [(a, b) for a in names_a for b in pos_b.keys()]
  for a, b in pairs:
    pa = pos_a[a]
    pb = pos_a[b] if pos_b is None else pos_b[b]
    sep = abs(angdiff(pa["lon"], pb["lon"]))
    for angle, cname, sym in ASPECTS:
      orb_lim = orbs[angle] * scale
      if a in ("太阳", "月亮") or b in ("太阳", "月亮"):
        orb_lim += 1.0 * scale
      orb = abs(sep - angle)
      if orb <= orb_lim:
        rel_speed = pa.get("speed", 0) - pb.get("speed", 0)
        going = abs(angdiff(pa["lon"] + pa.get("speed", 0) * 0.1,
                            pb["lon"] + pb.get("speed", 0) * 0.1))
        applying = abs(going - angle) < orb
        res.append({
          "a": cross_label[0] + a, "b": cross_label[1] + b,
          "aspect": cname, "symbol": sym, "angle": angle,
          "orb": round(orb, 2), "applying": applying,
        })
        break
  res.sort(key=lambda x: x["orb"])
  return res


def build_chart(local_dt, tzinfo, lat=None, lon=None, house_system="placidus",
                true_node=True, time_known=True):
  aware = local_dt.replace(tzinfo=tzinfo)
  utc_dt = aware.astimezone(timezone.utc).replace(tzinfo=None)
  jd_ut = datetime_to_jd_ut(utc_dt)
  jde = jd_ut_to_jde(jd_ut)
  t = (jde - 2451545.0) / 36525.0
  warnings = []
  y = utc_dt.year
  if y < 1800 or y > 2050:
    warnings.append("行星根数适用 1800–2050 年，此外年份外行星误差增大（太阳/月亮不受影响）")
  positions = compute_positions(jde, true_node)
  if not time_known:
    warnings.append("出生时间未知：按当日 12:00 计算，上升/宫位不可用；月亮一天移动约 13°")
    def _moon_at(hh, mm):
      u = local_dt.replace(hour=hh, minute=mm, tzinfo=tzinfo).astimezone(timezone.utc)
      return moon_position(jd_ut_to_jde(datetime_to_jd_ut(u.replace(tzinfo=None))))[0]
    l0, l1 = _moon_at(0, 0), _moon_at(23, 59)
    if sign_of(l0) != sign_of(l1):
      warnings.append(f"月亮当日从{SIGNS[sign_of(l0)]}移入{SIGNS[sign_of(l1)]}，月亮星座需出生时间确认")

  chart = {
    "datetime_local": local_dt.strftime("%Y-%m-%d %H:%M") + ("" if time_known else "（时间未知，按12:00）"),
    "tz": str(tzinfo), "utc": utc_dt.strftime("%Y-%m-%d %H:%M:%S"),
    "jd_ut": round(jd_ut, 6), "lat": lat, "lon": lon,
    "node_type": "true" if true_node else "mean",
    "positions": positions,
  }

  if lat is not None and lon is not None and time_known:
    eps_deg = true_obliquity_deg(t)
    eps = math.radians(eps_deg)
    ramc = (sidereal_deg(jd_ut, jde) + lon) % 360
    asc = asc_lon(ramc, lat, eps)
    mc = mc_lon(ramc, eps)
    if asc is None:
      warnings.append("极地纬度：黄道与地平无稳定交点，不排宫位")
    else:
      cusps = None
      used = house_system
      if house_system == "placidus":
        cusps = placidus_cusps(ramc, lat, eps_deg)
        if cusps is None:
          used = "whole"
          warnings.append("高纬 Placidus 失效，改用整宫制")
      if cusps is None:
        cusps = whole_sign_cusps(asc) if used == "whole" else equal_cusps(asc)
      if house_system in ("whole", "equal"):
        cusps = whole_sign_cusps(asc) if house_system == "whole" else equal_cusps(asc)
        used = house_system
      chart["angles"] = {
        "ASC": {"lon": round(asc, 4), "pos": fmt_lon(asc)},
        "MC": {"lon": round(mc, 4), "pos": fmt_lon(mc)},
        "DSC": {"pos": fmt_lon(asc + 180)}, "IC": {"pos": fmt_lon(mc + 180)},
      }
      chart["house_system"] = used
      chart["cusps"] = [round(c, 4) for c in cusps]
      for name, d in positions.items():
        d["house"] = house_of(d["lon"], cusps)
  elif time_known and (lat is None or lon is None):
    warnings.append("未提供出生地经纬度：不排上升与宫位（--lat/--lon）")

  chart["aspects"] = find_aspects(positions)
  elems = {"火": 0, "土": 0, "风": 0, "水": 0}
  modes = {"基本": 0, "固定": 0, "变动": 0}
  for p in PLANETS:
    s = sign_of(positions[p]["lon"])
    elems[element_of_sign(s)] += 1
    modes[mode_of_sign(s)] += 1
  chart["elements"] = elems
  chart["modes"] = modes
  elong = (positions["月亮"]["lon"] - positions["太阳"]["lon"]) % 360
  phase_names = ["新月", "蛾眉月", "上弦月", "盈凸月", "满月", "亏凸月", "下弦月", "残月"]
  chart["moon_phase"] = {
    "name": phase_names[int(((elong + 22.5) % 360) // 45)],
    "sun_moon_angle": round(elong, 1),
    "illumination": round((1 - math.cos(math.radians(elong))) / 2, 3),
  }
  chart["warnings"] = warnings
  return chart


# --------------------------------------------------------------- 文本输出 ---
def render_chart(c, title="本命星盘"):
  L = []
  place = f" @ {c['lat']}°N,{c['lon']}°E" if c.get("lat") is not None else ""
  L.append(f"「{title}」{c['datetime_local']} {c['tz']}{place}")
  L.append(f"UTC {c['utc']}  JD {c['jd_ut']}  交点:{'真' if c['node_type']=='true' else '平'}")
  L.append("")
  for name in PLANETS + ["北交点"]:
    d = c["positions"][name]
    h = f"  {d['house']:2d}宫" if "house" in d else ""
    r = "  逆" if d["retrograde"] else ""
    b = "  ⚠近星座边界" if d.get("near_sign_boundary") else ""
    L.append(f"{name:　<3}  {d['pos']}  黄经{d['lon']:8.3f}°{h}{r}{b}")
  if "angles" in c:
    a = c["angles"]
    L.append(f"上升 ASC  {a['ASC']['pos']}    天顶 MC  {a['MC']['pos']}"
             f"    下降 {a['DSC']['pos']}    天底 {a['IC']['pos']}")
    sys_cn = {"placidus": "Placidus", "whole": "整宫", "equal": "等宫"}[c["house_system"]]
    L.append(f"宫头（{sys_cn}）  " + "  ".join(f"{i+1}:{fmt_lon(x)}" for i, x in enumerate(c["cusps"])))
  L.append("")
  if c["aspects"]:
    L.append("相位（按容许度排序）")
    for x in c["aspects"]:
      ap = "入相" if x["applying"] else "出相"
      L.append(f"  {x['a']} {x['symbol']} {x['b']}  {x['aspect']}  orb {x['orb']:.2f}°  {ap}")
  el, mo = c["elements"], c["modes"]
  L.append("")
  L.append("元素  " + " ".join(f"{k}{v}" for k, v in el.items())
           + "    模式  " + " ".join(f"{k}{v}" for k, v in mo.items()) + "（十行星计数）")
  mp = c["moon_phase"]
  L.append(f"月相  {mp['name']}（日月夹角 {mp['sun_moon_angle']}°，照亮 {mp['illumination']*100:.0f}%）")
  for w in c.get("warnings", []):
    L.append(f"⚠ {w}")
  return "\n".join(L)


def render_aspects_only(aspects, header):
  L = [header]
  if not aspects:
    L.append("  （给定容许度内无相位）")
  for x in aspects:
    ap = "入相" if x["applying"] else "出相"
    L.append(f"  {x['a']} {x['symbol']} {x['b']}  {x['aspect']}  orb {x['orb']:.2f}°  {ap}")
  return "\n".join(L)


# ------------------------------------------------------------------- CLI ---
def _birth_args(ap, prefix="", required=True):
  p = ("--" + prefix) if prefix else "--"
  ap.add_argument(f"{p}date", required=required, help="公历日期 YYYY-MM-DD")
  ap.add_argument(f"{p}time", help="时间 HH:MM（不给按时间未知处理）")
  ap.add_argument(f"{p}tz", default="Asia/Shanghai", help="时区：IANA 名或小时数，默认 Asia/Shanghai")
  ap.add_argument(f"{p}lat", type=float, help="纬度（北纬为正）")
  ap.add_argument(f"{p}lon", type=float, help="经度（东经为正）")


def _build_from(ns, prefix="", house="placidus", node=True):
  g = lambda k: getattr(ns, (prefix + k).replace("-", "_"))
  time_known = g("time") is not None
  ts = g("time") if time_known else "12:00"
  local_dt = datetime.fromisoformat(f"{g('date').replace('/', '-')} {ts}")
  return build_chart(local_dt, parse_tz(g("tz")), lat=g("lat"), lon=g("lon"),
                     house_system=house, true_node=node, time_known=time_known)


def cmd_natal(args):
  c = _build_from(args, house=args.house, node=not args.mean_node)
  print(json.dumps(c, ensure_ascii=False, indent=2) if args.json else render_chart(c))


def cmd_now(args):
  dt = datetime.now(timezone.utc)
  tzv = parse_tz(args.tz)
  local = dt.astimezone(tzv).replace(tzinfo=None, second=0, microsecond=0)
  c = build_chart(local, tzv, lat=args.lat, lon=args.lon,
                  house_system=args.house, true_node=not args.mean_node)
  print(json.dumps(c, ensure_ascii=False, indent=2) if args.json else render_chart(c, "当下天象"))


def cmd_transits(args):
  natal = _build_from(args, node=not args.mean_node)
  if args.on:
    on_dt = datetime.fromisoformat(args.on.replace("/", "-"))
  else:
    on_dt = datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0)
  trans = build_chart(on_dt, timezone.utc, true_node=not args.mean_node)
  aspects = find_aspects(trans["positions"], natal["positions"],
                         orbs=TRANSIT_ORBS, scale=args.orb_scale,
                         cross_label=("行运", "本命"))
  # 行运行星落本命宫
  houses = []
  if "cusps" in natal:
    for name in PLANETS + ["北交点"]:
      h = house_of(trans["positions"][name]["lon"], natal["cusps"])
      houses.append({"planet": name, "pos": trans["positions"][name]["pos"], "natal_house": h,
                     "retrograde": trans["positions"][name]["retrograde"]})
  out = {"transit_utc": trans["utc"], "aspects": aspects, "transit_in_natal_houses": houses,
         "natal": {"datetime": natal["datetime_local"], "tz": natal["tz"]},
         "warnings": natal["warnings"] + trans["warnings"]}
  if args.json:
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return
  print(f"「行运」UTC {trans['utc']} → 本命 {natal['datetime_local']}")
  print(render_aspects_only(aspects, "行运相位（容许度较紧）"))
  if houses:
    print("行运落宫  " + "  ".join(f"{x['planet']}→{x['natal_house']}宫" for x in houses))
  for w in out["warnings"]:
    print(f"⚠ {w}")


def cmd_synastry(args):
  a = _build_from(args, prefix="a-", node=not args.mean_node)
  b = _build_from(args, prefix="b-", node=not args.mean_node)
  aspects = find_aspects(a["positions"], b["positions"],
                         orbs=SYNASTRY_ORBS, scale=args.orb_scale,
                         cross_label=("A", "B"))
  out = {"a": {"datetime": a["datetime_local"], "positions": a["positions"]},
         "b": {"datetime": b["datetime_local"], "positions": b["positions"]},
         "aspects": aspects, "warnings": a["warnings"] + b["warnings"]}
  if args.json:
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return
  print(f"「合盘」A {a['datetime_local']} × B {b['datetime_local']}")
  for label, cc in (("A", a), ("B", b)):
    line = "  ".join(f"{p}{cc['positions'][p]['pos']}" for p in ("太阳", "月亮", "金星", "火星"))
    asc = cc.get("angles", {}).get("ASC", {}).get("pos", "—")
    print(f"{label}  {line}  上升 {asc}")
  print(render_aspects_only(aspects, "跨盘相位"))
  for w in out["warnings"]:
    print(f"⚠ {w}")


def main(argv=None):
  ap = argparse.ArgumentParser(prog="astro-chart",
                               description="西方占星排盘：本命/当下天象/行运/合盘（离线，纯标准库）")
  sub = ap.add_subparsers(dest="cmd", required=True)

  n = sub.add_parser("natal", help="本命盘：行星星座宫位、上升天顶、相位、元素分布")
  _birth_args(n)
  n.add_argument("--house", choices=["placidus", "whole", "equal"], default="placidus")
  n.add_argument("--mean-node", action="store_true", help="用平交点（默认真交点）")
  n.add_argument("--json", action="store_true")
  n.set_defaults(func=cmd_natal)

  w = sub.add_parser("now", help="当下天象（行星位置/月相；给经纬度则含宫位）")
  w.add_argument("--tz", default="Asia/Shanghai")
  w.add_argument("--lat", type=float)
  w.add_argument("--lon", type=float)
  w.add_argument("--house", choices=["placidus", "whole", "equal"], default="placidus")
  w.add_argument("--mean-node", action="store_true")
  w.add_argument("--json", action="store_true")
  w.set_defaults(func=cmd_now)

  t = sub.add_parser("transits", help="行运：指定时刻行星对本命盘的相位与落宫")
  _birth_args(t)
  t.add_argument("--on", help="行运时刻（UTC）YYYY-MM-DD HH:MM，默认现在")
  t.add_argument("--orb-scale", type=float, default=1.0)
  t.add_argument("--mean-node", action="store_true")
  t.add_argument("--json", action="store_true")
  t.set_defaults(func=cmd_transits)

  s = sub.add_parser("synastry", help="合盘：两张本命盘的跨盘相位")
  _birth_args(s, prefix="a-")
  _birth_args(s, prefix="b-")
  s.add_argument("--orb-scale", type=float, default=1.0)
  s.add_argument("--mean-node", action="store_true")
  s.add_argument("--json", action="store_true")
  s.set_defaults(func=cmd_synastry)

  args = ap.parse_args(argv)
  args.func(args)


if __name__ == "__main__":
  main()
