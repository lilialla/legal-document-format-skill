# 更新日志

本项目遵循语义化版本思路记录公开发布变化。

## 2.1.0 - 2026-05-29

### 修复

- 支持替换同一段落内被 Word 拆分到多个 run/text 节点的 `{{KEY}}` 占位符。
- 模板应用失败时不再留下目标 DOCX，避免后续流水线误用失败产物。
- `compare_rendered_pages.py` 增加 `--fail-on-warning`，可将 PNG 大小或内容差异升级为阻断门禁。
- `compare_docx_template_parity.py` 不再忽略 `w:instrText`，页码字段等 field code 变化会被模板一致性门禁发现。
- `audit_docx_structure.py` 新增 DOCX 内半角标点 issue、页码字段审计、页眉页脚引用审计、style `basedOn` 与 `docDefaults` 继承解析。
- 文本审计与聚合门禁默认不输出原文摘录；需要调试时显式使用 `--with-excerpt`。
- DOCX/ZIP/PNG 读取增加基础大小、条目数、解压体积、压缩比和流式哈希保护；LibreOffice/Poppler 渲染增加脚本级超时。

### 验证

- 当前 V2 本地验证：`65 passed`。
- 发布 smoke gate 继续覆盖模板应用、模板一致性、DOCX -> PDF -> PNG 渲染、并行 LibreOffice 渲染和格式门禁。

## 2.0.1 - 2026-05-29

### 新增

- 文本审计增强：中文语境下新增半角逗号、分号、问号、叹号和括号检查。
- DOCX 格式细节审计增强：新增标题字体、标题字号、标题内部字体字号混用、标点符号字体混乱和中文标点缺少 eastAsia 字体设置检查。

### 验证

- 当前 V2 本地验证：`57 passed`。
- 发布 smoke gate 继续覆盖模板应用、模板一致性、DOCX -> PDF -> PNG 渲染、并行 LibreOffice 渲染和格式门禁。

## 2.0.0 - 2026-05-29

### 新增

- V2 精确模板生成：`apply_docx_template.py` 从用户提供的 DOCX 模板复制包结构，只替换 `{{KEY}}` 文本占位符。
- 模板一致性门禁：`compare_docx_template_parity.py` 对比模板与输出，要求除文本节点内容外的 OpenXML 结构、样式、页眉页脚、分节、页码字段、编号、关系和非文本部件保持一致。
- synthetic DOCX 生成器增加页眉、页脚和 PAGE 字段，用于覆盖页眉页脚与页码场景。
- 发布 smoke gate 增加模板应用与模板一致性检查，当前共 10 步。

### 验证

- 当前 V2 本地验证：`55 passed`。
- 发布 smoke gate 已覆盖 DOCX 模板生成、占位符替换、OpenXML 模板一致性、DOCX -> PDF -> PNG 渲染、并行 LibreOffice 渲染和格式门禁。

### 边界

- V2 要求模板内存在明确 `{{KEY}}` 占位符；不对无占位符文档进行语义猜测替换。
- 为了保证版式一致性，默认只替换单个 Word 文本节点内的占位符；跨多个 Word run 的占位符会被未解析占位符门禁阻断。

## 1.0.0 - 2026-05-29

### 新增

- 发布版强制视觉校验：完整发布档必须具备 LibreOffice `soffice` 和 Poppler `pdftoppm`。
- `check_release_requirements.py`：检查 Python、LibreOffice 和 Poppler 是否满足发布档要求。
- `release_smoke.py`：一键运行 V1 发布 smoke gate，包括依赖、脚本语法、Python 编译、synthetic DOCX、DOCX 渲染、`--require-visual`/`--fail-on-warning` 格式门禁和测试。
- 并行渲染防护：`render_docx.sh` 为每次 LibreOffice 渲染使用独立 profile，`release_smoke.py` 覆盖 3 路并行渲染。
- PNG 内容差异检查：`compare_rendered_pages.py` 增加文件哈希差异 warning，避免同尺寸同大小不同内容被误判为通过。
- `format_gate.py --require-visual`：缺少 baseline/candidate PNG 渲染页时直接失败。
- `project-basis.md`：沉淀内部文书格式经验的公开抽象版，并说明不公开真实案件和私有模板。
- 现代中文 README 首页、Logo、Badges、Topics、分发档位、隐私安全和外部参考说明。

### 验证

- 当前 V1 本地验证：`51 passed`。
- 发布 smoke gate 已覆盖 DOCX -> PDF -> PNG 渲染链路。

### 边界

- 本项目提供格式质量门禁和 Agent Skill 规则，不提供法律意见，也不替代律师审阅。
- 像素级 PDF diff 作为增强项保留，不作为 V1 默认依赖。
