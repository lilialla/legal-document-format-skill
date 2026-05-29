#!/usr/bin/env python3
"""Check local runtime requirements for the legal document format skill."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


MIN_PYTHON = (3, 9)
MACOS_SOFFICE = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")


@dataclass
class Requirement:
    name: str
    required: bool
    status: str
    detail: str
    path: str | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check whether core or release-grade document format requirements are installed."
    )
    parser.add_argument(
        "--mode",
        choices=("core", "release"),
        default="release",
        help="core checks Python only; release also requires LibreOffice and Poppler.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write a structured JSON report.",
    )
    return parser


def executable_version(path: str, args: list[str]) -> str:
    try:
        result = subprocess.run(
            [path, *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"version check failed: {exc}"
    first_line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else "no version output"
    return first_line


def find_soffice() -> str | None:
    env_path = os.environ.get("SOFFICE")
    if env_path and os.access(env_path, os.X_OK):
        return env_path
    path = shutil.which("soffice")
    if path:
        return path
    if MACOS_SOFFICE.exists() and os.access(MACOS_SOFFICE, os.X_OK):
        return str(MACOS_SOFFICE)
    return None


def check_python() -> Requirement:
    version = sys.version_info
    ok = version >= MIN_PYTHON
    detail = f"Python {version.major}.{version.minor}.{version.micro}"
    return Requirement(
        name="python",
        required=True,
        status="pass" if ok else "fail",
        detail=detail if ok else f"{detail}; require Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+",
        path=sys.executable,
    )


def check_executable(name: str, required: bool, path: str | None, version_args: list[str]) -> Requirement:
    if not path:
        return Requirement(
            name=name,
            required=required,
            status="fail" if required else "skip",
            detail=f"{name} not found",
        )
    return Requirement(
        name=name,
        required=required,
        status="pass",
        detail=executable_version(path, version_args),
        path=path,
    )


def build_report(mode: str) -> dict[str, object]:
    release_mode = mode == "release"
    requirements = [
        check_python(),
        check_executable("soffice", release_mode, find_soffice(), ["--version"]),
        check_executable("pdftoppm", release_mode, shutil.which("pdftoppm"), ["-h"]),
    ]
    blocking_failures = [item for item in requirements if item.required and item.status != "pass"]
    status = "pass" if not blocking_failures else "fail"
    return {
        "mode": mode,
        "status": status,
        "requirement_count": len(requirements),
        "blocking_failure_count": len(blocking_failures),
        "requirements": [asdict(item) for item in requirements],
    }


def format_human_report(report: dict[str, object]) -> str:
    lines = [
        "Release Requirement Check",
        "",
        f"Mode: {report['mode']}",
        f"Status: {str(report['status']).upper()}",
        "",
        "Requirements:",
    ]
    for item in report["requirements"]:  # type: ignore[index]
        required = "required" if item["required"] else "optional"
        path = f" [{item['path']}]" if item.get("path") else ""
        lines.append(f"- {item['name']}: {item['status'].upper()} ({required}){path}: {item['detail']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = build_report(args.mode)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_human_report(report))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
