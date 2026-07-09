# anti-slop — 反 AI 味分级禁令

总测试：**"如果有人说这是 AI 做的，别人会立刻信吗？"** 分三级：Critical=一眼 AI；Major=设计师会皱眉；Minor=好与卓越的差距。`scripts/ui_taste check` 能机械抓到的条目已标 ⚙。扫描器对上下文相关条目（bounce 缓动、禁语、reduced-motion）刻意降一档报告——机器不知道场景，最终定级以本表为准。

## Critical（出现即重做）

- ⚙ 紫/蓝渐变、霓虹发光、AI 紫按钮（LILA 规则）。品牌本来就是紫除外——那就用得有纪律。
- 三张等宽"图标+标题+两行字"特性卡片横排（含 4/6 张变体）。改：2 栏错落、不对称网格、横向滚动。
- emoji 当功能图标；正文/标题/按钮里的 emoji（明确要玩趣风才允许，且克制）。
- 全大写标题/导航/按钮（唯一例外：11-13px 小标签 + 宽 tracking）。
- bounce/elastic 缓动用在功能性 UI 上。
- 暗底玻璃拟态+霓虹叠满全页。
- div 拼的假产品截图/假终端/假仪表盘（#1 AI 印记，判断层裁定）。用真截图、生成图、真组件迷你预览，或干脆不放。
- ⚙ 英文可见文案里的 em-dash（—）：标题/眉标/按钮/正文/引用/alt 全禁，用句号、逗号或改写（这是实测中最顽固的 AI 印记，按二值规则执行）。**中文破折号（——）是正常标点**，正常但克制地用。
- 纯文字页冒充极简：再克制的页面也要 2-3 张真图。文字+渐变斑点不是 hero，是占位符。

## Major（发布前必须清）

**布局节奏**
- ⚙ 眉标配给：小型全大写宽 tracking 眉标 ≤ ceil(节数/3)，连续两节不得都有（每节一个眉标是 AI 语法的第一大破绽）。多数时候答案是删掉——标题自己够用。
- 图文左右交替（zigzag）连续 ≤2 节；第 3 节必须换布局家族（整宽/纵排/bento/marquee）。
- 一个布局家族每页最多出现一次；8 节的页面至少 4 个家族。
- 分割式节头（左大标题+右上角浮着小段落）默认禁；标题下面垂直排正文（max-w 65ch）。
- hero 纪律：文字元素 ≤4（眉标或品牌条二选一 + 标题 ≤2 行 + 副文 ≤20 词 ≤4 行 + CTA 1 主 1 副）；顶部 padding ≤96px；logo 墙放 hero 下面不塞里面；禁 hero 内版本标（V0.6/BETA）、信任微条、定价预告。
- 居中 hero 只在"信息本身即设计"（宣言/发布）或低 VARIANCE 时用；居中且四周全对称=模板感，居中就要有不对称的支撑元素破一下。
- 编号眉标（01/02/03、00-INDEX）默认禁：编号只在内容**真的是序列**（真流程/时间线）时才成立。
- bento：格数=内容数（不留空格）；至少 2-3 格有真实视觉变化（图/纹理/色块），全白底纯文字格=无聊默认；禁 `01/4` 式分页标。
- 导航桌面端一行放下、高度 ≤80px；两行导航=broken。
- 卡片是懒人答案：仅当"抬升"传达真层级时用卡片，否则用间距/border-t/divide-y 分组；卡片套卡片永远是错的。
- 长列表（>5 条）不用默认 `<ul>`+每行 hairline：分组、卡格、tab/手风琴、横向 scroll-snap、marquee 里挑。spec 表每行 border-b 是最懒布局。
- 侧色条（border-left ≥3px 彩色）当强调，⚙ 全禁；用整边框、底色 tint、序号或什么都不加。
- ⚙ 渐变文字（bg-clip-text+渐变）当大标题；hero 指标配渐变强调。
- 时间序列用竖条图（应为线/面积图）；饼图 ≥5 片；雷达图 >3 个数据系列；纯红绿配对编码数据（色盲不可分，配形状/图标）；网络图/3D 图当主视图不配数据表后备；带满底轨道的进度条当对比图。

**装饰与元信息**
- 滚动提示（Scroll ↓ / Scroll to explore）；装饰性定位/天气/时间条（LIS 14:23 · 18°C）；版本页脚（v1.4.2 / Build 0048）；图片上叠 pill 标签（Plate · Brand）；装饰性摄影署名（Field study no. 12）；hero 底部装饰词条（BRAND. MOTION. SPATIAL.）；90° 竖排文字；纯装饰十字线/hairline 网格。全禁，除非 brief 真需要（真实体场馆/真分布式团队等）。
- 中点（·）每行 ≤1 个；彩色状态点默认为零，只在表达真实语义状态时用且每节 ≤1。
- 装饰性 blob/光晕/发光当 affordance；`repeating-linear-gradient` 斜条纹背景；`linear-gradient 1px` 装饰网格底（画布/地图/蓝图类才允许）。

**文案**
- 禁语：Elevate/Seamless/Unleash/Next-Gen/Revolutionize/Game-changer/Delve/"In the world of…"；中文对应"赋能/极致/重新定义/开启新篇章"同罪。写具体动词。
- ⚙ 假名假牌：John/Jane Doe、Acme/Nexus/SmartFlow/Quantumly、Lorem ipsum。用有语境的可信名字与品牌。
- 假精确数字（99.99%、50%、1234567）：要么来自真数据，要么标注 mock，要么用有机数值（47.2%）；三列相同结构的统计（99% 满意/∞ 扩展）禁。
- "Quietly trusted by"式做作社证头、"From the field/工坊手记"式表演型小标、模仿谦逊的 micro-meta 句。用平实功能性标签或不加。
- 引用 ≤3 行，署名=姓名+角色（不许只有"- Sarah"）；泛 CTA（Learn more/Click here）改具体动词短语；同一意图的 CTA 全页一个措辞（"联系我们"别再来一个"聊聊"）。
- 发布前**逐句重读所有可见字符串**：语法破碎、指代不明、AI 俏皮话、强行诗意，全部改成平实句子。

## Minor

数字列没上 tabular-nums；标题没 text-wrap: balance；直引号没用弯引号；品牌名没加 nbsp；证言配五星图形；纯黑 #000 当底色（用 zinc-950 档）；hover 放大 >1.02 的 CTA。

## 分模型已知缺陷（自查自己那款的）

- **Claude 系**：三种默认长相（奶油+衬线+陶土 / 近黑+酸绿 / 报纸 hairline），见 direction.md 第 6 节。
- **Codex/GPT 系**：ghost-card（1px 边框+≥16px 大模糊影叠加）；过度圆角（卡片 24-40px）；手绘感 SVG 插画（feTurbulence/doodle 类，宁可不放图）；斜条纹背景；装饰网格底。
- **Gemini 系**：图片 hover 缩放/位移（含 group-hover:scale 经由父级触发）——图片不是动作目标，要反馈就动卡片底色/边框/阴影，永不动图。
- **通用**：Inter+slate-900 三连；serif=创意的条件反射（Fraunces/Instrument Serif 两款 LLM 最爱 display 衬线默认禁，Instrument Serif 正在被用烂的路上）；已被用烂的 display 字体连带平替：Fraunces→Newsreader、Inter 当 display（它为 UI 小字设计，大字号匀质无表情）→Archivo、Space Grotesk→Schibsted Grotesk、Playfair Display→DM Serif Display；高端消费品的奶油底+黄铜/陶土强调+espresso 深字全家桶（OKLCH L .84-.97、C<.06、hue 40-100 整个暖纸带；token 叫 --cream/--sand/--paper 本身就是印记）→ 六族轮换：冷奢银灰铬 / 森绿+骨白+琥珀 / 真黑+暖棕 / 钴蓝+奶 / 陶锈+板灰 / 单色+一个饱和跳色；连续两个项目不用同族。

## 例外条款（让禁令可信的部分）

brief 明说要的就做，且做得有纪律：品牌是紫→紫得体系化；要 brutalist→零圆角全大写是该风格的语法；要玩趣→emoji 有节制地上。禁的是**无意识默认**，不是风格本身。风格包（brutalist/极简编辑部/暗色终端）各自的内部规则允许覆盖本表对应条目，但覆盖要点名说明。
反向收紧：**信任行业**（金融/医疗/政务/法务/保险）按更严一档执行——紫渐变这类 AI 印记即便品牌授权也慎用，实验风/brutalist 整体回避。
反例隔离：页面本身要展示坏设计时（反面教材/对比页），把反例关进虚线边框 + 「反例·不要这样做」角标的诚实容器——讲 slop 的页面不能自己变成 slop。
