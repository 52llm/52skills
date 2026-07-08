---
name: bazi
description: 八字排盘与农历/节气计算，纯标准库、完全离线（内置截断 VSOP87 太阳黄经 + Meeus 定朔的天文算法，节气秒级精度）。三个子命令：chart(排盘：四柱/藏干/十神/纳音/星运/空亡/神煞/合冲刑害/胎元/大运/流年，支持公历或农历生日、真太阳时、早晚子时流派、历史夏令时)、solar-terms(某年 24 节气时刻)、lunar(公历↔农历互转+当日干支)。脚本只做确定性计算，解读框架见 references/interpretation.md（十神/旺衰/用神/大运流年读法）。当用户要排八字、算四柱、看生辰八字/五行缺什么/大运流年、问农历生日对应公历、查某年节气或今日干支黄历时使用。
---

# BaZi 八字排盘

## 用途与分工

脚本负责**一切不能靠语言模型心算的确定性计算**：节气交接时刻（定气法，秒级）、
真太阳时（经度差+均时差）、四柱干支、藏干十神、大运起运、农历互转（含闰月）。
**解读是使用者（agent）的工作**：拿到 JSON/文本结果后，按
`references/interpretation.md` 的框架（定旺衰→取用神→看大运流年）生成命理分析。
不要自己心算干支或节气——模型心算这类历法几乎必错，一律跑脚本。

## 快速开始

从 skill 目录运行：

```bash
bash scripts/bazi chart --date 1990-05-17 --time 14:30 --gender m        # 基本排盘
bash scripts/bazi chart --date 1990-05-17 --time 14:30 --gender m \
  --lon 116.4 --liunian 2026:2031                                        # 真太阳时 + 流年
bash scripts/bazi chart --lunar 1990-4-23 --time 14:30 --gender f        # 农历生日直接排
bash scripts/bazi chart --date 1990-05-17                                # 时辰不详 → 排三柱
bash scripts/bazi chart --date ... --json                                # 结构化输出
bash scripts/bazi solar-terms 2026                                       # 全年节气时刻
bash scripts/bazi lunar 2026-07-06                                       # 公历→农历+当日干支
bash scripts/bazi lunar 1990-4-23 --reverse [--leap]                     # 农历→公历
```

解释器顺序：`BAZI_PYTHON` → `VIRTUAL_ENV/bin/python` → `PYTHON` → `python3`
（共享约定见仓库 `AGENTS.md`）。纯标准库、无网络、无浏览器。

## 排盘前先向用户确认

1. **公历还是农历**生日（农历要问是否闰月）；
2. **出生时间**（不知道就不给 `--time`，脚本会排三柱并说明影响）；
3. **性别**（决定大运顺逆；不给则男女两套都排）；
4. **出生地**（城市即可，换算成经度传 `--lon` 启用真太阳时；国外出生再给 `--tz`）。

## 规则与流派开关（默认为主流做法）

| 事项 | 默认 | 开关 |
|---|---|---|
| 年柱分界 | 立春交接时刻 | 无（子平标准） |
| 月柱分界 | 十二节交接时刻（定气） | 无 |
| 晚子时(23-24点) | 日柱算次日 | `--zishi split` 早晚子时派（日柱当天、时干按次日遁） |
| 真太阳时 | 给了 `--lon` 才启用 | `--no-tst` 关闭 |
| 时区/夏令时 | Asia/Shanghai（自动处理 1986–1991 中国夏令时） | `--tz` IANA 名或数字 |

年/月柱由出生**绝对时刻**与节气交接时刻比较得出，与真太阳时无关（真太阳时只影响日/时柱）；
出生时刻距立春/交节/子时边界很近时输出会带 ⚠ 警告，此时应提醒用户核实出生时间。

## 输出契约（--json）

顶层键：`input / true_solar_time / lunar / bazi / pillars / day_master / wuxing /
kongwang / taiyuan / shensha / interactions / jieqi / dayun / liunian / warnings`。
`pillars.{year,month,day,hour}` 各含 `ganzhi / stem_shishen / hidden[](藏干+十神) /
nayin / changsheng`；`dayun.{male,female}` 含 `direction / qiyun / list[](ganzhi,
stem_shishen, start_age, start_year)`；`wuxing.counts` 为八字表面五行计数（"缺X"即据此）、
`weighted_with_hidden` 为含藏干加权。文本输出为同一数据的人读版。

## 校验与精度

- 节气时刻与紫金山天文台发布值差在数秒内（ΔT 模型误差）；农历经 1990–2033
  已知春节/闰月全套锚点验证（含 2033 闰十一月边界案例）；日柱锚点 1900-01-01 甲戌、
  2000-01-07 甲子、1949-10-01 甲子。改动算法后用 `solar-terms 2024` 与这些锚点回归。
- 适用范围约 1700–2150 年；范围外 ΔT 外推误差增大。
- 大运起运的"约X岁"按周岁取整；各派折算取整略有差异，报告里不必精确到天。

## 解读

排盘结果本身不含吉凶判断。生成解读时读 `references/interpretation.md`；
表达上避免宿命论断言（"必然""注定"），用倾向性语言，重要决策建议仅供参考。
算法细节与流派依据见 `references/algorithms.md`。
