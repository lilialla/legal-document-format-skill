#!/usr/bin/env python3
"""Lightweight rendered PNG page gate for legal document format checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SIZE_DELTA_WARNING_THRESHOLD = 0


@dataclass(frozen=True)
class PageInfo:
    name: str
    path: Path
    size_bytes: int
    png_valid: bool
    width: int | None
    height: int | None
    sha256: str | None
    error: str | None = None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare two directories of rendered PNG pages using release gates: "
            "page count, file names, PNG validity, IHDR dimensions, file size, and byte hashes."
        )
    )
    parser.add_argument(
        "baseline_dir",
        metavar="BASELINE_DIR",
        help="Directory containing baseline PNG pages.",
    )
    parser.add_argument(
        "candidate_dir",
        metavar="CANDIDATE_DIR",
        help="Directory containing candidate PNG pages.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write a structured JSON report instead of a human-readable report.",
    )
    return parser.parse_args(argv)


def read_png_info(path: Path) -> tuple[bool, int | None, int | None, str | None]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        return False, None, None, f"cannot read PNG: {exc}"

    if len(data) < 33:
        return False, None, None, "file is too small to contain a complete PNG IHDR chunk"
    if data[:8] != PNG_SIGNATURE:
        return False, None, None, "invalid PNG signature"

    ihdr_length = struct.unpack(">I", data[8:12])[0]
    chunk_type = data[12:16]
    if chunk_type != b"IHDR":
        return False, None, None, "first PNG chunk is not IHDR"
    if ihdr_length != 13:
        return False, None, None, "IHDR chunk length must be 13 bytes"

    ihdr_end = 16 + ihdr_length
    ihdr_crc_end = ihdr_end + 4
    if len(data) < ihdr_crc_end:
        return False, None, None, "file is truncated before the IHDR CRC"

    expected_crc = struct.unpack(">I", data[ihdr_end:ihdr_crc_end])[0]
    actual_crc = zlib.crc32(data[12:ihdr_end]) & 0xFFFFFFFF
    if expected_crc != actual_crc:
        return False, None, None, "IHDR CRC does not match"

    width, height = struct.unpack(">II", data[16:24])
    if width == 0 or height == 0:
        return False, width, height, "IHDR dimensions must be non-zero"

    offset = ihdr_crc_end
    found_iend = False
    while offset < len(data):
        if len(data) < offset + 8:
            return False, width, height, "file ends in the middle of a PNG chunk header"
        chunk_length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_data_start = offset + 8
        chunk_data_end = chunk_data_start + chunk_length
        chunk_crc_end = chunk_data_end + 4
        if len(data) < chunk_crc_end:
            return False, width, height, f"file is truncated in {chunk_type.decode('latin1')} chunk"
        expected_chunk_crc = struct.unpack(">I", data[chunk_data_end:chunk_crc_end])[0]
        actual_chunk_crc = zlib.crc32(data[offset + 4 : chunk_data_end]) & 0xFFFFFFFF
        if expected_chunk_crc != actual_chunk_crc:
            return False, width, height, f"{chunk_type.decode('latin1')} CRC does not match"
        offset = chunk_crc_end
        if chunk_type == b"IEND":
            found_iend = True
            break

    if not found_iend:
        return False, width, height, "PNG has no complete IEND chunk"

    return True, width, height, None


def file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def collect_png_pages(directory: Path) -> tuple[dict[str, PageInfo], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    pages: dict[str, PageInfo] = {}

    if not directory.exists():
        issues.append(
            issue(
                "directory_missing",
                f"Directory does not exist: {directory}",
                "error",
                directory=str(directory),
            )
        )
        return pages, issues
    if not directory.is_dir():
        issues.append(
            issue(
                "directory_not_found",
                f"Path is not a directory: {directory}",
                "error",
                directory=str(directory),
            )
        )
        return pages, issues

    for path in sorted(directory.iterdir(), key=lambda item: item.name):
        if not path.is_file() or path.suffix.lower() != ".png":
            continue
        stat = path.stat()
        valid, width, height, error = read_png_info(path)
        pages[path.name] = PageInfo(
            name=path.name,
            path=path,
            size_bytes=stat.st_size,
            png_valid=valid,
            width=width,
            height=height,
            sha256=file_sha256(path),
            error=error,
        )
        if not valid:
            issues.append(
                issue(
                    "invalid_png",
                    f"{path.name}: {error}",
                    "error",
                    file=path.name,
                    path=str(path),
                )
            )

    return pages, issues


def issue(code: str, message: str, severity: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "code": code,
        "message": message,
        "severity": severity,
    }
    payload.update(extra)
    return payload


def compare_page_sets(baseline_dir: Path, candidate_dir: Path) -> dict[str, Any]:
    baseline_pages, baseline_issues = collect_png_pages(baseline_dir)
    candidate_pages, candidate_issues = collect_png_pages(candidate_dir)
    issues = baseline_issues + candidate_issues

    baseline_names = set(baseline_pages)
    candidate_names = set(candidate_pages)

    if not baseline_names and not baseline_issues:
        issues.append(
            issue(
                "no_png_pages",
                f"Baseline directory contains no PNG pages: {baseline_dir}",
                "error",
                directory=str(baseline_dir),
            )
        )
    if not candidate_names and not candidate_issues:
        issues.append(
            issue(
                "no_png_pages",
                f"Candidate directory contains no PNG pages: {candidate_dir}",
                "error",
                directory=str(candidate_dir),
            )
        )

    if len(baseline_names) != len(candidate_names):
        issues.append(
            issue(
                "page_count_mismatch",
                (
                    "PNG page count differs: "
                    f"baseline has {len(baseline_names)}, candidate has {len(candidate_names)}"
                ),
                "error",
                baseline_count=len(baseline_names),
                candidate_count=len(candidate_names),
            )
        )

    for name in sorted(baseline_names - candidate_names):
        issues.append(
            issue(
                "missing_page",
                f"Candidate is missing baseline page: {name}",
                "error",
                file=name,
            )
        )

    for name in sorted(candidate_names - baseline_names):
        issues.append(
            issue(
                "extra_page",
                f"Candidate has an extra page not found in baseline: {name}",
                "warning",
                file=name,
            )
        )

    common_names = sorted(baseline_names & candidate_names)
    for name in common_names:
        baseline = baseline_pages[name]
        candidate = candidate_pages[name]

        if (
            baseline.png_valid
            and candidate.png_valid
            and (baseline.width, baseline.height) != (candidate.width, candidate.height)
        ):
            issues.append(
                issue(
                    "dimension_mismatch",
                    (
                        f"{name}: dimensions differ: baseline "
                        f"{baseline.width}x{baseline.height}, candidate "
                        f"{candidate.width}x{candidate.height}"
                    ),
                    "error",
                    file=name,
                    baseline_width=baseline.width,
                    baseline_height=baseline.height,
                    candidate_width=candidate.width,
                    candidate_height=candidate.height,
                )
            )

        delta_bytes = candidate.size_bytes - baseline.size_bytes
        if abs(delta_bytes) > SIZE_DELTA_WARNING_THRESHOLD:
            delta_percent = (
                (delta_bytes / baseline.size_bytes) * 100
                if baseline.size_bytes
                else None
            )
            issues.append(
                issue(
                    "size_delta",
                    (
                        f"{name}: file size differs by {delta_bytes:+d} bytes "
                        f"(baseline {baseline.size_bytes}, candidate {candidate.size_bytes})"
                    ),
                    "warning",
                    file=name,
                    baseline_size=baseline.size_bytes,
                    candidate_size=candidate.size_bytes,
                    delta_bytes=delta_bytes,
                    delta_percent=round(delta_percent, 4)
                    if delta_percent is not None
                    else None,
                )
            )

        if (
            baseline.png_valid
            and candidate.png_valid
            and baseline.sha256
            and candidate.sha256
            and baseline.sha256 != candidate.sha256
        ):
            issues.append(
                issue(
                    "content_delta",
                    f"{name}: PNG bytes differ while page name is shared",
                    "warning",
                    file=name,
                    baseline_sha256=baseline.sha256,
                    candidate_sha256=candidate.sha256,
                )
            )

    error_count = sum(1 for item in issues if item["severity"] == "error")
    warning_count = sum(1 for item in issues if item["severity"] == "warning")
    if error_count:
        status = "fail"
    elif warning_count:
        status = "warning"
    else:
        status = "pass"
    summary = {
        "status": status,
        "baseline_dir": str(baseline_dir),
        "candidate_dir": str(candidate_dir),
        "baseline_page_count": len(baseline_names),
        "candidate_page_count": len(candidate_names),
        "compared_page_count": len(common_names),
        "error_count": error_count,
        "warning_count": warning_count,
    }

    return {
        "summary": summary,
        "issue_count": len(issues),
        "issues": issues,
    }


def format_human_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "Rendered PNG Page Comparison",
        "",
        f"Status: {summary['status'].upper()}",
        f"Baseline: {summary['baseline_dir']}",
        f"Candidate: {summary['candidate_dir']}",
        (
            "Pages: "
            f"baseline={summary['baseline_page_count']} "
            f"candidate={summary['candidate_page_count']} "
            f"compared={summary['compared_page_count']}"
        ),
        (
            "Issues: "
            f"{report['issue_count']} "
            f"(errors={summary['error_count']}, warnings={summary['warning_count']})"
        ),
    ]

    if report["issues"]:
        lines.extend(["", "Issue Details:"])
        for item in report["issues"]:
            lines.append(f"- [{item['severity']}] {item['code']}: {item['message']}")
    else:
        lines.extend(["", "No rendered page differences found by the built-in gate."])

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = compare_page_sets(Path(args.baseline_dir), Path(args.candidate_dir))

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_human_report(report))

    return 1 if report["summary"]["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
