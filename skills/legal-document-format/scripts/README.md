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

## `format_gate.py`

Aggregates text, DOCX structure, and rendered-page checks into one local report.

```bash
./skills/legal-document-format/scripts/format_gate.py \
  --text "申请人: 张三" \
  --docx input.docx \
  --baseline-png baseline/png \
  --candidate-png candidate/png \
  --json --no-excerpt
```

Use `--text-file path/to/input.txt` when the text input must be read from a file.

The aggregate gate returns exit code `1` only when at least one check reports an error. Warning-only reports exit `0`.

## `make_synthetic_docx.py`

Generates a minimal synthetic DOCX fixture for local smoke tests.

```bash
./skills/legal-document-format/scripts/make_synthetic_docx.py output/synthetic.docx
```

The generator refuses to overwrite existing files unless `--force` is provided.

All scripts support `--help`; Python audit scripts support human-readable output and `--json`. Scripts return non-zero for structural or visual errors. Warning-only text audits return zero unless `--fail-on-issue` is used. Rendered-page comparison reports `status: warning` for warning-only differences while keeping exit code `0`.
