# Visual Validation

Visual validation checks whether a DOCX can be rendered and reviewed as pages. It does not prove legal correctness.

## Default Render Chain

```text
DOCX -> LibreOffice headless -> PDF -> Poppler pdftoppm -> PNG pages
```

Use `scripts/render_docx.sh` for the default local path.

Use `scripts/compare_rendered_pages.py` when both baseline PNG pages and candidate PNG pages are available. The built-in comparison is a lightweight gate for page count, file names, file size, PNG validity, and dimensions. It is not a pixel diff.

## Required Tools

- `soffice` from LibreOffice.
- `pdftoppm` from Poppler.

On macOS, LibreOffice may be available at:

```text
/Applications/LibreOffice.app/Contents/MacOS/soffice
```

## What To Inspect

After rendering, inspect:

- first page title and margins;
- headers and footers;
- page numbers;
- section transitions;
- tables and long paragraphs;
- numbering and indentation;
- signature and seal blocks;
- final page overflow;
- blank trailing pages.

## Baseline Comparison

If a baseline PDF or PNG snapshot is supplied, compare:

- page count;
- page dimensions;
- visible text position;
- headers, footers, and page numbers;
- signature block location;
- unexpected blank regions or overflow.

Optional tools include `diff-pdf`, Python-based PDF visual comparison, or snapshot-style PNG comparison.

## Report Status

Use:

- `rendered`: PDF and PNG pages were created;
- `render failed`: conversion failed;
- `baseline matched`: visual comparison passed under the chosen tolerance;
- `baseline differed`: visual comparison found differences;
- `no baseline`: render succeeded but no visual diff was possible.
