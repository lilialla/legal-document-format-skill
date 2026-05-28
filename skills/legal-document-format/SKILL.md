---
name: legal-document-format
description: Route and execute legal document formatting tasks with content lock, DOCX template preservation, and optional LibreOffice visual validation.
---

# Legal Document Format

Use this skill when the user asks to format, finalize, typeset, template, render-check, or visually validate a legal document, especially a Chinese legal document, arbitration award, pleading, legal memo, contract, or template-based DOCX.

## Hard Rules

- Formatting must not change legal substance.
- Lock parties, dates, amounts, case numbers, law citations, claims, findings, reasoning, dispositive text, signatures, and attachment lists.
- If the user requests exact template formatting, use the supplied base DOCX or template as the source of truth.
- Do not use ordinary Markdown-to-DOCX conversion as a substitute for exact template inheritance.
- Do not claim a document is delivery-ready until the relevant checklist and render checks are complete.
- Use only synthetic examples unless the user explicitly supplies and authorizes real material.

## Route First

Classify the request before loading detailed references:

| Route | Trigger | Read |
|---|---|---|
| L0 text-clean | Clean pasted law, cases, clauses, headings, or punctuation without DOCX output | `references/content-lock.md`, `references/format-checklist.md` |
| L1 ordinary-docx-format | Make a normal Word document from text or Markdown | `references/routing.md`, `references/format-checklist.md` |
| L2 exact-template | Preserve a supplied DOCX template or base document | `references/exact-template.md`, `references/content-lock.md`, `references/format-checklist.md` |
| L3 arbitration-award | Format an arbitration award or award-like formal instrument | `references/routing.md`, `references/content-lock.md`, `references/exact-template.md`, `references/format-checklist.md`, `references/visual-validation.md` |
| L4 visual-validation | Render DOCX, compare PDF/PNG output, or inspect pagination/layout | `references/visual-validation.md` |

## Tooling

Use the bundled scripts when local files are available:

- `scripts/audit_text.py`: legal text punctuation and spacing audit.
- `scripts/audit_docx_structure.py`: DOCX package and OpenXML structure audit.
- `scripts/render_docx.sh`: DOCX to PDF to PNG render chain.
- `scripts/compare_rendered_pages.py`: lightweight metadata comparison for rendered PNG page directories.

## Output Requirements

For every substantive formatting task, report:

- selected route;
- source files used;
- whether content lock was preserved;
- whether exact template inheritance was required and used;
- checks performed;
- generated files;
- unresolved format or verification items.

For lawyer-facing deliverables, include a final format pass covering line spacing, fonts, paragraph indentation, font size, color, and full-width or half-width punctuation, especially quotation marks and colons.
