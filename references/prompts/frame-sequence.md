# 动作帧表提示词

```text
ONE animation sprite sheet for ONE looping reaction, not different stickers.
Use the attached master for identity and style: {master_path}
Keep invariant: {invariants}
Style: {style}
Chat intent: {intent}. Dominant action: {action}.
Exactly {cols} columns x {rows} rows, {count} equal cells, row-major time order.
Fixed viewpoint, same character scale and canvas anchor; wide empty gutters.
Frame-by-frame plan:
{frame_beats}
Every adjacent pose must be reachable; the final pose leads naturally to frame one.
Text: {caption_instruction}
Real alpha if supported. No checkerboard, labels, borders, unrelated props or scene.
No new limbs, costume changes, mirrored signature markings or whole-canvas-only motion.
```

工具生成的网格未经检查不能信任。静字保持位置与字形一致；计划中的文字动作单独记录，并用同一字稿合成，不将无关抖字当成动效。文字意外跳变时重做文字层/候选，不靠抠图消除。无字角色帧则 caption_instruction 明确 no text。

需要控制构图漂移时，附上独立的等格定位模板，声明角色母版负责身份、模板负责相对位置；要求辅助线不进入交付角色图层。具体适用条件与对照验收见 [定位模板](../technical/registration-guides.md)。
