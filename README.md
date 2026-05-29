<p align="center">
  <img src="assets/logo.png" alt="文格 Logo" width="156">
</p>

<h1 align="center">文格：法律文书模板执行 Skill</h1>

<p align="center">
  <strong>把 Word 模板交给 Claude Code、Codex 或兼容 Agent，让 AI 按模板生成、批处理并校验法律文书。</strong>
</p>

<p align="center">
  <a href="#它是做什么的">它是做什么的</a>
  · <a href="#适合谁使用">适合谁使用</a>
  · <a href="#三分钟理解">三分钟理解</a>
  · <a href="#模板怎么交给-ai">模板怎么交给 AI</a>
  · <a href="#交付前检查什么">交付前检查什么</a>
  · <a href="#给技术同事看的说明">技术说明</a>
</p>

<p align="center">
  <img alt="发布状态" src="https://img.shields.io/badge/状态-v2.2.0%20模板执行版-blue">
  <img alt="适用对象" src="https://img.shields.io/badge/适用对象-律师%20%2F%20法务%20%2F%20法律助理-7aa2a7">
  <img alt="文书格式" src="https://img.shields.io/badge/格式-DOCX%20%2F%20PDF%20%2F%20PNG-8aa0b2">
  <img alt="许可证" src="https://img.shields.io/badge/许可证-MIT-green">
  <img alt="示例数据" src="https://img.shields.io/badge/示例-仅使用模拟材料-orange">
</p>

## 它是做什么的

文格不是一个“字段替换工具”。它是给 Claude Code、Codex 或兼容 Agent 使用的法律文书格式 Skill。

更准确地说，文格把一份 Word 模板变成 AI 可以执行的格式规则：

- 用户提供一份 `.docx` 模板或母版文书；
- 用户用自然语言说明要生成什么、填什么、处理多少份；
- AI 读取模板，把它当作格式事实来源；
- AI 按模板生成或批量处理文书；
- AI 在交付前运行格式、结构和视觉门禁；
- 最后报告哪些文件通过，哪些需要人工复核。

模板不是附件。模板本身就是任务说明的一部分。

它重点处理格式和交付，不替代律师判断。事实、请求、理由、主文、金额、日期、案号和法条仍然需要律师确认。

## 适合谁使用

| 使用者 | 可以用它做什么 |
|---|---|
| 律师 | 把正式 Word 模板直接交给 AI，让 AI 按模板生成新文书并做格式复核。 |
| 法律助理 | 批量处理同一版式的律师函、报告、函件、附件或诉讼/仲裁文书初稿。 |
| 法务团队 | 统一公司内部法律文书、函件、报告或模板化文件的格式。 |
| 仲裁、诉讼团队 | 检查裁决书风格文书、诉讼文书或正式报告的页眉、页脚、页码和段落格式。 |
| 技术同事 | 把模板执行和格式门禁接入 Codex、Claude Code 或其他本地 Agent 工作流。 |

## 现在能做到什么

| 需求 | 当前支持情况 |
|---|---|
| 把 DOCX 模板作为 AI 执行依据 | 支持，Skill 会要求 Agent 以模板为格式事实来源。 |
| 用自然语言描述生成要求 | 支持，这是主路径，例如“用这个模板生成 20 份律师函”。 |
| 批量生成后做格式检查 | 支持，门禁脚本可检查文本、DOCX 结构和渲染页。 |
| 保留页眉、页脚和页码 | 支持检查，生成过程必须以模板为准，交付前校验。 |
| 检查标题字体、字号、段落和标点 | 支持，覆盖标题字体字号、中文标点和标点字体混乱。 |
| DOCX -> PDF -> PNG 视觉校验 | 支持，需要安装 LibreOffice 和 Poppler。 |
| 明确字段模板的确定性替换 | 支持，但这是 deterministic mode，不是普通用户主路径。 |
| 自动判断法律内容是否正确 | 不支持，这仍然属于律师审阅范围。 |
| 对无标注复杂模板承诺 100% 自动精确填充 | 不承诺，无法证明的位置需要人工确认或二次标注。 |

## 三分钟理解

你不用先学什么模板字段。

你真正要做的是，把模板和任务一起交给 AI：

```text
这是我们所里的律师函模板。
请按这个模板生成 8 份律师函。
收件人、案号、欠款金额和截止日期在表格里。
页眉、页脚、标题、字号、行距、落款和签名区都按模板来。
生成后逐份做格式检查，告诉我哪些通过，哪些需要人工看。
```

或者：

```text
这是裁决书风格模板。
请把我提供的事实、争议焦点和裁判理由整理成同版式文书。
不要改变法律判断。
生成后检查页码、页眉页脚、标题字体、段落行距和中文标点。
```

如果模板已经专门设计了 `{{CASE_NO}}`、`{{CLAIMANT}}` 这类字段，Agent 可以走确定性脚本，直接替换并验证结构。

如果模板没有字段，Agent 也不应该简单放弃。它应当先识别模板的格式结构，再根据用户的自然语言任务和材料生成候选文书，并明确报告哪些部分已校验、哪些部分需要人工确认。

## 模板怎么交给 AI

建议交给 AI 的材料包括：

| 材料 | 说明 |
|---|---|
| 模板 DOCX | 使用正式机构模板，先删除真实案件内容或改成脱敏样例。 |
| 任务说明 | 用自然语言说明要生成什么、多少份、输出到哪里。 |
| 填充材料 | 可以是表格、JSON、Markdown、案情摘要或已脱敏材料包。 |
| 格式要求 | 特别强调页眉页脚、页码、标题、字体、行距、落款、签名区。 |
| 交付标准 | 明确哪些检查必须 PASS，哪些 WARNING 需要人工确认。 |

对律师和助理来说，正常使用方式应该是“给模板 + 说需求”，不是手工改模板去放字段。

字段化模板只适合这些场景：

- 团队已经有固定字段清单；
- 需要大批量稳定替换；
- 要求 OpenXML 结构差异可证明；
- 技术同事愿意维护模板字段。

## 交付前检查什么

正式交付前，建议至少检查以下项目：

| 检查项 | 为什么重要 |
|---|---|
| 页眉、页脚 | 很多机构模板要求固定页眉页脚。 |
| 页码 | 页码错乱会影响正式提交和归档。 |
| 标题、字体、字号 | 正式文书通常有统一格式。 |
| 段落、缩进、行距 | 影响可读性，也影响机构格式要求。 |
| 分页 | 签名区、落款、附件清单不应被挤到错误位置。 |
| 中文标点 | 全角冒号、中文引号等问题在法律文书中很常见。 |
| 标点字体 | 标点被设置成 Times New Roman 等英文字体时，版面会显得不统一。 |
| 内容锁定 | 格式阶段不应改动事实、金额、日期、案号、请求、理由和主文。 |

## 需要安装什么

如果只是让技术同事部署，可以把这一段发给他：

| 用途 | 需要安装 |
|---|---|
| 基本文书检查 | Python 3.9+ |
| Word 转 PDF、图片检查 | LibreOffice + Poppler |
| 通过 Agent 使用 | Codex、Claude Code 或兼容 Skill Runner |

对外展示、正式分发或声称“可以做完整交付前检查”时，必须安装 LibreOffice 和 Poppler。否则只能说“可以做基础预检”，不能说“完整发布版可用”。

## 常见问题

### 它能不能直接替代律师审稿？

不能。它检查的是格式、模板执行和交付前风险，不判断事实是否真实、请求是否成立、法律适用是否正确。

### 是不是必须使用字段？

不是。

字段只是确定性模式，适合技术同事维护稳定模板和批量字段替换。普通使用者更自然的方式是把模板文件交给 Claude Code、Codex 或兼容 Agent，再用自然语言说明任务。

### 没有字段时还能不能用？

可以用，但要诚实区分“模板执行”和“可证明的结构一致”。

没有字段时，Agent 应根据模板识别版式、生成候选文书并做格式校验；但如果某个填充位置无法被可靠定位，必须报告需要人工确认，不能装作已经 100% 自动完成。

### 能不能做到完全一模一样？

目标是尽量继承模板，并在交付前发现偏差。实际视觉效果会受到填充文字长度、字体环境、Word 渲染差异和模板复杂度影响，所以正式交付前仍应做渲染检查和人工复核。

### 会不会上传真实案件材料？

本项目默认是本地执行，不提供托管服务。公开仓库中的示例只使用模拟材料。真实案件、客户名称、合同、证据和私有模板不要提交到公开仓库。

## 给律师团队的推荐工作流

1. 律师或团队负责人确认一份正式模板。
2. 助理把模板和任务说明交给本地 Agent。
3. Agent 读取模板，按自然语言要求生成或批量处理文书。
4. Agent 跑格式检查、结构检查和视觉校验。
5. 律师最后复核法律内容、签名区、附件和分页。

## 给技术同事看的说明

以下内容面向维护者、集成者和 Agent 工作流开发者。

### 项目状态

| 项目 | 说明 |
|---|---|
| 当前版本 | `v2.2.0 模板执行版` |
| 核心语言 | Python 3.9+ |
| 主要文件格式 | DOCX、PDF、PNG、JSON |
| 发布版强制工具 | LibreOffice、Poppler |
| 当前验证结果 | `65 passed`，V2 release smoke 共 10 步通过 |
| 安全策略 | synthetic 示例；不提交真实案件或私有模板 |

### Agent 执行路由

| 模式 | 什么时候用 | 说明 |
|---|---|---|
| Template Execution | 用户给模板 + 自然语言任务 | 主路径。Agent 读取模板，把模板作为格式事实来源，生成并校验文书。 |
| Deterministic Replace | 模板已有 `{{KEY}}` 字段 | 稳定批量替换路径。可用脚本证明 OpenXML 结构基本未漂移。 |
| Format Gate Only | 用户已有候选 DOCX | 不生成，只检查文本、结构、渲染和视觉风险。 |

### 核心命令

安装测试依赖：

```bash
python3 -m pip install -e ".[test]"
```

检查发布版依赖：

```bash
./skills/legal-document-format/scripts/check_release_requirements.py --mode release
```

确定性字段替换：

```bash
./skills/legal-document-format/scripts/apply_docx_template.py \
  template.docx output.docx \
  --replacements-json replacements.json \
  --json
```

检查模板一致性：

```bash
./skills/legal-document-format/scripts/compare_docx_template_parity.py \
  template.docx output.docx \
  --json
```

渲染 DOCX：

```bash
./skills/legal-document-format/scripts/render_docx.sh output.docx out/rendered
```

运行完整发布 smoke：

```bash
./skills/legal-document-format/scripts/release_smoke.py
```

### 脚本清单

| 脚本 | 用途 |
|---|---|
| `apply_docx_template.py` | 确定性模式：复制 DOCX 模板包结构并替换 `{{KEY}}` 文本字段。 |
| `compare_docx_template_parity.py` | 检查模板与输出除文本节点外的 OpenXML 结构是否一致。 |
| `audit_text.py` | 检查中文法律文本中的标点、全半角混用和空格问题。 |
| `audit_docx_structure.py` | 检查 DOCX 包结构、标题字体字号、标点字体、段落、表格、页眉页脚、样式、编号等。 |
| `render_docx.sh` | 用 LibreOffice 和 Poppler 执行 DOCX -> PDF -> PNG。 |
| `compare_rendered_pages.py` | 比较 PNG 渲染页的页数、尺寸、有效性、大小和哈希。 |
| `format_gate.py` | 聚合文本、DOCX 和渲染页检查。 |
| `check_release_requirements.py` | 检查 Python、LibreOffice、Poppler 是否满足发布要求。 |
| `release_smoke.py` | 一键跑发布门禁。 |
| `make_synthetic_docx.py` | 生成模拟 DOCX，用于演示和测试。 |

### 仓库结构

```text
legal-document-format-skill/
├── assets/
├── README.md
├── CHANGELOG.md
├── RELEASE.md
├── SECURITY.md
├── pyproject.toml
├── skills/
│   └── legal-document-format/
│       ├── SKILL.md
│       ├── references/
│       ├── scripts/
│       └── examples/
└── tests/
```

### 路由口径

| 层级 | 场景 | 主要依据 |
|---|---|---|
| L0 | 只清理文本、标点、空格 | `content-lock.md`、`audit_text.py` |
| L1 | 普通 DOCX 排版 | `routing.md`、`format-checklist.md` |
| L2 | 模板执行 | `template-execution.md`、`exact-template.md` |
| L3 | 裁决书风格定稿 | 内容锁定、模板继承、格式清单、视觉校验 |
| L4 | 视觉校验 | LibreOffice、Poppler、PNG comparison |

### 技术边界

- 主路径是 Agent 读取模板并按自然语言任务执行，不是要求用户手写字段。
- 确定性模式支持替换位于同一段落内、被多个 Word run/text 节点拆开的 `{{KEY}}` 字段。
- 模板一致性检查会忽略正文文本节点差异，但会比较字段指令、XML 结构、关系、样式、编号、页眉页脚、分节和非文本部件。
- 没有字段或人工标注时，Agent 必须报告无法证明的填充位置，不得承诺任意模板 100% 自动精确填充。
- 不内置第三方像素级 PDF diff；可后续接入 `diff-pdf`、`diff-pdf-visually` 或同类工具。
- 文本审计和聚合门禁默认不输出原文摘录，需要调试时显式使用 `--with-excerpt`。

### 本地验证

```bash
git diff --check
bash -n skills/legal-document-format/scripts/render_docx.sh
python3 -m py_compile skills/legal-document-format/scripts/*.py tests/*.py
python3 -m pytest
./skills/legal-document-format/scripts/release_smoke.py
```

当前验证结果：

```text
65 passed
V2 Release Smoke Gate: 10 steps, 0 failures
```

### 外部参考

| 项目 | 借鉴点 | 本项目取舍 |
|---|---|---|
| [GitHub README 官方说明](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes) | README 应说明项目做什么、为什么有用、如何开始、如何获得帮助。 | 首页改成律师可读的使用手册，技术说明放在后半部分。 |
| [python-docx-template / docxtpl](https://github.com/elapouya/python-docx-template) | Word 模板中放变量，再用数据生成 DOCX。 | 作为确定性模式参考，不作为普通用户主路径。 |
| [docx4j](https://github.com/plutext/docx4j) | OpenXML 包、变量、内容控件和 MERGEFIELD 的重型处理能力。 | 作为后续内容控件和复杂块替换参考，不引入 Java 运行时。 |
| [python-docx](https://github.com/python-openxml/python-docx) | DOCX 读写生态。 | 暂不作为核心依赖，当前以标准库处理 ZIP/OpenXML。 |
| [diff-pdf](https://github.com/vslavik/diff-pdf) | PDF 视觉比较和差异高亮。 | 作为增强项参考。 |
| [diff-pdf-visually](https://github.com/bgeron/diff-pdf-visually) | PDF 转 PNG 后做视觉比较。 | 借鉴页面渲染比较思路。 |
| [pdf-visual-diff](https://github.com/moshensky/pdf-visual-diff) | snapshot 式 PDF 视觉回归。 | 作为长期模板基线管理参考。 |

### GitHub Topics

```text
legaltech agent-skill docx openxml libreoffice poppler legal-documents
document-automation visual-validation quality-gate python synthetic-data
```

### 发布资料

- [CHANGELOG.md](CHANGELOG.md)：版本变化。
- [RELEASE.md](RELEASE.md)：发布范围、发布前命令和当前证据。
- [CONTRIBUTING.md](CONTRIBUTING.md)：贡献、验证和文档规则。
- [SECURITY.md](SECURITY.md)：安全报告和敏感信息处理规则。

### 后续计划

- 增加可选像素级视觉 diff。
- 增强无字段模板的结构识别和人工标注流程。
- 支持更复杂的模板块执行，例如表格行、整段、内容控件。
- 增加更多模拟模板，用于分页漂移、签名区和附件清单场景。
- 面向常见 Agent Runner 打包 Skill。
