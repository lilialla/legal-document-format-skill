# Exact Template Formatting

Exact template formatting means the output inherits the supplied base DOCX structure. It is not visual imitation.

## Base-Replace Principle

When the user supplies a template or base document:

1. Open the base DOCX as the starting file.
2. Replace only the document content that must change.
3. Preserve template-owned structure and metadata unless the user explicitly authorizes a change.
4. Run structural and visual checks before delivery.

## Preserve

Preserve by default:

- sections and section properties;
- page size and margins;
- headers, footers, page fields, and page numbering;
- styles and latent styles;
- numbering definitions;
- table properties;
- paragraph properties for signature and seal areas;
- footnotes and endnotes where present;
- document settings, compatibility settings, and theme data unless they are known to be harmful.

## High-Risk Failure Modes

- Blank-DOCX recreation that looks similar but lacks the original structure.
- Missing or flattened headers and footers.
- Lost section breaks causing pagination drift.
- Numbering converted to plain text.
- Signature block moved to a different page.
- Font fallback or mixed East Asian / Western font settings.
- Fields converted to stale literal text.
- Unintended content edits during format cleanup.

## Minimum Acceptance Criteria

For exact-template work, the format report must state:

- source template or base document path;
- whether output was generated from the base document;
- whether headers, footers, sections, page numbers, styles, and numbering were preserved;
- whether visual render succeeded;
- known deviations from the base.

