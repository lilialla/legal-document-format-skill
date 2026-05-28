#!/usr/bin/env python3
"""Generate a synthetic minimal DOCX fixture for format-gate testing."""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CONTENT_TYPE_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

DEFAULT_TITLE = "Synthetic DOCX 示例文书"
DEFAULT_CASE_NO = "SYNTHETIC-CASE-NO-0001"
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def xml_text(value: str) -> str:
    return escape(value, {"'": "&apos;", '"': "&quot;"})


def paragraph(text: str, style: str | None = None) -> str:
    style_xml = f'<w:pPr><w:pStyle w:val="{xml_text(style)}"/></w:pPr>' if style else ""
    return f"<w:p>{style_xml}<w:r><w:t>{xml_text(text)}</w:t></w:r></w:p>"


def content_types_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="{CONTENT_TYPE_NS}">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
</Types>
"""


def package_relationships_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{REL_NS}">
  <Relationship Id="rId1" Type="{OFFICE_REL_NS}/officeDocument" Target="word/document.xml"/>
</Relationships>
"""


def document_relationships_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{REL_NS}">
  <Relationship Id="rId1" Type="{OFFICE_REL_NS}/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="{OFFICE_REL_NS}/numbering" Target="numbering.xml"/>
</Relationships>
"""


def document_xml(title: str, case_no: str) -> str:
    body = "\n    ".join(
        [
            paragraph(title, "Title"),
            paragraph(f"案号：{case_no}"),
            paragraph("申请人：Synthetic Claimant Placeholder"),
            paragraph("被申请人：Synthetic Respondent Placeholder"),
            paragraph("声明：本 DOCX 由 make_synthetic_docx.py 生成，仅用于 synthetic 格式测试；不含真实案件、当事人或机构模板。"),
            paragraph("一、Synthetic Facts"),
            paragraph("本段为 synthetic 占位内容，用于验证 DOCX 结构、渲染与格式审计流程。"),
        ]
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{WORD_NS}">
  <w:body>
    {body}
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1800" w:bottom="1440" w:left="1800" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>
"""


def styles_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{WORD_NS}">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:qFormat/>
    <w:rPr>
      <w:rFonts w:ascii="Times New Roman" w:eastAsia="SimSun" w:hAnsi="Times New Roman"/>
      <w:sz w:val="24"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:basedOn w:val="Normal"/>
    <w:qFormat/>
    <w:pPr>
      <w:jc w:val="center"/>
      <w:spacing w:after="240"/>
    </w:pPr>
    <w:rPr>
      <w:b/>
      <w:rFonts w:ascii="Times New Roman" w:eastAsia="SimSun" w:hAnsi="Times New Roman"/>
      <w:sz w:val="32"/>
    </w:rPr>
  </w:style>
</w:styles>
"""


def numbering_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="{WORD_NS}"/>
"""


def docx_parts(title: str, case_no: str) -> dict[str, str]:
    return {
        "[Content_Types].xml": content_types_xml(),
        "_rels/.rels": package_relationships_xml(),
        "word/document.xml": document_xml(title, case_no),
        "word/_rels/document.xml.rels": document_relationships_xml(),
        "word/styles.xml": styles_xml(),
        "word/numbering.xml": numbering_xml(),
    }


def write_docx(output_path: Path, title: str, case_no: str) -> None:
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as docx:
        for name, content in docx_parts(title, case_no).items():
            info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            docx.writestr(info, content.encode("utf-8"))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a minimal synthetic DOCX fixture for legal document format tests.",
    )
    parser.add_argument("output_docx", metavar="OUTPUT.docx", help="destination DOCX path")
    parser.add_argument("--title", default=DEFAULT_TITLE, help="synthetic document title")
    parser.add_argument("--case-no", default=DEFAULT_CASE_NO, help="synthetic case number")
    parser.add_argument("--force", action="store_true", help="overwrite OUTPUT.docx if it already exists")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    output_path = Path(args.output_docx)

    if output_path.suffix.lower() != ".docx":
        print(f"Output path must use a .docx extension: {output_path}", file=sys.stderr)
        return 2
    if output_path.exists() and not args.force:
        print(f"Output file already exists; use --force to overwrite: {output_path}", file=sys.stderr)
        return 2
    if output_path.exists() and not output_path.is_file():
        print(f"Output path exists and is not a file: {output_path}", file=sys.stderr)
        return 2
    if not output_path.parent.exists():
        print(f"Output directory does not exist: {output_path.parent}", file=sys.stderr)
        return 2

    try:
        write_docx(output_path, args.title, args.case_no)
    except OSError as exc:
        print(f"Could not write DOCX: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote synthetic DOCX: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
