# Legal Document Format Skill

**DOCX template preservation, content lock, render validation, and reviewable format gates for AI legal workflows.**

![Status](https://img.shields.io/badge/status-v0.1%20technical%20preview-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Runtime](https://img.shields.io/badge/runtime-standard%20library-green)
![License](https://img.shields.io/badge/license-MIT-green)
![Examples](https://img.shields.io/badge/examples-synthetic%20only-orange)

Most AI legal workflows stop after drafting text. This project focuses on the last mile: preserving DOCX templates, locking legal content during formatting, rendering with LibreOffice, and producing a reviewable format report before delivery.

This is a synthetic-first Agent Skill for Chinese legal documents, arbitration-award-style formal documents, template-based DOCX finalization, and local quality gates.

## Release Status

`v0.1 Technical Preview`

This repository is ready for local trial, skill packaging experiments, and public review. It is not marketed as a complete legal delivery system, and it does not replace lawyer review.

## Topics

Recommended GitHub topics:

```text
legaltech agent-skill docx openxml libreoffice poppler legal-documents
document-automation visual-validation quality-gate python synthetic-data
```

## What It Provides

- Progressive-disclosure routing for text cleanup, ordinary DOCX formatting, exact-template formatting, arbitration-award formatting, and visual validation.
- Content lock rules: formatting should not silently change parties, dates, amounts, law citations, claims, findings, reasoning, dispositive text, signatures, or annex lists.
- Exact-template guidance: when fidelity matters, start from the supplied base DOCX instead of recreating a blank document that merely looks similar.
- Local quality gates for text, DOCX OpenXML structure, rendered PNG pages, and aggregate reports.
- Synthetic DOCX fixture generation for smoke tests and demos without exposing real matters.

## What It Does Not Provide

- Legal advice.
- Court-ready or arbitration-ready documents without human review.
- Real case files, private arbitration templates, client facts, institution-specific rules, or confidential examples.
- Pixel-level visual diff. The current PNG comparison is a metadata gate; stronger visual diff can be added later.
- A hosted service or remote processing path. The current tools are local-first.

## Capability Matrix

| Capability | Script | Required tools | Status |
|---|---|---|---|
| Text and punctuation audit | `audit_text.py` | Python 3.9+ | Ready |
| DOCX OpenXML structure audit | `audit_docx_structure.py` | Python 3.9+ | Ready |
| DOCX to PDF to PNG render | `render_docx.sh` | LibreOffice + Poppler | Ready |
| Rendered PNG page comparison | `compare_rendered_pages.py` | Python 3.9+ | Ready |
| Aggregate format gate | `format_gate.py` | Python 3.9+; render inputs optional | Ready |
| Synthetic DOCX generation | `make_synthetic_docx.py` | Python 3.9+ | Ready |

## Prerequisites

Core audit scripts use only the Python standard library at runtime:

```bash
python --version  # 3.9+
```

Render validation requires local document tools:

```bash
soffice --version   # LibreOffice
pdftoppm -h         # Poppler
```

On macOS, LibreOffice is also detected at:

```text
/Applications/LibreOffice.app/Contents/MacOS/soffice
```

For development tests:

```bash
python -m pip install -e ".[test]"
```

## Agent And Plugin Strategy

The skill is designed to degrade by capability instead of forcing every user into a heavy setup:

| Layer | Required for users | Notes |
|---|---|---|
| Core CLI audits | Python 3.9+ | No external runtime package dependency. |
| Render validation | LibreOffice + Poppler | Required only when users want DOCX -> PDF -> PNG checks. |
| Agent skill use | Codex, Claude Code, or a compatible skill runner | Optional; scripts can run directly without an agent. |
| Future pixel diff | Optional visual diff tooling | Not included in v0.1. |

For packaged distributions, declare LibreOffice and Poppler as required extras for render validation, not as mandatory dependencies for text/OpenXML audit use.

## Quickstart

Clone the repository:

```bash
git clone https://github.com/lilialla/legal-document-format-skill.git
cd legal-document-format-skill
```

Generate a synthetic DOCX fixture:

```bash
mkdir -p out
./skills/legal-document-format/scripts/make_synthetic_docx.py out/synthetic.docx
```

Audit DOCX structure:

```bash
./skills/legal-document-format/scripts/audit_docx_structure.py out/synthetic.docx --json
```

Run a text audit without leaking excerpts:

```bash
./skills/legal-document-format/scripts/audit_text.py "申请人: 张三" --json --no-excerpt
```

Render the DOCX to PDF and PNG pages:

```bash
./skills/legal-document-format/scripts/render_docx.sh out/synthetic.docx out/rendered
```

Run the aggregate format gate:

```bash
./skills/legal-document-format/scripts/format_gate.py \
  --text "申请人: 张三" \
  --docx out/synthetic.docx \
  --baseline-png out/rendered/png \
  --candidate-png out/rendered/png \
  --json --no-excerpt
```

Expected result: the synthetic DOCX and PNG checks should pass; the sample text should produce a warning for the half-width colon.

## Script Reference

| Script | Purpose |
|---|---|
| `audit_text.py` | Audits Chinese legal text for punctuation and spacing issues. |
| `audit_docx_structure.py` | Reads DOCX ZIP/OpenXML parts and reports sections, paragraphs, tables, headers, footers, styles, numbering, and malformed required parts. |
| `render_docx.sh` | Uses LibreOffice headless and Poppler to render DOCX -> PDF -> PNG pages. |
| `compare_rendered_pages.py` | Compares rendered PNG page directories by page count, filenames, PNG validity, dimensions, and size deltas. |
| `format_gate.py` | Aggregates text, DOCX, and rendered-page checks into one JSON or human-readable report. |
| `make_synthetic_docx.py` | Creates a synthetic DOCX fixture for demos and smoke tests. |

## Repository Layout

```text
legal-document-format-skill/
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

## Routing Model

| Level | Request type | Load | Typical tooling |
|---|---|---|---|
| L0 | Legal text cleanup | `content-lock.md`, text rules | `audit_text.py` |
| L1 | Ordinary DOCX formatting | `routing.md`, `format-checklist.md` | Word or Markdown-to-DOCX tooling |
| L2 | Exact template formatting | `exact-template.md`, `content-lock.md` | Base-replace DOCX pipeline |
| L3 | Arbitration-award-style finalization | routing, content lock, template, checklist, visual validation | OpenXML and render checks |
| L4 | Visual validation | `visual-validation.md`, `failure-modes.md` | LibreOffice, Poppler, PNG comparison |

The default path is intentionally light. Exact-template and arbitration-award-style rules are loaded only when the request calls for them.

## Local Verification

Run:

```bash
bash -n skills/legal-document-format/scripts/render_docx.sh
python -m py_compile skills/legal-document-format/scripts/*.py tests/*.py
python -m pytest
```

Current local verification result:

```text
39 passed
```

## Format Gate Policy

Before delivering a formatted legal document, confirm:

- content lock was respected;
- exact-template inheritance was used when requested;
- fonts, font size, line spacing, paragraph indentation, margins, headers, footers, page numbers, and punctuation were checked;
- DOCX rendered successfully to PDF and PNG when visual validation was required;
- reports distinguish errors, warnings, and informational findings;
- all examples and reports are synthetic or properly sanitized.

## Privacy And Safety

Do not commit:

- real pleadings, awards, contracts, evidence, or correspondence;
- private institution templates;
- client names, case numbers, trade secrets, or unpublished facts;
- exported commercial-platform records containing private matter context.

Use synthetic examples unless a human explicitly approves sanitized sample material.

## Roadmap

- Add optional CI once repository credentials support GitHub workflow updates.
- Add pixel-level visual diff as an optional advanced gate.
- Expand OpenXML checks for style inheritance, section properties, fields, and numbering definitions.
- Add more synthetic fixtures for template inheritance and pagination drift.
- Package the skill for common agent runners.
