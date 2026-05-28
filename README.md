# Legal Document Format Skill

Most AI legal workflows stop after drafting text. This project focuses on the last mile: preserving DOCX templates, locking legal content during formatting, rendering with LibreOffice, and producing a reviewable format report before delivery.

This is an open, synthetic-first Agent Skill for legal document formatting. It is designed for Chinese legal documents, arbitration awards, template-based DOCX finalization, and delivery checks where format quality matters.

## What This Skill Does

- Routes formatting requests by cost and risk instead of loading every rule every time.
- Separates ordinary text cleanup, ordinary Word formatting, exact DOCX template work, arbitration-award formatting, and visual validation.
- Requires content locking during formatting: no silent edits to facts, parties, dates, amounts, law citations, claims, holdings, or dispositive text.
- Favors template inheritance for exact DOCX work instead of recreating a document from a blank file.
- Uses LibreOffice headless and Poppler to render DOCX files into PDF and PNG pages for visual review.

## What This Skill Does Not Do

- It does not provide legal advice.
- It does not generate court-ready or arbitration-ready documents without human review.
- It does not include real cases, private arbitration templates, client facts, institution-specific rules, or confidential examples.
- It does not claim pixel-perfect output without a supplied baseline and a visual comparison step.

## Repository Layout

```text
legal-document-format-skill/
├── README.md
├── LICENSE
├── AGENTS.md
└── skills/
    └── legal-document-format/
        ├── SKILL.md
        ├── references/
        │   ├── routing.md
        │   ├── content-lock.md
        │   ├── exact-template.md
        │   ├── failure-modes.md
        │   ├── format-checklist.md
        │   └── visual-validation.md
        ├── scripts/
        │   ├── README.md
        │   ├── audit_docx_structure.py
        │   ├── audit_text.py
        │   ├── compare_rendered_pages.py
        │   ├── format_gate.py
        │   ├── make_synthetic_docx.py
        │   └── render_docx.sh
        └── examples/
            ├── README.md
            └── synthetic-award-fragment.md
├── tests/
└── pyproject.toml
```

## Routing Model

The skill uses progressive disclosure:

| Level | Request Type | Load | Typical Tooling |
|---|---|---|---|
| L0 | Legal text cleanup | `content-lock.md`, text rules | editor or text audit |
| L1 | Ordinary DOCX formatting | `routing.md`, `format-checklist.md` | Markdown-to-DOCX or Word tooling |
| L2 | Exact template formatting | `exact-template.md`, `content-lock.md` | base-replace DOCX pipeline |
| L3 | Arbitration award finalization | `arbitration-award` route plus format checks | OpenXML and render review |
| L4 | Visual validation | `visual-validation.md` | LibreOffice, Poppler, optional visual diff |

The default path is intentionally light. Exact-template and arbitration-award rules are loaded only when the request calls for them.

## Requirements

Required for rendering:

- LibreOffice with `soffice`
- Poppler with `pdftoppm`

On macOS, the script also checks:

```text
/Applications/LibreOffice.app/Contents/MacOS/soffice
```

## Render A DOCX

```bash
./skills/legal-document-format/scripts/render_docx.sh input.docx output/rendered
```

The command writes:

- `output/rendered/pdf/<name>.pdf`
- `output/rendered/png/<name>-page-1.png`
- one PNG per rendered PDF page

## Audit Text And DOCX Structure

Run a text punctuation and spacing audit:

```bash
./skills/legal-document-format/scripts/audit_text.py "申请人: 张三" --json
```

For sensitive material, use `--no-excerpt` before writing reports to shared logs. Use `--file` when the input must be read from a file. Use `--fail-on-issue` when the audit is acting as a strict gate.

Run a lightweight DOCX OpenXML structure audit:

```bash
./skills/legal-document-format/scripts/audit_docx_structure.py input.docx --json
```

Compare two directories of rendered PNG pages:

```bash
./skills/legal-document-format/scripts/compare_rendered_pages.py baseline/png candidate/png --json
```

Run an aggregate gate over text, DOCX structure, and rendered pages:

```bash
./skills/legal-document-format/scripts/format_gate.py \
  --text "申请人: 张三" \
  --docx input.docx \
  --baseline-png baseline/png \
  --candidate-png candidate/png \
  --json --no-excerpt
```

Use `--text-file path/to/input.txt` when the text input must be read from a file.

Generate a synthetic DOCX fixture for local smoke tests:

```bash
./skills/legal-document-format/scripts/make_synthetic_docx.py output/synthetic.docx
```

## Local Verification

Run the available checks before committing:

```bash
bash -n skills/legal-document-format/scripts/render_docx.sh
python -m py_compile skills/legal-document-format/scripts/*.py tests/*.py
python -m pytest
```

The Python audit scripts use standard-library runtime code. Test execution uses `pytest`.

## Format Gate

Before delivering a formatted legal document, confirm:

- content lock was respected;
- template inheritance was used when exact formatting was requested;
- fonts, font size, line spacing, paragraph indentation, margins, headers, footers, page numbers, and punctuation were checked;
- DOCX rendered successfully to PDF and PNG when visual validation was required;
- all examples and reports are synthetic or properly sanitized.

## Privacy

Do not commit:

- real pleadings, awards, contracts, evidence, or correspondence;
- private institution templates;
- client names, case numbers, trade secrets, or unpublished facts;
- exported commercial-platform records containing private matter context.

Use synthetic examples unless a human explicitly approves sanitized sample material.
