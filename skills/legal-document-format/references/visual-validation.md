# 视觉校验

视觉校验用于检查 DOCX 是否可以渲染为可审阅页面。它不证明法律实体内容正确。

对外发布、插件分发、正式演示以及 L3/L4 文书格式任务，视觉校验不是可选项。缺少 LibreOffice 或 Poppler 时，只能说明 core 预检可用，不能说明发布版完整可用。

## 默认渲染链路

```text
DOCX -> LibreOffice headless -> PDF -> Poppler pdftoppm -> PNG 页面
```

默认使用 `scripts/render_docx.sh`。

当同时存在基准 PNG 页面和候选 PNG 页面时，使用 `scripts/compare_rendered_pages.py`。内置比较是轻量门禁，检查页数、文件名、文件大小、PNG 有效性和尺寸；它不是像素级 diff。

## 必需工具

- LibreOffice 的 `soffice`；
- Poppler 的 `pdftoppm`；
- `scripts/check_release_requirements.py --mode release` 必须通过。

macOS 上 LibreOffice 可能位于：

```text
/Applications/LibreOffice.app/Contents/MacOS/soffice
```

## 渲染后检查重点

- 首页标题和页边距；
- 页眉页脚；
- 页码；
- 分节转换；
- 表格和长段落；
- 编号和缩进；
- 签名区和盖章区；
- 末页是否溢出；
- 是否存在多余空白页。

## 基准比较

如果提供了基准 PDF 或 PNG 快照，应比较：

- 页数；
- 页面尺寸；
- 可见文字位置；
- 页眉页脚和页码；
- 签名区位置；
- 异常空白区域或溢出。

可选增强工具包括 `diff-pdf`、Python PDF 视觉比较工具或 PNG snapshot 比较。

## 报告状态

建议使用：

- `rendered`：已生成 PDF 和 PNG 页面；
- `render failed`：转换失败；
- `baseline matched`：在选定容差下视觉比较通过；
- `baseline differed`：视觉比较发现差异；
- `no baseline`：渲染成功，但无法进行视觉 diff。

发布档门禁应使用 `scripts/format_gate.py --require-visual`。如果没有 `--baseline-png` 和 `--candidate-png`，应视为发布门禁未完成。
