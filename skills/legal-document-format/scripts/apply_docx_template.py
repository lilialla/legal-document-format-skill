#!/usr/bin/env python3
"""Apply text replacements to a DOCX template while preserving its package layout."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
TEXT_TAGS = {f"{{{WORD_NS}}}t"}
PARAGRAPH_TAG = f"{{{WORD_NS}}}p"
PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}")
MAX_DOCX_BYTES = 100 * 1024 * 1024
MAX_ZIP_ENTRIES = 2000
MAX_UNCOMPRESSED_BYTES = 250 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100

ElementTree.register_namespace("w", WORD_NS)


@dataclass
class ReplacementHit:
    key: str
    part: str
    count: int


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Copy a DOCX template and replace {{KEY}} placeholders inside existing "
            "Word text nodes. Layout, headers, footers, styles, numbering, sections, "
            "relationships, and media are preserved from the template package."
        )
    )
    parser.add_argument("template_docx", metavar="TEMPLATE.docx", help="source DOCX template")
    parser.add_argument("output_docx", metavar="OUTPUT.docx", help="destination DOCX")
    parser.add_argument(
        "--replacements-json",
        metavar="PATH",
        help="JSON object mapping placeholder keys to replacement strings.",
    )
    parser.add_argument(
        "--set",
        dest="sets",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Replacement pair. Can be provided multiple times.",
    )
    parser.add_argument("--force", action="store_true", help="overwrite OUTPUT.docx if it exists")
    parser.add_argument("--json", action="store_true", help="write a structured JSON report")
    return parser


def issue(code: str, severity: str, message: str, **extra: Any) -> dict[str, Any]:
    payload = {"code": code, "severity": severity, "message": message}
    payload.update(extra)
    return payload


def load_replacements(json_path: str | None, set_pairs: list[str]) -> tuple[dict[str, str], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    replacements: dict[str, str] = {}
    if json_path:
        try:
            payload = json.loads(Path(json_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return {}, [issue("replacement_json_error", "error", f"Could not read replacements JSON: {exc}")]
        if not isinstance(payload, dict):
            return {}, [issue("replacement_json_not_object", "error", "Replacement JSON must be an object.")]
        for key, value in payload.items():
            replacements[str(key)] = str(value)

    for pair in set_pairs:
        if "=" not in pair:
            issues.append(issue("invalid_set_pair", "error", f"--set value must be KEY=VALUE: {pair}"))
            continue
        key, value = pair.split("=", 1)
        if not key:
            issues.append(issue("empty_replacement_key", "error", "--set key cannot be empty"))
            continue
        replacements[key] = value
    if not replacements and not issues:
        issues.append(issue("no_replacements", "error", "Provide --replacements-json or at least one --set KEY=VALUE."))
    return replacements, issues


def is_candidate_xml_part(part_name: str) -> bool:
    return part_name.startswith("word/") and part_name.endswith(".xml")


def replace_text_node(text: str, replacements: dict[str, str]) -> tuple[str, dict[str, int]]:
    hits: dict[str, int] = {}

    def replace_match(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in replacements:
            return match.group(0)
        hits[key] = hits.get(key, 0) + 1
        return replacements[key]

    return PLACEHOLDER_RE.sub(replace_match, text), hits


def has_unsafe_zip_name(name: str) -> bool:
    return (
        name.startswith("/")
        or name.startswith("\\")
        or "\\" in name
        or any(part == ".." for part in Path(name).parts)
        or any(ord(char) < 32 for char in name)
    )


def validate_docx_package(path: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    try:
        if path.stat().st_size > MAX_DOCX_BYTES:
            issues.append(
                issue(
                    "docx_too_large",
                    "error",
                    f"DOCX is larger than the limit of {MAX_DOCX_BYTES} bytes: {path}",
                )
            )
            return issues
        with zipfile.ZipFile(path) as docx:
            infos = docx.infolist()
    except zipfile.BadZipFile:
        return [issue("template_not_docx", "error", "Template is not a readable DOCX zip package.")]
    except OSError as exc:
        return [issue("template_read_error", "error", f"Could not read template: {exc}")]

    if len(infos) > MAX_ZIP_ENTRIES:
        issues.append(
            issue(
                "zip_entry_limit",
                "error",
                f"DOCX has too many package entries: {len(infos)} > {MAX_ZIP_ENTRIES}",
            )
        )
    total_uncompressed = 0
    for info in infos:
        total_uncompressed += info.file_size
        if has_unsafe_zip_name(info.filename):
            issues.append(
                issue(
                    "unsafe_zip_entry_name",
                    "error",
                    f"DOCX contains an unsafe package entry name: {info.filename}",
                    part=info.filename,
                )
            )
        if info.compress_size and info.file_size / info.compress_size > MAX_COMPRESSION_RATIO:
            issues.append(
                issue(
                    "zip_compression_ratio",
                    "error",
                    f"DOCX package entry compression ratio is too high: {info.filename}",
                    part=info.filename,
                )
            )
    if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
        issues.append(
            issue(
                "zip_uncompressed_limit",
                "error",
                f"DOCX uncompressed size is too large: {total_uncompressed} > {MAX_UNCOMPRESSED_BYTES}",
            )
        )
    return issues


def set_xml_space_if_needed(node: ElementTree.Element) -> None:
    text = node.text or ""
    xml_space = f"{{{XML_NS}}}space"
    if text[:1].isspace() or text[-1:].isspace():
        node.set(xml_space, "preserve")


def replace_text_nodes_in_block(nodes: list[ElementTree.Element], replacements: dict[str, str]) -> tuple[bool, dict[str, int]]:
    texts = [node.text or "" for node in nodes]
    combined = "".join(texts)
    if not combined:
        return False, {}

    owners: list[int] = []
    for index, text in enumerate(texts):
        owners.extend([index] * len(text))

    matches = [match for match in PLACEHOLDER_RE.finditer(combined) if match.group(1) in replacements]
    if not matches:
        return False, {}

    starts = {match.start(): match for match in matches}
    output = [""] * len(nodes)
    hit_counts: dict[str, int] = {}
    position = 0
    while position < len(combined):
        match = starts.get(position)
        if match is not None:
            key = match.group(1)
            output[owners[position]] += replacements[key]
            hit_counts[key] = hit_counts.get(key, 0) + 1
            position = match.end()
            continue
        output[owners[position]] += combined[position]
        position += 1

    for node, text in zip(nodes, output):
        node.text = text
        set_xml_space_if_needed(node)
    return True, hit_counts


def replace_xml_part(part_name: str, data: bytes, replacements: dict[str, str]) -> tuple[bytes, list[ReplacementHit], list[dict[str, Any]], bool]:
    issues: list[dict[str, Any]] = []
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError:
        return data, [], [], False

    changed = False
    hit_counts: dict[str, int] = {}
    text_blocks = list(root.iter(PARAGRAPH_TAG)) or [root]
    for block in text_blocks:
        text_nodes = [node for node in block.iter() if node.tag in TEXT_TAGS and node.text is not None]
        block_changed, hits = replace_text_nodes_in_block(text_nodes, replacements)
        if block_changed:
            changed = True
            for key, count in hits.items():
                hit_counts[key] = hit_counts.get(key, 0) + count

    combined_text = "".join(node.text or "" for node in root.iter() if node.tag in TEXT_TAGS)
    unresolved = sorted(set(PLACEHOLDER_RE.findall(combined_text)))
    for key in unresolved:
        issues.append(
            issue(
                "unresolved_placeholder",
                "error",
                f"Unresolved placeholder remains in {part_name}: {key}",
                part=part_name,
                key=key,
            )
        )

    if not changed:
        return data, [], issues, False
    new_data = ElementTree.tostring(root, encoding="utf-8", xml_declaration=True)
    hits = [ReplacementHit(key=key, part=part_name, count=count) for key, count in sorted(hit_counts.items())]
    return new_data, hits, issues, True


def clone_zip_info(info: zipfile.ZipInfo) -> zipfile.ZipInfo:
    clone = zipfile.ZipInfo(info.filename, info.date_time)
    clone.compress_type = info.compress_type
    clone.comment = info.comment
    clone.extra = info.extra
    clone.internal_attr = info.internal_attr
    clone.external_attr = info.external_attr
    clone.create_system = info.create_system
    return clone


def apply_template(template_path: Path, output_path: Path, replacements: dict[str, str], force: bool = False) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    hits: list[ReplacementHit] = []
    changed_parts: list[str] = []

    if not template_path.exists():
        return {"summary": {"status": "fail"}, "issues": [issue("template_not_found", "error", f"Template not found: {template_path}")]}
    package_issues = validate_docx_package(template_path)
    if package_issues:
        return {"summary": {"status": "fail"}, "issues": package_issues}
    if template_path.suffix.lower() != ".docx":
        issues.append(issue("template_extension", "warning", "Template path does not use a .docx extension."))
    if output_path.exists() and not force:
        return {"summary": {"status": "fail"}, "issues": [issue("output_exists", "error", f"Output exists; use --force: {output_path}")]}
    if output_path.exists() and not output_path.is_file():
        return {"summary": {"status": "fail"}, "issues": [issue("output_not_file", "error", f"Output exists and is not a file: {output_path}")]}
    if not output_path.parent.exists():
        return {"summary": {"status": "fail"}, "issues": [issue("output_parent_missing", "error", f"Output directory does not exist: {output_path.parent}")]}

    temp_output: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent, delete=False) as temp_file:
            temp_output = Path(temp_file.name)
        with zipfile.ZipFile(template_path) as source, zipfile.ZipFile(temp_output, "w") as target:
            for info in source.infolist():
                data = source.read(info.filename)
                if is_candidate_xml_part(info.filename):
                    data, part_hits, part_issues, changed = replace_xml_part(info.filename, data, replacements)
                    hits.extend(part_hits)
                    issues.extend(part_issues)
                    if changed:
                        changed_parts.append(info.filename)
                target.writestr(clone_zip_info(info), data)
    except zipfile.BadZipFile:
        if temp_output is not None:
            temp_output.unlink(missing_ok=True)
        return {"summary": {"status": "fail"}, "issues": [issue("template_not_docx", "error", "Template is not a readable DOCX zip package.")]}
    except OSError as exc:
        if temp_output is not None:
            temp_output.unlink(missing_ok=True)
        return {"summary": {"status": "fail"}, "issues": [issue("io_error", "error", f"Could not apply template: {exc}")]}

    hit_keys = {hit.key for hit in hits}
    for key in sorted(set(replacements) - hit_keys):
        issues.append(issue("replacement_not_used", "warning", f"Replacement key was not used: {key}", key=key))

    error_count = sum(1 for item in issues if item["severity"] == "error")
    warning_count = sum(1 for item in issues if item["severity"] == "warning")
    status = "fail" if error_count else "warning" if warning_count else "pass"
    if status == "fail":
        if temp_output is not None:
            temp_output.unlink(missing_ok=True)
    elif temp_output is not None:
        os.replace(temp_output, output_path)
    return {
        "summary": {
            "status": status,
            "template": str(template_path),
            "output": str(output_path),
            "replacement_key_count": len(replacements),
            "changed_part_count": len(changed_parts),
            "changed_parts": changed_parts,
            "error_count": error_count,
            "warning_count": warning_count,
        },
        "replacement_hits": [asdict(hit) for hit in hits],
        "issue_count": len(issues),
        "issues": issues,
    }


def format_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "DOCX Template Apply",
        "",
        f"Status: {summary['status'].upper()}",
        f"Template: {summary.get('template', '')}",
        f"Output: {summary.get('output', '')}",
        f"Changed parts: {summary.get('changed_part_count', 0)}",
        f"Issues: {report.get('issue_count', len(report.get('issues', [])))}",
    ]
    if report.get("replacement_hits"):
        lines.append("")
        lines.append("Replacement Hits:")
        for hit in report["replacement_hits"]:
            lines.append(f"- {hit['key']} in {hit['part']}: {hit['count']}")
    if report.get("issues"):
        lines.append("")
        lines.append("Issue Details:")
        for item in report["issues"]:
            lines.append(f"- {item['severity'].upper()} {item['code']}: {item['message']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    replacements, issues = load_replacements(args.replacements_json, args.sets)
    if any(item["severity"] == "error" for item in issues):
        report = {"summary": {"status": "fail"}, "replacement_hits": [], "issue_count": len(issues), "issues": issues}
    else:
        report = apply_template(Path(args.template_docx), Path(args.output_docx), replacements, force=args.force)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_report(report))
    return 1 if report["summary"]["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
