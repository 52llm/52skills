# motion — 动效：加多少、怎么加

## 第一问：这个动效传达什么？

合法答案只有四种：层级（引导视线）/ 叙事（按序揭示）/ 反馈（确认操作）/ 状态转换（可视化变化）。答不出一句话就删。"看起来酷"不是答案；GSAP 装了不等于要处处用。

## 按场景的动效预算（硬上限）

| 场景 | 预算 |
| --- | --- |
| 落地页 hero | ≤3 个交错入场 + 1 个滚动联动 |
| 特性区 | 每卡 1 次 reveal，stagger 40ms，只播一次 |
| **仪表盘/产品 UI** | **只有微交互反馈，无入场动画**（除非用户明确要求） |
| 表单 | 每字段 1 个 focus 环过渡 |
| 模态 | 背板淡入 + 面板一次，无内部编排 |
| 设置/后台 | 零 |
| marquee | 全页 ≤1 个 |

"声明了动效就要动"：旋钮 >4 却整页静止 = broken；反之做不完就把旋钮降到 3 交付干净的静态页，永不交付半残动效（截断的 ScrollTrigger、跳帧入场）。

## 时长与缓动

- token 见 tokens.md：120/200/280/400ms + 4 条 bezier。感知带：<100ms 即时、100-250ms 过渡、250-400ms 明显、>400ms 郑重。交互反馈 ≤100-200ms。
- **退场 = 入场时长的 75%**（最重要的一条），同 ease-out 或更平尾。
- stagger 兄弟间 30-80ms（营销页可到 100-150ms）；永不全体同时蹦出，也永不 >80ms 拖沓（营销页除外）。
- 缓动禁令：功能 UI 禁 bounce/elastic（`cubic-bezier(0.68,-0.55,0.27,1.55)` 即红灯）；空间移动禁 linear；UI 禁 ease-in 入场；进出用不同缓动族=错。
- 弹簧四档（Motion）：Snappy `stiffness300/damping30` ｜ Smooth `150/20` ｜ Bouncy `100/10`（仅玩趣场景）｜ Heavy `60/20`。
- `:active` 微按压 `scale(0.98)` 或 `-translate-y-[1px]`。hover 放大：CTA ≤1.02，卡片 ≤1.05。

## 机制硬规则

- 只动 `transform/opacity`（filter/clip-path 在小面积且流畅时允许）；**永不**动 width/height/top/left/margin/padding/font-size。
- **禁 `transition: all`**——逐属性列出。
- **禁 `window.addEventListener('scroll')`** 与 scrollY 进 React state：用 Motion `useScroll`/ScrollTrigger/IntersectionObserver/CSS scroll-driven animations。
- 连续值（鼠标位置/滚动进度/磁性 hover）**禁 useState**：用 `useMotionValue`/`useTransform`（useState 每帧重渲染，移动端直接崩）。
- rAF 循环必须有停止条件；`repeat:-1` 的循环 tween 组件卸载时必须 kill（SPA 内存泄漏）；同一组件树**禁混** GSAP 与 Motion（抢帧）；Three.js 同理隔离在叶子组件。
- `transform-origin` 按运动语义设对；SVG 动 `<g>` 包裹层并配 `transform-box: fill-box; transform-origin: center`；动画可中断——中途响应用户输入，别锁死到播完。
- 逐词/逐字文字动画 >8 个词禁（劫持阅读节奏）。
- **reveal 安全**：内容可见性不许依赖 class 触发的过渡（隐藏 tab/无头渲染下过渡不触发→整节空白）。默认可见，动画只做增强。
- **禁图片 hover 缩放/位移**（含 group-hover 经父级触发）——图不是动作目标；要反馈动卡片的底色/边框/阴影。
- 循环动画离屏暂停；移动端粒子上限 桌面800/平板300/手机100；GSAP pin 在 <768px 禁用。

## reduced-motion（不可协商）

一切自动动效必须处理 `prefers-reduced-motion`：Motion 用 `useReducedMotion()` 降级为静态；CSS 在 reduce 下塌缩到 `0.01ms`。保留加载 spinner 与焦点反馈。无限循环/视差/滚动劫持/磁性物理在 reduce 下必须完全静止。

## 滚动编排骨架（营销页高旋钮时才用）

轻量优先——只是"入场即现"就用 Motion `whileInView`，别上 GSAP：

```tsx
<motion.li initial={reduce ? false : { opacity: 0, y: 24 }}
  whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.3 }}
  transition={{ duration: 0.6, delay: i * 0.06, ease: [0.22, 1, 0.36, 1] }} />
```

真要 pin/scrub（sticky 卡片堆、横向劫持）用 GSAP ScrollTrigger，两个已知翻车点都靠同一把钥匙：

- **`start: "top top"`**（不是 `top center`/`top 80%`——否则滚到一半就触发、用户看到半张卡）。
- sticky 堆：每张卡（除最后一张）`pin: true, pinSpacing: false`，前一张的缩小/降透明由**下一张**的 trigger scrub 驱动。
- 横向劫持：pin 外层 wrapper，`end: "+=${track.scrollWidth - innerWidth}"`，scrub 内层 track 的 x。
- 全部包 `gsap.context` 并在 cleanup `ctx.revert()`；`useReducedMotion` 时整段跳过。
- 整页包 `overflow-x-hidden` 防离屏动画拉出横向滚动条。

## 工具选型

CSS（hover/focus/简单过渡）→ Motion `motion/react`（UI 进出/layout/布局共享元素/`layoutId`）→ GSAP+ScrollTrigger（整页滚动叙事/pin/scrub 专用）→ Three.js/R3F（3D 画布，独立叶子）。从左往右升级，能用左边的不用右边的。
