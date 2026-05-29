#!/usr/bin/env python3
"""Compare a generated DOCX against its template for layout/parity drift."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
TEXT_TAGS = {
    f"{{{WORD_NS}}}t",
    f"{{{WORD_NS}}}instrText",
    f"{{{WORD_NS}}}delText",
}

ElementTree.register_namespace("w", WORD_NS)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify that a generated DOCX preserves the template package and "
            "OpenXML layout structure. Text node contents may differ; styles, "
            "headers, footers, sections, numbering, relationships, media, and "
            "non-text XML structure must match."
        )
    )
    parser.add_argument("template_docx", metavar="TEMPLATE.docx")
    parser.add_argument("candidate_docx", metavar="CANDIDATE.docx")
    parser.add_argument("--json", action="store_true", help="write structured JSON")
    return parser


def issue(code: str, severity: str, message: str, **extra: Any) -> dict[str, Any]:
    payload = {"code": code, "severity": severity, "message": message}
    payload.update(extra)
    return payload


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def strip_whitespace(node: ElementTree.Element) -> None:
    if node.text is not None and node.text.strip() == "":
        node.text = None
    if node.tail is not None and node.tail.strip() == "":
        node.tail = None
    for child in list(node):
        strip_whitespace(child)


def normalized_xml(data: bytes) -> bytes | None:
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError:
        return None
    for node in root.iter():
        if node.tag in TEXT_TAGS:
            node.text = ""
    strip_whitespace(root)
    return ElementTree.tostring(root, encoding="utf-8")


def compare_docx(template_path: Path, candidate_path: Path) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    if not template_path.exists():
        issues.append(issue("template_not_found", "error", f"Template not found: {template_path}"))
    if not candidate_path.exists():
        issues.append(issue("candidate_not_found", "error", f"Candidate not found: {candidate_path}"))
    if issues:
        return build_report(template_path, candidate_path, issues, 0, 0, 0)

    try:
        with zipfile.ZipFile(template_path) as template_zip, zipfile.ZipFile(candidate_path) as candidate_zip:
            template_parts = set(template_zip.namelist())
            candidate_parts = set(candidate_zip.namelist())

            for part in sorted(template_parts - candidate_parts):
                issues.append(issue("missing_part", "error", f"Candidate is missing template part: {part}", part=part))
            for part in sorted(candidate_parts - template_parts):
                issues.append(issue("extra_part", "error", f"Candidate has extra part not present in template: {part}", part=part))

            exact_checked = 0
            normalized_checked = 0
            differing_parts = 0
            for part in sorted(template_parts & candidate_parts):
                template_data = template_zip.read(part)
                candidate_data = candidate_zip.read(part)
                if part.endswith(".xml"):
                    template_normalized = normalized_xml(template_data)
                    candidate_normalized = normalized_xml(candidate_data)
                    if template_normalized is not None and candidate_normalized is not None:
                        normalized_checked += 1
                        if sha256(template_normalized) != sha256(candidate_normalized):
                            differing_parts += 1
                            issues.append(
                                issue(
                                    "xml_structure_delta",
                                    "error",
                                    f"OpenXML structure differs after ignoring text node contents: {part}",
                                    part=part,
                                )
                            )
                        continue
                exact_checked += 1
                if sha256(template_data) != sha256(candidate_data):
                    differing_parts += 1
                    issues.append(
                        issue(
                            "binary_part_delta",
                            "error",
                            f"Non-normalized part differs from template: {part}",
                            part=part,
                        )
                    )
    except zipfile.BadZipFile as exc:
        issues.append(issue("bad_docx_zip", "error", f"DOCX zip read failed: {exc}"))
        return build_report(template_path, candidate_path, issues, 0, 0, 0)
    except OSError as exc:
        issues.append(issue("read_error", "error", f"Could not compare DOCX files: {exc}"))
        return build_report(template_path, candidate_path, issues, 0, 0, 0)

    return build_report(template_path, candidate_path, issues, exact_checked, normalized_checked, differing_parts)


def build_report(
    template_path: Path,
    candidate_path: Path,
    issues: list[dict[str, Any]],
    exact_checked: int,
    normalized_checked: int,
    differing_parts: int,
) -> dict[str, Any]:
    error_count = sum(1 for item in issues if item["severity"] == "error")
    warning_count = sum(1 for item in issues if item["severity"] == "warning")
    return {
        "summary": {
            "status": "fail" if error_count else "warning" if warning_count else "pass",
            "template": str(template_path),
            "candidate": str(candidate_path),
            "exact_part_count": exact_checked,
            "normalized_xml_part_count": normalized_checked,
            "differing_part_count": differing_parts,
            "error_count": error_count,
            "warning_count": warning_count,
        },
        "issue_count": len(issues),
        "issues": issues,
    }


def format_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "DOCX Template Parity",
        "",
        f"Status: {summary['status'].upper()}",
        f"Template: {summary['template']}",
        f"Candidate: {summary['candidate']}",
        f"Exact parts checked: {summary['exact_part_count']}",
        f"Normalized XML parts checked: {summary['normalized_xml_part_count']}",
        f"Differing parts: {summary['differing_part_count']}",
        f"Issues: {report['issue_count']}",
    ]
    if report["issues"]:
        lines.append("")
        lines.append("Issue Details:")
        for item in report["issues"]:
            lines.append(f"- {item['severity'].upper()} {item['code']}: {item['message']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = compare_docx(Path(args.template_docx), Path(args.candidate_docx))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_report(report))
    return 1 if report["summary"]["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
