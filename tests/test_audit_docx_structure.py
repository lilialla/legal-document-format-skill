import json
import os
import stat
import subprocess
import sys
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills" / "legal-document-format" / "scripts" / "audit_docx_structure.py"


CONTENT_TYPES_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""

PACKAGE_RELS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="word/document.xml"/>
</Relationships>
"""

EMPTY_DOCUMENT_RELS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>
"""

DOCUMENT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>First paragraph</w:t></w:r></w:p>
    <w:p><w:r><w:t>Second paragraph</w:t></w:r></w:p>
    <w:tbl>
      <w:tr>
        <w:tc><w:p><w:r><w:t>Cell text</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
    <w:sectPr/>
  </w:body>
</w:document>
"""

EMPTY_DOCUMENT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body/>
</w:document>
"""

FORMATTED_DOCUMENT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:pPr><w:pStyle w:val="Title"/></w:pPr><w:r><w:t>裁决书</w:t></w:r></w:p>
    <w:p><w:r><w:t>申请人：甲方贸易有限公司。</w:t></w:r></w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""

MIXED_FORMAT_DOCUMENT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:pPr><w:pStyle w:val="Title"/></w:pPr>
      <w:r><w:rPr><w:rFonts w:eastAsia="SimSun" w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="32"/></w:rPr><w:t>裁</w:t></w:r>
      <w:r><w:rPr><w:rFonts w:eastAsia="KaiTi" w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="28"/></w:rPr><w:t>决书</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:rPr><w:rFonts w:eastAsia="SimSun" w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:t>申请人：</w:t></w:r>
      <w:r><w:rPr><w:rFonts w:eastAsia="KaiTi" w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="24"/></w:rPr><w:t>被申请人。</w:t></w:r>
      <w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:t>第三人；</w:t></w:r>
    </w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""

STYLES_XML = """<?xml version="1.0" encoding="UTF-8"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:rPr><w:rFonts w:eastAsia="SimSun" w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:rPr><w:rFonts w:eastAsia="SimSun" w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="32"/></w:rPr>
  </w:style>
</w:styles>
"""

STYLES_WITH_BASED_ON_XML = """<?xml version="1.0" encoding="UTF-8"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr><w:rFonts w:eastAsia="SimSun" w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr>
    </w:rPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:styleId="BaseTitle">
    <w:name w:val="BaseTitle"/>
    <w:rPr><w:sz w:val="32"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:basedOn w:val="BaseTitle"/>
  </w:style>
</w:styles>
"""

FOOTER_WITH_PAGE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p>
    <w:r><w:fldChar w:fldCharType="begin"/></w:r>
    <w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>
    <w:r><w:fldChar w:fldCharType="end"/></w:r>
  </w:p>
</w:ftr>
"""

DOCUMENT_WITH_REFERENCES_XML = DOCUMENT_XML.replace(
    "<w:sectPr/>",
    '<w:sectPr><w:headerReference w:type="default" r:id="rId3" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/><w:footerReference w:type="default" r:id="rId4" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/></w:sectPr>',
)

DOCX_HALFWIDTH_PUNCTUATION_XML = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>申请人: 张三, 李四。</w:t></w:r></w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""

CJK_QUOTE_FONT_MISMATCH_XML = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:r><w:rPr><w:rFonts w:eastAsia="FangSong"/></w:rPr><w:t>依据“合作协议”确认。</w:t></w:r>
    </w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""

CJK_QUOTE_FONT_ALIGNED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:r><w:rPr><w:rFonts w:eastAsia="FangSong" w:ascii="FangSong" w:hAnsi="FangSong" w:cs="FangSong"/></w:rPr><w:t>依据“合作协议”确认。</w:t></w:r>
    </w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""


def write_docx(path, parts):
    with zipfile.ZipFile(path, "w") as docx:
        for name, content in parts.items():
            docx.writestr(name, content)


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_audits_minimal_synthetic_docx_with_optional_parts(tmp_path):
    docx_path = tmp_path / "synthetic.docx"
    write_docx(
        docx_path,
        {
            "[Content_Types].xml": CONTENT_TYPES_XML,
            "_rels/.rels": PACKAGE_RELS_XML,
            "word/document.xml": DOCUMENT_WITH_REFERENCES_XML,
            "word/_rels/document.xml.rels": EMPTY_DOCUMENT_RELS_XML,
            "word/styles.xml": "<w:styles xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"/>",
            "word/numbering.xml": "<w:numbering xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"/>",
            "word/header1.xml": "<w:hdr xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"/>",
            "word/footer1.xml": FOOTER_WITH_PAGE_XML,
        },
    )

    completed = run_cli(str(docx_path), "--json")

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["issue_count"] == 0
    assert result["issues"] == []
    assert result["summary"]["section_count"] == 1
    assert result["summary"]["paragraph_count"] == 3
    assert result["summary"]["table_count"] == 1
    assert result["summary"]["has_header_parts"] is True
    assert result["summary"]["has_footer_parts"] is True
    assert result["summary"]["has_styles"] is True
    assert result["summary"]["has_numbering"] is True
    assert result["summary"]["page_field_count"] == 1
    assert result["summary"]["section_footer_reference_count"] == 1


def test_reports_missing_relationships_and_empty_document(tmp_path):
    docx_path = tmp_path / "broken.docx"
    write_docx(
        docx_path,
        {
            "[Content_Types].xml": CONTENT_TYPES_XML,
            "word/document.xml": EMPTY_DOCUMENT_XML,
        },
    )

    completed = run_cli(str(docx_path), "--json")

    assert completed.returncode == 1
    result = json.loads(completed.stdout)
    codes = {issue["code"] for issue in result["issues"]}
    assert "missing_part" in codes
    assert "missing_document_relationships" in codes
    assert "empty_document" in codes
    assert result["summary"]["has_package_relationships"] is False
    assert result["summary"]["has_document_relationships"] is False


def test_reports_malformed_document_relationships(tmp_path):
    docx_path = tmp_path / "broken-rels.docx"
    write_docx(
        docx_path,
        {
            "[Content_Types].xml": CONTENT_TYPES_XML,
            "_rels/.rels": PACKAGE_RELS_XML,
            "word/document.xml": DOCUMENT_XML,
            "word/_rels/document.xml.rels": "<Relationships>",
        },
    )

    completed = run_cli(str(docx_path), "--json")

    assert completed.returncode == 1
    result = json.loads(completed.stdout)
    assert any(
        issue["code"] == "malformed_xml"
        and issue["path"] == "word/_rels/document.xml.rels"
        for issue in result["issues"]
    )


def test_reports_title_and_punctuation_format_summary(tmp_path):
    docx_path = tmp_path / "formatted.docx"
    write_docx(
        docx_path,
        {
            "[Content_Types].xml": CONTENT_TYPES_XML,
            "_rels/.rels": PACKAGE_RELS_XML,
            "word/document.xml": FORMATTED_DOCUMENT_XML,
            "word/_rels/document.xml.rels": EMPTY_DOCUMENT_RELS_XML,
            "word/styles.xml": STYLES_XML,
        },
    )

    completed = run_cli(str(docx_path), "--json")

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["issue_count"] == 0
    assert result["summary"]["title_paragraph_count"] == 1
    assert result["summary"]["title_font_signature_count"] == 1
    assert result["summary"]["title_size_count"] == 1
    assert result["summary"]["punctuation_run_count"] >= 1
    assert result["summary"]["punctuation_font_signature_count"] == 1


def test_resolves_title_style_based_on_and_doc_defaults(tmp_path):
    docx_path = tmp_path / "based-on.docx"
    write_docx(
        docx_path,
        {
            "[Content_Types].xml": CONTENT_TYPES_XML,
            "_rels/.rels": PACKAGE_RELS_XML,
            "word/document.xml": FORMATTED_DOCUMENT_XML,
            "word/_rels/document.xml.rels": EMPTY_DOCUMENT_RELS_XML,
            "word/styles.xml": STYLES_WITH_BASED_ON_XML,
        },
    )

    completed = run_cli(str(docx_path), "--json")

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    codes = {issue["code"] for issue in result["issues"]}
    assert "title_font_missing" not in codes
    assert "title_size_missing" not in codes
    assert result["summary"]["title_size_count"] == 1


def test_reports_mixed_title_and_punctuation_fonts(tmp_path):
    docx_path = tmp_path / "mixed-format.docx"
    write_docx(
        docx_path,
        {
            "[Content_Types].xml": CONTENT_TYPES_XML,
            "_rels/.rels": PACKAGE_RELS_XML,
            "word/document.xml": MIXED_FORMAT_DOCUMENT_XML,
            "word/_rels/document.xml.rels": EMPTY_DOCUMENT_RELS_XML,
            "word/styles.xml": STYLES_XML,
        },
    )

    completed = run_cli(str(docx_path), "--json")

    assert completed.returncode == 0
    result = json.loads(completed.stdout)
    codes = {issue["code"] for issue in result["issues"]}
    assert "title_font_mixed" in codes
    assert "title_size_mixed" in codes
    assert "punctuation_font_missing_east_asia" in codes
    assert "punctuation_font_mixed" in codes
    assert result["summary"]["punctuation_missing_east_asia_count"] >= 1


def test_reports_docx_halfwidth_punctuation_issue(tmp_path):
    docx_path = tmp_path / "halfwidth.docx"
    write_docx(
        docx_path,
        {
            "[Content_Types].xml": CONTENT_TYPES_XML,
            "_rels/.rels": PACKAGE_RELS_XML,
            "word/document.xml": DOCX_HALFWIDTH_PUNCTUATION_XML,
            "word/_rels/document.xml.rels": EMPTY_DOCUMENT_RELS_XML,
            "word/styles.xml": STYLES_XML,
        },
    )

    completed = run_cli(str(docx_path), "--json")

    assert completed.returncode == 0
    result = json.loads(completed.stdout)
    assert any(issue["code"] == "halfwidth_punctuation_cn" for issue in result["issues"])
    assert result["summary"]["halfwidth_punctuation_run_count"] >= 1


def test_reports_cjk_quote_font_mismatch(tmp_path):
    docx_path = tmp_path / "quote-mismatch.docx"
    write_docx(
        docx_path,
        {
            "[Content_Types].xml": CONTENT_TYPES_XML,
            "_rels/.rels": PACKAGE_RELS_XML,
            "word/document.xml": CJK_QUOTE_FONT_MISMATCH_XML,
            "word/_rels/document.xml.rels": EMPTY_DOCUMENT_RELS_XML,
            "word/styles.xml": STYLES_XML,
        },
    )

    completed = run_cli(str(docx_path), "--json")

    assert completed.returncode == 0
    result = json.loads(completed.stdout)
    assert any(issue["code"] == "cjk_quote_font_mismatch" for issue in result["issues"])
    assert result["summary"]["cjk_quote_run_count"] == 1
    assert result["summary"]["cjk_quote_font_mismatch_count"] == 1


def test_accepts_cjk_quote_font_aligned_with_chinese_font(tmp_path):
    docx_path = tmp_path / "quote-aligned.docx"
    write_docx(
        docx_path,
        {
            "[Content_Types].xml": CONTENT_TYPES_XML,
            "_rels/.rels": PACKAGE_RELS_XML,
            "word/document.xml": CJK_QUOTE_FONT_ALIGNED_XML,
            "word/_rels/document.xml.rels": EMPTY_DOCUMENT_RELS_XML,
            "word/styles.xml": STYLES_XML,
        },
    )

    completed = run_cli(str(docx_path), "--json")

    assert completed.returncode == 0
    result = json.loads(completed.stdout)
    assert not any(issue["code"] == "cjk_quote_font_mismatch" for issue in result["issues"])
    assert result["summary"]["cjk_quote_run_count"] == 1
    assert result["summary"]["cjk_quote_font_mismatch_count"] == 0


def test_reports_footer_without_page_field(tmp_path):
    docx_path = tmp_path / "missing-page-field.docx"
    write_docx(
        docx_path,
        {
            "[Content_Types].xml": CONTENT_TYPES_XML,
            "_rels/.rels": PACKAGE_RELS_XML,
            "word/document.xml": DOCUMENT_WITH_REFERENCES_XML,
            "word/_rels/document.xml.rels": EMPTY_DOCUMENT_RELS_XML,
            "word/footer1.xml": "<w:ftr xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"/>",
        },
    )

    completed = run_cli(str(docx_path), "--json")

    assert completed.returncode == 0
    result = json.loads(completed.stdout)
    assert any(issue["code"] == "page_field_missing" for issue in result["issues"])
    assert result["summary"]["page_field_count"] == 0


def test_human_report_and_help_are_available(tmp_path):
    docx_path = tmp_path / "synthetic.docx"
    write_docx(
        docx_path,
        {
            "[Content_Types].xml": CONTENT_TYPES_XML,
            "_rels/.rels": PACKAGE_RELS_XML,
            "word/document.xml": DOCUMENT_XML,
            "word/_rels/document.xml.rels": EMPTY_DOCUMENT_RELS_XML,
        },
    )

    report = run_cli(str(docx_path))
    help_result = run_cli("--help")

    assert report.returncode == 0
    assert "DOCX OpenXML Structure Audit" in report.stdout
    assert "Issues: 0" in report.stdout
    assert help_result.returncode == 0
    assert "audit" in help_result.stdout.lower()


def test_script_is_executable():
    mode = SCRIPT.stat().st_mode
    assert mode & stat.S_IXUSR
    assert os.access(SCRIPT, os.X_OK)
