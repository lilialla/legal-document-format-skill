---
name: legal-document-format
description: 面向法律文书格式处理的 Agent Skill，把用户提供的 DOCX 模板作为格式事实来源，支持自然语言模板执行、内容锁定、DOCX 结构审计和发布档强制 LibreOffice + Poppler 视觉校验。
---

# 法律文书模板执行与格式门禁

当用户要求格式化、定稿、排版、套版、批量生成、按模板生成、渲染检查或视觉校验法律文书时，使用本 Skill。典型对象包括中文法律文书、仲裁裁决书风格文书、诉讼文书、法律备忘录、合同和模板化 DOCX。

本 Skill 的核心不是“要求用户维护模板字段”，而是让 Claude Code、Codex 或兼容 Agent 把用户提供的 Word 模板当作可执行的格式规则。

## 硬性规则

- 格式处理不得改变法律实体内容。
- 锁定当事人、日期、金额、案号、法条、请求、认定、理由、主文、签名和附件清单。
- 用户提供 DOCX 模板、母版或样本文书时，必须以该文件为格式事实来源。
- 用户用自然语言说明填充内容、批处理要求或输出标准时，应按模板执行，而不是要求用户先改成字段化模板。
- `{{KEY}}` 字段只是确定性替换模式；只有模板已经明确字段化，或用户/技术同事选择该模式时才作为主路径。
- 没有字段或人工标注时，不得承诺任意复杂模板已 100% 自动精确填充；必须报告已校验范围和需要人工确认的位置。
- 不要用普通 Markdown-to-DOCX 转换冒充精确模板执行。
- 在完成相应清单和渲染检查前，不要宣称文档可交付或发布档完整可用。
- 对外发布、插件分发、正式演示和 L3/L4 任务必须具备 LibreOffice + Poppler，并运行视觉校验。
- 除非用户明确提供并授权真实材料，否则只使用 synthetic 示例。

## 先路由

加载详细规则前，先判断任务类型：

| 路由 | 触发条件 | 读取内容 |
|---|---|---|
| L0 文本清理 | 清理法条、案例、条款、标题或标点，不输出 DOCX | `references/content-lock.md`、`references/format-checklist.md` |
| L1 普通 DOCX 排版 | 将文本或 Markdown 制作为普通 Word 文档 | `references/routing.md`、`references/format-checklist.md` |
| L2 模板执行 | 用户提供 DOCX 模板、母版或样本文书，并要求按该模板生成、填充、批处理或校验 | `references/template-execution.md`、`references/exact-template.md`、`references/content-lock.md`、`references/format-checklist.md` |
| L3 裁决书风格定稿 | 格式化仲裁裁决书或类似正式文书 | `references/routing.md`、`references/template-execution.md`、`references/content-lock.md`、`references/exact-template.md`、`references/format-checklist.md`、`references/visual-validation.md` |
| L4 视觉校验 | 渲染 DOCX、比较 PDF/PNG、检查分页和版面 | `references/visual-validation.md`、`references/failure-modes.md` |

## 模板执行原则

用户给模板时，Agent 应先做四件事：

1. 确认模板来源和任务目标：生成单份、批量生成、格式迁移、候选文书校验，还是定稿复核。
2. 识别模板结构：页眉页脚、页码字段、标题层级、字体字号、段落、表格、编号、落款、签名区和附件区。
3. 根据用户自然语言和材料生成候选文书；若模板已有 `{{KEY}}` 字段，可切换到确定性替换脚本。
4. 交付前运行文本、DOCX 结构、模板一致性或视觉校验，并报告无法自动确认的项目。

## 工具

本地文件可用时，优先使用仓库内脚本：

- `scripts/audit_text.py`：法律文本标点和空格审计。
- `scripts/audit_docx_structure.py`：DOCX 包结构和 OpenXML 结构审计。
- `scripts/apply_docx_template.py`：确定性模式，从用户 DOCX 模板复制包结构并替换 `{{KEY}}` 文本字段。
- `scripts/compare_docx_template_parity.py`：对比模板与输出，确认除文本节点内容外的 OpenXML 布局结构一致。
- `scripts/render_docx.sh`：DOCX -> PDF -> PNG 渲染链路。
- `scripts/compare_rendered_pages.py`：PNG 渲染页目录的轻量元数据比较。
- `scripts/check_release_requirements.py`：发布版依赖门禁，检查 Python、LibreOffice 和 Poppler。
- `scripts/format_gate.py`：聚合文本、DOCX 和渲染页检查，输出统一报告。
- `scripts/release_smoke.py`：发布 smoke gate，覆盖依赖、模板应用、模板一致性、渲染、强制视觉门禁和测试。
- `scripts/make_synthetic_docx.py`：生成 synthetic DOCX，用于本地 smoke test。

同时运行多项检查时，用 `references/failure-modes.md` 分类结果：error 阻断交付，warning 需要复核；格式门禁通过并不等于法律实体内容正确。发布档检查应使用 `format_gate.py --require-visual`，避免缺少渲染页时误报为完整通过。

## 输出要求

每次实质格式任务都应报告：

- 选用的路由；
- 使用的源模板、源文书和输入材料；
- 内容锁定是否保持；
- 是否按模板执行，是否使用确定性字段替换；
- 已执行的检查；
- 已生成的文件；
- 自动校验通过项；
- 需要人工复核的格式或验证事项。

面向律师的交付物，还应明确完成格式复核：行距、字体、段落缩进、字号、颜色、标题字体字号、标点符号字体统一性，以及全角/半角标点，尤其是引号、冒号、括号、逗号和分号。
