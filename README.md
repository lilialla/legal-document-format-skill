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
        │   ├── format-checklist.md
        │   └── visual-validation.md
        ├── scripts/
        │   └── render_docx.sh
        └── examples/
            ├── README.md
            └── synthetic-award-fragment.md
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

