# 项目依据与取舍

本参考文件沉淀“文书格式 Skill 项目方案报告”中可以公开的工程经验。它只保留抽象方法、开源参考和质量门禁原则，不包含真实案件、客户名称、私有模板或机构内部规则。

## 仓库内经验

本项目已经吸收以下内部经验：

- 从格式任务入口先分层路由，避免普通排版、模板执行和裁决书风格定稿混用。
- 格式阶段必须执行内容锁定，不能因为排版修改当事人、日期、金额、请求、认定、理由、主文、签名或附件清单。
- 用户提供 DOCX 模板时，模板本身就是格式事实来源，不是普通附件。
- 面向 Claude Code、Codex 或兼容 Agent 的主路径应是“模板 + 自然语言任务 + 材料 + 交付门禁”，而不是要求普通用户先维护字段。
- 字段化模板是确定性模式：复制模板 DOCX 包结构，只替换明确文本字段，再用模板一致性门禁证明结构未漂移。
- DOCX 交付前要同时检查文本、OpenXML 结构、渲染结果和人工可读报告。
- 视觉校验默认使用 LibreOffice headless 渲染 PDF，再用 Poppler 输出 PNG 页面。
- 示例和测试只使用 synthetic 数据，避免真实法律材料进入公开仓库。

## 已公开化的能力

| 内部经验 | 仓库内落点 |
|---|---|
| 内容锁定 | `references/content-lock.md` |
| 路由分层 | `references/routing.md` |
| 模板执行原则 | `references/template-execution.md` |
| 精确模板和确定性字段模式 | `references/exact-template.md` |
| 格式清单 | `references/format-checklist.md` |
| 视觉校验 | `references/visual-validation.md` |
| 失败模式 | `references/failure-modes.md` |
| 确定性字段替换与一致性门禁 | `scripts/apply_docx_template.py`、`scripts/compare_docx_template_parity.py` |
| 本地门禁脚本 | `scripts/` |

## 未公开内容

以下内容不进入本仓库：

- 真实裁决书、诉状、合同、证据、往来函件；
- 客户名称、案号、金额、商业秘密或未公开事实；
- 私有仲裁机构模板或机构特定格式细则；
- 商业平台导出记录或未脱敏的核验结果；
- 内部重型 OpenXML 重排实现和非公开业务规则。

## 外部项目参考

本项目参考开源生态中的机制，但不盲目扩大默认依赖：

- `python-docx`：说明 DOCX 读写生态成熟，但本项目核心检查优先使用 Python 标准库读取 ZIP/OpenXML，以降低安装负担。
- `python-docx-template` / `docxtpl`：说明“用户在 Word 模板中放置变量，再渲染为 DOCX”是成熟路线；本项目把它作为确定性字段模式参考，而不是普通用户的唯一入口。
- `docx4j`：说明内容控件、MERGEFIELD、复杂 OpenXML 块处理有成熟重型生态，适合作为后续复杂模板执行参考。
- `diff-pdf`：说明 PDF 视觉比较可以作为增强能力，尤其适合输出高亮差异 PDF。
- `diff-pdf-visually`：说明 PDF 转 PNG 后做页面视觉一致性判断是合理方向，和本项目 LibreOffice + Poppler 链路一致。
- `pdf-visual-diff`：说明 snapshot 式视觉回归适合长期模板基线管理，但 Node/Jest 不作为默认运行时。

## 发布取舍

`core` 档位只适合开发预检；完整发布档必须具备 LibreOffice + Poppler 并执行视觉校验。否则只能说“结构和文本预检可用”，不能说“格式门禁完整可用”。

模板执行能力必须诚实描述：Agent 可以根据模板和自然语言任务生成、批处理并校验文书；但对无标注、复杂、歧义位置较多的模板，必须报告无法自动确认的部分，不能承诺 100% 自动精确填充。
