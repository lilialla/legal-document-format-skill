<p align="center">
  <img src="assets/logo.svg" alt="文格 Logo" width="132">
</p>

<h1 align="center">文格：法律文书格式门禁 Skill</h1>

<p align="center">
  <strong>面向 AI 法律工作流的 DOCX 模板继承、内容锁定、渲染校验与可审阅格式门禁。</strong>
</p>

<p align="center">
  <a href="#快速开始">快速开始</a>
  · <a href="#能力矩阵">能力矩阵</a>
  · <a href="#agent-与插件策略">Agent 与插件策略</a>
  · <a href="#脚本说明">脚本说明</a>
  · <a href="#隐私与安全">隐私与安全</a>
</p>

<p align="center">
  <img alt="发布状态" src="https://img.shields.io/badge/状态-v0.1%20技术预览-blue">
  <img alt="Python 版本" src="https://img.shields.io/badge/Python-3.9%2B-blue">
  <img alt="运行时依赖" src="https://img.shields.io/badge/核心运行时-标准库-green">
  <img alt="许可证" src="https://img.shields.io/badge/许可证-MIT-green">
  <img alt="示例数据" src="https://img.shields.io/badge/示例-synthetic%20only-orange">
</p>

大多数 AI 法律工作流止步于“写出文字”。但法律文书真正的交付难点往往在最后一公里：**继承 Word 母版、锁定实体内容、避免格式阶段污染法律事实，并在交付前生成可审阅的格式报告**。

本项目是一个 synthetic-first 的 Agent Skill，面向中文法律文书、仲裁裁决书风格文书、模板化 DOCX 定稿，以及本地格式质量门禁。

## 一眼看懂

| 项目 | 说明 |
|---|---|
| 发布状态 | `v0.1 技术预览版` |
| 核心运行时 | Python 3.9+，核心审计脚本仅使用标准库 |
| 渲染工具 | LibreOffice + Poppler，用于 DOCX -> PDF -> PNG |
| 主要输出 | JSON 报告、人类可读门禁报告、PDF/PNG 渲染产物 |
| 安全策略 | 仅使用 synthetic 示例；不包含真实案件、客户信息或私有模板 |
| 适合场景 | 本地试用、Agent Skill 打包、法律文书格式 QA、公开评审 |

## 发布状态

`v0.1 技术预览版`

当前版本已经适合本地试用、Skill 打包实验和公开展示。它不是完整的法律交付系统，也不替代律师审阅。

## 推荐 Topics

GitHub 仓库建议使用以下 topics。本仓库已设置：

```text
legaltech agent-skill docx openxml libreoffice poppler legal-documents
document-automation visual-validation quality-gate python synthetic-data
```

## 它能做什么

- 按任务复杂度分层加载规则：文本清理、普通 DOCX 排版、精确模板套版、裁决书风格定稿、视觉校验。
- 在格式阶段执行内容锁定：不静默改动当事人、日期、金额、法条、请求、认定、理由、主文、签名和附件清单。
- 强调精确模板继承：需要高度一致时，应从用户提供的 DOCX 母版出发，而不是从空白文档“仿一个差不多的”。
- 提供本地质量门禁：文本审计、DOCX OpenXML 结构审计、渲染页比较、聚合门禁报告。
- 提供 synthetic DOCX 生成器，方便演示和 smoke test，不暴露真实材料。

## 它不做什么

- 不提供法律意见。
- 不承诺自动生成可提交法院或仲裁机构的正式文件。
- 不包含真实案件、私有仲裁模板、客户事实、机构特定规则或保密示例。
- 不提供像素级视觉 diff。当前 PNG 比较是轻量元数据门禁，像素级 diff 可作为后续增强。
- 不提供托管服务或远程处理路径。当前工具以本地执行为主。

## 能力矩阵

| 能力 | 脚本 | 依赖 | 状态 |
|---|---|---|---|
| 文本与标点审计 | `audit_text.py` | Python 3.9+ | 可用 |
| DOCX OpenXML 结构审计 | `audit_docx_structure.py` | Python 3.9+ | 可用 |
| DOCX -> PDF -> PNG 渲染 | `render_docx.sh` | LibreOffice + Poppler | 可用 |
| PNG 渲染页比较 | `compare_rendered_pages.py` | Python 3.9+ | 可用 |
| 聚合格式门禁 | `format_gate.py` | Python 3.9+；渲染输入可选 | 可用 |
| synthetic DOCX 生成 | `make_synthetic_docx.py` | Python 3.9+ | 可用 |

## 环境要求

核心审计脚本运行时只依赖 Python 标准库：

```bash
python --version  # 3.9+
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
python -m pip install -e ".[test]"
```

## Agent 与插件策略

后续分发不应强制所有用户安装重型依赖。本项目按能力分层降级：

| 层级 | 用户必须安装 | 说明 |
|---|---|---|
| 核心 CLI 审计 | Python 3.9+ | 无额外运行时包依赖。 |
| 渲染校验 | LibreOffice + Poppler | 仅当用户需要 DOCX -> PDF -> PNG 时必需。 |
| Agent Skill 使用 | Codex、Claude Code 或兼容 Skill Runner | 可选；脚本可脱离 Agent 直接运行。 |
| 未来像素级 diff | 可选视觉 diff 工具 | v0.1 暂未内置。 |

打包分发时，建议默认安装或说明 `core` 能力；只有用户需要渲染校验时，才要求安装 LibreOffice 和 Poppler。

## 分发档位

| 档位 | 组件 | 适合用户 |
|---|---|---|
| `core` | Python 3.9+、`audit_text.py`、`audit_docx_structure.py`、`format_gate.py` | 只需要文本和 DOCX 结构门禁的用户。 |
| `render` | `core` + LibreOffice + Poppler + `render_docx.sh` + `compare_rendered_pages.py` | 需要视觉 smoke check 和页面级产物的用户。 |
| `agent-skill` | `core` 或 `render` + `skills/legal-document-format/SKILL.md` | Codex、Claude Code 或兼容 Skill Runner。 |
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
  --json --no-excerpt
```

预期结果：synthetic DOCX 和 PNG 检查通过；示例文本会因为中文语境中的半角冒号产生一个 warning。

## 脚本说明

| 脚本 | 用途 |
|---|---|
| `audit_text.py` | 审计中文法律文本中的标点和空格问题。 |
| `audit_docx_structure.py` | 读取 DOCX ZIP/OpenXML，报告 section、段落、表格、页眉页脚、样式、编号和损坏的关键 part。 |
| `render_docx.sh` | 使用 LibreOffice headless 和 Poppler 执行 DOCX -> PDF -> PNG。 |
| `compare_rendered_pages.py` | 比较 PNG 渲染页目录的页数、文件名、PNG 有效性、尺寸和文件大小差异。 |
| `format_gate.py` | 将文本、DOCX 和渲染页检查聚合为一个 JSON 或人类可读报告。 |
| `make_synthetic_docx.py` | 创建 synthetic DOCX，用于演示和 smoke test。 |

## 仓库结构

```text
legal-document-format-skill/
├── assets/
│   └── logo.svg
├── README.md
├── LICENSE
├── AGENTS.md
├── pyproject.toml
├── skills/
│   └── legal-document-format/
│       ├── SKILL.md
│       ├── references/
│       │   ├── routing.md
│       │   ├── content-lock.md
│       │   ├── exact-template.md
│       │   ├── failure-modes.md
│       │   ├── format-checklist.md
│       │   └── visual-validation.md
│       ├── scripts/
│       │   ├── README.md
│       │   ├── audit_docx_structure.py
│       │   ├── audit_text.py
│       │   ├── compare_rendered_pages.py
│       │   ├── format_gate.py
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
python -m py_compile skills/legal-document-format/scripts/*.py tests/*.py
python -m pytest
```

当前本地验证结果：

```text
39 passed
```

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
```

`logo.svg` 是 README 使用的可维护矢量版；`logo-generated.png` 是生成式图像版本，适用于发布说明、包页面和 Skill 目录卡片。Logo 采用“文书 + 门禁 + 盾牌 + 对勾”的组合。

## 路线图

- 在仓库凭证支持 GitHub workflow 后补充 CI。
- 增加可选的像素级视觉 diff。
- 扩展 OpenXML 检查：样式继承、section 属性、字段、编号定义。
- 增加更多 synthetic fixtures，用于模板继承和分页漂移场景。
- 面向常见 Agent Runner 打包 Skill。
