from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "skills" / "legal-document-format" / "scripts" / "make_synthetic_docx.py"
AUDIT_SCRIPT_PATH = REPO_ROOT / "skills" / "legal-document-format" / "scripts" / "audit_docx_structure.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def read_document_xml(path: Path) -> str:
    with zipfile.ZipFile(path) as docx:
        return docx.read("word/document.xml").decode("utf-8")


def test_generates_docx_that_structure_audit_accepts(tmp_path):
    audit_docx_structure = load_module("audit_docx_structure", AUDIT_SCRIPT_PATH)
    output = tmp_path / "synthetic.docx"

    result = run_cli(str(output))

    assert result.returncode == 0, result.stderr
    assert output.exists()
    audit = audit_docx_structure.audit_docx(output)
    assert audit["issue_count"] == 0
    assert audit["summary"]["has_content_types"] is True
    assert audit["summary"]["has_package_relationships"] is True
    assert audit["summary"]["has_document_xml"] is True
    assert audit["summary"]["has_document_relationships"] is True
    assert audit["summary"]["has_styles"] is True
    assert audit["summary"]["has_numbering"] is True
    assert audit["summary"]["has_header_parts"] is True
    assert audit["summary"]["has_footer_parts"] is True
    assert audit["summary"]["paragraph_count"] >= 5
    assert audit["summary"]["section_count"] == 1


def test_default_cli_does_not_overwrite_existing_file(tmp_path):
    output = tmp_path / "synthetic.docx"
    output.write_bytes(b"existing")

    result = run_cli(str(output))

    assert result.returncode == 2
    assert output.read_bytes() == b"existing"
    assert "already exists" in result.stderr


def test_force_overwrites_existing_file(tmp_path):
    output = tmp_path / "synthetic.docx"
    output.write_bytes(b"existing")

    result = run_cli(str(output), "--force")

    assert result.returncode == 0, result.stderr
    assert output.read_bytes() != b"existing"
    with zipfile.ZipFile(output) as docx:
        assert "word/document.xml" in docx.namelist()
        assert "word/header1.xml" in docx.namelist()
        assert "word/footer1.xml" in docx.namelist()


def test_custom_title_and_case_no_are_written_to_document_xml(tmp_path):
    output = tmp_path / "custom.docx"
    title = "Synthetic Custom Title"
    case_no = "SYN-2026-0009"

    result = run_cli(str(output), "--title", title, "--case-no", case_no)

    assert result.returncode == 0, result.stderr
    document_xml = read_document_xml(output)
    assert title in document_xml
    assert case_no in document_xml
    assert "申请人：Synthetic Claimant Placeholder" in document_xml
    assert "被申请人：Synthetic Respondent Placeholder" in document_xml
    assert "synthetic" in document_xml.lower()


def test_cli_help_and_executable_bit():
    result = subprocess.run(
        [str(SCRIPT_PATH), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )

    mode = SCRIPT_PATH.stat().st_mode
    assert mode & stat.S_IXUSR
    assert os.access(SCRIPT_PATH, os.X_OK)
    assert "OUTPUT.docx" in result.stdout
    assert "--title" in result.stdout
    assert "--case-no" in result.stdout
    assert "--force" in result.stdout
