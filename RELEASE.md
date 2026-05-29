# V2 发布说明

## 发布定位

`2.2.0` 是“文格：法律文书模板执行 Skill”的模板执行版。它面向 Claude Code、Codex 和兼容 Agent 分发，核心定位是把用户提供的 DOCX 模板作为格式事实来源，让 AI 按自然语言任务生成、批处理并校验法律文书。

文格不提供法律意见，也不替代律师审阅。

## V2 必须满足

- README 首页中文化，说明主路径是“模板 + 自然语言任务 + 材料 + 交付门禁”，而不是要求普通用户维护字段。
- `pyproject.toml` 版本为 `2.2.0`。
- `SKILL.md` 将 L2 主路由定义为模板执行，适用于用户提供 DOCX 模板、母版或样本文书的场景。
- `references/template-execution.md` 说明 Claude Code / Codex 应如何读取模板、理解自然语言任务、生成候选文书并报告人工复核项。
- `apply_docx_template.py` 保留为确定性字段模式，能从 DOCX 模板复制包结构并替换 `{{KEY}}` 文本字段。
- `compare_docx_template_parity.py` 能在确定性字段模式下证明除文本节点内容外，模板和输出的 OpenXML 布局结构一致。
- `audit_text.py` 覆盖中文法律语境中的常见全半角标点问题。
- `audit_docx_structure.py` 覆盖 DOCX 内全半角标点、标题字体字号、标点符号字体统一性、页码字段和页眉页脚引用风险。
- 完整发布档强制安装 Python 3.9+、LibreOffice 和 Poppler。
- `format_gate.py --require-visual` 能阻断缺少视觉渲染页的发布门禁。
- `compare_rendered_pages.py --fail-on-warning` 能把 PNG 大小或内容差异作为阻断门禁。
- `release_smoke.py` 能跑通 synthetic 模板 DOCX 生成、确定性字段应用、模板一致性、渲染和聚合门禁。
- LibreOffice 渲染使用独立 profile，并通过 3 路并行渲染 smoke。
- 测试通过，且不依赖真实案件、客户材料或私有模板。

## 发布前命令

```bash
python3 -m pip install -e ".[test]"
./skills/legal-document-format/scripts/check_release_requirements.py --mode release
./skills/legal-document-format/scripts/release_smoke.py
```

## 当前 V2 证据

- 依赖门禁：Python、LibreOffice、Poppler 均通过。
- 自动化测试：`65 passed`。
- smoke gate：`release_smoke.py` 覆盖发布版关键链路，共 10 步。
- 远端分支：`main`。

## 不纳入 V2 默认范围

- 第三方像素级 PDF diff 默认集成；
- 对任意无标注复杂 DOCX 模板承诺 100% 自动精确填充；
- 跨段落、跨表格单元格或跨复杂块的字段自动合并；
- 私有模板；
- 真实案件 fixture；
- 托管服务；
- 法律实体内容正确性判断。
