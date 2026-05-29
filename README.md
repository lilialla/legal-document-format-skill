<p align="center">
  <img src="assets/logo.png" alt="文格 Logo" width="156">
</p>

<h1 align="center">文格：法律文书格式门禁 Skill</h1>

<p align="center">
  <strong>面向 AI 法律工作流的 DOCX 模板继承、内容锁定、渲染校验与可审阅格式门禁。</strong>
</p>

<p align="center">
  <a href="#快速开始">快速开始</a>
  · <a href="#能力矩阵">能力矩阵</a>
  · <a href="#agent-与插件策略">Agent 与插件策略</a>
  · <a href="#发布版强制校验">发布版强制校验</a>
  · <a href="#项目经验与外部参考">项目经验与外部参考</a>
  · <a href="#v2-精确模板生成">V2 精确模板生成</a>
  · <a href="#v2-发布资料">V2 发布资料</a>
  · <a href="#脚本说明">脚本说明</a>
  · <a href="#隐私与安全">隐私与安全</a>
</p>

<p align="center">
  <img alt="发布状态" src="https://img.shields.io/badge/状态-v2.0.0%20精确模板版-blue">
  <img alt="Python 版本" src="https://img.shields.io/badge/Python-3.9%2B-blue">
  <img alt="视觉校验" src="https://img.shields.io/badge/视觉校验-LibreOffice%20%2B%20Poppler-7aa2a7">
  <img alt="许可证" src="https://img.shields.io/badge/许可证-MIT-green">
  <img alt="示例数据" src="https://img.shields.io/badge/示例-synthetic%20only-orange">
</p>

大多数 AI 法律工作流止步于“写出文字”。但法律文书真正的交付难点往往在最后一公里：**继承 Word 母版、锁定实体内容、避免格式阶段污染法律事实，并在交付前生成可审阅的格式报告**。

本项目是一个 synthetic-first 的 Agent Skill，面向中文法律文书、仲裁裁决书风格文书、模板化 DOCX 定稿，以及本地格式质量门禁。

## 一眼看懂

| 项目 | 说明 |
|---|---|
| 发布状态 | `v2.0.0 精确模板版` |
| 核心运行时 | Python 3.9+，核心审计脚本仅使用标准库 |
| 发布版强制工具 | LibreOffice + Poppler，用于 DOCX -> PDF -> PNG 视觉校验 |
| 主要输出 | JSON 报告、人类可读门禁报告、PDF/PNG 渲染产物 |
| 安全策略 | 仅使用 synthetic 示例；不包含真实案件、客户信息或私有模板 |
| 适合场景 | 本地试用、Agent Skill 打包、法律文书格式 QA、公开评审 |

## 发布状态

`v2.0.0 精确模板版`

当前版本适合本地试用、Skill 打包实验、公开展示和 V2 精确模板生成。对外分发时，应按“发布版强制校验”安装视觉校验工具；只安装 Python 的 `core` 档位仅用于开发、演示或无渲染环境的预检，不应被称为完整发布版。

## 推荐 Topics

GitHub 仓库建议使用以下 topics；发布前应在仓库设置中保持一致：

```text
legaltech agent-skill docx openxml libreoffice poppler legal-documents
document-automation visual-validation quality-gate python synthetic-data
```

## 它能做什么

- 按任务复杂度分层加载规则：文本清理、普通 DOCX 排版、精确模板套版、裁决书风格定稿、视觉校验。
- 在格式阶段执行内容锁定：不静默改动当事人、日期、金额、法条、请求、认定、理由、主文、签名和附件清单。
- 强调精确模板继承：需要高度一致时，应从用户提供的 DOCX 母版出发，而不是从空白文档“仿一个差不多的”。
- 提供 V2 模板生成链路：复制用户 DOCX 模板包，只替换 `{{KEY}}` 文本占位符，并用 OpenXML 模板一致性门禁证明页眉、页脚、样式、分节、页码字段和编号未漂移。
- 提供本地质量门禁：文本审计、DOCX OpenXML 结构审计、渲染页比较、聚合门禁报告。
- 提供 synthetic DOCX 生成器，方便演示和 smoke test，不暴露真实材料。

## 它不做什么

- 不提供法律意见。
- 不承诺自动生成可提交法院或仲裁机构的正式文件。
- 不包含真实案件、私有仲裁模板、客户事实、机构特定规则或保密示例。
- 不承诺对没有占位符的任意 DOCX 自动猜测应替换内容。V2 精确生成要求模板中存在单个文本节点内的 `{{KEY}}` 占位符；跨多个 Word run 的占位符会被门禁阻断。
- 不内置第三方像素级视觉 diff。当前 PNG 比较覆盖页数、尺寸、有效性、大小和文件哈希；如需像素级或 PDF 高亮差异，可接入 `diff-pdf`、`diff-pdf-visually` 或同类工具。
- 不提供托管服务或远程处理路径。当前工具以本地执行为主。

## 能力矩阵

| 能力 | 脚本 | 依赖 | 状态 |
|---|---|---|---|
| 文本与标点审计 | `audit_text.py` | Python 3.9+ | 可用 |
| DOCX OpenXML 结构审计 | `audit_docx_structure.py` | Python 3.9+ | 可用 |
| DOCX 模板占位符生成 | `apply_docx_template.py` | Python 3.9+ | 可用 |
| DOCX 模板一致性门禁 | `compare_docx_template_parity.py` | Python 3.9+ | 可用 |
| DOCX -> PDF -> PNG 渲染 | `render_docx.sh` | LibreOffice + Poppler | 可用 |
| PNG 渲染页比较 | `compare_rendered_pages.py` | Python 3.9+ | 可用 |
| 发布版依赖检查 | `check_release_requirements.py` | Python 3.9+；发布档要求 LibreOffice + Poppler | 可用 |
| 聚合格式门禁 | `format_gate.py` | Python 3.9+；渲染输入可选 | 可用 |
| synthetic DOCX 生成 | `make_synthetic_docx.py` | Python 3.9+ | 可用 |

## 环境要求

核心审计脚本运行时只依赖 Python 标准库：

```bash
python3 --version  # 3.9+
```

渲染校验需要本地文档工具：

```bash
soffice --version   # LibreOffice
pdftoppm -h         # Poppler
```

在 macOS 上，脚本也会检测：

```text
/Applications/LibreOffice.app/Contents/MacOS/soffice
```

开发测试依赖：

```bash
python3 -m pip install -e ".[test]"
```

## Agent 与插件策略

本项目区分开发预检档与完整发布档。对外展示、分发或声称“可交付格式门禁”时，必须使用完整发布档并安装视觉校验工具。

| 档位 | 用户必须安装 | 说明 |
|---|---|---|
| `core` 开发预检 | Python 3.9+ | 仅用于文本和 DOCX 结构检查；不是完整发布版。 |
| `release` 完整发布 | Python 3.9+、LibreOffice、Poppler | 必须可以执行 DOCX -> PDF -> PNG，并纳入格式门禁。 |
| Agent Skill 使用 | Codex、Claude Code 或兼容 Skill Runner | 可选；脚本可脱离 Agent 直接运行。 |
| 增强视觉 diff | `diff-pdf`、`diff-pdf-visually` 或同类工具 | 可选增强；不替代默认 LibreOffice + Poppler 渲染链路。 |

发布包、插件包或 Agent Skill 分发说明应默认要求 `release` 档位。缺少 LibreOffice 或 Poppler 时，只能标记为“预检能力可用”，不能标记为“发布版完整可用”。

## 发布版强制校验

完整发布前先运行依赖门禁：

```bash
./skills/legal-document-format/scripts/check_release_requirements.py --mode release
```

发布版格式任务至少应执行：

```bash
./skills/legal-document-format/scripts/render_docx.sh out/synthetic.docx out/rendered

./skills/legal-document-format/scripts/format_gate.py \
  --docx out/synthetic.docx \
  --baseline-png out/rendered/png \
  --candidate-png out/rendered/png \
  --require-visual \
  --fail-on-warning \
  --json
```

`--require-visual` 会强制要求 PNG 渲染页输入。缺少视觉校验输入时，门禁直接报错。

一键发布 smoke：

```bash
./skills/legal-document-format/scripts/release_smoke.py
```

## V2 精确模板生成

V2 的核心原则是：**输出文件必须从用户提供的 DOCX 模板包复制而来，只替换模板中明确标记的文本占位符，不能从空白 DOCX 重建版式。**

模板中使用 `{{KEY}}` 占位符，例如：

```text
案号：{{CASE_NO}}
申请人：{{CLAIMANT}}
被申请人：{{RESPONDENT}}
```

准备替换数据：

```json
{
  "CASE_NO": "SYN-2026-0001",
  "CLAIMANT": "甲方贸易有限公司",
  "RESPONDENT": "乙方设备有限公司"
}
```

生成文件并检查模板一致性：

```bash
./skills/legal-document-format/scripts/apply_docx_template.py \
  template.docx output.docx \
  --replacements-json replacements.json \
  --json

./skills/legal-document-format/scripts/compare_docx_template_parity.py \
  template.docx output.docx \
  --json
```

模板一致性门禁会忽略 `w:t` 等文本节点内容差异，但要求 DOCX 包结构、样式、页眉页脚、分节、页码字段、编号、关系和非文本部件保持一致。随后应继续执行渲染和格式门禁：

```bash
./skills/legal-document-format/scripts/render_docx.sh output.docx out/rendered
./skills/legal-document-format/scripts/format_gate.py \
  --docx output.docx \
  --baseline-png out/rendered/png \
  --candidate-png out/rendered/png \
  --require-visual \
  --fail-on-warning \
  --json
```

## 分发档位

以下为发布能力档位，不是 `pip` extras 名称。

| 档位 | 组件 | 适合用户 |
|---|---|---|
| `core` | Python 3.9+、`audit_text.py`、`audit_docx_structure.py`、`format_gate.py` | 只需要文本和 DOCX 结构门禁的用户。 |
| `release` | `core` + LibreOffice + Poppler + `render_docx.sh` + `compare_rendered_pages.py` + `--require-visual` | 对外发布、插件分发和正式演示的默认档位。 |
| `agent-skill` | `release` + `skills/legal-document-format/SKILL.md` | Codex、Claude Code 或兼容 Skill Runner。 |
| `dev` | 以上任一档位 + `pytest` | 贡献者和维护者。 |

## 快速开始

克隆仓库：

```bash
git clone https://github.com/lilialla/legal-document-format-skill.git
cd legal-document-format-skill
```

生成 synthetic DOCX：

```bash
mkdir -p out
./skills/legal-document-format/scripts/make_synthetic_docx.py out/synthetic.docx
```

审计 DOCX 结构：

```bash
./skills/legal-document-format/scripts/audit_docx_structure.py out/synthetic.docx --json
```

执行文本审计，并避免在日志中输出原文片段：

```bash
./skills/legal-document-format/scripts/audit_text.py "申请人: 张三" --json --no-excerpt
```

将 DOCX 渲染为 PDF 和 PNG：

```bash
./skills/legal-document-format/scripts/render_docx.sh out/synthetic.docx out/rendered
```

运行聚合格式门禁：

```bash
./skills/legal-document-format/scripts/format_gate.py \
  --text "申请人: 张三" \
  --docx out/synthetic.docx \
  --baseline-png out/rendered/png \
  --candidate-png out/rendered/png \
  --require-visual \
  --json --no-excerpt
```

预期结果：synthetic DOCX 和 PNG 检查通过；示例文本会因为中文语境中的半角冒号产生一个 warning。

## 脚本说明

| 脚本 | 用途 |
|---|---|
| `audit_text.py` | 审计中文法律文本中的标点和空格问题。 |
| `audit_docx_structure.py` | 读取 DOCX ZIP/OpenXML，报告 section、段落、表格、页眉页脚、样式、编号和损坏的关键 part。 |
| `apply_docx_template.py` | 从用户 DOCX 模板复制包结构并替换 `{{KEY}}` 文本占位符。 |
| `compare_docx_template_parity.py` | 对比模板和输出，确认除文本节点外的 OpenXML 布局结构保持一致。 |
| `render_docx.sh` | 使用 LibreOffice headless 和 Poppler 执行 DOCX -> PDF -> PNG。 |
| `compare_rendered_pages.py` | 比较 PNG 渲染页目录的页数、文件名、PNG 有效性、尺寸、文件大小和页面文件哈希差异。 |
| `check_release_requirements.py` | 检查发布版所需的 Python、LibreOffice 和 Poppler 是否可用。 |
| `format_gate.py` | 将文本、DOCX 和渲染页检查聚合为一个 JSON 或人类可读报告。 |
| `release_smoke.py` | 一键运行 V2 发布 smoke gate，包括模板生成、模板一致性、并行 LibreOffice 渲染检查。 |
| `make_synthetic_docx.py` | 创建 synthetic DOCX，用于演示和 smoke test。 |

## 仓库结构

```text
legal-document-format-skill/
├── assets/
│   ├── logo.png
│   ├── logo-generated.png
│   └── logo.svg
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── RELEASE.md
├── SECURITY.md
├── AGENTS.md
├── pyproject.toml
├── skills/
│   └── legal-document-format/
│       ├── SKILL.md
│       ├── references/
│       │   ├── project-basis.md
│       │   ├── routing.md
│       │   ├── content-lock.md
│       │   ├── exact-template.md
│       │   ├── failure-modes.md
│       │   ├── format-checklist.md
│       │   └── visual-validation.md
│       ├── scripts/
│       │   ├── README.md
│       │   ├── apply_docx_template.py
│       │   ├── audit_docx_structure.py
│       │   ├── audit_text.py
│       │   ├── check_release_requirements.py
│       │   ├── compare_docx_template_parity.py
│       │   ├── compare_rendered_pages.py
│       │   ├── format_gate.py
│       │   ├── release_smoke.py
│       │   ├── make_synthetic_docx.py
│       │   └── render_docx.sh
│       └── examples/
│           ├── README.md
│           └── synthetic-award-fragment.md
└── tests/
```

## 路由模型

| 层级 | 请求类型 | 加载内容 | 常用工具 |
|---|---|---|---|
| L0 | 法律文本清理 | `content-lock.md`、文本规则 | `audit_text.py` |
| L1 | 普通 DOCX 排版 | `routing.md`、`format-checklist.md` | Word 或 Markdown-to-DOCX 工具 |
| L2 | 精确模板套版 | `exact-template.md`、`content-lock.md` | Base-replace DOCX pipeline |
| L3 | 裁决书风格定稿 | 路由、内容锁定、模板、清单、视觉校验 | OpenXML 与渲染检查 |
| L4 | 视觉校验 | `visual-validation.md`、`failure-modes.md` | LibreOffice、Poppler、PNG 比较 |

默认路径保持轻量。只有当任务确实需要时，才加载精确模板和裁决书风格规则。

## 本地验证

运行：

```bash
bash -n skills/legal-document-format/scripts/render_docx.sh
python3 -m py_compile skills/legal-document-format/scripts/*.py tests/*.py
python3 -m pytest
./skills/legal-document-format/scripts/release_smoke.py
```

当前本地验证结果：

```text
55 passed
```

## 项目经验与外部参考

本仓库不是从空白 prompt 临时拼出的展示页，已经抽取了内部文书格式经验，并保留了公开可审阅的取舍说明：

- [项目依据与取舍](skills/legal-document-format/references/project-basis.md)：来自本仓库方案报告的安全抽象版，说明哪些内部经验被公开化，哪些私有模板和真实案件信息不进入仓库。
- [视觉校验](skills/legal-document-format/references/visual-validation.md)：明确 LibreOffice + Poppler 是默认渲染链路。
- [失败模式](skills/legal-document-format/references/failure-modes.md)：把内容锁定、模板继承、OpenXML、标点和视觉失败分成可审查门禁。

外部参考采用“借鉴机制，不盲目引依赖”的原则：

| 项目 | 借鉴点 | 本项目取舍 |
|---|---|---|
| [GitHub README 官方说明](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes) | README 应说明项目做什么、为什么有用、如何开始、如何获得帮助。 | 首页保留标题、Logo、Badges、快速开始、依赖、脚本、隐私和路线图。 |
| [python-docx-template / docxtpl](https://github.com/elapouya/python-docx-template) | 在 Word 模板中放置变量，再用数据渲染生成 DOCX。 | 借鉴“模板先行、变量替换”的交互模型；V2 默认只替换文本占位符并保持低依赖。 |
| [docx4j](https://github.com/plutext/docx4j) | Java 生态中面向 OpenXML 包、变量、内容控件和 MERGEFIELD 的重型处理能力。 | 作为后续内容控件、复杂块替换和更深 OpenXML 操作的参考；V2 不引入 Java 运行时。 |
| [docx-mailmerge](https://github.com/Bouke/docx-mailmerge) | 以 Office Open XML mail merge 字段生成 DOCX。 | 借鉴字段化模板思路；当前项目避免依赖已归档库作为发布默认路径。 |
| [python-docx](https://github.com/python-openxml/python-docx) | DOCX 读写生态的事实标准之一。 | 暂不作为核心依赖；当前以标准库检查 OpenXML，降低安装面。 |
| [diff-pdf](https://github.com/vslavik/diff-pdf) | PDF 视觉比较和差异高亮。 | 作为增强视觉 diff 参考；默认链路仍是 LibreOffice + Poppler + PNG 渲染页门禁。 |
| [diff-pdf-visually](https://github.com/bgeron/diff-pdf-visually) | PDF 转 PNG 后做页面视觉一致性判断。 | 借鉴“页数、尺寸、渲染图比较”的思路。 |
| [pdf-visual-diff](https://github.com/moshensky/pdf-visual-diff) | snapshot 式 PDF 视觉回归。 | 借鉴 snapshot 机制；不引入 Node/Jest 作为默认依赖。 |

参考范围：截至 2026-05-29，仅用于公开功能定位和工程机制取舍，不等同于完整竞品审计。

## V2 发布资料

- [CHANGELOG.md](CHANGELOG.md)：公开版本变化。
- [RELEASE.md](RELEASE.md)：V2 发布范围、发布前命令和当前证据。
- [CONTRIBUTING.md](CONTRIBUTING.md)：贡献、验证和文档规则。
- [SECURITY.md](SECURITY.md)：安全报告和敏感信息处理规则。

说明：当前仓库写入凭证没有 GitHub workflow scope，V2 以本地 `release_smoke.py` 作为发布门禁；启用 GitHub Actions 后应复用同一命令。

## 格式门禁口径

交付格式化法律文书前，应确认：

- 内容锁定已遵守；
- 需要精确套版时，已经从母版继承；
- 字体、字号、行距、缩进、页边距、页眉页脚、页码和标点已检查；
- 需要视觉校验时，DOCX 已成功渲染为 PDF 和 PNG；
- 报告区分 error、warning 和 info；
- 示例和报告均为 synthetic 或已完成脱敏。

## 隐私与安全

不要提交：

- 真实诉状、裁决书、合同、证据或往来函件；
- 私有机构模板；
- 客户名称、案号、商业秘密或未公开事实；
- 带有真实项目上下文的商业平台导出记录。

除非获得明确授权并完成脱敏，否则仅使用 synthetic 示例。

## 品牌资产

项目 Logo 位于：

```text
assets/logo.svg
assets/logo-generated.png
assets/logo.png
```

`logo.png` 是 README 使用的现代杂志风主 Logo；`logo-generated.png` 保留同版生成图；`logo.svg` 是可维护矢量备用版。Logo 采用低饱和淡色、留白和文书格线语言，避免重型企业图标风。

## 路线图

- 增加可选的像素级视觉 diff。
- 扩展 OpenXML 检查：样式继承、section 属性、字段、编号定义。
- 增加更多 synthetic fixtures，用于模板继承和分页漂移场景。
- 面向常见 Agent Runner 打包 Skill。
