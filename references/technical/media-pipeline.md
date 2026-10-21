# 媒体处理契约与命令

## 依赖与边界

Python + Pillow 为本地必需；视频抽帧另外需要 FFmpeg/FFprobe。没有云端生成调用封装，Agent 使用当前真实工具。所有脚本默认拒绝覆盖。prepare 处理媒体裁切/规格，不用来代替图像模型重绘或文字修图。

## 帧表准备

```powershell
python scripts/prepare_frames.py --sheet SHEET.png --cols 4 --rows 2 --size 512 --out PROJECT/frames/01/v001
```

要求网格数值由实际候选检查确定；不会假装自动找格。尺寸不能整除时共享切线取整，每格最多补一像素并输出告警，不对每格分别缩放。真实 Alpha 优先，格内前景非空且不碰边。所有格用同一 union crop 和 scale，保留姿态相对位移。角色在格内漂移先回到生成端检查，不能逐帧强行居中纠正。

有明确纯色幕且技术抠像路线适用时加 `--screen FF00FF`，只删与外边缘连通的近似幕色。它保留封闭区域内同色细节，但无法保住与外幕连通的同色衣服；必须选不撞前景的幕色并视觉检查。假棋盘、渐变、场景图不猜抠；失败就重新生成或用明确的分割工具。

产物：固定画布PNG、frames.json、contact-light.jpg、contact-dark.jpg。唯一帧数仅辅助判断。prepare 不插帧、不改变角色动作、不自动写审阅通过。

等分切线碰到前景时，先检查真正的透明间隔。`recover_grid.py --sheet SOURCE --cols 4 --rows 4 --out RECOVERED.png` 只在邻近名义切线存在连续透明带时调整分隔；各格仍保留相对于名义格原点的位置，共同补透明边，不按各自包围盒居中或拉伸。重排后再 prepare。找不到透明带、画面内容相互重叠或源图外边真实裁断则拒绝。`--allow-bottom-viewport` 仅用于已视觉确认的半身腰部取景，不能放行手、道具或全身脚部截断。

几何测量使用 Alpha≥16 的前景，避免几乎不可见的背景噪点影响边界判断；裁切范围内保留原始 Alpha。测量阈值记录在 frames.json，不代替浅深背景的边缘检查。

## 编码

```powershell
python scripts/sticker_media.py assemble --frames PROJECT/frames/01/v001/frames --output PROJECT/exports/generic/01.gif --durations 200,140,140,180,300,140,140,200
python scripts/sticker_media.py assemble --frames PROJECT/frames/01/v001/frames --output PROJECT/exports/generic/01.webp --durations 200,140,140,180,300,140,140,200
python scripts/sticker_media.py inspect PROJECT/exports/generic/01.gif --animated --loop --transparent --size 512x512
```

512 是通用母版建议，不是平台规格。GIF 二值透明且量化色彩；WebP保留柔和 Alpha。编码后检查实际透明、前景、时长与循环。若编码器合并相邻同图，时长应保留。不能只重命名扩展名。

GIF 可加 `--colors 64` 或 `--colors 32` 控制调色板以降低体积。低色数采用无抖动量化；检查皮肤、渐变和文字边缘后再选择，不能以体积达标代替观感验收。

局部运动可试 `--delta`：首次完整画布后，仅重绘变化区域。首帧停留须至少40ms，以两次相同姿势拆分原停留完成背景初始化，不能插入空白初始化帧。编码会增加一个存储帧但不增加动作姿势或总时长；脚本将每个解码帧与同调色板完整帧比对，发现残留手臂、静止区丢失或透明错误即失败。此模式使用当前 Pillow 编码接口，升级依赖后须重跑相应回归测试。

## 视频抽帧与展示版

```powershell
python scripts/extract_video.py --video SOURCE.mp4 --start 1 --duration 2 --fps 10 --out PROJECT/video-frames/01/v001
```

此命令不抠像、不自动切九格、不生成视频。透明母版或合法纯幕视频仍需明确的抠像流程。网格视频要逐帧核实格子位置，当前工具不做自动跟踪；宁可单条制作，不承诺未实现的批量拆网格。

将实际通过的PNG序列合成社媒MP4时用 FFmpeg 显式背景与偶数尺寸，例如由 Agent 构造 subprocess 参数数组；注意可变帧时长不能用固定fps错误替代。没有生成 MP4 就不列为交付文件。

## 完整包

把最终文件相对路径填入 pack.files，运行 verify。视觉检查后填写 actual hash 与证据，运行 package。profile-generic.json 中 null 表示未约束；平台阈值不得在这里偷标官方，单独 evidence 核实。已有错误报告不覆盖，保存新文件。
