from __future__ import annotations

import importlib.util
import json
import os
import stat
import struct
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills" / "legal-document-format" / "scripts" / "format_gate.py"


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
    <w:sectPr/>
  </w:body>
</w:document>
"""

EMPTY_DOCUMENT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body/>
</w:document>
"""


def load_module():
    spec = importlib.util.spec_from_file_location("format_gate", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_cli(*args: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def write_docx(path: Path, parts: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w") as docx:
        for name, content in parts.items():
            docx.writestr(name, content)


def write_valid_docx(path: Path) -> None:
    write_docx(
        path,
        {
            "[Content_Types].xml": CONTENT_TYPES_XML,
            "_rels/.rels": PACKAGE_RELS_XML,
            "word/document.xml": DOCUMENT_XML,
            "word/_rels/document.xml.rels": EMPTY_DOCUMENT_RELS_XML,
        },
    )


def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def minimal_png(width: int, height: int, payload: bytes = b"") -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + (png_chunk(b"tEXt", payload) if payload else b"")
        + png_chunk(b"IEND", b"")
    )


def write_png(directory: Path, name: str, width: int, height: int, payload: bytes = b"") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_bytes(minimal_png(width, height, payload))


def test_text_warning_returns_zero_and_aggregates_json():
    result = run_cli("--text", "申请人: 张三", "--json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert set(payload) == {"summary", "checks", "issue_count", "issues"}
    assert payload["summary"]["status"] == "warning"
    assert payload["summary"]["warning_count"] >= 1
    assert payload["checks"][0]["name"] == "text"
    assert any(issue["check"] == "text" and issue["code"] == "HALFWIDTH_COLON_CN" for issue in payload["issues"])


def test_fail_on_warning_returns_one_for_text_warning():
    result = run_cli("--text", "申请人: 张三", "--json", "--fail-on-warning")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["summary"]["status"] == "warning"


def test_docx_error_returns_one(tmp_path: Path):
    broken_docx = tmp_path / "broken.docx"
    write_docx(
        broken_docx,
        {
            "[Content_Types].xml": CONTENT_TYPES_XML,
            "_rels/.rels": PACKAGE_RELS_XML,
            "word/document.xml": EMPTY_DOCUMENT_XML,
            "word/_rels/document.xml.rels": EMPTY_DOCUMENT_RELS_XML,
        },
    )

    result = run_cli("--docx", str(broken_docx), "--json")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["summary"]["status"] == "fail"
    assert any(issue["check"] == "docx" and issue["code"] == "empty_document" for issue in payload["issues"])


def test_png_warning_only_returns_zero(tmp_path: Path):
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    write_png(baseline, "page-1.png", 800, 1000)
    write_png(candidate, "page-1.png", 800, 1000, b"candidate-size-delta")

    result = run_cli("--baseline-png", str(baseline), "--candidate-png", str(candidate), "--json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["summary"]["status"] == "warning"
    assert payload["summary"]["error_count"] == 0
    assert any(issue["check"] == "png" and issue["code"] == "size_delta" for issue in payload["issues"])


def test_no_input_is_argument_error():
    result = run_cli("--json")

    assert result.returncode == 2
    assert "provide at least one check input" in result.stderr


def test_require_visual_requires_png_pair():
    result = run_cli("--docx", "input.docx", "--require-visual", "--json")

    assert result.returncode == 2
    assert "--require-visual requires --baseline-png and --candidate-png" in result.stderr


def test_no_excerpt_omits_sensitive_text_from_json_and_report():
    json_result = run_cli("--text", "申请人: 张三", "--json", "--no-excerpt")
    human_result = run_cli("--text", "申请人: 张三", "--no-excerpt")

    assert json_result.returncode == 0
    payload = json.loads(json_result.stdout)
    assert payload["issues"]
    assert all("excerpt" not in issue for issue in payload["issues"])
    assert "申请人: 张三" not in human_result.stdout
    assert "HALFWIDTH_COLON_CN" in human_result.stdout


def test_text_with_slash_is_direct_text_not_missing_path():
    result = run_cli("--text", "合同编号：A/B", "--json", "--no-excerpt")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["checks"][0]["summary"]["source"] == "direct text"
    assert all("合同编号：A/B" not in json.dumps(issue, ensure_ascii=False) for issue in payload["issues"])


def test_text_file_decode_error_returns_structured_json(tmp_path: Path):
    input_file = tmp_path / "binary.txt"
    input_file.write_bytes(b"\xff\xfe\x00")

    result = run_cli("--text-file", str(input_file), "--json", "--no-excerpt")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["summary"]["status"] == "fail"
    assert payload["checks"][0]["summary"]["source"] == str(input_file)
    assert any(issue["code"] == "text_input_error" for issue in payload["issues"])
    assert "\ufffd" not in result.stdout


def test_text_file_requires_existing_file(tmp_path: Path):
    missing = tmp_path / "missing.txt"

    result = run_cli("--text-file", str(missing), "--json")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["summary"]["status"] == "fail"
    assert any(issue["code"] == "text_input_error" for issue in payload["issues"])


def test_combines_all_successful_check_types(tmp_path: Path):
    docx_path = tmp_path / "valid.docx"
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    write_valid_docx(docx_path)
    write_png(baseline, "page-1.png", 800, 1000)
    write_png(candidate, "page-1.png", 800, 1000)

    result = run_cli(
        "--text",
        "申请人认为，本案事实清楚。",
        "--docx",
        str(docx_path),
        "--baseline-png",
        str(baseline),
        "--candidate-png",
        str(candidate),
        "--json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["summary"]["status"] == "pass"
    assert payload["summary"]["checks_run"] == ["text", "docx", "png"]
    assert payload["issue_count"] == 0


def test_module_build_report_can_read_text_file(tmp_path: Path):
    module = load_module()
    input_file = tmp_path / "sample.txt"
    input_file.write_text("申请人: 张三\n", encoding="utf-8")
    parser = module.build_parser()
    args = parser.parse_args(["--text", str(input_file), "--json"])

    report = module.build_report(args)

    assert report["checks"][0]["summary"]["source"] == str(input_file)
    assert any(issue["code"] == "HALFWIDTH_COLON_CN" for issue in report["issues"])


def test_help_and_executable_bit():
    result = subprocess.run(
        [str(SCRIPT), "--help"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0
    assert os.access(SCRIPT, os.X_OK)
    assert SCRIPT.stat().st_mode & stat.S_IXUSR
    assert "--text" in result.stdout
    assert "--text-file" in result.stdout
    assert "--docx" in result.stdout
    assert "--baseline-png" in result.stdout
    assert "--require-visual" in result.stdout
    assert "--fail-on-warning" in result.stdout
