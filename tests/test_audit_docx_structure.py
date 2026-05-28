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
            "word/document.xml": DOCUMENT_XML,
            "word/_rels/document.xml.rels": EMPTY_DOCUMENT_RELS_XML,
            "word/styles.xml": "<w:styles xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"/>",
            "word/numbering.xml": "<w:numbering xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"/>",
            "word/header1.xml": "<w:hdr xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"/>",
            "word/footer1.xml": "<w:ftr xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"/>",
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
