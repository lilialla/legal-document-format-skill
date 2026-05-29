from __future__ import annotations

import importlib.util
import json
import struct
import subprocess
import sys
import zlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT
    / "skills"
    / "legal-document-format"
    / "scripts"
    / "compare_rendered_pages.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("compare_rendered_pages", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def minimal_png(width: int, height: int, payload: bytes = b"") -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = png_chunk(
        b"IHDR",
        struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0),
    )
    text = png_chunk(b"tEXt", payload) if payload else b""
    iend = png_chunk(b"IEND", b"")
    return signature + ihdr + text + iend


def write_png(directory: Path, name: str, width: int, height: int, payload: bytes = b""):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_bytes(minimal_png(width, height, payload))


def test_compare_passes_for_matching_png_metadata(tmp_path: Path):
    module = load_module()
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    write_png(baseline, "doc-page-1.png", 800, 1000)
    write_png(candidate, "doc-page-1.png", 800, 1000)

    report = module.compare_page_sets(baseline, candidate)

    assert report["summary"]["status"] == "pass"
    assert report["issue_count"] == 0
    assert report["issues"] == []


def test_compare_reports_page_count_missing_extra_dimensions_and_size(tmp_path: Path):
    module = load_module()
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    write_png(baseline, "doc-page-1.png", 800, 1000)
    write_png(baseline, "doc-page-2.png", 800, 1000)
    write_png(baseline, "doc-page-4.png", 800, 1000)
    write_png(candidate, "doc-page-1.png", 801, 1000, b"candidate-size-delta")
    write_png(candidate, "doc-page-3.png", 800, 1000)

    report = module.compare_page_sets(baseline, candidate)
    codes = [item["code"] for item in report["issues"]]

    assert report["summary"]["status"] == "fail"
    assert "page_count_mismatch" in codes
    assert "missing_page" in codes
    assert "extra_page" in codes
    assert "dimension_mismatch" in codes
    assert "size_delta" in codes
    assert any(item["severity"] == "error" for item in report["issues"])


def test_compare_reports_invalid_png_signature(tmp_path: Path):
    module = load_module()
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    write_png(baseline, "doc-page-1.png", 800, 1000)
    candidate.mkdir()
    (candidate / "doc-page-1.png").write_bytes(b"not a png")

    report = module.compare_page_sets(baseline, candidate)

    assert any(item["code"] == "invalid_png" for item in report["issues"])
    assert any(item["code"] == "size_delta" for item in report["issues"])


def test_compare_reports_empty_png_directories_as_error(tmp_path: Path):
    module = load_module()
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    baseline.mkdir()
    candidate.mkdir()

    report = module.compare_page_sets(baseline, candidate)

    assert report["summary"]["status"] == "fail"
    assert report["summary"]["error_count"] == 2
    assert [item["code"] for item in report["issues"]].count("no_png_pages") == 2


def test_compare_reports_truncated_pseudo_png(tmp_path: Path):
    module = load_module()
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    write_png(baseline, "doc-page-1.png", 800, 1000)
    candidate.mkdir()
    pseudo_header = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 800, 1000)
    (candidate / "doc-page-1.png").write_bytes(pseudo_header)

    report = module.compare_page_sets(baseline, candidate)

    assert any(item["code"] == "invalid_png" for item in report["issues"])
    assert report["summary"]["error_count"] >= 1


def test_cli_returns_zero_for_warning_only_size_delta(tmp_path: Path):
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    write_png(baseline, "doc-page-1.png", 800, 1000)
    write_png(candidate, "doc-page-1.png", 800, 1000, b"candidate-size-delta")

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(baseline), str(candidate), "--json"],
        check=False,
        text=True,
        capture_output=True,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["summary"]["status"] == "warning"
    assert payload["summary"]["error_count"] == 0
    assert any(item["code"] == "size_delta" for item in payload["issues"])
    assert any(item["code"] == "content_delta" for item in payload["issues"])


def test_cli_fail_on_warning_returns_one_for_content_delta(tmp_path: Path):
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    write_png(baseline, "doc-page-1.png", 800, 1000)
    write_png(candidate, "doc-page-1.png", 800, 1000, b"candidate-size-delta")

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(baseline), str(candidate), "--json", "--fail-on-warning"],
        check=False,
        text=True,
        capture_output=True,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["summary"]["status"] == "warning"


def test_compare_reports_content_delta_for_same_size_different_png(tmp_path: Path):
    module = load_module()
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    write_png(baseline, "doc-page-1.png", 800, 1000, b"alpha")
    write_png(candidate, "doc-page-1.png", 800, 1000, b"bravo")

    report = module.compare_page_sets(baseline, candidate)

    assert report["summary"]["status"] == "warning"
    assert any(item["code"] == "content_delta" for item in report["issues"])


def test_cli_help_runs():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "BASELINE_DIR" in result.stdout
    assert "--json" in result.stdout
    assert "--fail-on-warning" in result.stdout


def test_cli_json_output(tmp_path: Path):
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    write_png(baseline, "doc-page-1.png", 800, 1000)
    write_png(candidate, "doc-page-1.png", 800, 1000)

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(baseline), str(candidate), "--json"],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert set(payload) == {"summary", "issue_count", "issues"}
    assert payload["summary"]["status"] == "pass"
    assert payload["issue_count"] == 0
