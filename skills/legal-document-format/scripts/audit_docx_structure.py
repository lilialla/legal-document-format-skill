#!/usr/bin/env python3
"""Audit the structural OpenXML parts of a DOCX package."""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"w": WORD_NS, "rel": REL_NS}

CONTENT_TYPES = "[Content_Types].xml"
PACKAGE_RELS = "_rels/.rels"
DOCUMENT_XML = "word/document.xml"
DOCUMENT_RELS = "word/_rels/document.xml.rels"
STYLES_XML = "word/styles.xml"
NUMBERING_XML = "word/numbering.xml"


def make_issue(code: str, severity: str, message: str, path: str | None = None) -> dict[str, str]:
    issue = {"code": code, "severity": severity, "message": message}
    if path is not None:
        issue["path"] = path
    return issue


def read_xml(zip_file: zipfile.ZipFile, part: str, issues: list[dict[str, str]]) -> ElementTree.Element | None:
    try:
        with zip_file.open(part) as xml_file:
            return ElementTree.parse(xml_file).getroot()
    except KeyError:
        issues.append(
            make_issue(
                "missing_part",
                "error",
                f"Missing required OpenXML part: {part}",
                part,
            )
        )
    except ElementTree.ParseError as exc:
        issues.append(
            make_issue(
                "malformed_xml",
                "error",
                f"Malformed XML in {part}: {exc}",
                part,
            )
        )
    return None


def count_content_runs(document_root: ElementTree.Element) -> int:
    text_count = 0
    drawing_count = 0
    for text_node in document_root.findall(".//w:t", NS):
        if text_node.text and text_node.text.strip():
            text_count += 1
    drawing_count = len(document_root.findall(".//w:drawing", NS))
    drawing_count += len(document_root.findall(".//w:pict", NS))
    return text_count + drawing_count


def has_office_document_relationship(package_root: ElementTree.Element | None) -> bool:
    if package_root is None:
        return False
    for relationship in package_root.findall("rel:Relationship", NS):
        rel_type = relationship.attrib.get("Type", "")
        target = relationship.attrib.get("Target", "")
        if rel_type.endswith("/officeDocument") and target == "word/document.xml":
            return True
    return False


def audit_docx(path: Path) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    summary: dict[str, Any] = {
        "input": str(path),
        "is_zip_package": False,
        "has_content_types": False,
        "has_package_relationships": False,
        "has_document_relationships": False,
        "has_office_document_relationship": False,
        "has_document_xml": False,
        "section_count": 0,
        "paragraph_count": 0,
        "table_count": 0,
        "has_header_parts": False,
        "header_part_count": 0,
        "has_footer_parts": False,
        "footer_part_count": 0,
        "has_styles": False,
        "has_numbering": False,
    }

    if not path.exists():
        issues.append(make_issue("input_not_found", "error", f"Input file not found: {path}"))
        return {"summary": summary, "issue_count": len(issues), "issues": issues}

    if not path.is_file():
        issues.append(make_issue("input_not_file", "error", f"Input path is not a file: {path}"))
        return {"summary": summary, "issue_count": len(issues), "issues": issues}

    if path.suffix.lower() != ".docx":
        issues.append(make_issue("unexpected_extension", "warning", "Input file does not use a .docx extension."))

    try:
        with zipfile.ZipFile(path) as docx:
            summary["is_zip_package"] = True
            parts = set(docx.namelist())

            summary["has_content_types"] = CONTENT_TYPES in parts
            summary["has_package_relationships"] = PACKAGE_RELS in parts
            summary["has_document_relationships"] = DOCUMENT_RELS in parts
            summary["has_document_xml"] = DOCUMENT_XML in parts
            summary["has_styles"] = STYLES_XML in parts
            summary["has_numbering"] = NUMBERING_XML in parts

            header_parts = sorted(part for part in parts if part.startswith("word/header") and part.endswith(".xml"))
            footer_parts = sorted(part for part in parts if part.startswith("word/footer") and part.endswith(".xml"))
            summary["header_part_count"] = len(header_parts)
            summary["has_header_parts"] = bool(header_parts)
            summary["footer_part_count"] = len(footer_parts)
            summary["has_footer_parts"] = bool(footer_parts)

            content_types_root = read_xml(docx, CONTENT_TYPES, issues)
            package_rels_root = read_xml(docx, PACKAGE_RELS, issues)
            document_root = read_xml(docx, DOCUMENT_XML, issues)
            if DOCUMENT_RELS in parts:
                read_xml(docx, DOCUMENT_RELS, issues)

            if content_types_root is not None and content_types_root.tag.rsplit("}", 1)[-1] != "Types":
                issues.append(
                    make_issue(
                        "unexpected_content_types_root",
                        "warning",
                        "[Content_Types].xml root element is not Types.",
                        CONTENT_TYPES,
                    )
                )

            summary["has_office_document_relationship"] = has_office_document_relationship(package_rels_root)
            if package_rels_root is not None and not summary["has_office_document_relationship"]:
                issues.append(
                    make_issue(
                        "missing_office_document_relationship",
                        "error",
                        "Package relationships do not point to word/document.xml as the office document.",
                        PACKAGE_RELS,
                    )
                )

            if DOCUMENT_RELS not in parts:
                issues.append(
                    make_issue(
                        "missing_document_relationships",
                        "warning",
                        "Missing document relationship part; headers, footers, images, and links may be unreachable.",
                        DOCUMENT_RELS,
                    )
                )

            if document_root is not None:
                summary["section_count"] = len(document_root.findall(".//w:sectPr", NS))
                summary["paragraph_count"] = len(document_root.findall(".//w:p", NS))
                summary["table_count"] = len(document_root.findall(".//w:tbl", NS))

                if summary["paragraph_count"] == 0 and summary["table_count"] == 0:
                    issues.append(
                        make_issue(
                            "empty_document",
                            "error",
                            "word/document.xml contains no paragraphs or tables.",
                            DOCUMENT_XML,
                        )
                    )
                elif count_content_runs(document_root) == 0:
                    issues.append(
                        make_issue(
                            "empty_document_content",
                            "warning",
                            "word/document.xml has structure but no non-empty text or drawing content.",
                            DOCUMENT_XML,
                        )
                    )
    except zipfile.BadZipFile:
        issues.append(make_issue("not_a_zip_package", "error", "Input is not a readable DOCX zip package."))
    except OSError as exc:
        issues.append(make_issue("read_error", "error", f"Could not read input file: {exc}"))

    return {"summary": summary, "issue_count": len(issues), "issues": issues}


def format_bool(value: bool) -> str:
    return "yes" if value else "no"


def format_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "DOCX OpenXML Structure Audit",
        f"Input: {summary['input']}",
        "",
        "Package:",
        f"- zip package: {format_bool(summary['is_zip_package'])}",
        f"- [Content_Types].xml: {format_bool(summary['has_content_types'])}",
        f"- package relationships: {format_bool(summary['has_package_relationships'])}",
        f"- document relationships: {format_bool(summary['has_document_relationships'])}",
        f"- office document relationship: {format_bool(summary['has_office_document_relationship'])}",
        f"- word/document.xml: {format_bool(summary['has_document_xml'])}",
        "",
        "Document counts:",
        f"- sections: {summary['section_count']}",
        f"- paragraphs: {summary['paragraph_count']}",
        f"- tables: {summary['table_count']}",
        "",
        "Optional parts:",
        f"- headers: {format_bool(summary['has_header_parts'])} ({summary['header_part_count']})",
        f"- footers: {format_bool(summary['has_footer_parts'])} ({summary['footer_part_count']})",
        f"- styles: {format_bool(summary['has_styles'])}",
        f"- numbering: {format_bool(summary['has_numbering'])}",
        "",
        f"Issues: {result['issue_count']}",
    ]
    if result["issues"]:
        for issue in result["issues"]:
            path = f" [{issue['path']}]" if "path" in issue else ""
            lines.append(f"- {issue['severity'].upper()} {issue['code']}{path}: {issue['message']}")
    else:
        lines.append("- none")
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit minimal DOCX OpenXML structure without python-docx.",
    )
    parser.add_argument("input_docx", metavar="INPUT.docx", help="DOCX file to audit")
    parser.add_argument("--json", action="store_true", help="write structured JSON instead of a text report")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = audit_docx(Path(args.input_docx))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_report(result))
    return 1 if any(issue["severity"] == "error" for issue in result["issues"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
