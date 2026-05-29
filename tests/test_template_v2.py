from __future__ import annotations

import importlib.util
import json
import os
import stat
import subprocess
import sys
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APPLY_SCRIPT = REPO_ROOT / "skills" / "legal-document-format" / "scripts" / "apply_docx_template.py"
PARITY_SCRIPT = REPO_ROOT / "skills" / "legal-document-format" / "scripts" / "compare_docx_template_parity.py"


CONTENT_TYPES_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
  <Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
  <Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
</Types>
"""

PACKAGE_RELS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="word/document.xml"/>
</Relationships>
"""

DOCUMENT_RELS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
</Relationships>
"""

DOCUMENT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    <w:p><w:pPr><w:pStyle w:val="Title"/></w:pPr><w:r><w:t>{{TITLE}}</w:t></w:r></w:p>
    <w:p><w:r><w:t>案号：{{CASE_NO}}</w:t></w:r></w:p>
    <w:p><w:r><w:t>申请人：{{CLAIMANT}}</w:t></w:r></w:p>
    <w:p><w:r><w:t>被申请人：{{RESPONDENT}}</w:t></w:r></w:p>
    <w:sectPr>
      <w:headerReference w:type="default" r:id="rId3"/>
      <w:footerReference w:type="default" r:id="rId4"/>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1800" w:bottom="1440" w:left="1800" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>
"""

HEADER_XML = """<?xml version="1.0" encoding="UTF-8"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:t>模板页眉：{{HEADER_TEXT}}</w:t></w:r></w:p>
</w:hdr>
"""

FOOTER_XML = """<?xml version="1.0" encoding="UTF-8"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p><w:pPr><w:jc w:val="center"/></w:pPr>
    <w:r><w:t>第 </w:t></w:r>
    <w:r><w:fldChar w:fldCharType="begin"/></w:r>
    <w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>
    <w:r><w:fldChar w:fldCharType="end"/></w:r>
    <w:r><w:t> 页</w:t></w:r>
  </w:p>
</w:ftr>
"""

STYLES_XML = """<?xml version="1.0" encoding="UTF-8"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:rPr><w:rFonts w:ascii="Times New Roman" w:eastAsia="SimSun" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:pPr><w:jc w:val="center"/></w:pPr>
    <w:rPr><w:b/><w:rFonts w:ascii="Times New Roman" w:eastAsia="SimSun" w:hAnsi="Times New Roman"/><w:sz w:val="32"/></w:rPr>
  </w:style>
</w:styles>
"""


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_template(path: Path, styles_xml: str = STYLES_XML) -> None:
    with zipfile.ZipFile(path, "w") as docx:
        docx.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        docx.writestr("_rels/.rels", PACKAGE_RELS_XML)
        docx.writestr("word/document.xml", DOCUMENT_XML)
        docx.writestr("word/_rels/document.xml.rels", DOCUMENT_RELS_XML)
        docx.writestr("word/header1.xml", HEADER_XML)
        docx.writestr("word/footer1.xml", FOOTER_XML)
        docx.writestr("word/styles.xml", styles_xml)
        docx.writestr("word/numbering.xml", '<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>')


def write_split_placeholder_template(path: Path) -> None:
    split_document_xml = DOCUMENT_XML.replace(
        "<w:r><w:t>{{TITLE}}</w:t></w:r>",
        "<w:r><w:t>{{TI</w:t></w:r><w:r><w:t>TLE}}</w:t></w:r>",
    )
    with zipfile.ZipFile(path, "w") as docx:
        docx.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        docx.writestr("_rels/.rels", PACKAGE_RELS_XML)
        docx.writestr("word/document.xml", split_document_xml)
        docx.writestr("word/_rels/document.xml.rels", DOCUMENT_RELS_XML)
        docx.writestr("word/header1.xml", HEADER_XML)
        docx.writestr("word/footer1.xml", FOOTER_XML)
        docx.writestr("word/styles.xml", STYLES_XML)
        docx.writestr("word/numbering.xml", '<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>')


def run_apply(*args: str):
    return subprocess.run([sys.executable, str(APPLY_SCRIPT), *args], check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def run_parity(*args: str):
    return subprocess.run([sys.executable, str(PARITY_SCRIPT), *args], check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def test_apply_replaces_placeholders_and_preserves_template_parity(tmp_path: Path):
    template = tmp_path / "template.docx"
    output = tmp_path / "output.docx"
    replacements = tmp_path / "replacements.json"
    write_template(template)
    replacements.write_text(
        json.dumps(
            {
                "TITLE": "裁决书",
                "CASE_NO": "SYN-2026-0001",
                "CLAIMANT": "甲方贸易有限公司",
                "RESPONDENT": "乙方设备有限公司",
                "HEADER_TEXT": "仲裁委员会",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    applied = run_apply(str(template), str(output), "--replacements-json", str(replacements), "--json")
    parity = run_parity(str(template), str(output), "--json")

    assert applied.returncode == 0, applied.stderr
    apply_report = json.loads(applied.stdout)
    assert apply_report["summary"]["status"] == "pass"
    assert output.exists()
    with zipfile.ZipFile(output) as docx:
        names = set(docx.namelist())
        assert "word/header1.xml" in names
        assert "word/footer1.xml" in names
        assert "甲方贸易有限公司" in docx.read("word/document.xml").decode("utf-8")
        assert "仲裁委员会" in docx.read("word/header1.xml").decode("utf-8")
        assert "PAGE" in docx.read("word/footer1.xml").decode("utf-8")
    assert parity.returncode == 0, parity.stderr
    parity_report = json.loads(parity.stdout)
    assert parity_report["summary"]["status"] == "pass"
    assert parity_report["issue_count"] == 0


def test_apply_reports_unresolved_placeholder(tmp_path: Path):
    template = tmp_path / "template.docx"
    output = tmp_path / "output.docx"
    write_template(template)

    result = run_apply(str(template), str(output), "--set", "TITLE=裁决书", "--json")

    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["summary"]["status"] == "fail"
    assert not output.exists()
    assert any(issue["code"] == "unresolved_placeholder" for issue in report["issues"])


def test_apply_replaces_placeholder_split_across_runs(tmp_path: Path):
    template = tmp_path / "split-template.docx"
    output = tmp_path / "output.docx"
    write_split_placeholder_template(template)

    result = run_apply(
        str(template),
        str(output),
        "--set",
        "TITLE=裁决书",
        "--set",
        "CASE_NO=SYN-2026-0001",
        "--set",
        "CLAIMANT=甲方贸易有限公司",
        "--set",
        "RESPONDENT=乙方设备有限公司",
        "--set",
        "HEADER_TEXT=仲裁委员会",
        "--json",
    )

    assert result.returncode == 0, result.stdout
    report = json.loads(result.stdout)
    assert report["summary"]["status"] == "pass"
    with zipfile.ZipFile(output) as docx:
        document_xml = docx.read("word/document.xml").decode("utf-8")
        assert "裁决书" in document_xml
        assert "{{TI" not in document_xml
        assert "TLE}}" not in document_xml


def test_parity_detects_style_delta(tmp_path: Path):
    template = tmp_path / "template.docx"
    candidate = tmp_path / "candidate.docx"
    write_template(template)
    write_template(candidate, styles_xml=STYLES_XML.replace('w:val="32"', 'w:val="28"'))

    result = run_parity(str(template), str(candidate), "--json")

    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["summary"]["status"] == "fail"
    assert any(issue["code"] == "xml_structure_delta" and issue["part"] == "word/styles.xml" for issue in report["issues"])


def test_parity_detects_page_field_delta(tmp_path: Path):
    template = tmp_path / "template.docx"
    candidate = tmp_path / "candidate.docx"
    write_template(template)
    with zipfile.ZipFile(candidate, "w") as docx:
        docx.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        docx.writestr("_rels/.rels", PACKAGE_RELS_XML)
        docx.writestr("word/document.xml", DOCUMENT_XML)
        docx.writestr("word/_rels/document.xml.rels", DOCUMENT_RELS_XML)
        docx.writestr("word/header1.xml", HEADER_XML)
        docx.writestr("word/footer1.xml", FOOTER_XML.replace(" PAGE ", " NUMPAGES "))
        docx.writestr("word/styles.xml", STYLES_XML)
        docx.writestr("word/numbering.xml", '<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>')

    result = run_parity(str(template), str(candidate), "--json")

    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert any(issue["code"] == "xml_structure_delta" and issue["part"] == "word/footer1.xml" for issue in report["issues"])


def test_help_and_executable_bits():
    for script in [APPLY_SCRIPT, PARITY_SCRIPT]:
        result = subprocess.run([str(script), "--help"], check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert result.returncode == 0
        assert os.access(script, os.X_OK)
        assert script.stat().st_mode & stat.S_IXUSR
