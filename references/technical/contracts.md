# 项目与产物契约

模板在 assets/templates。所有 JSON 使用 UTF-8、schema_version=2。读取前验证字段与数据类型，不匹配的项目须显式转换。路径：项目内部产物使用相对路径且禁止越出项目，角色原参考和母版可记录实际绝对路径。原参考不自动打包。

## 三个生产源文件

- project.json：项目名、主题、mode、count、style、required_formats、平台与授权记录。
- character.json：原参考、master_path、invariants、allowed_variations、选择状态。
- pack.json：grid 与 items；每项 ID 稳定，不随排序改名，具体意图与逐帧分镜是生成依据。

pack item 示例：
```json
{
  "id": "01",
  "intent": "回应任务",
  "caption": "收到",
  "action": "右手抬起敬礼并放下",
  "motion_key": "salute",
  "frame_beats": ["手在胸前", "抬肘", "手举半程", "指尖到额侧", "敬礼停留", "轻点头", "手放下半程", "接近初态"],
  "durations_ms": [200,140,140,180,300,140,140,200],
  "state": "planned",
  "files": {"gif": "exports/generic/01.gif", "webp": "exports/generic/01.webp"}
}
```

compile 检查母版存在、不变量非空、意图/动作存在、动态格数与时长数量一致、时长可编码。它不理解动作是否合理，也不保证主题契合，需 Agent 检查。

## 帧与时间

prepare_frames 输出 `frames/001.png...` 和 frames.json：来源哈希、网格、共同裁切、共同缩放、帧清单和哈希、画布、唯一帧数、是否插帧。assemble 读取 PNG 顺序；使用与 pack 一致的 durations，不传时仅用默认恒定时长。编码器合并重复停留帧正常，必须复核总时长。

## 视觉审阅示例

visual-review.json 的 items 按 ID 记录：
```json
{
  "file_hashes": {"exports/generic/01.gif": "实际SHA256", "exports/generic/01.webp": "实际SHA256"},
  "checks": {"identity":"pass","anatomy":"pass","caption":"pass","motion":"pass","loop":"pass","edges":"pass"},
  "method": "查看母版与接触表，浅深底检查，完整播放两个循环",
  "evidence": "previews/01-review.html",
  "notes": "具体观察，不得由测试自动填写真实成品的结论"
}
```

程序只能检查记录完整与哈希一致，不能证明审阅诚实。填写证据必须真实完成检查；本地证据文件实际保存，或用可访问的回执/截图。测试中使用合成素材的模拟审阅必须标为 fixture，不可冒充真实角色验收。

## 续作失效范围

| 改动 | 失效 |
|---|---|
| 角色母版/主风格 | 全套生成候选、媒体导出与视觉审阅 |
| 单条动作/台词 | 该条提示词、相关帧、导出与审阅 |
| 平台规格 | 对应入口导出及平台核验，不改高质量母版 |
| 标题/介绍 | 投稿文案，图像无需重画 |
| 输出重新编码 | 相应文件哈希与审阅绑定重验 |

失败状态保留原原因和版本。只修改已经完成的 ID 时，不重新初始化项目。任何项目 JSON 的授权字段只是授权记录，不独立授权外部发布。
