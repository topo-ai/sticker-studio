---
name: sticker-studio
description: 基于人物、宠物或原创形象设计静态与动态表情套系，完成角色设定、主题策划、动作分镜、参考图生成、切帧编码、质量验收、微信/抖音发布物料及授权范围内的投稿发布。适用于IP表情包、GIF贴纸和表情系列生产，不用于仅从表情库选图回复。
metadata:
  version: 2.2.5
---

# 表情包工作室

以项目文件为生产依据，交付独立可用的表情文件、可追溯的源素材、质检结果及对应发布材料。拼图、提示词、静态帧表都不能代替动态成品。创作、编码、平台适配与实际发布是不同阶段，各自有通过条件。

支持的投稿平台：微信与抖音。平台材料分别规划，素材规格与授权条款分别核验。

## 工作模式与加载路由

先识别当前任务，只加载所需模块；已有素材从对应阶段续作，按用户指定的任务范围执行。

| 阶段 | 必读 | 输出 / 通过条件 |
|---|---|---|
| 需求与能力盘点 | [需求与路由](references/workflows/01-intake.md) | project.json；知道角色、主题、静/动态、用途、可用工具 |
| 角色与画风 | [角色设计](references/workflows/02-character.md)、[风格目录](references/styles/catalog.md) | character.json + 选定母版；识别点可复用 |
| 套系与文案 | [套系策划](references/workflows/03-pack.md)、[文字设计](references/styles/typography.md) | pack.json；聊天意图、套内排版模式、字体与文字动作方案 |
| 提示词与动画 | [动作生产](references/workflows/04-production.md)、[动作库](references/motion/library.md) | 提示词、逐帧分镜、样张及帧契约 |
| 媒体处理 | [媒体管线](references/technical/media-pipeline.md) | 对齐帧、GIF/WebP/PNG、接触表与参数报告 |
| 质检与返工 | [验收](references/workflows/05-quality.md)、[故障诊断](references/technical/failure-recovery.md) | 文件通过 + 与文件哈希绑定的视觉审阅 |
| 平台适配 | [平台入口](references/platforms/index.md) → 指定平台文档 | 当前入口规格证据、对应文件、投稿文案 |
| 交付与发布 | [交付发布](references/workflows/06-delivery-publishing.md) | 完整输出文件夹、提交回执；不把待审核称为上架 |
| 续作与复盘 | [项目契约](references/technical/contracts.md) | 精确失效范围、版本和下一期建议 |

各层职责与验收边界见 [系统架构](references/technical/architecture.md)。需要验收整个 Skill 时读 [行为评估](evals/scenarios.md)，运行本地测试，不把结构校验当效果验证。

## 必须保持的生产约束

1. **用户约束优先。** 既有选择跨轮保留，明确指定的输出形式优先于默认值。素材制作、准备投稿、发布到账号是不同授权范围。缺主题等关键条件时集中问一次，其余可独立准备。
2. **母版先于批量。** 保存参考角色的识别点与母版文件，再做一个复杂动作样张并完成端到端编码检查。样张未过检不开始整套；用户已要求整套时内部过检后可继续，不强制逐张确认。
3. **真实角色表演。** 动态人物/吉祥物要有合理姿势或面部变化；整张图平移、旋转不能冒充挥手、点头。照片/文字动效只在用户选择该效果时使用并如实描述。不能自动将动态任务降成静态。
4. **构图安全与不漂移。** 帧表只是候选输入；先检查格数、边界和真实 Alpha。整个动作使用同一缩放与画布坐标，不逐帧裁到包围盒再放大。保留动作位移与重心变化。
5. **工具能力不编造。** 参考图、透明背景、视频生成、插帧、种子、并发和发布能力都要检查真实接口。缺视频模型时使用可用动作帧路线或提供接力包，不声称已生成视频。生成图片/编辑遵循当前可用 imagegen Skill，不擅自换 CLI/API。
6. **生成可回溯。** 提示词先落盘，记录输入引用、输出路径、版本和失败原因；失败只重做对应项。每批默认不超过 2 条动画，先预估调用量；用户对规模已有要求时按要求执行。
7. **质量不可跳过。** 参数检查、动作观感和平台适配分别验收。脚本 PASS 不证明角色一致或动作自然；没完整播放时写未验证。最多两轮修复仍失败就改路线或交付失败清单，不无限生成。
8. **发布必须有证据。** 具体平台规则记录来源、入口、日期与账号类型。未知参数为 null，不能当作无限制。发布需观察回执；超时先查已提交记录，不盲目重试。

## 默认角色还原准则

用户提供人物、宠物或原创角色参考时，除非明确要求大幅改造，默认将角色复刻程度（身份还原度）作为核心验收标准。风格化不等于换角色：优先保留原参考的脸型、五官比例与位置、眼睛颜色、毛色或发型、轮廓及标志配饰，不为了可爱、画风或动作方便而泛化成普通同类角色。还原度指“看得出是同一个角色”，不要求照搬写实材质或固定姿势。

制作前从原参考提取并记录可见识别点；用户选定风格后，原参考负责身份，风格母版负责绘制方式；用户认可长相不等于允许改变已选画风，后续明确选定的版本优先；用户认可长相不等于允许改变已选画风，后续明确选定的版本优先，每条生成都回到这两类依据，不仅沿用上一张生成图。静态、动态各帧及夸张表情均检查角色辨识度；出现脸型、五官或关键特征漂移时返工，不将其当成风格差异放行。用户明确指定的变形、简化或重新设计要求优先，仅在该范围内放宽。

## 默认交付形式

默认交付整理好的输出文件夹，不自动生成 ZIP 或其他压缩包。只有用户明确要求打包时才额外生成压缩包；文件夹交付仍须完成文件检查与视觉验收。

## 交付命名与含义词

表情成品统一使用“编号-中文表情名.扩展名”，例如 `01-收到.gif`、`01-收到.webp`；同一条表情跨格式、尺寸保持相同编号与名称，尺寸和平台通过目录区分。每套同时准备逐张含义词，并与文件名对应。详细规则见 [交付发布](references/workflows/06-delivery-publishing.md)。

## 内置工具入口

先运行 doctor。以下命令以 Skill 目录为工作目录；调用时把 PROJECT 替换为项目绝对路径。具体参数与契约见技术文档。

```powershell
python scripts/studio.py doctor
python scripts/studio.py init --project PROJECT --name office-reactions --theme 打工仔 --mode animated --count 6 --style chibi-ink
python scripts/studio.py compile --project PROJECT
python scripts/prepare_frames.py --sheet SHEET.png --cols 4 --rows 2 --size 512 --out PROJECT/frames/01/v001
python scripts/sticker_media.py assemble --frames PROJECT/frames/01/v001/frames --output PROJECT/exports/generic/01.gif --frame-ms 160
python scripts/sticker_media.py assemble --frames PROJECT/frames/01/v001/frames --output PROJECT/exports/generic/01.webp --frame-ms 160
python scripts/studio.py verify --project PROJECT
# 仅用户明确要求压缩包时运行：
python scripts/studio.py package --project PROJECT --output DELIVERY.zip
```

init 仅创建可填写的真实项目结构，不生成表情。compile 需要已填写角色和动作计划，不自动编故事。prepare_frames 只做媒体技术处理；不替用户艺术重绘。package 重新检查文件与视觉审阅的哈希，拒绝不完整或过期审阅；它不会发帖，也不会认证平台规则。

## 完整套系默认交付

用户要求制作整套成品且未另行缩小范围时，默认交付独立表情文件、含义词、整套预览，以及头像、专辑封面、横幅、聊天图标、赞赏引导图与引导语、赞赏致谢图与感谢文案。所有配套物料沿用同一已确认母版，分别按用途设计与导出；详见[完整套系清单](references/workflows/06-delivery-publishing.md)。仅选风格、看样张或修单张时不自动扩成全套；制作物料不等于授权开启赞赏、上传或发布。

## 完成状态

每条表情：planned → designed → frames_ready → encoded → reviewed。每个目标平台独立记录 prepared / ready_to_submit / submitted / live / needs_revision / blocked。状态推进必须有对应产物；修改母版、动作、文字或输出文件时使相关审阅失效。

最终答复给代表动态预览、输出文件夹与独立文件链接（仅用户明确要求时提供 ZIP）、已完成数量和未完成事项。用户只要设计时不要偷偷生产；用户要整套时不要只给策划。禁止以“大体完成”掩盖缺文件、假透明或单帧 GIF。
