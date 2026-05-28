# Routing

Use the narrowest route that fits the request. Escalate only when the user asks for stronger fidelity or the document type demands it.

## L0 Text Cleanup

Use for pasted text, law provisions, case excerpts, headings, and punctuation cleanup.

Do:

- preserve legal substance;
- normalize obvious spacing and punctuation defects;
- keep source order unless the user requests restructuring.

Do not:

- infer missing legal content;
- rewrite holdings, claims, amounts, or dates;
- convert to DOCX unless requested.

## L1 Ordinary DOCX Formatting

Use for ordinary legal memos, drafts, reports, or Markdown-to-Word work where exact template fidelity is not required.

Do:

- apply the requested font, font size, line spacing, paragraph indentation, margins, and heading hierarchy;
- produce a readable format report;
- run render validation when delivery quality matters.

Do not:

- represent the result as exact template formatting;
- imitate a template from visual memory.

## L2 Exact Template Formatting

Use when the user provides a DOCX template, base award, institutional format, or asks to keep the same style, header, footer, page setup, sections, or pagination logic.

Do:

- start from the supplied base DOCX;
- replace content inside the base structure;
- preserve styles, headers, footers, sections, numbering, page setup, and signature blocks unless explicitly changed.

Do not:

- create a blank DOCX and manually approximate the template;
- drop section breaks or page fields;
- flatten headers, footers, or numbering.

## L3 Arbitration Award Formatting

Use for arbitration awards, award-like dispositive documents, and final-format formal instruments.

Do:

- treat content as locked unless the user explicitly authorizes legal edits;
- preserve dispositive text and signature areas;
- check title, parties, procedural history, facts, tribunal reasoning, award items, costs, dates, seals, and annexes as formatting surfaces only;
- run visual validation when tools are available.

Do not:

- alter the award result while formatting;
- add unsupported facts or legal reasoning;
- claim readiness without lawyer review.

## L4 Visual Validation

Use when the user asks to render, inspect, compare, or validate layout.

Do:

- render DOCX to PDF with LibreOffice;
- render PDF to PNG with Poppler;
- compare against a baseline only when a baseline exists;
- report visual risks such as pagination shifts, missing headers, missing footers, broken numbering, overflow, and signature block displacement.

Do not:

- treat a successful render as proof of legal correctness;
- claim pixel-level identity without a visual diff.

