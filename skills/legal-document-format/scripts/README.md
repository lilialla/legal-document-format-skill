# 脚本说明

这些脚本是“文格”法律文书模板执行 Skill 的本地质量检查工具。脚本只处理本地文件，不应包含密钥、私有模板或真实案件材料。

## `render_docx.sh`

使用 LibreOffice headless 将 DOCX 渲染为 PDF，再使用 Poppler 将 PDF 渲染为 PNG 页面。

```bash
./skills/legal-document-format/scripts/render_docx.sh input.docx output/rendered
```

## `check_release_requirements.py`

检查发布版依赖。完整发布档要求 Python 3.9+、LibreOffice `soffice` 和 Poppler `pdftoppm` 全部可用。

```bash
./skills/legal-document-format/scripts/check_release_requirements.py --mode release
```

只做开发预检时可使用 `--mode core`，但 core 通过不代表发布版完整可用。

## `audit_text.py`

审计文本或 UTF-8 文本文件中的法律文书标点、全半角混用、空格和疑似空字段问题。当前会提示中文语境中的半角冒号、逗号、分号、问号、叹号、括号、英文直引号等常见问题。

```bash
./skills/legal-document-format/scripts/audit_text.py "申请人: 张三" --json
```

当输入必须是文件路径时使用 `--file`；默认不输出原文摘录，需要调试非敏感文本时使用 `--with-excerpt`；需要严格门禁时使用 `--fail-on-issue`。

## `audit_docx_structure.py`

使用 Python 标准库读取 DOCX ZIP/OpenXML 结构，报告关键包部件、section、段落、表格、页眉页脚、样式和编号，并审计标题字体字号、标题内部字体字号混用、标点符号字体混乱和中文标点缺少 eastAsia 字体设置等问题。

```bash
./skills/legal-document-format/scripts/audit_docx_structure.py input.docx --json
```

## `apply_docx_template.py`

确定性字段模式：从用户提供的 DOCX 模板复制完整包结构，只替换模板中已有的 `{{KEY}}` 文本字段。支持同一段落内跨 run/text 节点的字段；页眉、页脚、分节、样式、编号、页码字段和媒体均继承自模板。

```bash
./skills/legal-document-format/scripts/apply_docx_template.py \
  template.docx output.docx \
  --replacements-json replacements.json \
  --json
```

也可以使用多个 `--set KEY=VALUE`。

## `compare_docx_template_parity.py`

检查生成文件是否保持模板的 OpenXML 布局结构。该门禁忽略正文文本节点内容差异，但不忽略 `w:instrText` 字段指令，要求结构、样式、页眉页脚、页码字段、分节、编号、关系和非文本部件一致。

```bash
./skills/legal-document-format/scripts/compare_docx_template_parity.py \
  template.docx output.docx \
  --json
```

## `compare_rendered_pages.py`

比较两个 PNG 渲染页目录。内置门禁检查页数、文件名、PNG 有效性、尺寸、文件大小和文件哈希；它仍不是第三方像素级 diff。

```bash
./skills/legal-document-format/scripts/compare_rendered_pages.py baseline/png candidate/png --json
```

发布门禁中可加入 `--fail-on-warning`，将 PNG 大小或内容哈希差异升级为阻断。

## `format_gate.py`

将文本、DOCX 结构和渲染页检查聚合成一个本地报告。

```bash
./skills/legal-document-format/scripts/format_gate.py \
  --text "申请人: 张三" \
  --docx input.docx \
  --baseline-png baseline/png \
  --candidate-png candidate/png \
  --require-visual \
  --fail-on-warning \
  --json
```

当文本输入必须来自文件时使用 `--text-file path/to/input.txt`。默认不输出原文摘录，需要调试非敏感文本时使用 `--with-excerpt`。
发布档门禁应使用 `--require-visual`，缺少渲染页输入时直接报错。
发布前严格门禁可同时使用 `--fail-on-warning`。

聚合门禁只有在至少一个检查返回 error 时才以退出码 `1` 结束；仅有 warning 时退出码为 `0`。

## `release_smoke.py`

运行发布 smoke gate，覆盖发布依赖、shell 语法、Python 编译、synthetic 模板 DOCX、确定性字段应用、模板一致性、DOCX 渲染、3 路并行 LibreOffice 渲染、强制视觉格式门禁和 pytest。

```bash
./skills/legal-document-format/scripts/release_smoke.py
```

如果只想验证渲染链路而暂时没有安装测试依赖，可使用：

```bash
./skills/legal-document-format/scripts/release_smoke.py --skip-tests
```

## `make_synthetic_docx.py`

生成最小 synthetic DOCX，用于本地演示和 smoke test。

```bash
./skills/legal-document-format/scripts/make_synthetic_docx.py output/synthetic.docx
```

除非显式传入 `--force`，否则生成器不会覆盖已有文件。

所有脚本均支持 `--help`。Python 审计脚本支持人类可读输出和 `--json`。结构性或视觉错误会返回非零退出码；文本 warning 默认不阻断，除非使用 `--fail-on-issue`。
