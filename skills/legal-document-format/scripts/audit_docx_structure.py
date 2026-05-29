#!/usr/bin/env python3
"""Audit the structural OpenXML parts of a DOCX package."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"w": WORD_NS, "rel": REL_NS}
TITLE_STYLE_IDS = {"Title", "Heading1", "Heading 1", "标题", "标题1", "标题 1"}
CJK_PUNCTUATION = set("，。、；：？！“”‘’（）《》〈〉【】、")
CJK_QUOTES = set("“”‘’")
HALFWIDTH_PUNCTUATION = set(",;:?!()\"'")
CJK_CHAR_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
PAGE_FIELD_RE = re.compile(r"\bPAGE\b", re.IGNORECASE)
NUMPAGES_FIELD_RE = re.compile(r"\bNUMPAGES\b", re.IGNORECASE)

CONTENT_TYPES = "[Content_Types].xml"
PACKAGE_RELS = "_rels/.rels"
DOCUMENT_XML = "word/document.xml"
DOCUMENT_RELS = "word/_rels/document.xml.rels"
STYLES_XML = "word/styles.xml"
NUMBERING_XML = "word/numbering.xml"
MAX_DOCX_BYTES = 100 * 1024 * 1024
MAX_ZIP_ENTRIES = 2000
MAX_UNCOMPRESSED_BYTES = 250 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100


def make_issue(code: str, severity: str, message: str, path: str | None = None) -> dict[str, str]:
    issue = {"code": code, "severity": severity, "message": message}
    if path is not None:
        issue["path"] = path
    return issue


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child(element: ElementTree.Element | None, path: str) -> ElementTree.Element | None:
    if element is None:
        return None
    return element.find(path, NS)


def attr_value(element: ElementTree.Element | None, name: str) -> str | None:
    if element is None:
        return None
    return element.attrib.get(f"{{{WORD_NS}}}{name}")


def has_unsafe_zip_name(name: str) -> bool:
    return (
        name.startswith("/")
        or name.startswith("\\")
        or "\\" in name
        or any(part == ".." for part in Path(name).parts)
        or any(ord(char) < 32 for char in name)
    )


def audit_zip_limits(path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if path.stat().st_size > MAX_DOCX_BYTES:
        return [
            make_issue(
                "docx_too_large",
                "error",
                f"DOCX is larger than the limit of {MAX_DOCX_BYTES} bytes.",
            )
        ]
    try:
        with zipfile.ZipFile(path) as docx:
            infos = docx.infolist()
    except zipfile.BadZipFile:
        return []

    if len(infos) > MAX_ZIP_ENTRIES:
        issues.append(make_issue("zip_entry_limit", "error", f"DOCX has too many package entries: {len(infos)}."))
    total_uncompressed = 0
    for info in infos:
        total_uncompressed += info.file_size
        if has_unsafe_zip_name(info.filename):
            issues.append(make_issue("unsafe_zip_entry_name", "error", f"Unsafe DOCX package entry name: {info.filename}", info.filename))
        if info.compress_size and info.file_size / info.compress_size > MAX_COMPRESSION_RATIO:
            issues.append(make_issue("zip_compression_ratio", "error", f"DOCX package entry compression ratio is too high: {info.filename}", info.filename))
    if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
        issues.append(
            make_issue(
                "zip_uncompressed_limit",
                "error",
                f"DOCX uncompressed size is too large: {total_uncompressed} > {MAX_UNCOMPRESSED_BYTES}.",
            )
        )
    return issues


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


def run_text(run: ElementTree.Element) -> str:
    return "".join(text.text or "" for text in run.findall(".//w:t", NS))


def run_fonts(run: ElementTree.Element, inherited: dict[str, str | None] | None = None) -> dict[str, str | None]:
    fonts = dict(inherited or {})
    r_fonts = child(child(run, "w:rPr"), "w:rFonts")
    if r_fonts is not None:
        for key in ("ascii", "hAnsi", "eastAsia", "cs"):
            value = attr_value(r_fonts, key)
            if value:
                fonts[key] = value
    return fonts


def run_size(run: ElementTree.Element, inherited: str | None = None) -> str | None:
    size = child(child(run, "w:rPr"), "w:sz")
    return attr_value(size, "val") or inherited


def rpr_defaults(r_pr: ElementTree.Element | None) -> dict[str, Any]:
    r_fonts = child(r_pr, "w:rFonts")
    fonts: dict[str, str | None] = {}
    if r_fonts is not None:
        for key in ("ascii", "hAnsi", "eastAsia", "cs"):
            fonts[key] = attr_value(r_fonts, key)
    return {"fonts": fonts, "size": attr_value(child(r_pr, "w:sz"), "val")}


def merge_defaults(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    fonts = dict(base.get("fonts", {}))
    fonts.update({key: value for key, value in override.get("fonts", {}).items() if value})
    return {
        "fonts": fonts,
        "size": override.get("size") or base.get("size"),
    }


def style_run_defaults(styles_root: ElementTree.Element | None) -> dict[str, dict[str, Any]]:
    if styles_root is None:
        return {}
    doc_default = rpr_defaults(child(child(child(styles_root, "w:docDefaults"), "w:rPrDefault"), "w:rPr"))
    raw_styles: dict[str, dict[str, Any]] = {}
    for style in styles_root.findall(".//w:style", NS):
        style_id = attr_value(style, "styleId")
        if not style_id:
            continue
        raw_styles[style_id] = {
            "based_on": attr_value(child(style, "w:basedOn"), "val"),
            "defaults": rpr_defaults(child(style, "w:rPr")),
        }

    resolved: dict[str, dict[str, Any]] = {}

    def resolve(style_id: str, stack: set[str] | None = None) -> dict[str, Any]:
        if style_id in resolved:
            return resolved[style_id]
        stack = set(stack or set())
        if style_id in stack:
            return doc_default
        stack.add(style_id)
        raw = raw_styles.get(style_id, {})
        parent_id = raw.get("based_on")
        base = resolve(parent_id, stack) if parent_id else doc_default
        resolved[style_id] = merge_defaults(base, raw.get("defaults", {}))
        return resolved[style_id]

    for style_id in raw_styles:
        resolve(style_id)
    if "Normal" not in resolved:
        resolved["Normal"] = doc_default
    return resolved


def paragraph_style_id(paragraph: ElementTree.Element) -> str | None:
    return attr_value(child(child(paragraph, "w:pPr"), "w:pStyle"), "val")


def paragraph_text(paragraph: ElementTree.Element) -> str:
    return "".join(text.text or "" for text in paragraph.findall(".//w:t", NS)).strip()


def has_cjk_context(text: str) -> bool:
    return bool(CJK_CHAR_RE.search(text))


def is_title_paragraph(paragraph: ElementTree.Element) -> bool:
    style_id = paragraph_style_id(paragraph)
    return style_id in TITLE_STYLE_IDS


def format_signature(fonts: dict[str, str | None], size: str | None) -> tuple[str | None, str | None, str | None, str | None, str | None]:
    return (
        fonts.get("eastAsia"),
        fonts.get("ascii"),
        fonts.get("hAnsi"),
        fonts.get("cs"),
        size,
    )


def audit_title_format(
    document_root: ElementTree.Element,
    style_defaults: dict[str, dict[str, Any]],
    issues: list[dict[str, str]],
) -> dict[str, Any]:
    paragraphs = document_root.findall(".//w:p", NS)
    title_count = 0
    fonts_seen: set[tuple[str | None, str | None, str | None, str | None]] = set()
    sizes_seen: set[str | None] = set()
    missing_font_count = 0
    missing_size_count = 0

    for paragraph in paragraphs:
        text = paragraph_text(paragraph)
        if not text:
            continue
        if not is_title_paragraph(paragraph):
            continue

        title_count += 1
        style_defaults_for_paragraph = style_defaults.get(paragraph_style_id(paragraph) or "", {})
        inherited_fonts = style_defaults_for_paragraph.get("fonts", {})
        inherited_size = style_defaults_for_paragraph.get("size")
        paragraph_signatures: set[tuple[str | None, str | None, str | None, str | None, str | None]] = set()
        for run in paragraph.findall("w:r", NS):
            if not run_text(run).strip():
                continue
            signature = format_signature(run_fonts(run, inherited_fonts), run_size(run, inherited_size))
            paragraph_signatures.add(signature)
            fonts_seen.add(signature[:4])
            sizes_seen.add(signature[4])
            if not signature[0]:
                missing_font_count += 1
            if not signature[4]:
                missing_size_count += 1

        if len({signature[:4] for signature in paragraph_signatures}) > 1:
            issues.append(
                make_issue(
                    "title_font_mixed",
                    "warning",
                    "同一标题段落中发现多种字体设置，建议统一标题字体。",
                    DOCUMENT_XML,
                )
            )
        if len({signature[4] for signature in paragraph_signatures}) > 1:
            issues.append(
                make_issue(
                    "title_size_mixed",
                    "warning",
                    "同一标题段落中发现多种字号设置，建议统一标题字号。",
                    DOCUMENT_XML,
                )
            )

    if missing_font_count:
        issues.append(
            make_issue(
                "title_font_missing",
                "warning",
                "标题文字存在无法解析的中文字体设置，建议明确标题字体。",
                DOCUMENT_XML,
            )
        )
    if missing_size_count:
        issues.append(
            make_issue(
                "title_size_missing",
                "warning",
                "标题文字存在无法解析的字号设置，建议明确标题字号。",
                DOCUMENT_XML,
            )
        )

    return {
        "title_paragraph_count": title_count,
        "title_font_signature_count": len(fonts_seen),
        "title_size_count": len(sizes_seen),
        "title_missing_font_run_count": missing_font_count,
        "title_missing_size_run_count": missing_size_count,
    }


def all_word_roots(docx: zipfile.ZipFile, parts: set[str], issues: list[dict[str, str]]) -> list[tuple[str, ElementTree.Element]]:
    roots: list[tuple[str, ElementTree.Element]] = []
    for part in sorted(parts):
        if not part.startswith("word/") or not part.endswith(".xml"):
            continue
        try:
            with docx.open(part) as xml_file:
                roots.append((part, ElementTree.parse(xml_file).getroot()))
        except ElementTree.ParseError:
            continue
        except KeyError:
            issues.append(make_issue("missing_part", "error", f"Missing required OpenXML part: {part}", part))
    return roots


def audit_punctuation_fonts(
    word_roots: list[tuple[str, ElementTree.Element]],
    style_defaults: dict[str, dict[str, Any]],
    issues: list[dict[str, str]],
) -> dict[str, Any]:
    punctuation_run_count = 0
    cjk_punctuation_run_count = 0
    halfwidth_punctuation_run_count = 0
    missing_east_asia_count = 0
    cjk_quote_run_count = 0
    cjk_quote_font_mismatch_count = 0
    signatures: set[tuple[str | None, str | None, str | None, str | None, str | None]] = set()
    default_fonts = style_defaults.get("Normal", {}).get("fonts", {})
    default_size = style_defaults.get("Normal", {}).get("size")

    for part, root in word_roots:
        if local_name(root.tag) not in {"document", "hdr", "ftr"}:
            continue
        for paragraph in root.findall(".//w:p", NS):
            paragraph_plain_text = paragraph_text(paragraph)
            style_defaults_for_paragraph = style_defaults.get(paragraph_style_id(paragraph) or "", {})
            inherited_fonts = style_defaults_for_paragraph.get("fonts", default_fonts)
            inherited_size = style_defaults_for_paragraph.get("size") or default_size
            for run in paragraph.findall("w:r", NS):
                text = run_text(run)
                if not text or not any(mark in text for mark in CJK_PUNCTUATION | HALFWIDTH_PUNCTUATION):
                    continue
                punctuation_run_count += 1
                has_cjk_punctuation = any(mark in text for mark in CJK_PUNCTUATION)
                has_cjk_quote = any(mark in text for mark in CJK_QUOTES)
                has_halfwidth_punctuation = any(mark in text for mark in HALFWIDTH_PUNCTUATION)
                cjk_punctuation_run_count += int(has_cjk_punctuation)
                cjk_quote_run_count += int(has_cjk_quote)
                halfwidth_punctuation_run_count += int(has_halfwidth_punctuation)
                if has_halfwidth_punctuation and has_cjk_context(paragraph_plain_text):
                    issues.append(
                        make_issue(
                            "halfwidth_punctuation_cn",
                            "warning",
                            "DOCX 中文语境中发现半角标点，建议核对是否应使用全角标点。",
                            part,
                        )
                    )
                direct_r_fonts = child(child(run, "w:rPr"), "w:rFonts")
                fonts = run_fonts(run, inherited_fonts)
                size = run_size(run, inherited_size)
                signatures.add(format_signature(fonts, size))
                direct_has_latin_font = bool(attr_value(direct_r_fonts, "ascii") or attr_value(direct_r_fonts, "hAnsi"))
                direct_missing_east_asia = direct_r_fonts is not None and direct_has_latin_font and not attr_value(direct_r_fonts, "eastAsia")
                if has_cjk_punctuation and (not fonts.get("eastAsia") or direct_missing_east_asia):
                    missing_east_asia_count += 1
                    issues.append(
                        make_issue(
                            "punctuation_font_missing_east_asia",
                            "warning",
                            "中文标点所在 run 缺少 eastAsia 字体设置，可能与模板字体规则不一致。",
                            part,
                        )
                    )
                east_asia_font = fonts.get("eastAsia")
                if has_cjk_quote and east_asia_font and any(fonts.get(key) != east_asia_font for key in ("ascii", "hAnsi", "cs")):
                    cjk_quote_font_mismatch_count += 1
                    issues.append(
                        make_issue(
                            "cjk_quote_font_mismatch",
                            "warning",
                            "中文弯引号所在 run 的 ascii/hAnsi/cs 字体未与 eastAsia 中文字体一致，WPS/Word 可能将引号回退为西文字体。",
                            part,
                        )
                    )

    if len(signatures) > 1:
        issues.append(
            make_issue(
                "punctuation_font_mixed",
                "warning",
                "文档标点所在 run 存在多种字体/字号组合，建议统一标点符号字体。",
                DOCUMENT_XML,
            )
        )
    return {
        "punctuation_run_count": punctuation_run_count,
        "cjk_punctuation_run_count": cjk_punctuation_run_count,
        "halfwidth_punctuation_run_count": halfwidth_punctuation_run_count,
        "punctuation_font_signature_count": len(signatures),
        "punctuation_missing_east_asia_count": missing_east_asia_count,
        "cjk_quote_run_count": cjk_quote_run_count,
        "cjk_quote_font_mismatch_count": cjk_quote_font_mismatch_count,
    }


def field_instruction_text(root: ElementTree.Element) -> list[str]:
    instructions = [node.text or "" for node in root.findall(".//w:instrText", NS)]
    instructions.extend(attr_value(node, "instr") or "" for node in root.findall(".//w:fldSimple", NS))
    return instructions


def audit_page_fields(
    document_root: ElementTree.Element,
    word_roots: list[tuple[str, ElementTree.Element]],
    header_part_count: int,
    footer_part_count: int,
    issues: list[dict[str, str]],
) -> dict[str, Any]:
    page_field_count = 0
    numpages_field_count = 0
    for _part, root in word_roots:
        for instruction in field_instruction_text(root):
            page_field_count += len(PAGE_FIELD_RE.findall(instruction))
            numpages_field_count += len(NUMPAGES_FIELD_RE.findall(instruction))

    header_reference_count = len(document_root.findall(".//w:headerReference", NS))
    footer_reference_count = len(document_root.findall(".//w:footerReference", NS))
    if footer_part_count and page_field_count == 0:
        issues.append(
            make_issue(
                "page_field_missing",
                "warning",
                "存在页脚 part，但未发现 PAGE 页码字段。",
                DOCUMENT_XML,
            )
        )
    if header_part_count and header_reference_count == 0:
        issues.append(
            make_issue(
                "header_reference_missing",
                "warning",
                "存在页眉 part，但正文分节中未发现 headerReference。",
                DOCUMENT_XML,
            )
        )
    if footer_part_count and footer_reference_count == 0:
        issues.append(
            make_issue(
                "footer_reference_missing",
                "warning",
                "存在页脚 part，但正文分节中未发现 footerReference。",
                DOCUMENT_XML,
            )
        )
    return {
        "page_field_count": page_field_count,
        "numpages_field_count": numpages_field_count,
        "section_header_reference_count": header_reference_count,
        "section_footer_reference_count": footer_reference_count,
    }


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
        "title_paragraph_count": 0,
        "title_font_signature_count": 0,
        "title_size_count": 0,
        "title_missing_font_run_count": 0,
        "title_missing_size_run_count": 0,
        "punctuation_run_count": 0,
        "cjk_punctuation_run_count": 0,
        "halfwidth_punctuation_run_count": 0,
        "punctuation_font_signature_count": 0,
        "punctuation_missing_east_asia_count": 0,
        "cjk_quote_run_count": 0,
        "cjk_quote_font_mismatch_count": 0,
        "page_field_count": 0,
        "numpages_field_count": 0,
        "section_header_reference_count": 0,
        "section_footer_reference_count": 0,
    }

    if not path.exists():
        issues.append(make_issue("input_not_found", "error", f"Input file not found: {path}"))
        return {"summary": summary, "issue_count": len(issues), "issues": issues}

    if not path.is_file():
        issues.append(make_issue("input_not_file", "error", f"Input path is not a file: {path}"))
        return {"summary": summary, "issue_count": len(issues), "issues": issues}

    if path.suffix.lower() != ".docx":
        issues.append(make_issue("unexpected_extension", "warning", "Input file does not use a .docx extension."))
    issues.extend(audit_zip_limits(path))
    if any(issue["severity"] == "error" for issue in issues):
        return {"summary": summary, "issue_count": len(issues), "issues": issues}

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
            styles_root = read_xml(docx, STYLES_XML, issues) if STYLES_XML in parts else None
            style_defaults = style_run_defaults(styles_root)
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
                word_roots = all_word_roots(docx, parts, issues)
                summary["section_count"] = len(document_root.findall(".//w:sectPr", NS))
                summary["paragraph_count"] = len(document_root.findall(".//w:p", NS))
                summary["table_count"] = len(document_root.findall(".//w:tbl", NS))
                summary.update(audit_title_format(document_root, style_defaults, issues))
                summary.update(audit_punctuation_fonts(word_roots, style_defaults, issues))
                summary.update(audit_page_fields(document_root, word_roots, len(header_parts), len(footer_parts), issues))

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
        "Format details:",
        f"- title paragraphs: {summary['title_paragraph_count']}",
        f"- title font signatures: {summary['title_font_signature_count']}",
        f"- title sizes: {summary['title_size_count']}",
        f"- punctuation runs: {summary['punctuation_run_count']}",
        f"- punctuation font signatures: {summary['punctuation_font_signature_count']}",
        f"- punctuation missing eastAsia font: {summary['punctuation_missing_east_asia_count']}",
        f"- CJK quote runs: {summary['cjk_quote_run_count']}",
        f"- CJK quote font mismatches: {summary['cjk_quote_font_mismatch_count']}",
        f"- PAGE fields: {summary['page_field_count']}",
        f"- NUMPAGES fields: {summary['numpages_field_count']}",
        f"- section header references: {summary['section_header_reference_count']}",
        f"- section footer references: {summary['section_footer_reference_count']}",
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
