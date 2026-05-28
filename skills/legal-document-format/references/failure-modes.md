# Failure Modes

Use this reference when a formatting task needs a delivery gate or a human-readable review report. These are formatting and technical failure modes, not legal-merits conclusions.

## Content Lock Failures

- Party names, dates, amounts, claims, citations, dispositive text, signatures, or annex lists changed during formatting.
- Text cleanup rewrote legal meaning instead of only correcting format.
- Suspected typos were corrected without confirmation.

Status: blocking until reviewed.

## Template Inheritance Failures

- Exact-template work started from a blank DOCX instead of the supplied base.
- Headers, footers, page fields, section breaks, styles, or numbering definitions were dropped.
- Signature or seal blocks moved after pagination changed.
- Template-specific page setup was replaced by generic defaults.

Status: blocking for exact-template tasks.

## OpenXML Structure Failures

- DOCX is not a readable ZIP package.
- `[Content_Types].xml`, `_rels/.rels`, `word/document.xml`, or document relationships are missing or malformed.
- `word/document.xml` has no paragraphs or tables.
- Header/footer parts are absent when the template is expected to contain them.

Status: missing or malformed required parts are blocking; absent optional parts are warnings unless the template requires them.

## Text And Punctuation Failures

- Half-width punctuation appears in Chinese legal context.
- English straight quotes appear where Chinese quotation marks are expected.
- Empty brackets or empty book-title marks indicate possible placeholders.
- Consecutive spaces or trailing whitespace suggest copied or unstable formatting.

Status: warnings by default; blocking only when the user chooses strict text audit.

## Render And Visual Failures

- DOCX cannot render to PDF.
- PDF cannot render to PNG pages.
- Rendered page directory is empty.
- Baseline and candidate page counts differ.
- PNG pages are invalid, truncated, or dimensionally different.
- Warning-only file size differences may indicate visual drift and should be inspected.

Status: render failures, empty outputs, invalid PNGs, page-count mismatches, and dimension mismatches are blocking. Size-only differences are warnings.

## Report Discipline

Every report should separate:

- `error`: blocks delivery until fixed or explicitly waived.
- `warning`: requires review but does not automatically block.
- `info`: context for the reviewer.

Do not claim legal correctness from formatting checks. A clean format gate means the checked formatting surfaces passed, not that the legal document is substantively correct.

