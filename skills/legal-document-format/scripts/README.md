# Scripts

These scripts are local quality gates for the legal document format skill. They use only local files and should not contain secrets, private templates, or real case material.

## `render_docx.sh`

Renders a DOCX to PDF with LibreOffice headless, then renders the PDF to PNG pages with Poppler.

```bash
./skills/legal-document-format/scripts/render_docx.sh input.docx output/rendered
```

## `audit_text.py`

Audits text or a UTF-8 text file for legal-format punctuation and spacing issues.

```bash
./skills/legal-document-format/scripts/audit_text.py "申请人: 张三" --json
```

Use `--file` when the input must be a file path, `--no-excerpt` for sensitive documents, and `--fail-on-issue` when the audit should behave as a strict gate.

## `audit_docx_structure.py`

Audits a DOCX package with standard-library ZIP and OpenXML parsing. It reports package parts, sections, paragraphs, tables, headers, footers, styles, and numbering.

```bash
./skills/legal-document-format/scripts/audit_docx_structure.py input.docx --json
```

## `compare_rendered_pages.py`

Compares two directories of rendered PNG pages. This is a metadata gate, not a pixel diff.

```bash
./skills/legal-document-format/scripts/compare_rendered_pages.py baseline/png candidate/png --json
```

All scripts support `--help`; Python audit scripts support human-readable output and `--json`. Scripts return non-zero for structural or visual errors. Warning-only text audits return zero unless `--fail-on-issue` is used. Rendered-page comparison reports `status: warning` for warning-only differences while keeping exit code `0`.
