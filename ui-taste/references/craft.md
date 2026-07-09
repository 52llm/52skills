# craft — 工程手艺硬规则（可用性、无障碍、鲁棒、性能）

主体融合 Vercel Web Interface Guidelines（在线最新版 `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md`，评审存量代码时可现拉对照）。以下为常驻精粹。

## 语义与无障碍

- 动作用 `<button>`、导航用 `<a>/<Link>`；禁 `<div onClick>`。语义标签（nav/main/article/table）先于 ARIA。
- 图标按钮必须 `aria-label`；装饰性图标 `aria-hidden`；图片必须 `alt`（装饰图 `alt=""`）。
- 异步反馈（toast/校验）加 `aria-live="polite"`；标题 h1-h6 层级连续；提供跳转正文的 skip link；锚点标题加 `scroll-margin-top`。
- 键盘可达：所有交互元素 Tab 可到；禁 `tabindex>0`；模态锁焦点、关闭时焦点还给触发元素。
- 颜色永不做唯一信号（涨跌/错误要有图标或文字伴随）。
- 永不禁用缩放：viewport 里禁 `user-scalable=no` / `maximum-scale=1`。

## 焦点

- 焦点必须可见：`focus-visible:ring-*`；**禁裸 `outline-none`**（无替代焦点样式）。
- 用 `:focus-visible` 不用 `:focus`（避免鼠标点击也出焦点环）；复合控件用 `:focus-within`。
- 一切可点元素要有 hover 反馈；hover/active/focus 的对比度按序**递增**（都要比静息态显眼）。

## 表单

- label 在输入框上方（`htmlFor` 关联或包裹）；**禁 placeholder 当 label**；helper 文案在 markup 里备位；错误内联在字段旁，提交时聚焦第一个错误。
- `autocomplete` + 语义化 `name` + 正确 `type/inputmode`（email/tel/url/number）；邮箱/代码/用户名 `spellCheck=false`。
- **禁 blockPaste**（onPaste+preventDefault）；提交按钮请求发出前保持可用、请求中转 spinner；未保存改动要拦截导航（beforeunload/路由守卫）。
- checkbox/radio 与 label 共享一个点击区（无死区）；破坏性操作必须确认框或可撤销窗口，永不立即执行。
- 移动端输入字号 ≥16px（防 iOS 聚焦缩放）。
- placeholder 以 `…` 结尾并给示例格式（`name@example.com…`）；非认证字段 `autocomplete="off"` 防密码管理器误弹。

## 排印微观（AI 最常漏的一层）

- `…` 不用 `...`；弯引号 " " 不用直引号；`10 MB`、`⌘ K`、品牌名内用 `&nbsp;` 防折行；加载文案以 `…` 结尾（"Saving…"）。
- 数字列 `tabular-nums`；标题 `text-wrap: balance` 防孤字，长段 `text-pretty`。
- 计数用数字（"8 次部署"不写"八次"）；英文空间紧张处可用 `&` 代 and。

## 内容鲁棒

- 文本容器都要处理长内容：`truncate`/`line-clamp-*`/`break-words`；flex 子元素配 `min-w-0` 才能截断。
- 空字符串/空数组不渲染破 UI；用户生成内容按"短/普通/超长"三档设想（用 120 字符的名字测试）。
- 缺数据显示 `—`（一个字符），永不 `N/A`/`null`/`0` 冒充。

## 图片与资产

- `<img>` 必须显式 `width/height`（防 CLS）；首屏关键图 `priority/fetchpriority=high`，折下 `loading="lazy"`。
- 资产优先级：环境里有图像生成工具就**先生成**分节资产（按节的比例出图）→ 没有就 `https://picsum.photos/seed/{语义化seed}/{w}/{h}` 或 brief 提供的真图 → 都不行就留显式占位注释并在结尾列清单告诉用户，**不许**用手绘 SVG 插画或 div 假截图凑数。
- logo 墙用真 SVG（`https://cdn.simpleicons.org/{slug}` 或 simple-icons 包）；虚构品牌就配一个内联 SVG 字标；logo 墙只放 logo，不在下面印行业注释。
- 图标：一个项目一族（Phosphor / Radix / Tabler / Heroicons 优先；lucide 仅显式要求或项目已有）；全局统一 `strokeWidth`（1.5 或 2）；**禁手绘 icon path**。

## 性能

- 大列表（>50 行）虚拟化（virtua / `content-visibility: auto`）；渲染路径里禁 layout 读取（getBoundingClientRect/offsetHeight）；DOM 读写分批。
- 输入框优先非受控；受控输入每击键成本要低。
- CDN 域 `<link rel="preconnect">`；关键字体 `<link rel="preload" as="font">` + `font-display: swap`；Next 用 `next/font`，生产环境禁 Google Fonts `<link>`。
- 颗粒/噪点滤镜只放 `fixed inset-0 pointer-events-none` 伪元素，永不放滚动容器；`backdrop-blur` 只用于 fixed/sticky 元素。
- 目标：LCP <2.5s、INP <200ms、CLS <0.1。

## 布局与视口

- 全屏区块用 `min-h-[100dvh]`，**禁 `h-screen`**（iOS 地址栏跳动）；fixed 元素处理 `env(safe-area-inset-*)`。
- 复杂多列用 CSS Grid，禁 flex 百分比算术（`w-[calc(33%-1rem)]`）；免断点响应网格 `repeat(auto-fit, minmax(280px, 1fr))`；一维 flex、二维 grid。
- 页面容器 `max-w-[1400px] mx-auto` 或 `max-w-7xl`；320px 宽下无横向滚动；每个多列布局在同组件里显式声明 <768px 的塌缩。
- dropdown 放在 `overflow:hidden/auto` 容器里会被裁：用 popover API / `position:fixed` / portal。
- 触控：`touch-action: manipulation`；`-webkit-tap-highlight-color` 有意设置；模态/抽屉 `overscroll-behavior: contain`；拖拽时禁文本选择、拖拽中的元素加 `inert`；`autoFocus` 仅桌面单主输入框场景。

## 导航与状态

- URL 反映状态：筛选/tab/分页/展开面板进 query 参数（可深链、可分享、Cmd+点击可新开）。
- 当前页在导航里有视觉标识；每页有回路（不留死端）；按钮链接到 `#` = 假链接，禁。

## 暗色与主题

- 暗色页在 `<html>` 设 `color-scheme: dark`（修正滚动条/原生控件）；`<meta name="theme-color">` 跟页面底色；原生 `<select>` 显式 bg/color（Windows 暗色）。
- 双模式从第一天设计，两种模式都亲眼看过再交付；策略二选一（Tailwind `dark:` 或 CSS 变量语义 token），全项目统一。

## i18n 与水合

- 日期/数字/货币用 `Intl.*`，禁手写格式；语言检测用 Accept-Language，不用 IP；品牌名/代码 token 包 `translate="no"`。
- 受控 input 有 `value` 必有 `onChange`（否则用 `defaultValue`）；日期时间渲染防服务端/客户端不一致；德语等膨胀语言按 1.3× 文本余量设计。

## 依赖与工程

- import 前先查 package.json，缺就先输出安装命令；Tailwind 看清 v3/v4（v4 用 `@tailwindcss/postcss`）。
- Next.js：全局状态只在 Client Component；动效/滚动监听组件做成 `'use client'` 叶子，Server Component 只渲染静态骨架。
- `useEffect` 动画必须有清理函数；能用渲染逻辑表达的不进 useEffect。
- CSS 选择器优先级互抵是高频翻车（`.section` 类选择器与 `.cta` 元素级选择器互相抵消节距）：区块间距只从一个方向、一套选择器给（统一 margin-top 或统一 padding-top），别两套都写。
- 布局测量（getBoundingClientRect/offsetWidth 驱动的 masonry/下划线对齐/标记定位）必须等 `document.fonts.ready` + 一帧 rAF——否则量的是回退字体的宽度，webfont 换入后永久错位。absolute 子元素记得给父级 `position: relative`。
- 交付前补：favicon、`<title>/description/og:image`、自定义 404、页脚法务链接。
