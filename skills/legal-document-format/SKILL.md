---
name: legal-document-format
description: 面向法律文书格式处理的 Agent Skill，支持内容锁定、DOCX 模板继承和可选 LibreOffice 视觉校验。
---

# 法律文书格式门禁

当用户要求格式化、定稿、排版、套版、渲染检查或视觉校验法律文书时，使用本 Skill。典型对象包括中文法律文书、仲裁裁决书风格文书、诉讼文书、法律备忘录、合同和模板化 DOCX。

## 硬性规则

- 格式处理不得改变法律实体内容。
- 锁定当事人、日期、金额、案号、法条、请求、认定、理由、主文、签名和附件清单。
- 如果用户要求精确模板套版，应以用户提供的 DOCX 母版或模板为事实来源。
- 不要用普通 Markdown-to-DOCX 转换冒充精确模板继承。
- 在完成相应清单和渲染检查前，不要宣称文档可交付。
- 除非用户明确提供并授权真实材料，否则只使用 synthetic 示例。

## 先路由

加载详细规则前，先判断任务类型：

| 路由 | 触发条件 | 读取内容 |
|---|---|---|
| L0 文本清理 | 清理法条、案例、条款、标题或标点，不输出 DOCX | `references/content-lock.md`、`references/format-checklist.md` |
| L1 普通 DOCX 排版 | 将文本或 Markdown 制作为普通 Word 文档 | `references/routing.md`、`references/format-checklist.md` |
| L2 精确模板套版 | 保留用户提供的 DOCX 模板或母版 | `references/exact-template.md`、`references/content-lock.md`、`references/format-checklist.md` |
| L3 裁决书风格定稿 | 格式化仲裁裁决书或类似正式文书 | `references/routing.md`、`references/content-lock.md`、`references/exact-template.md`、`references/format-checklist.md`、`references/visual-validation.md` |
| L4 视觉校验 | 渲染 DOCX、比较 PDF/PNG、检查分页和版面 | `references/visual-validation.md`、`references/failure-modes.md` |

## 工具

本地文件可用时，优先使用仓库内脚本：

- `scripts/audit_text.py`：法律文本标点和空格审计。
- `scripts/audit_docx_structure.py`：DOCX 包结构和 OpenXML 结构审计。
- `scripts/render_docx.sh`：DOCX -> PDF -> PNG 渲染链路。
- `scripts/compare_rendered_pages.py`：PNG 渲染页目录的轻量元数据比较。
- `scripts/format_gate.py`：聚合文本、DOCX 和渲染页检查，输出统一报告。
- `scripts/make_synthetic_docx.py`：生成 synthetic DOCX，用于本地 smoke test。

同时运行多项检查时，用 `references/failure-modes.md` 分类结果：error 阻断交付，warning 需要复核；格式门禁通过并不等于法律实体内容正确。

## 输出要求

每次实质格式任务都应报告：

- 选用的路由；
- 使用的源文件；
- 内容锁定是否保持；
- 是否需要并使用精确模板继承；
- 已执行的检查；
- 已生成的文件；
- 未解决的格式或验证事项。

面向律师的交付物，还应明确完成格式复核：行距、字体、段落缩进、字号、颜色，以及全角/半角标点，尤其是引号和冒号。
