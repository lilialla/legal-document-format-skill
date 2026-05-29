<p align="center">
  <img src="assets/logo.png" alt="文格 Logo" width="156">
</p>

<h1 align="center">文格：法律文书格式助手</h1>

<p align="center">
  <strong>给律师、法务和法律助理使用的 Word 文书套版、格式检查与交付前复核工具。</strong>
</p>

<p align="center">
  <a href="#它是做什么的">它是做什么的</a>
  · <a href="#适合谁使用">适合谁使用</a>
  · <a href="#三分钟上手">三分钟上手</a>
  · <a href="#怎么让新文书和模板长得一样">怎么让新文书和模板长得一样</a>
  · <a href="#交付前检查什么">交付前检查什么</a>
  · <a href="#常见问题">常见问题</a>
  · <a href="#给技术同事看的说明">技术说明</a>
</p>

<p align="center">
  <img alt="发布状态" src="https://img.shields.io/badge/状态-v2.1.0%20审计修复版-blue">
  <img alt="适用对象" src="https://img.shields.io/badge/适用对象-律师%20%2F%20法务%20%2F%20法律助理-7aa2a7">
  <img alt="文书格式" src="https://img.shields.io/badge/格式-DOCX%20%2F%20PDF%20%2F%20PNG-8aa0b2">
  <img alt="许可证" src="https://img.shields.io/badge/许可证-MIT-green">
  <img alt="示例数据" src="https://img.shields.io/badge/示例-仅使用模拟材料-orange">
</p>

## 它是做什么的

文格解决的是法律文书最后一步最容易出错的问题：**文字已经写好，但 Word 版式必须严格跟模板一致，交付前还要检查页眉、页脚、页码、字体、字号、行距、段落、标点和分页。**

你可以把它理解成一个“文书格式助理”：

- 你给它一份 Word 模板；
- 在模板里标好哪些地方需要替换；
- 再给它案号、当事人、标题等信息；
- 它生成一份新 Word 文书；
- 并检查新文书是否仍然保留原模板的版式。

它重点处理格式，不替代律师判断。事实、请求、理由、主文、金额、日期、案号和法条仍然需要律师确认。

## 适合谁使用

| 使用者 | 可以用它做什么 |
|---|---|
| 律师 | 把已有文书模板套到新案件，减少手动改格式的时间。 |
| 法律助理 | 批量生成同一版式的文书初稿，并做交付前格式检查。 |
| 法务团队 | 统一公司内部法律文书、函件、报告或模板化文件的格式。 |
| 仲裁、诉讼团队 | 检查裁决书风格文书、诉讼文书或正式报告的页眉、页脚、页码和段落格式。 |
| 技术同事 | 把这套能力接入 Codex、Claude Code 或其他本地 Agent 工作流。 |

## 现在能做到什么

| 需求 | 当前支持情况 |
|---|---|
| 生成和模板同版式的 Word 文件 | 支持，前提是模板中放了明确的 `{{占位符}}`。 |
| 保留页眉、页脚和页码 | 支持，生成文件从模板复制而来。 |
| 保留标题、字体、字号和段落样式 | 支持，默认不重建样式。 |
| 检查行距、段落、分页和渲染结果 | 支持，需要安装 LibreOffice 和 Poppler。 |
| 检查中文标点，例如全角冒号、引号 | 支持，覆盖常见全半角标点混用。 |
| 检查标题字体、标题字号和标点字体混乱 | 支持，会提示标题字体字号不统一、中文标点回退到英文字体等风险。 |
| 自动判断法律内容是否正确 | 不支持，这仍然属于律师审阅范围。 |
| 不放占位符也自动猜哪些内容要替换 | 不支持，这样很容易改错位置。 |

## 三分钟上手

### 第一步：准备模板

准备一份 `.docx` 模板。模板中应该已经设置好：

- 页眉、页脚；
- 页码；
- 标题样式；
- 字体、字号；
- 段前段后、行距、首行缩进；
- 表格、签名区、盖章区等固定位置。

### 第二步：在模板中放占位符

把需要替换的位置写成这种形式：

```text
案号：{{CASE_NO}}
申请人：{{CLAIMANT}}
被申请人：{{RESPONDENT}}
文书标题：{{TITLE}}
```

建议占位符使用英文大写、数字和下划线，便于识别。占位符不要拆开写，也不要一半加粗一半不加粗。

### 第三步：准备替换信息

把要填入模板的信息整理成一张清单：

```json
{
  "TITLE": "仲裁裁决书",
  "CASE_NO": "SYN-2026-0001",
  "CLAIMANT": "甲方贸易有限公司",
  "RESPONDENT": "乙方设备有限公司"
}
```

如果你通过 Agent 使用，可以直接说：

```text
请用我提供的 Word 模板生成新文书。
模板里 {{CASE_NO}} 替换为 SYN-2026-0001，
{{CLAIMANT}} 替换为甲方贸易有限公司，
{{RESPONDENT}} 替换为乙方设备有限公司。
要求页眉、页脚、页码、字体、字号、行距和段落格式都保留模板原样。
生成后请做格式检查并告诉我是否通过。
```

### 第四步：生成并检查

技术同事可以直接运行脚本；不懂技术的使用者只需要把模板、替换信息和上述要求交给本地 Agent。

```bash
./skills/legal-document-format/scripts/apply_docx_template.py \
  template.docx output.docx \
  --replacements-json replacements.json

./skills/legal-document-format/scripts/compare_docx_template_parity.py \
  template.docx output.docx
```

### 第五步：看检查结果

检查结果只需要关注三类：

| 结果 | 含义 |
|---|---|
| `PASS` | 当前检查通过。 |
| `WARNING` | 有风险，需要人工看一眼。 |
| `FAIL` | 不能交付，应先修正。 |

## 怎么让新文书和模板长得一样

文格采用的是最稳妥的做法：**不是重新做一个“看起来差不多”的 Word，而是直接以你的模板为底稿，只替换你明确标出的文字。**

这样做的好处是：

- 页眉页脚不会被重新写坏；
- 页码字段不会轻易丢失；
- 标题样式、正文字体、字号和行距从模板继承；
- 分节、页边距、编号、表格和签名区更容易保持原样；
- 检查工具可以对比模板和输出，发现不该发生的结构变化。

需要注意：如果替换后的文字比原来长很多，分页仍然可能变化。例如当事人名称特别长，可能把签名区挤到下一页。这类问题需要通过渲染检查和人工复核确认。

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

不能。它检查的是格式和模板一致性，不判断事实是否真实、请求是否成立、法律适用是否正确。

### 为什么一定要放占位符？

因为法律文书不能靠猜。模板中明确写 `{{CASE_NO}}`，工具才知道这里应替换案号。没有占位符时，自动猜测很容易改错位置。

### 为什么占位符不要拆开设置格式？

Word 有时会把一个词拆成多个小片段。当前工具可以处理同一段落内被拆开的 `{{CASE_NO}}`，但最稳妥的做法仍然是把一个占位符作为连续文本输入，不要拆到不同段落或表格单元格。

### 能不能做到完全一模一样？

在“模板有明确占位符”的前提下，工具会从模板复制生成新文件，并检查除替换文字外的版式结构是否保持一致。实际视觉效果还会受到替换文字长度、字体环境和 Word 渲染差异影响，所以正式交付前仍应做渲染检查。

### 会不会上传真实案件材料？

本项目默认是本地执行，不提供托管服务。公开仓库中的示例只使用模拟材料。真实案件、客户名称、合同、证据和私有模板不要提交到公开仓库。

## 给律师团队的推荐工作流

1. 由律师或团队负责人确认一份正式模板。
2. 由助理在模板中放入 `{{CASE_NO}}`、`{{CLAIMANT}}` 等占位符。
3. 每次新案件只填写替换信息，不手动改版式。
4. 生成新文书后先跑格式检查。
5. 律师最后复核法律内容、签名区、附件和分页。

## 给技术同事看的说明

以下内容面向维护者、集成者和 Agent 工作流开发者。

### 项目状态

| 项目 | 说明 |
|---|---|
| 当前版本 | `v2.1.0 审计修复版` |
| 核心语言 | Python 3.9+ |
| 主要文件格式 | DOCX、PDF、PNG、JSON |
| 发布版强制工具 | LibreOffice、Poppler |
| 当前验证结果 | `65 passed`，V2 release smoke 共 10 步通过 |
| 安全策略 | synthetic 示例；不提交真实案件或私有模板 |

### 核心命令

安装测试依赖：

```bash
python3 -m pip install -e ".[test]"
```

检查发布版依赖：

```bash
./skills/legal-document-format/scripts/check_release_requirements.py --mode release
```

生成模板输出：

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
| `apply_docx_template.py` | 复制 DOCX 模板包结构并替换 `{{KEY}}` 文本占位符。 |
| `compare_docx_template_parity.py` | 检查模板与输出除文本节点外的 OpenXML 结构是否一致。 |
| `audit_text.py` | 检查中文法律文本中的标点、全半角混用和空格问题。 |
| `audit_docx_structure.py` | 检查 DOCX 包结构、标题字体字号、标点字体、段落、表格、页眉页脚、样式、编号等。 |
| `render_docx.sh` | 用 LibreOffice 和 Poppler 执行 DOCX -> PDF -> PNG。 |
| `compare_rendered_pages.py` | 比较 PNG 渲染页的页数、尺寸、有效性、大小和哈希。 |
| `format_gate.py` | 聚合文本、DOCX 和渲染页检查。 |
| `check_release_requirements.py` | 检查 Python、LibreOffice、Poppler 是否满足发布要求。 |
| `release_smoke.py` | 一键跑 V2 发布门禁。 |
| `make_synthetic_docx.py` | 生成模拟 DOCX，用于演示和测试。 |

### 仓库结构

```text
legal-document-format-skill/
├── assets/
│   ├── logo.png
│   ├── logo-generated.png
│   └── logo.svg
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
| L2 | 精确模板套版 | `exact-template.md`、V2 template pipeline |
| L3 | 裁决书风格定稿 | 内容锁定、模板继承、格式清单、视觉校验 |
| L4 | 视觉校验 | LibreOffice、Poppler、PNG comparison |

### V2 的技术边界

- 支持替换位于同一段落内、被多个 Word run/text 节点拆开的 `{{KEY}}` 占位符。
- 模板一致性检查会忽略正文文本节点差异，但会比较字段指令、XML 结构、关系、样式、编号、页眉页脚、分节和非文本部件。
- 不默认支持无占位符文档的语义猜测替换。
- 不默认合并跨段落、跨表格单元格或跨复杂块的占位符。
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
| [python-docx-template / docxtpl](https://github.com/elapouya/python-docx-template) | Word 模板中放变量，再用数据生成 DOCX。 | 借鉴模板先行的交互模型，V2 默认保持低依赖。 |
| [docx4j](https://github.com/plutext/docx4j) | OpenXML 包、变量、内容控件和 MERGEFIELD 的重型处理能力。 | 作为后续内容控件和复杂块替换参考，不引入 Java 运行时。 |
| [docx-mailmerge](https://github.com/Bouke/docx-mailmerge) | Office Open XML mail merge 字段生成 DOCX。 | 借鉴字段化模板思路，不作为默认依赖。 |
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
- [RELEASE.md](RELEASE.md)：V2 发布范围、发布前命令和当前证据。
- [CONTRIBUTING.md](CONTRIBUTING.md)：贡献、验证和文档规则。
- [SECURITY.md](SECURITY.md)：安全报告和敏感信息处理规则。

### 品牌资产

```text
assets/logo.svg
assets/logo-generated.png
assets/logo.png
```

`logo.png` 是 README 使用的主 Logo；`logo-generated.png` 保留同版生成图；`logo.svg` 是可维护矢量备用版。

### 后续计划

- 增加可选像素级视觉 diff。
- 支持更复杂的模板块替换，例如表格行、整段、内容控件。
- 增加更多模拟模板，用于分页漂移、签名区和附件清单场景。
- 面向常见 Agent Runner 打包 Skill。
