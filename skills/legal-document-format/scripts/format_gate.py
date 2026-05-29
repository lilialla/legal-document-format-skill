#!/usr/bin/env python3
"""Aggregate legal document format checks into one local gate."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import audit_docx_structure  # noqa: E402
import audit_text  # noqa: E402
import compare_rendered_pages  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run aggregate legal document format gates over text, DOCX structure, "
            "and rendered PNG page sets."
        )
    )
    text_group = parser.add_mutually_exclusive_group()
    text_group.add_argument(
        "--text",
        metavar="TEXT_OR_FILE",
        help="Direct text, or an existing UTF-8 text file, to audit for punctuation and spacing issues.",
    )
    text_group.add_argument(
        "--text-file",
        metavar="PATH",
        help="UTF-8 text file to audit. Fails if PATH does not exist.",
    )
    parser.add_argument(
        "--docx",
        metavar="INPUT.docx",
        help="DOCX file to audit for basic OpenXML structure.",
    )
    parser.add_argument(
        "--baseline-png",
        metavar="DIR",
        help="Directory containing baseline rendered PNG pages.",
    )
    parser.add_argument(
        "--candidate-png",
        metavar="DIR",
        help="Directory containing candidate rendered PNG pages.",
    )
    parser.add_argument(
        "--require-visual",
        action="store_true",
        help="Require baseline and candidate PNG page directories for release-grade visual validation.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write a structured JSON report instead of a human-readable report.",
    )
    parser.add_argument(
        "--no-excerpt",
        action="store_true",
        help="Omit source text excerpts from aggregate JSON and human-readable output.",
    )
    return parser


def read_text_input(text_or_file: str, require_file: bool = False) -> tuple[str, str]:
    candidate = Path(text_or_file)
    if candidate.is_file():
        return candidate.read_text(encoding="utf-8"), str(candidate)
    if candidate.exists() and not candidate.is_file():
        raise IsADirectoryError(f"Text input path is not a file: {text_or_file}")
    if require_file:
        raise FileNotFoundError(f"Text input file not found: {text_or_file}")
    return text_or_file, "direct text"


def count_severities(issues: list[dict[str, Any]]) -> tuple[int, int]:
    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "warning")
    return error_count, warning_count


def status_from_counts(error_count: int, warning_count: int) -> str:
    if error_count:
        return "fail"
    if warning_count:
        return "warning"
    return "pass"


def normalize_issue(check: str, issue: dict[str, Any]) -> dict[str, Any]:
    normalized = {"check": check}
    normalized.update(issue)
    normalized.setdefault("severity", "warning")
    return normalized


def run_text_check(text_or_file: str, no_excerpt: bool, require_file: bool = False) -> dict[str, Any]:
    try:
        text, source = read_text_input(text_or_file, require_file=require_file)
    except (FileNotFoundError, IsADirectoryError, OSError, UnicodeDecodeError) as exc:
        issues = [
            normalize_issue(
                "text",
                {
                    "code": "text_input_error",
                    "severity": "error",
                    "message": str(exc),
                },
            )
        ]
        error_count, warning_count = count_severities(issues)
        return {
            "name": "text",
            "status": status_from_counts(error_count, warning_count),
            "issue_count": len(issues),
            "error_count": error_count,
            "warning_count": warning_count,
            "summary": {"source": str(text_or_file) if require_file else "text input"},
            "issues": issues,
        }

    issues: list[dict[str, Any]] = []
    for issue in audit_text.audit_text(text):
        payload = asdict(issue)
        if no_excerpt:
            payload.pop("excerpt", None)
        issues.append(normalize_issue("text", payload))

    error_count, warning_count = count_severities(issues)
    return {
        "name": "text",
        "status": status_from_counts(error_count, warning_count),
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": warning_count,
        "summary": {"source": source},
        "issues": issues,
    }


def run_docx_check(docx_path: str) -> dict[str, Any]:
    report = audit_docx_structure.audit_docx(Path(docx_path))
    issues = [normalize_issue("docx", issue) for issue in report["issues"]]
    error_count, warning_count = count_severities(issues)
    return {
        "name": "docx",
        "status": status_from_counts(error_count, warning_count),
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": warning_count,
        "summary": report["summary"],
        "issues": issues,
    }


def run_png_check(baseline_dir: str, candidate_dir: str) -> dict[str, Any]:
    report = compare_rendered_pages.compare_page_sets(Path(baseline_dir), Path(candidate_dir))
    issues = [normalize_issue("png", issue) for issue in report["issues"]]
    error_count, warning_count = count_severities(issues)
    return {
        "name": "png",
        "status": status_from_counts(error_count, warning_count),
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": warning_count,
        "summary": report["summary"],
        "issues": issues,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    if args.text is not None:
        checks.append(run_text_check(args.text, no_excerpt=args.no_excerpt))
    if args.text_file is not None:
        checks.append(run_text_check(args.text_file, no_excerpt=args.no_excerpt, require_file=True))
    if args.docx is not None:
        checks.append(run_docx_check(args.docx))
    if args.baseline_png is not None and args.candidate_png is not None:
        checks.append(run_png_check(args.baseline_png, args.candidate_png))

    issues = [issue for check in checks for issue in check["issues"]]
    error_count, warning_count = count_severities(issues)
    summary = {
        "status": status_from_counts(error_count, warning_count),
        "check_count": len(checks),
        "checks_run": [check["name"] for check in checks],
        "error_count": error_count,
        "warning_count": warning_count,
    }
    public_checks = [
        {key: value for key, value in check.items() if key != "issues"}
        for check in checks
    ]
    return {
        "summary": summary,
        "checks": public_checks,
        "issue_count": len(issues),
        "issues": issues,
    }


def format_human_report(report: dict[str, Any], no_excerpt: bool) -> str:
    summary = report["summary"]
    lines = [
        "Legal Document Format Gate",
        "",
        f"Status: {summary['status'].upper()}",
        (
            "Issues: "
            f"{report['issue_count']} "
            f"(errors={summary['error_count']}, warnings={summary['warning_count']})"
        ),
        "",
        "Checks:",
    ]

    for check in report["checks"]:
        lines.append(
            f"- {check['name']}: {check['status'].upper()} "
            f"(issues={check['issue_count']}, errors={check['error_count']}, "
            f"warnings={check['warning_count']})"
        )

    if report["issues"]:
        lines.extend(["", "Issue Details:"])
        for issue in report["issues"]:
            location = ""
            if issue["check"] == "text":
                line = issue.get("line")
                column = issue.get("column")
                if line is not None and column is not None:
                    location = f" L{line}:C{column}"
            elif issue.get("path"):
                location = f" [{issue['path']}]"
            elif issue.get("file"):
                location = f" [{issue['file']}]"
            lines.append(
                f"- {issue['check']} {issue['severity'].upper()} "
                f"{issue.get('code', 'issue')}{location}: {issue.get('message', '')}"
            )
            excerpt = issue.get("excerpt")
            if excerpt and not no_excerpt:
                lines.append(f"  > {excerpt}")
    else:
        lines.extend(["", "No issues found."])

    return "\n".join(lines)


def validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    has_text = args.text is not None or args.text_file is not None
    has_docx = args.docx is not None
    has_png = args.baseline_png is not None or args.candidate_png is not None
    has_png_pair = args.baseline_png is not None and args.candidate_png is not None
    if not has_text and not has_docx and not has_png:
        parser.error("provide at least one check input")
    if (args.baseline_png is None) != (args.candidate_png is None):
        parser.error("--baseline-png and --candidate-png must be provided together")
    if args.require_visual and not has_png_pair:
        parser.error("--require-visual requires --baseline-png and --candidate-png")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(parser, args)
    report = build_report(args)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_human_report(report, no_excerpt=args.no_excerpt))

    return 1 if report["summary"]["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
