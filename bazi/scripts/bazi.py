#!/usr/bin/env python3
"""bazi — 八字排盘（四柱/大运/流年/神煞/农历互转/节气），纯标准库、离线天文算法。

天文核心：截断 VSOP87 太阳视黄经（含章动/光行差，约角秒级）推节气（定气法：
太阳视黄经到达 15° 整倍数），Meeus 定朔序列推新月，农历按「定朔 + 冬至定十一月 +
无中气置闰」规则构造；ΔT 用 Espenak–Meeus 分段多项式。适用约 1700–2150 年，
精度与流派差异见 references/algorithms.md。

排盘规则：年柱以立春为界、月柱以十二节为界（都按出生绝对时刻与节气交接时刻比较，
与用不用真太阳时无关）；日柱默认 23:00 换日（可选 --zishi split 早晚子时派）；
时柱五鼠遁。--lon 给出出生地经度即启用真太阳时（经度差 + 均时差）。
历史时区与夏令时由 IANA zoneinfo 处理（如中国 1986–1991 夏令时）。
"""

import argparse
import functools
import json
import math
from datetime import datetime, timedelta, timezone

try:
  from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
  ZoneInfo = None

# ------------------------------------------------------------------ 基础表 ---
STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
ELEMENTS = "木火土金水"
STEM_ELEM = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]          # 甲乙木 丙丁火 戊己土 庚辛金 壬癸水
BRANCH_ELEM = [4, 2, 0, 0, 2, 1, 1, 2, 3, 3, 2, 4]  # 子水丑土寅卯木辰土巳午火未土申酉金戌土亥水
ZODIAC = "鼠牛虎兔龙蛇马羊猴鸡狗猪"

# 地支藏干（本气在前）
HIDDEN = {
  0: [9], 1: [5, 9, 7], 2: [0, 2, 4], 3: [1], 4: [4, 1, 9], 5: [2, 6, 4],
  6: [3, 5], 7: [5, 3, 1], 8: [6, 8, 4], 9: [7], 10: [4, 7, 3], 11: [8, 0],
}

NAYIN = [
  "海中金", "炉中火", "大林木", "路旁土", "剑锋金",
  "山头火", "涧下水", "城头土", "白蜡金", "杨柳木",
  "井泉水", "屋上土", "霹雳火", "松柏木", "长流水",
  "沙中金", "山下火", "平地木", "壁上土", "金箔金",
  "覆灯火", "天河水", "大驿土", "钗钏金", "桑柘木",
  "大溪水", "沙中土", "天上火", "石榴木", "大海水",
]

CHANGSHENG = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]
CS_START = {0: 11, 1: 6, 2: 2, 3: 9, 4: 2, 5: 9, 6: 5, 7: 0, 8: 8, 9: 3}  # 各日干长生位

JIEQI = [
  "立春", "雨水", "惊蛰", "春分", "清明", "谷雨", "立夏", "小满",
  "芒种", "夏至", "小暑", "大暑", "立秋", "处暑", "白露", "秋分",
  "寒露", "霜降", "立冬", "小雪", "大雪", "冬至", "小寒", "大寒",
]  # 从立春起，黄经 315°+15°*i；偶数下标为「节」（换月），奇数为「中气」（定闰）

# 各节气在公历年内的大致日期（Newton 迭代初值）
TERM_GUESS = {
  "小寒": (1, 5), "大寒": (1, 20), "立春": (2, 4), "雨水": (2, 19),
  "惊蛰": (3, 5), "春分": (3, 20), "清明": (4, 5), "谷雨": (4, 20),
  "立夏": (5, 5), "小满": (5, 21), "芒种": (6, 5), "夏至": (6, 21),
  "小暑": (7, 7), "大暑": (7, 22), "立秋": (8, 7), "处暑": (8, 23),
  "白露": (9, 7), "秋分": (9, 23), "寒露": (10, 8), "霜降": (10, 23),
  "立冬": (11, 7), "小雪": (11, 22), "大雪": (12, 7), "冬至": (12, 21),
}

LUNAR_MONTH_NAMES = ["正月", "二月", "三月", "四月", "五月", "六月",
                     "七月", "八月", "九月", "十月", "冬月", "腊月"]
LUNAR_DAY_NAMES = (
  ["初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
   "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
   "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"])


def stem_name(i): return STEMS[i % 10]
def branch_name(i): return BRANCHES[i % 12]
def ganzhi_name(i): return stem_name(i % 10) + branch_name(i % 12)


def sexagenary(stem, branch):
  """由干支序号求六十甲子序号（0=甲子）。"""
  for k in range(60):
    if k % 10 == stem % 10 and k % 12 == branch % 12:
      return k
  raise ValueError("非法干支组合")


# ---------------------------------------------------------------- 儒略日 ---
def gregorian_to_jd(y, m, d):
  """公历 -> 儒略日（d 可带小数）。"""
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


def jd_ut_to_datetime(jd_ut, tz_hours=0.0):
  """儒略日(UT) -> 该时区的公历 naive datetime（四舍五入到秒）。"""
  y, m, d = jd_to_gregorian(jd_ut + tz_hours / 24)
  day = int(d)
  secs = round((d - day) * 86400)
  if secs >= 86400:
    secs -= 86400
    day += 1
    dim = _days_in_month(y, m)
    if day > dim:
      day = 1
      m += 1
      if m > 12:
        m = 1
        y += 1
  return datetime(y, m, day) + timedelta(seconds=secs)


def _days_in_month(y, m):
  if m in (1, 3, 5, 7, 8, 10, 12):
    return 31
  if m in (4, 6, 9, 11):
    return 30
  leap = (y % 4 == 0 and y % 100 != 0) or y % 400 == 0
  return 29 if leap else 28


# ------------------------------------------------------------------- ΔT ---
def delta_t_seconds(year_frac):
  """ΔT = TT - UT（秒），Espenak–Meeus 分段多项式。"""
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
  t = y - 1700  # 1700-1800
  return 8.83 + 0.1603 * t - 0.0059285 * t * t + 0.00013336 * t**3 - t**4 / 1174000


def jde_to_jd_ut(jde):
  y, m, _ = jd_to_gregorian(jde)
  return jde - delta_t_seconds(y + (m - 0.5) / 12) / 86400


def jd_ut_to_jde(jd_ut):
  y, m, _ = jd_to_gregorian(jd_ut)
  return jd_ut + delta_t_seconds(y + (m - 0.5) / 12) / 86400


# ------------------------------------------- 太阳视黄经（截断 VSOP87） ---
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


def nutation_lon_arcsec(t):
  """黄经章动 Δψ（角秒），主项。t 为 J2000 起儒略世纪。"""
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


def mean_obliquity_deg(t):
  return 23.4392911111 - (46.8150 * t + 0.00059 * t * t - 0.001813 * t**3) / 3600


def sun_radius_au(t):
  m = math.radians((357.52911 + 35999.05029 * t - 0.0001537 * t * t) % 360)
  e = 0.016708634 - 0.000042037 * t - 0.0000001267 * t * t
  c = ((1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(m)
       + (0.019993 - 0.000101 * t) * math.sin(2 * m) + 0.000289 * math.sin(3 * m))
  nu = m + math.radians(c)
  return 1.000001018 * (1 - e * e) / (1 + e * math.cos(nu))


def sun_apparent_lon(jde):
  """太阳视黄经（度，含章动与光行差），JDE 为力学时儒略日。"""
  tau = (jde - 2451545.0) / 365250.0
  t = tau * 10
  l = (_series(_L0, tau) + _series(_L1, tau) * tau + _series(_L2, tau) * tau**2
       + _series(_L3, tau) * tau**3 + _series(_L4, tau) * tau**4
       + _series(_L5, tau) * tau**5) * 1e-8
  lon = (math.degrees(l) + 180) % 360           # 地心黄经 = 日心黄经 + 180°
  lon -= 0.09033 / 3600                          # VSOP -> FK5 参考架微调
  lon += nutation_lon_arcsec(t) / 3600           # 章动
  lon -= 20.4898 / 3600 / sun_radius_au(t)       # 光行差
  return lon % 360


def sun_mean_lon_deg(t):
  return (280.46646 + 36000.76983 * t + 0.0003032 * t * t) % 360


def equation_of_time_minutes(jde):
  """均时差（分钟，真太阳时 - 平太阳时）。Meeus 28.1。"""
  t = (jde - 2451545.0) / 36525.0
  lam = sun_apparent_lon(jde)
  eps = math.radians(mean_obliquity_deg(t) + nutation_obl_arcsec(t) / 3600)
  lr = math.radians(lam)
  alpha = math.degrees(math.atan2(math.cos(eps) * math.sin(lr), math.cos(lr))) % 360
  e = sun_mean_lon_deg(t) - 0.0057183 - alpha + nutation_lon_arcsec(t) / 3600 * math.cos(eps)
  e = ((e + 180) % 360) - 180
  return e * 4


def find_term_jde(target_deg, jde_guess):
  """Newton 迭代求太阳视黄经到达 target_deg 的时刻（JDE）。"""
  jde = jde_guess
  for _ in range(50):
    diff = ((target_deg - sun_apparent_lon(jde) + 180) % 360) - 180
    if abs(diff) < 1e-9:
      break
    jde += diff / 0.9856473
  return jde


def term_angle(name):
  return (315 + 15 * JIEQI.index(name)) % 360


@functools.lru_cache(maxsize=4096)
def term_time_jde(year, name):
  """公历 year 年内 name 节气的 JDE。"""
  m, d = TERM_GUESS[name]
  return find_term_jde(term_angle(name), gregorian_to_jd(year, m, d + 0.5))


def terms_of_year(year):
  """公历一年内的 24 节气，按时间排序：[(名, JDE, 是否节), ...]"""
  order = ["小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨",
           "立夏", "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑",
           "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至"]
  out = []
  for name in order:
    jde = term_time_jde(year, name)
    out.append((name, jde, JIEQI.index(name) % 2 == 0))
  return out


# ------------------------------------------------- 定朔（Meeus 第 49 章） ---
@functools.lru_cache(maxsize=4096)
def new_moon_jde(k):
  """第 k 个朔（k=0 为 2000-01-06 附近），返回 JDE。"""
  t = k / 1236.85
  jde = (2451550.09766 + 29.530588861 * k + 0.00015437 * t * t
         - 0.000000150 * t**3 + 0.00000000073 * t**4)
  e = 1 - 0.002516 * t - 0.0000074 * t * t
  m = math.radians((2.5534 + 29.10535670 * k - 0.0000014 * t * t - 0.00000011 * t**3) % 360)
  mp = math.radians((201.5643 + 385.81693528 * k + 0.0107582 * t * t
                     + 0.00001238 * t**3 - 0.000000058 * t**4) % 360)
  f = math.radians((160.7108 + 390.67050284 * k - 0.0016118 * t * t
                    - 0.00000227 * t**3 + 0.000000011 * t**4) % 360)
  om = math.radians((124.7746 - 1.56375588 * k + 0.0020672 * t * t + 0.00000215 * t**3) % 360)
  s = math.sin
  corr = (-0.40720 * s(mp) + 0.17241 * e * s(m) + 0.01608 * s(2 * mp)
          + 0.01039 * s(2 * f) + 0.00739 * e * s(mp - m) - 0.00514 * e * s(mp + m)
          + 0.00208 * e * e * s(2 * m) - 0.00111 * s(mp - 2 * f) - 0.00057 * s(mp + 2 * f)
          + 0.00056 * e * s(2 * mp + m) - 0.00042 * s(3 * mp) + 0.00042 * e * s(m + 2 * f)
          + 0.00038 * e * s(m - 2 * f) - 0.00024 * e * s(2 * mp - m) - 0.00017 * s(om)
          - 0.00007 * s(mp + 2 * m) + 0.00004 * s(2 * mp - 2 * f) + 0.00004 * s(3 * m)
          + 0.00003 * s(mp + m - 2 * f) + 0.00003 * s(2 * mp + 2 * f)
          - 0.00003 * s(mp + m + 2 * f) + 0.00003 * s(mp - m + 2 * f)
          - 0.00002 * s(mp - m - 2 * f) - 0.00002 * s(3 * mp + m) + 0.00002 * s(4 * mp))
  aa = ((299.77, 0.107408, -0.009173), (251.88, 0.016321, 0), (251.83, 26.651886, 0),
        (349.42, 36.412478, 0), (84.66, 18.206239, 0), (141.74, 53.303771, 0),
        (207.14, 2.453732, 0), (154.84, 7.306860, 0), (34.52, 27.261239, 0),
        (207.19, 0.121824, 0), (291.34, 1.844379, 0), (161.72, 24.198154, 0),
        (239.56, 25.513099, 0), (331.55, 3.592518, 0))
  coef = (0.000325, 0.000165, 0.000164, 0.000126, 0.000110, 0.000062, 0.000060,
          0.000056, 0.000047, 0.000042, 0.000040, 0.000037, 0.000035, 0.000023)
  extra = sum(c * s(math.radians((a0 + a1 * k + a2 * t * t) % 360))
              for c, (a0, a1, a2) in zip(coef, aa))
  return jde + corr + extra


def _cst_date_num(jde):
  """JDE -> 北京时间（UTC+8）日期序号（当日 JDN）。农历/节气归日均按此。"""
  return math.floor(jde_to_jd_ut(jde) + 8 / 24 + 0.5)


# ------------------------------------------------------------------- 农历 ---
def _winter_solstice_datenum(year):
  return _cst_date_num(term_time_jde(year, "冬至"))


def _new_moons_around(year):
  """返回覆盖 [year-1 年 10 月, year+1 年 3 月] 的朔日北京时间日期序号列表。"""
  k0 = math.floor((year - 1 - 2000) * 12.3685) - 4
  out = []
  for k in range(k0, k0 + 34):
    out.append((_cst_date_num(new_moon_jde(k)), k))
  return out


def _zhongqi_datenums(year):
  """year-1 与 year 两年中气（奇下标节气）的日期序号集合。"""
  nums = {}
  for yy in (year - 1, year, year + 1):
    for name, jde, is_jie in terms_of_year(yy):
      if not is_jie:
        nums[_cst_date_num(jde)] = name
  return nums


def _build_suite(year):
  """冬至(year-1) 所在月到冬至(year) 所在月之间的农历月序列。

  返回 [(月序号 1..12, 是否闰月, 起始日期序号, 天数), ...]，
  首项为 year-1 年十一月，末项为 year 年十一月的前一个月。
  """
  w_prev = _winter_solstice_datenum(year - 1)
  w_cur = _winter_solstice_datenum(year)
  moons = _new_moons_around(year)
  starts = [dn for dn, _ in moons]
  i0 = max(i for i, dn in enumerate(starts) if dn <= w_prev)
  i1 = max(i for i, dn in enumerate(starts) if dn <= w_cur)
  n = i1 - i0  # 两个十一月间的朔望月数：12 无闰，13 有闰
  zhongqi = _zhongqi_datenums(year)
  leap_idx = None
  if n == 13:
    for j in range(i0 + 1, i1 + 1):
      has_zq = any(starts[j] <= dn < starts[j + 1] for dn in zhongqi)
      if not has_zq:
        leap_idx = j
        break
    if leap_idx is None:  # 理论上不该发生；容错为不置闰
      n = 12
  months = []
  num = 11
  for j in range(i0, i1):
    is_leap = (j == leap_idx)
    if not is_leap:
      if j > i0:
        num = num % 12 + 1
    months.append((num, is_leap, starts[j], starts[j + 1] - starts[j]))
  return months


@functools.lru_cache(maxsize=512)
def build_lunar_year(ly):
  """农历 ly 年正月到腊月（含闰月）的月表。"""
  a = _build_suite(ly)      # ly-1 十一月 ~ ly 十月（含闰）
  b = _build_suite(ly + 1)  # ly 十一月 ~ ly+1 十月
  months = [m for m in a if m[0] not in (11, 12)]
  months += [m for m in b if m[0] in (11, 12)]
  return months


def solar_to_lunar(y, m, d):
  """公历 -> 农历。返回 dict。"""
  dn = int(gregorian_to_jd(y, m, d) + 0.5)
  for ly in (y, y - 1):
    months = build_lunar_year(ly)
    if not months or dn < months[0][2]:
      continue
    for num, leap, start, days in months:
      if start <= dn < start + days:
        gz = (ly - 4) % 60
        return {
          "lunar_year": ly, "year_ganzhi": ganzhi_name(gz), "zodiac": ZODIAC[gz % 12],
          "month": num, "leap": leap, "day": dn - start + 1,
          "month_name": ("闰" if leap else "") + LUNAR_MONTH_NAMES[num - 1],
          "day_name": LUNAR_DAY_NAMES[dn - start],
          "month_days": days,
        }
  raise ValueError("日期超出可推算范围")


def lunar_to_solar(ly, lm, ld, leap=False):
  """农历 -> 公历 (y, m, d)。"""
  for num, is_leap, start, days in build_lunar_year(ly):
    if num == lm and is_leap == leap:
      if not 1 <= ld <= days:
        raise ValueError(f"农历{ly}年{'闰' if leap else ''}{LUNAR_MONTH_NAMES[lm-1]}只有{days}天")
      yy, mm, dd = jd_to_gregorian(start + ld - 1)
      return yy, mm, int(dd)
  raise ValueError(f"农历{ly}年没有{'闰' if leap else ''}{LUNAR_MONTH_NAMES[lm-1]}")


# ------------------------------------------------------------------- 四柱 ---
def day_ganzhi_index(y, m, d):
  """某公历日的日柱六十甲子序号。锚点：2000-01-07 甲子（(JDN+49) mod 60）。"""
  jdn = int(gregorian_to_jd(y, m, d) + 0.5)
  return (jdn + 49) % 60


def shishen(day_stem, other_stem):
  de, oe = STEM_ELEM[day_stem], STEM_ELEM[other_stem]
  same = (day_stem % 2) == (other_stem % 2)
  if de == oe:
    return "比肩" if same else "劫财"
  if (de + 1) % 5 == oe:
    return "食神" if same else "伤官"
  if (de + 2) % 5 == oe:
    return "偏财" if same else "正财"
  if (oe + 2) % 5 == de:
    return "七杀" if same else "正官"
  return "偏印" if same else "正印"


def changsheng_stage(day_stem, branch):
  start = CS_START[day_stem]
  idx = (branch - start) % 12 if day_stem % 2 == 0 else (start - branch) % 12
  return CHANGSHENG[idx]


def kongwang(gz_index):
  """该柱所在旬的旬首与两个空亡支。"""
  stem, branch = gz_index % 10, gz_index % 12
  xun_start = (gz_index - stem) % 60
  k1, k2 = (branch - stem + 10) % 12, (branch - stem + 11) % 12
  return ganzhi_name(xun_start), branch_name(k1) + branch_name(k2)


# 神煞表
TIANYI = {0: (1, 7), 4: (1, 7), 6: (1, 7), 1: (0, 8), 5: (0, 8),
          2: (11, 9), 3: (11, 9), 8: (3, 5), 9: (3, 5), 7: (6, 2)}
SANHE_GROUP = {8: 0, 0: 0, 4: 0, 2: 1, 6: 1, 10: 1, 5: 2, 9: 2, 1: 2, 11: 3, 3: 3, 7: 3}
TAOHUA = {0: 9, 1: 3, 2: 6, 3: 0}   # 申子辰→酉 寅午戌→卯 巳酉丑→午 亥卯未→子
YIMA = {0: 2, 1: 8, 2: 11, 3: 5}    # →寅 →申 →亥 →巳
HUAGAI = {0: 4, 1: 10, 2: 1, 3: 7}  # →辰 →戌 →丑 →未
JIANGXING = {0: 0, 1: 6, 2: 9, 3: 3}
WENCHANG = {0: 5, 1: 6, 2: 8, 3: 9, 4: 8, 5: 9, 6: 11, 7: 0, 8: 2, 9: 3}
LUSHEN = {0: 2, 1: 3, 2: 5, 3: 6, 4: 5, 5: 6, 6: 8, 7: 9, 8: 11, 9: 0}
YANGREN = {0: 3, 2: 6, 4: 6, 6: 9, 8: 0}
YUEDE = {1: 2, 0: 8, 3: 0, 2: 6}     # 三合组→干：火局丙 水局壬 木局甲 金局庚
TIANDE = {2: ("干", 3), 3: ("支", 8), 4: ("干", 8), 5: ("干", 7), 6: ("支", 11),
          7: ("干", 0), 8: ("干", 9), 9: ("支", 2), 10: ("干", 2), 11: ("干", 1),
          0: ("支", 5), 1: ("干", 6)}  # 月支→天德（干或支）
KUIGANG = {"庚辰", "庚戌", "壬辰", "戊戌"}

LIUHE = {(0, 1): "土", (2, 11): "木", (3, 10): "火", (4, 9): "金", (5, 8): "水", (6, 7): "土"}
LIUHAI = {(0, 7), (1, 6), (2, 5), (3, 4), (8, 11), (9, 10)}
SANHE_JU = {(8, 0, 4): "水", (2, 6, 10): "火", (11, 3, 7): "木", (5, 9, 1): "金"}
SANHUI = {(2, 3, 4): "木", (5, 6, 7): "火", (8, 9, 10): "金", (11, 0, 1): "水"}
WUHE = {0: "土", 1: "金", 2: "水", 3: "木", 4: "火"}  # 甲己/乙庚/丙辛/丁壬/戊癸


def detect_interactions(stems, branches, labels_s, labels_b):
  """四柱干支间的合冲刑害。stems/branches 为序号列表，labels 为柱名。"""
  out = []
  n = len(stems)
  for i in range(n):
    for j in range(i + 1, n):
      a, b = stems[i], stems[j]
      if a is None or b is None:
        continue
      if (a - b) % 10 == 5 or (b - a) % 10 == 5:
        lo = min(a % 5, b % 5)
        out.append(f"{stem_name(a)}{stem_name(b)}相合化{WUHE[lo]}（{labels_s[i]}-{labels_s[j]}）")
  m = len(branches)
  for i in range(m):
    for j in range(i + 1, m):
      a, b = branches[i], branches[j]
      if a is None or b is None:
        continue
      key = (min(a, b), max(a, b))
      pos = f"（{labels_b[i]}-{labels_b[j]}）"
      if (a - b) % 12 == 6:
        out.append(f"{branch_name(a)}{branch_name(b)}相冲{pos}")
      if key in LIUHE:
        out.append(f"{branch_name(key[0])}{branch_name(key[1])}六合化{LIUHE[key]}{pos}")
      if key in LIUHAI:
        out.append(f"{branch_name(key[0])}{branch_name(key[1])}相害{pos}")
      if key in ((0, 3),):
        out.append(f"子卯相刑{pos}")
      if a == b and a in (4, 6, 9, 11):
        out.append(f"{branch_name(a)}{branch_name(b)}自刑{pos}")
      if key in ((2, 5), (5, 8), (2, 8)):
        out.append(f"{branch_name(key[0])}{branch_name(key[1])}相刑（寅巳申）{pos}")
      if key in ((1, 10), (7, 10), (1, 7)):
        out.append(f"{branch_name(key[0])}{branch_name(key[1])}相刑（丑戌未）{pos}")
  present = set(b for b in branches if b is not None)
  for trio, elem in SANHE_JU.items():
    if set(trio) <= present:
      out.append("".join(branch_name(x) for x in trio) + f"三合{elem}局")
  for trio, elem in SANHUI.items():
    if set(trio) <= present:
      out.append("".join(branch_name(x) for x in trio) + f"三会{elem}方")
  return out


def detect_shensha(p):
  """p: dict(year=(s,b), month=(s,b), day=(s,b), hour=(s,b)|None)"""
  ds, db = p["day"]
  ys, yb = p["year"]
  pillars = [("年", p["year"]), ("月", p["month"]), ("日", p["day"])]
  if p.get("hour"):
    pillars.append(("时", p["hour"]))
  branches = [(lab, b) for lab, (s, b) in pillars]
  stems = [(lab, s) for lab, (s, b) in pillars]
  out = []

  def hits_branch(targets, note):
    got = [f"{branch_name(b)}({lab}支)" for lab, b in branches if b in targets]
    if got:
      out.append(f"{note}：" + "、".join(got))

  hits_branch(TIANYI[ds], "天乙贵人(日干)")
  for base_lab, base_b in (("年", yb), ("日", db)):
    g = SANHE_GROUP[base_b]
    for name, table in (("桃花", TAOHUA), ("驿马", YIMA), ("华盖", HUAGAI), ("将星", JIANGXING)):
      t = table[g]
      got = [f"{branch_name(b)}({lab}支)" for lab, b in branches
             if b == t and not (lab == base_lab)]
      if got:
        out.append(f"{name}({base_lab}支起)：" + "、".join(got))
  hits_branch([WENCHANG[ds]], "文昌贵人(日干)")
  hits_branch([LUSHEN[ds]], "禄神(日干)")
  if ds in YANGREN:
    hits_branch([YANGREN[ds]], "羊刃(日干)")
  mb = p["month"][1]
  yd = YUEDE[SANHE_GROUP[mb]]
  got = [f"{stem_name(s)}({lab}干)" for lab, s in stems if s == yd]
  if got:
    out.append("月德贵人：" + "、".join(got))
  kind, tgt = TIANDE[mb]
  if kind == "干":
    got = [f"{stem_name(s)}({lab}干)" for lab, s in stems if s == tgt]
  else:
    got = [f"{branch_name(b)}({lab}支)" for lab, b in branches if b == tgt]
  if got:
    out.append("天德贵人：" + "、".join(got))
  if ganzhi_name(sexagenary(ds, db)) in KUIGANG:
    out.append(f"魁罡（日柱{ganzhi_name(sexagenary(ds, db))}）")
  return out


# --------------------------------------------------------------- 排盘主体 ---
def parse_tz(s):
  if "/" in s:
    if ZoneInfo is None:
      raise SystemExit("当前 Python 无 zoneinfo，请用数字时区如 --tz +8")
    return ZoneInfo(s)
  return timezone(timedelta(hours=float(s)))


def hour_branch_of(dt):
  return ((dt.hour + 1) // 2) % 12


def compute_chart(local_dt, tzinfo, lon=None, use_tst=True, zishi="next",
                  gender=None, dayun_n=8, liunian=None, time_known=True):
  aware = local_dt.replace(tzinfo=tzinfo)
  utc_dt = aware.astimezone(timezone.utc).replace(tzinfo=None)
  jd_ut = datetime_to_jd_ut(utc_dt)
  jde = jd_ut_to_jde(jd_ut)
  warnings = []

  # 排日/时柱用的"墙上时间"：真太阳时或输入本地时
  eot = equation_of_time_minutes(jde)
  if lon is not None and use_tst and time_known:
    wall = utc_dt + timedelta(hours=lon / 15, minutes=eot)
    tst_info = {"enabled": True, "eot_minutes": round(eot, 2),
                "true_solar": wall.strftime("%Y-%m-%d %H:%M:%S"),
                "offset_minutes": round((wall - local_dt).total_seconds() / 60, 1)}
  else:
    wall = local_dt
    tst_info = {"enabled": False, "eot_minutes": round(eot, 2)}

  # 年柱：以立春为界
  gy = wall.year
  lichun = term_time_jde(gy, "立春")
  by = gy if jde >= lichun else gy - 1  # 生于当年立春前 -> 上一年干支
  ys, yb = (by - 4) % 10, (by - 4) % 12
  d_lichun_h = abs(jde - lichun) * 24
  if d_lichun_h < 2:
    warnings.append(f"出生时刻距立春交接仅 {d_lichun_h*60:.0f} 分钟，年柱/月柱敏感，请核对出生时间")

  # 月柱：按太阳视黄经所处的"节"区间
  lam = sun_apparent_lon(jde)
  midx = int(((lam - 315) % 360) // 30)      # 0=寅月
  mb = (midx + 2) % 12
  first_stem = (ys % 5) * 2 + 2               # 五虎遁
  ms = (first_stem + midx) % 10
  # 距最近节的时间（同时用于大运起运）
  off = (lam - 315) % 30
  prev_angle = round((lam - off) % 360) % 360
  next_angle = (prev_angle + 30) % 360
  prev_jie_jde = find_term_jde(prev_angle, jde - off / 0.9856473)
  next_jie_jde = find_term_jde(next_angle, jde + (30 - off) / 0.9856473)
  near_h = min(abs(jde - prev_jie_jde), abs(next_jie_jde - jde)) * 24
  if near_h < 2:
    warnings.append(f"出生时刻距节气交接仅 {near_h*60:.0f} 分钟，月柱敏感，请核对出生时间")

  # 日柱
  day_date = wall.date()
  hb = hour_branch_of(wall) if time_known else None
  late_zi = time_known and wall.hour == 23
  if late_zi and zishi == "next":
    day_date = day_date + timedelta(days=1)
  dgz = day_ganzhi_index(day_date.year, day_date.month, day_date.day)
  ds, db = dgz % 10, dgz % 12
  if time_known and (wall.hour == 23 or wall.hour == 0):
    warnings.append("出生于子时（23:00–01:00），日柱换日存在流派差异（--zishi next|split），两种结果建议都参考")
  if time_known and wall.minute >= 55 and wall.hour % 2 == 0:
    warnings.append("出生时间贴近时辰交界，时柱敏感")

  # 时柱：五鼠遁；晚子时在 split 派下用次日日干起子时
  hs = None
  if time_known:
    zi_base_stem = ds
    if late_zi and zishi == "split":
      zi_base_stem = (day_ganzhi_index(*(day_date + timedelta(days=1)).timetuple()[:3])) % 10
    hs = ((zi_base_stem % 5) * 2 + hb) % 10

  pil = {"year": (ys, yb), "month": (ms, mb), "day": (ds, db),
         "hour": (hs, hb) if time_known else None}

  # 大运
  yang_year = ys % 2 == 0
  def build_dayun(sex):
    forward = (yang_year and sex == "male") or (not yang_year and sex == "female")
    edge = next_jie_jde if forward else prev_jie_jde
    days = abs(edge - jde)
    months_f = days * 4  # 3天=1年 → 1天=4个月
    y_n = int(months_f // 12)
    m_n = int(months_f % 12)
    d_n = int(round((months_f - int(months_f)) * 30))
    total_m = int(round(months_f))
    sy, sm = divmod((local_dt.year * 12 + local_dt.month - 1) + total_m, 12)
    mgz = sexagenary(ms, mb)
    steps = []
    for i in range(1, dayun_n + 1):
      g = (mgz + i) % 60 if forward else (mgz - i) % 60
      steps.append({
        "ganzhi": ganzhi_name(g),
        "stem_shishen": shishen(ds, g % 10),
        "start_age": round(days / 3) + (i - 1) * 10,
        "start_year": sy + (i - 1) * 10,
      })
    return {"direction": "顺行" if forward else "逆行",
            "qiyun": f"出生后{y_n}年{m_n}个月{d_n}天起运",
            "qiyun_year": sy, "qiyun_month": sm + 1, "list": steps}

  dayun = {}
  if time_known:
    if gender in ("male", "female"):
      dayun[gender] = build_dayun(gender)
    else:
      dayun["male"] = build_dayun("male")
      dayun["female"] = build_dayun("female")
  else:
    warnings.append("未提供出生时间：不排时柱；大运起运按正午近似（误差可达数月）")
    if gender in ("male", "female"):
      dayun[gender] = build_dayun(gender)

  # 流年
  liunian_list = []
  if liunian:
    a, b = liunian
    for y in range(a, b + 1):
      g = (y - 4) % 60
      liunian_list.append({"year": y, "ganzhi": ganzhi_name(g),
                           "stem_shishen": shishen(ds, g % 10)})

  # 农历生日
  try:
    lunar = solar_to_lunar(local_dt.year, local_dt.month, local_dt.day)
  except Exception:
    lunar = None

  # 汇总
  def pillar_info(s, b):
    gz = sexagenary(s, b)
    return {
      "ganzhi": ganzhi_name(gz),
      "stem": stem_name(s), "branch": branch_name(b),
      "stem_shishen": shishen(ds, s),
      "hidden": [{"stem": stem_name(h), "shishen": shishen(ds, h)} for h in HIDDEN[b]],
      "nayin": NAYIN[gz // 2],
      "changsheng": changsheng_stage(ds, b),
    }

  pillars = {
    "year": pillar_info(ys, yb), "month": pillar_info(ms, mb), "day": pillar_info(ds, db),
    "hour": pillar_info(hs, hb) if time_known else None,
  }
  pillars["day"]["stem_shishen"] = "日主"

  counts = {e: 0 for e in ELEMENTS}
  hidden_counts = {e: 0.0 for e in ELEMENTS}
  chars = [(ys, yb), (ms, mb), (ds, db)] + ([(hs, hb)] if time_known else [])
  for s, b in chars:
    counts[ELEMENTS[STEM_ELEM[s]]] += 1
    counts[ELEMENTS[BRANCH_ELEM[b]]] += 1
    for w, h in zip((1.0, 0.5, 0.3), HIDDEN[b]):
      hidden_counts[ELEMENTS[STEM_ELEM[h]]] += w
  for s, b in chars:
    hidden_counts[ELEMENTS[STEM_ELEM[s]]] += 1

  stems_l = [ys, ms, ds] + ([hs] if time_known else [])
  brs_l = [yb, mb, db] + ([hb] if time_known else [])
  labels = ["年", "月", "日", "时"][:len(stems_l)]
  interactions = detect_interactions(stems_l, brs_l,
                                     [x + "干" for x in labels], [x + "支" for x in labels])
  shensha = detect_shensha(pil)
  xun, kw = kongwang(dgz)
  taiyuan = ganzhi_name(sexagenary((ms + 1) % 10, (mb + 3) % 12))

  return {
    "input": {
      "solar": local_dt.strftime("%Y-%m-%d %H:%M") if time_known else local_dt.strftime("%Y-%m-%d 时辰不详"),
      "tz": str(tzinfo), "lon": lon, "gender": gender,
    },
    "true_solar_time": tst_info,
    "lunar": lunar,
    "bazi": " ".join(pillars[k]["ganzhi"] for k in ("year", "month", "day", "hour") if pillars[k]),
    "pillars": pillars,
    "day_master": {"stem": stem_name(ds), "element": ELEMENTS[STEM_ELEM[ds]],
                   "yinyang": "阳" if ds % 2 == 0 else "阴",
                   "month_branch": branch_name(mb)},
    "wuxing": {"counts": counts,
               "weighted_with_hidden": {k: round(v, 1) for k, v in hidden_counts.items()},
               "missing": [e for e in ELEMENTS if counts[e] == 0]},
    "kongwang": {"day_xun": xun, "empty": kw},
    "taiyuan": taiyuan,
    "shensha": shensha,
    "interactions": interactions,
    "jieqi": {
      "prev_jie": {"name": JIEQI[((prev_angle - 315) % 360) // 15],
                   "time_cst": jd_ut_to_datetime(jde_to_jd_ut(prev_jie_jde), 8).strftime("%Y-%m-%d %H:%M:%S")},
      "next_jie": {"name": JIEQI[((next_angle - 315) % 360) // 15],
                   "time_cst": jd_ut_to_datetime(jde_to_jd_ut(next_jie_jde), 8).strftime("%Y-%m-%d %H:%M:%S")},
      "days_after_prev_jie": round(jde - prev_jie_jde, 2),
    },
    "dayun": dayun,
    "liunian": liunian_list,
    "warnings": warnings,
  }


# --------------------------------------------------------------- 文本输出 ---
def render_chart(c):
  L = []
  gender_cn = {"male": "男命", "female": "女命", None: "未注明性别"}
  L.append(f"「八字排盘」{c['input']['solar']}  {c['input']['tz']}  {gender_cn.get(c['input']['gender'])}")
  t = c["true_solar_time"]
  if t.get("enabled"):
    L.append(f"真太阳时  {t['true_solar']}（较输入钟表时 {t['offset_minutes']:+.1f} 分："
             f"时区/夏令时+经度差+均时差 {t['eot_minutes']:+.1f} 分；日/时柱按此排）")
  if c.get("lunar"):
    lu = c["lunar"]
    L.append(f"农历  {lu['year_ganzhi']}年（属{lu['zodiac']}）{lu['month_name']}{lu['day_name']}")
  jq = c["jieqi"]
  L.append(f"节气  {jq['prev_jie']['name']} {jq['prev_jie']['time_cst']} ～ "
           f"{jq['next_jie']['name']} {jq['next_jie']['time_cst']}（生于{jq['prev_jie']['name']}后 {jq['days_after_prev_jie']} 天）")
  L.append("")
  L.append(f"八字  {c['bazi']}    日主 {c['day_master']['stem']}{c['day_master']['element']}"
           f"（{c['day_master']['yinyang']}），生于{c['day_master']['month_branch']}月")
  for key, lab in (("year", "年柱"), ("month", "月柱"), ("day", "日柱"), ("hour", "时柱")):
    p = c["pillars"].get(key)
    if not p:
      L.append("时柱  （时辰不详）")
      continue
    hid = " ".join(f"{h['stem']}({h['shishen']})" for h in p["hidden"])
    L.append(f"{lab}  {p['ganzhi']}  {p['stem']}:{p['stem_shishen']}  藏干 {hid}  纳音 {p['nayin']}  星运 {p['changsheng']}")
  L.append("")
  w = c["wuxing"]
  L.append("五行  " + " ".join(f"{e}{w['counts'][e]}" for e in ELEMENTS)
           + "（含藏干加权: " + " ".join(f"{e}{w['weighted_with_hidden'][e]}" for e in ELEMENTS) + "）"
           + ("  缺" + "".join(w["missing"]) if w["missing"] else ""))
  L.append(f"空亡  日柱{c['kongwang']['day_xun']}旬，旬空 {c['kongwang']['empty']}    胎元  {c['taiyuan']}")
  if c["shensha"]:
    L.append("神煞  " + "；".join(c["shensha"]))
  if c["interactions"]:
    L.append("合冲刑害  " + "；".join(c["interactions"]))
  for sex, dy in c["dayun"].items():
    L.append("")
    L.append(f"大运（{'男命' if sex == 'male' else '女命'}，{dy['direction']}）  {dy['qiyun']}，"
             f"约 {dy['qiyun_year']}年{dy['qiyun_month']}月交运")
    for i, s in enumerate(dy["list"], 1):
      L.append(f"  {i:2d}. {s['ganzhi']}（{s['stem_shishen']}）  约{s['start_age']}岁起 / {s['start_year']}年起")
  if c["liunian"]:
    L.append("")
    L.append("流年（按立春换年）  " + "  ".join(f"{x['year']}{x['ganzhi']}({x['stem_shishen']})" for x in c["liunian"]))
  if c["warnings"]:
    L.append("")
    for wmsg in c["warnings"]:
      L.append(f"⚠ {wmsg}")
  return "\n".join(L)


# ------------------------------------------------------------------- CLI ---
def cmd_chart(args):
  tz = parse_tz(args.tz)
  if args.lunar:
    parts = args.lunar.replace("/", "-").split("-")
    ly, lm, ld = int(parts[0]), int(parts[1]), int(parts[2])
    y, m, d = lunar_to_solar(ly, lm, ld, leap=args.leap)
    date_s = f"{y:04d}-{m:02d}-{d:02d}"
  else:
    date_s = args.date.replace("/", "-")
  time_known = args.time is not None
  ts = args.time if time_known else "12:00"
  hh, mm = ts.split(":")[0], ts.split(":")[1]
  local_dt = datetime.fromisoformat(f"{date_s} {int(hh):02d}:{int(mm):02d}")
  gender = None
  if args.gender:
    g = args.gender.lower()
    gender = "male" if g in ("m", "male", "男", "乾") else "female" if g in ("f", "female", "女", "坤") else None
  liunian = None
  if args.liunian:
    a, b = args.liunian.replace("-", ":").split(":")
    liunian = (int(a), int(b))
  c = compute_chart(local_dt, tz, lon=args.lon, use_tst=not args.no_tst,
                    zishi=args.zishi, gender=gender, dayun_n=args.dayun,
                    liunian=liunian, time_known=time_known)
  if args.json:
    print(json.dumps(c, ensure_ascii=False, indent=2))
  else:
    print(render_chart(c))


def cmd_solar_terms(args):
  rows = []
  for name, jde, is_jie in terms_of_year(args.year):
    t = jd_ut_to_datetime(jde_to_jd_ut(jde), 8)
    rows.append({"name": name, "type": "节" if is_jie else "中气",
                 "time_cst": t.strftime("%Y-%m-%d %H:%M:%S")})
  if args.json:
    print(json.dumps(rows, ensure_ascii=False, indent=2))
  else:
    print(f"{args.year} 年二十四节气（北京时间，定气法）")
    for r in rows:
      print(f"  {r['name']}  {r['time_cst']}  [{r['type']}]")


def cmd_lunar(args):
  if args.reverse:
    parts = args.date.replace("/", "-").split("-")
    ly, lm, ld = int(parts[0]), int(parts[1]), int(parts[2])
    y, m, d = lunar_to_solar(ly, lm, ld, leap=args.leap)
    dgz = day_ganzhi_index(y, m, d)
    out = {"solar": f"{y:04d}-{m:02d}-{d:02d}",
           "weekday": "一二三四五六日"[datetime(y, m, d).weekday()],
           "day_ganzhi": ganzhi_name(dgz)}
    if args.json:
      print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
      leaps = "闰" if args.leap else ""
      print(f"农历{ly}年{leaps}{LUNAR_MONTH_NAMES[lm-1]}{LUNAR_DAY_NAMES[ld-1]} = 公历 {out['solar']}"
            f"（星期{out['weekday']}，{out['day_ganzhi']}日）")
    return
  parts = args.date.replace("/", "-").split("-")
  y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
  lu = solar_to_lunar(y, m, d)
  dgz = day_ganzhi_index(y, m, d)
  # 该日所属的干支年月（按节气）
  jde = jd_ut_to_jde(gregorian_to_jd(y, m, d + 0.5) - 8 / 24)  # 当日北京正午
  lam = sun_apparent_lon(jde)
  midx = int(((lam - 315) % 360) // 30)
  lichun = term_time_jde(y, "立春")
  by = y if jde >= lichun else y - 1
  ys = (by - 4) % 10
  ms, mb = ((ys % 5) * 2 + 2 + midx) % 10, (midx + 2) % 12
  out = {
    "solar": f"{y:04d}-{m:02d}-{d:02d}",
    "weekday": "一二三四五六日"[datetime(y, m, d).weekday()],
    "lunar": lu,
    "ganzhi": {"year": ganzhi_name((by - 4) % 60), "month": ganzhi_name(sexagenary(ms, mb)),
               "day": ganzhi_name(dgz)},
    "note": "干支年月按节气（立春换年、交节换月）；农历年按正月初一。",
  }
  if args.json:
    print(json.dumps(out, ensure_ascii=False, indent=2))
  else:
    print(f"公历 {out['solar']} 星期{out['weekday']}")
    print(f"农历 {lu['year_ganzhi']}年（属{lu['zodiac']}）{lu['month_name']}{lu['day_name']}")
    print(f"干支 {out['ganzhi']['year']}年 {out['ganzhi']['month']}月 {out['ganzhi']['day']}日（年月按节气界）")


def main(argv=None):
  ap = argparse.ArgumentParser(
    prog="bazi", description="八字排盘/节气/农历互转（离线天文算法，纯标准库）")
  sub = ap.add_subparsers(dest="cmd", required=True)

  c = sub.add_parser("chart", help="排八字：四柱/藏干/十神/纳音/神煞/大运/流年")
  c.add_argument("--date", help="公历生日 YYYY-MM-DD")
  c.add_argument("--lunar", help="农历生日 YYYY-M-D（与 --date 二选一）")
  c.add_argument("--leap", action="store_true", help="农历生日为闰月")
  c.add_argument("--time", help="出生时间 HH:MM（不给则按时辰不详处理）")
  c.add_argument("--tz", default="Asia/Shanghai",
                 help="时区：IANA 名或小时数，默认 Asia/Shanghai（含历史夏令时）")
  c.add_argument("--lon", type=float, help="出生地经度（东经为正），给出即按真太阳时排日/时柱")
  c.add_argument("--no-tst", action="store_true", help="给了 --lon 也不用真太阳时")
  c.add_argument("--gender", help="性别 m/f（决定大运顺逆；不给则两种都排）")
  c.add_argument("--zishi", choices=["next", "split"], default="next",
                 help="晚子时(23-24点)规则：next=日柱算次日(默认)；split=早晚子时派")
  c.add_argument("--dayun", type=int, default=8, help="大运步数，默认 8")
  c.add_argument("--liunian", help="流年范围，如 2026:2035")
  c.add_argument("--json", action="store_true")
  c.set_defaults(func=cmd_chart)

  s = sub.add_parser("solar-terms", help="某公历年 24 节气时刻（北京时间）")
  s.add_argument("year", type=int)
  s.add_argument("--json", action="store_true")
  s.set_defaults(func=cmd_solar_terms)

  l = sub.add_parser("lunar", help="公历↔农历互转 + 当日干支")
  l.add_argument("date", help="公历 YYYY-MM-DD；配合 --reverse 时为农历 YYYY-M-D")
  l.add_argument("--reverse", action="store_true", help="农历转公历")
  l.add_argument("--leap", action="store_true", help="（--reverse 时）指定闰月")
  l.add_argument("--json", action="store_true")
  l.set_defaults(func=cmd_lunar)

  args = ap.parse_args(argv)
  if args.cmd == "chart" and not args.date and not args.lunar:
    ap.error("chart 需要 --date 或 --lunar")
  args.func(args)


if __name__ == "__main__":
  main()
