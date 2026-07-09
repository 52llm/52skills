---
name: ui-taste
description: 前端页面的审美与工艺融合技能（反 AI 味）。融合 taste-skill(基准)/ui-craft/impeccable/Vercel WIG/Anthropic frontend-design/ui-design-brain 等十余个项目之所长（清单见 references/sources.md）：设计读法与三旋钮、签名赌注、数值 token 基准（间距/字阶/圆角/阴影/时长/缓动）、分级反 AI 味禁令、组件数值规范、状态八格、截图自评与完工十关，附机械检查脚本（scripts/ui_taste check 静态扫描 AI 味 + contrast 对比度计算）。当用户要写落地页/作品集/官网/仪表盘/产品 UI/组件，抱怨页面"太丑""AI 味""没有高级感"，要求"设计好看点""美化""打磨"，要做设计评审/打分，或要改版美化存量页面、从参考站取设计 token 时使用。Anti-slop frontend design: direction, numeric tokens, graded bans, component specs, screenshot self-critique, mechanical tell-scanner.
---

# ui-taste — 让 AI 写的前端不像 AI 写的

判断层（本文与 references，管方向与品味）+ 机械层（`scripts/ui_taste`，管可确定判定的 AI 味与对比度）分离。
**总测试：如果有人说"这是 AI 做的"，别人会立刻相信吗？会 → 重来。**

## 场景分流（先认场景，再定规则）

| 场景 | 变化/动效/密度 旋钮默认(1-10) | 侧重 references |
| --- | --- | --- |
| 落地页/官网/营销页 | 7 / 6 / 4 | direction, anti-slop, motion |
| 作品集/工作室 | 8 / 7 / 3 | direction, anti-slop |
| 编辑部/博客/长文 | 6 / 4 / 3 | direction, tokens(字阶) |
| 产品 UI/工具/表单/管理后台 | 4 / 2 / 5 | components, craft, tokens |
| 仪表盘/数据密集页 | 4 / 2 / 9 | components, tokens(密集变体) |
| 存量改版 | 沿用现状读数 | redesign |

场景按**页面**认不按项目认：管理系统整体走产品 UI 档，但其中的大表格列表页/报表页/监控页单独按仪表盘档（密集间距变体+语义色板）；一个官网的博客区按编辑部档。
三旋钮：DESIGN_VARIANCE（对称↔失衡）/ MOTION_INTENSITY（静↔影院）/ VISUAL_DENSITY（画廊↔驾驶舱）。
用户的氛围词覆盖默认（"Linear 风/极简"→5/3/3；"Awwwards/实验"→9/8/3；"政务/信任优先"→3/2/5）。
**产品 UI 与营销页规则不同**：产品 UI 默认不加动效（交互反馈 ≤200ms 除外）、中性字体（Inter 可以）、语义色板；营销页按旋钮上动效、字体要有性格。两套别互相污染。

## 流程（五步）

1. **设计读法**：动手前输出一行——"读作：<场景> for <受众>，<氛围>语言，倾向 <设计系统或美学家族>；旋钮 V/M/D"。歧义大时只问**一个**问题；能推断就不问。
2. **定方向**（读 `references/direction.md`）：出 token 计划（4-6 个具名色 hex/OKLCH + 2-3 个字体角色 + 布局概念 + **签名赌注**——本页唯一的记忆点）。自检：换一个同类品牌，我还会出同样的方案吗？会 = 那是条件反射不是设计，改掉再动工。
3. **建**：按 `references/tokens.md`（数值基准）+ `craft.md`（工程手艺）+ `components.md`（组件规范）+ `motion.md`（动效）写码。真实内容优先：真图（生成/picsum seed/真 logo），真文案（禁 Lorem/Acme/Jane Doe），状态全周期。签名赌注在第一遍就建，不留给"以后润色"。
4. **机械检查**：`bash scripts/ui_taste check <文件/目录>` 扫 AI 味硬信号；配色定稿前 `bash scripts/ui_taste contrast <前景> <背景>` 验对比度。
5. **自评**（读 `references/review.md`）：能截图就截图三视口自评（没有浏览器工具就明说没看过渲染效果），过完工十关，给 READY/NOT READY/BLOCKED 结论。

## 核心纪律（不读任何 reference 也要遵守）

- **一处大胆**：每个页面恰好一个签名元素，其余保持安静克制。两个记忆点=零个。
- **层级 1.5×**：相邻层级在字号/字重/对比度/面积至少一项上差 ≥1.5 倍。眯眼测试：视线必须先落在唯一一处。
- **90% 中性 + 一个强调色**：首屏强调色 ≤3-5 处（CTA、一个关键数字、激活态）。默认别选蓝，更别选紫。
- **禁 AI 三件套**：紫/蓝渐变发光、三张等宽图标卡片、居中 hero + 暗色网格背景。全禁令见 `references/anti-slop.md`。
- **排版**：视口内 ≤3 个字重；正文行长 45-75ch（中文 36em）、行高 1.5-1.65（中文 1.7-1.85）；hero 标题 ≤2 行（4 行=字号错误）；数字列 `tabular-nums`。中文页另过 tokens.md「中文排印」专章（fallback 链顺序/无斜体/避头尾/子集化）。
- **状态全周期**：loading（骨架屏匹配最终布局）/ empty（给下一步动作）/ error（原因+恢复路径）。静态成功态 ≠ 完成。
- **动效**：只动 `transform/opacity`；退场时长 = 入场的 75%；`prefers-reduced-motion` 必须处理；禁 `transition: all`、禁 `window.addEventListener('scroll')`。
- **对比度**：正文 4.5:1、大字 3:1（含按钮文字、placeholder）。"浅灰显高级"是 AI 页面难读的头号原因。
- **无障碍地板**：图标按钮带 `aria-label`；触达 ≥44px；焦点可见（禁裸 `outline-none`）；真按钮真链接（禁 div onClick）。
- **一致性锁**：一个页面一个主题（明/暗不中途翻转）、一个强调色、一套圆角制、一族图标（statiky `strokeWidth`）。
- **先查再引**：import 任何库前先看 package.json；缺就先给安装命令。

## 机械层（scripts/ui_taste）

```bash
bash scripts/ui_taste check src/            # 静态扫描 AI 味硬信号（em-dash/紫渐变/transition:all/h-screen/无alt…）
bash scripts/ui_taste check src/ --json     # 结构化输出；有 critical 时退出码 1（可挂 CI）
bash scripts/ui_taste contrast "#666" "#fff"  # WCAG 对比度与 AA/AAA 判定
```

扫描是**启发式**：命中是强信号，未命中不等于干净；中文正文的破折号（——）属正常标点，按提示人工裁决。
解释器顺序：`UI_TASTE_PYTHON` → `VIRTUAL_ENV/bin/python` → `PYTHON` → `python3`（共享约定见仓库 `AGENTS.md`）。纯标准库。

## 路由表

| 任务 | 读 |
| --- | --- |
| 新页面定方向/选风格/选设计系统 | references/direction.md |
| 建立/审计设计 token | references/tokens.md |
| 避免与排查 AI 味 | references/anti-slop.md |
| 无障碍/表单/排印细节/性能 | references/craft.md |
| 动效怎么加、加多少 | references/motion.md |
| 具体组件怎么做对 | references/components.md |
| 自评/评审/打分/收工判定 | references/review.md |
| 改造存量页面/取参考站 token | references/redesign.md |
| 各规则出处与取舍 | references/sources.md |

与同仓库技能的关系：本 skill 是**领域规范层**，只管前端设计；工作纪律归 careful、工程流水线归 forge（forge-build 执行前端任务时把本 skill 当 standards 用）。规则冲突时以用户明示 > 项目既有设计系统 > 本 skill 默认。
