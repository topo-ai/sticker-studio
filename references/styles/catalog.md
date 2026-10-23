# 风格目录与选择规则

这是可扩展的常用风格库，不是图像工具全部能力的穷尽清单，也不保证每种风格都已通过动态验证。用户可提供新参考，先拆解线条、色彩、质感、比例与动作表达，再新增合适的 preset；不受本表限制。

优先级：用户当前明确要求 > 用户已确认母版 > 项目选择 > 推荐。原参考负责身份，风格母版负责绘制方式。用户认可长相不代表同意换画风。编号只在当次选风格图里有效：历史“09”“15”不是跨项目的永久ID，应同时记录名称、preset ID与选定母版。

## 状态与使用方式

- 已制作动态套系：有本会话实际产物，不意味着所有动作都已验收；查看对应项目的具体质量记录。
- 已有风格预览：有静态示例，动态连续性仍需样张验证。
- 本次参考已识别：已分析用户截图，不声称已经复刻或生成。
- 可探索：可走当前图像生成路线尝试；先出母版与动作样张，不直接承诺稳定整套。
- 每个下列ID都有独立 `presets/ID.md`，可直接用于 `studio.py init --style ID` 与 compile。不用相近的旧ID冒充新风格。

展示选项时按用户主题挑选少量有差异的候选，不一口气强制生成整个库。用户只问风格或要求维护Skill时不自动扩大为新套系。参考截图用于抽取视觉语法，不把其中其他角色的毛色、眼色、饰物、文字、水印或界面当作用户角色设定；不去水印复用原图作为自己的成品。

## 原有基础预设

| ID | 风格 | 状态 | 入口 |
|---|---|---|---|
| handdrawn-soft | 柔软手绘 | 原有预设，具体产物另查 | [规则](presets/handdrawn-soft.md) |
| chibi-ink | Q版墨线 | 原有预设，具体产物另查 | [规则](presets/chibi-ink.md) |
| flat-bold | 醒目扁平 | 原有预设，具体产物另查 | [规则](presets/flat-bold.md) |
| clay-toy | 软陶玩偶 | 原有预设，具体产物另查 | [规则](presets/clay-toy.md) |

## 手绘与卡通

| ID | 风格 | 证据状态 | 入口 |
|---|---|---|---|
| big-eye-handdrawn | 大眼萌系手绘Q版 | 本次参考已识别，待样张 | [规则](presets/big-eye-handdrawn.md) |
| simple-chibi | 简笔卡通Q版 | 本次参考已识别，待样张 | [规则](presets/simple-chibi.md) |
| child-crayon | 儿童蜡笔涂鸦 | 已制作动态套系 | [规则](presets/child-crayon.md) |
| shojo-manga | 少女漫画 | 已制作动态套系 | [规则](presets/shojo-manga.md) |
| japanese-flat | 日系扁平萌系 | 已有风格预览，动态待样张 | [规则](presets/japanese-flat.md) |
| american-cartoon | 美式卡通 | 已有风格预览，动态待样张 | [规则](presets/american-cartoon.md) |
| ugly-cute-doodle | 丑萌简笔涂鸦 | 可探索，待样张 | [规则](presets/ugly-cute-doodle.md) |
| retro-comic | 复古漫画网点 | 可探索，待样张 | [规则](presets/retro-comic.md) |

## 绘画与线稿

| ID | 风格 | 证据状态 | 入口 |
|---|---|---|---|
| storybook | 童话绘本 | 可探索，待样张 | [规则](presets/storybook.md) |
| colored-pencil | 彩铅速写 | 已有风格预览，动态待样张 | [规则](presets/colored-pencil.md) |
| watercolor | 水彩淡彩 | 可探索，待样张 | [规则](presets/watercolor.md) |
| ink-wash | 水墨写意 | 可探索，待样张 | [规则](presets/ink-wash.md) |
| minimal-line | 极简线描 | 可探索，待样张 | [规则](presets/minimal-line.md) |
| pen-sketch | 钢笔速写 | 可探索，待样张 | [规则](presets/pen-sketch.md) |

## 材质与立体

| ID | 风格 | 证据状态 | 入口 |
|---|---|---|---|
| plush-toy | 毛毡绒毛玩偶 | 已有风格预览，动态待样张 | [规则](presets/plush-toy.md) |
| felt-applique | 不织布贴布 | 可探索，待样张 | [规则](presets/felt-applique.md) |
| knitted-yarn | 毛线针织 | 可探索，待样张 | [规则](presets/knitted-yarn.md) |
| embroidery | 刺绣布章 | 可探索，待样张 | [规则](presets/embroidery.md) |
| paper-collage | 彩纸拼贴 | 已有风格预览，动态待样张 | [规则](presets/paper-collage.md) |
| soft-3d | 柔软3D卡通 | 可探索，待样张 | [规则](presets/soft-3d.md) |
| mochi-blob | 糯米团子 | 已有风格预览，动态待样张 | [规则](presets/mochi-blob.md) |
| jelly-translucent | 果冻半透明 | 可探索，待样张 | [规则](presets/jelly-translucent.md) |

## 印刷与像素

| ID | 风格 | 证据状态 | 入口 |
|---|---|---|---|
| rubber-stamp | 复古橡皮章 | 已有风格预览，动态待样张 | [规则](presets/rubber-stamp.md) |
| woodcut | 木刻版画 | 可探索，待样张 | [规则](presets/woodcut.md) |
| pixel-art | 像素游戏风 | 可探索，待样张 | [规则](presets/pixel-art.md) |
| stained-glass | 彩玻璃镶嵌 | 可探索，待样张 | [规则](presets/stained-glass.md) |

## 写实与照片

| ID | 风格 | 证据状态 | 入口 |
|---|---|---|---|
| realistic-pet | 写实宠物插画 | 可探索，待样张 | [规则](presets/realistic-pet.md) |
| photo-cutout | 照片抠图贴纸 | 可探索，路线需用户选择 | [规则](presets/photo-cutout.md) |

## 共通验收

画风不能替代角色、肢体、文字、真实Alpha和循环验收。任何风格的动画都回到同一母版；只让角色做动作，不靠整个图层平移冒充表演。静态可做不等于动态已验证。细线、绒毛、网点、半透明材质在实际聊天尺寸与深浅底分别检查。每套仍默认交付文件夹及完整配套物料，只有用户明确要求才压缩。
