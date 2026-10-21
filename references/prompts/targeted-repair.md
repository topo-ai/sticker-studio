# 定向修复提示词

```text
Edit candidate [file], using [master] as identity anchor.
Change only: [specific observed defect, affected frames/region].
Keep unchanged: [identity, outfit, palette, pose sequence, unaffected frames, caption].
Required result: [observable condition].
Background/transparency: preserve existing alpha unless this is the defect being fixed.
```

先写修复记录，再调用；输出新版本。换脸、缺手、中文错误交图像编辑工具；切帧偏移/尺寸/格式交媒体管线。修复成功后相关文件与审阅重新计算，不能拿旧哈希。
