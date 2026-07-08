# sources — 出处与取舍（2026-07 融合，素材在 ~/git/github/design/）

| 来源 | 权重 | 取了什么 | 没取什么（理由） |
| --- | --- | --- | --- |
| **taste-skill**（Leonxlnx，基准） | ★★★ | 设计读法与一行 Design Read、三旋钮与推断表、设计系统映射与诚实规则、反默认纪律、布局硬规则（hero 纪律/眉标配给/zigzag 上限/布局家族）、AI 印记大清单（9.A-G 含 em-dash 二值禁令）、图片资产优先级、GSAP 双骨架与禁止模式、真太阳内容规则（真名/真数/真图）、改版协议、Pre-Flight 思想 | v1（被 v2 取代）；Block Library（未建成）；imagegen/stitch/brandkit 的图像生成机制（非代码路径）；风格变体全文（取其结构规则并入例外条款） |
| **ui-craft**（评分与数值最全） | ★★★ | 8 级间距尺与不变量、字阶/tracking/行高（含 CJK 1.7-1.85）、圆角随元素、分层阴影、z-index 语义梯、时长/缓动 token 与退场 75%、层级 1.5× 与眯眼测试、强调色 3-5 处预算、APCA 数值、4 套主题包与强调色轮换池、签名赌注机制、状态八格与契约、完工十关、启发式打分公式与影响标签、BLOCKED/NOT READY/READY 判定、三视口截图强制、机械分/判断分永不平均 | 25 个 slash 命令的编排壳（单 skill 内收敛为流程五步）；CLI/MCP/CI/安装器（分发管道）；UICraftScore 权重（依赖其扫描器）；.ui-craft/ 持久产物目录（我们有 forge） |
| **Vercel web-interface-guidelines**（agent-skills） | ★★★ | craft.md 的主体：a11y/焦点/表单/排印微观/内容鲁棒/图片/性能/URL 状态/触控/安全区/暗色/i18n/水合 全部机械规则 + file:line 简洁评审格式；在线源地址保留供现拉最新版 | 薄壳 skill 本身（其机制=现场 WebFetch；我们默认离线，改为常驻精粹+可选现拉） |
| **impeccable** | ★★☆ | OKLCH 反奶油带（含 token 名即印记）、色彩策略四档、明暗主题物理场景法、二阶反射检查、绝对禁令（侧色条/渐变文字/hero-metric/等卡网格）、分模型缺陷清单（codex/gemini）、hero clamp ≤6rem 与 tracking ≥-0.04em、reveal 安全规则、字体对比轴配对 | 浏览器扩展/hooks/live 变体模式（产品化机制）；PRODUCT.md/DESIGN.md 双档（并入 direction 的 token 计划）；STYLE.md 写作规范（careful write.md 已覆盖同类） |
| **Anthropic frontend-design** | ★★☆ | hero 即论点、结构即信息（编号只给真序列）、签名元素与"大胆花在一处"、Chanel 减一件、三种 AI 默认长相自省、两遍流程（token 计划→换牌自检→再写码）、UX 文案纪律（动词按钮/同名贯穿/错误不道歉） | web-artifacts-builder（claude.ai 工件工具链）；theme-factory 的 PDF 展示流（取其"色板+角色映射"思想入 tokens） |
| **ui-design-brain** | ★★☆ | components.md 的组件数值规范精粹（60 组件中按"模型最易做错"取 ~20）+ 组件反模式 + 8px 网格 | 五方向预设（与 direction 组合引擎重叠）；组件全文（1262 行，按需回读原库） |
| **ui-skills**（ibelick） | ★★ | 产品 UI 场景的 MUST/NEVER：默认不加动效、反馈 ≤200ms、text-balance/pretty、tabular-nums、size-*、z-index 定标、Base UI/React Aria 基元优先、AlertDialog 管破坏性操作 | root 路由器与 CLI（我们用路由表）；fixing-metadata（并入 craft 交付清单一行） |
| **minimax-skills / frontend-dev** | ★★ | 动效工具选型矩阵、弹簧四档参数、GPU 属性白名单、移动端粒子上限、GSAP/Motion 混用禁令、"grep 输出查 unsplash/placeholder"式质量门思想 | MiniMax API 资产管线（厂商锁定）；p5 生成艺术；文案 AIDA 模板（过营销化，取 CTA 动词规则） |
| **redesign-skill**（taste-skill 内） | ★★ | 改版审计清单的骨架、修复优先序（字体→色→交互态→布局→组件→状态）、按钮底对齐/基线对齐这类对照细节 | 与主文件重复的禁令（已合并去重） |
| **extract-design-system** | ★ | 参考站取 token 的 CLI 流程与"不可信第三方输入"纪律、手工兜底清单 | CLI 本体（npx 现调，不内置） |
| **image-to-code / imagegen-frontend-web** | ★ | 对图实现的忠实纪律（不简化回模板/不压缩留白）、组合变化引擎目录、渐变纪律（允许的低饱和同相 vs 禁的紫蓝橙粉） | 逐节出图机制、图片数量学（图像生成路径专用） |

## 冲突裁决记录

- **Inter**：taste 默认禁 vs ui-skills 不禁 → 场景分流：营销/展示页换性格字体；产品 UI 中性字体合法（别成三连默认）。
- **动效**：taste 营销页按旋钮上 vs ui-skills"没要求不加" → 按场景预算表（motion.md），产品 UI 从 ui-skills、营销页从 taste。
- **居中 hero**：taste 高变化时禁 vs gpt-taste 偏爱影院居中 vs ui-craft 实测"成熟 SaaS 多居中" → 采 ui-craft 调和：居中合法，但要有不对称支撑元素破格；禁的是全对称模板感。
- **serif**：taste 严禁默认 serif（Fraunces/Instrument Serif 点名禁）vs minimalist 变体用 Instrument Serif → 按 taste（用户指定权重高），风格包覆盖需点名声明。
- **em-dash**：taste 全域二值禁 → 保留英文可见文案零容忍；中文破折号（——）为正常标点不禁，克制即可。
- **眉标**：taste 机械配给（≤ceil(节数/3)）vs impeccable"换一种节奏" → 取 taste 的可机检版本为门，impeccable 的"删掉最好"为首选修法。
- **60-30-10**：ui-craft 明确指出该法则属于室内/营销，产品 UI 用 90%+中性 → 两者按场景各归其位。

维护约定：新增规则先问"对应哪个真实观察到的翻车"；Vercel WIG 在线源与各上游仓库演进后，可重跑对照更新本 skill（更新时同步本表）。
