---
name: astro-chart
description: 西方占星排盘，纯标准库、完全离线（内置 VSOP87 截断太阳、Meeus 月亮级数、JPL 开普勒行星根数，行星位置角分级精度）。四个子命令：natal(本命盘：十行星+北交点的星座/宫位/逆行、上升天顶、Placidus/整宫/等宫宫头、相位表、元素模式分布、月相)、now(当下天象)、transits(行运对本命的相位与落宫)、synastry(双人合盘跨盘相位)。时区含历史夏令时自动处理，未知出生时间自动降级并提示月亮换座风险。脚本只做天文计算，解读框架见 references/interpretation.md。当用户要看星盘/本命盘/上升星座/月亮星座、问行运/水逆/土星回归、要合盘配对、或问当前行星位置时使用。
---

# Astro Chart 西方占星排盘

## 用途与分工

脚本负责**天文计算**：行星视黄经（含岁差/章动/光行差/光行时）、上升天顶、
宫头、相位、逆行、月相。**解读是使用者（agent）的工作**：拿到结果后按
`references/interpretation.md` 的框架（三巨头→元素格局→紧密相位→整合）生成分析。
不要自己心算行星位置或上升星座——模型心算天文必错，一律跑脚本。

## 快速开始

从 skill 目录运行：

```bash
bash scripts/astro_chart natal --date 1990-05-17 --time 14:30 \
  --tz Asia/Shanghai --lat 31.23 --lon 121.47                   # 本命盘（上海）
bash scripts/astro_chart natal --date 1990-05-17                # 时间未知 → 无宫位并提示
bash scripts/astro_chart now                                     # 当下天象+月相
bash scripts/astro_chart transits --date 1990-05-17 --time 14:30 \
  --lat 31.23 --lon 121.47 [--on "2026-12-01 00:00"]            # 行运（默认此刻）
bash scripts/astro_chart synastry \
  --a-date 1990-05-17 --a-time 14:30 --a-lat 31.23 --a-lon 121.47 \
  --b-date 1992-11-03 --b-time 08:00 --b-lat 39.9 --b-lon 116.4  # 合盘
```

每个子命令支持 `--json`。解释器顺序：`ASTRO_CHART_PYTHON` → `VIRTUAL_ENV/bin/python`
→ `PYTHON` → `python3`（共享约定见仓库 `AGENTS.md`）。纯标准库、无网络。

## 排盘前先向用户确认

1. **出生日期与当地时间**（尽量精确到分钟——上升每 4 分钟走 1°）；
2. **出生地**（城市→经纬度自己换算填入，东经/北纬为正）；
3. 时区一般给 IANA 名（如 `America/New_York`），**历史夏令时自动处理**；
4. 时间未知也能排：日月行星星座照出，宫位/上升缺省，月亮若当日换座会提示。

## 选项

| 选项 | 默认 | 说明 |
|---|---|---|
| `--house` | placidus | 也可 whole(整宫)/equal(等宫)；纬度>66° 自动退整宫 |
| `--mean-node` | 真交点 | 改用平交点 |
| `--orb-scale` | 1.0 | transits/synastry 容许度缩放 |
| `--on` | 现在 | transits 的行运时刻（UTC） |

相位容许度：本命 合/冲/拱 8°、刑 7°、六合 5°（日月再 +1°）；行运收紧到 2–3°；
合盘 4–6°。只报五大相位（0/60/90/120/180）。

## 输出契约（--json）

`natal`：`positions.{行星}` 含 `lon/lat/sign/pos/house/speed/retrograde
[/near_sign_boundary]`；`angles.{ASC,MC,DSC,IC}`；`cusps[12]`；`aspects[]` 含
`a/b/aspect/angle/orb/applying`；`elements/modes`（十行星计数）；`moon_phase`；
`warnings[]`。`transits`：`aspects[]`(行运×本命) + `transit_in_natal_houses[]`。
`synastry`：双方 `positions` + 跨盘 `aspects[]`。文本输出为同一数据的人读版。

## 校验与精度

- 已验证锚点：2024 春分太阳黄经 0″；满月日月正对冲；2024-06 木土天海冥星座及
  土星留驻位置（差 5′）；2024-04 日食交点位置；ASC 数值满足"地平高度=0 且在东方"、
  Placidus 宫头满足半弧方程（随机回归各 20–30 组）。
- 行星根数适用 **1800–2050**（范围外会警告，太阳/月亮不受影响）。总体精度角分级，
  远好于占星需要；行星距星座边界 <15′ 时输出 `near_sign_boundary` 提醒。
- 小行星/凯龙星无内置星历，不支持；北交点默认真交点。

## 解读

排盘结果不含吉凶判断。生成解读时读 `references/interpretation.md`；
表达用倾向性语言，不做医疗/投资/婚姻的确定性断言。
算法与精度细节见 `references/algorithms.md`。
