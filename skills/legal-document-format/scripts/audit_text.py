#!/usr/bin/env python3
"""Audit Chinese legal text for lightweight punctuation and spacing issues."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable


CJK_RE = r"\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
CJK_CHAR_RE = re.compile(rf"[{CJK_RE}]")

HALFWIDTH_PUNCTUATION = {
    ",": "逗号",
    ";": "分号",
    "?": "问号",
    "!": "叹号",
    "(": "左括号",
    ")": "右括号",
}


@dataclass(frozen=True)
class Issue:
    code: str
    message: str
    line: int
    severity: str
    column: int
    excerpt: str


def _excerpt(line: str, limit: int = 80) -> str:
    clean = line.replace("\t", "\\t")
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1] + "..."


def _make_issue(
    code: str,
    message: str,
    line_number: int,
    column: int,
    line: str,
    severity: str = "warning",
) -> Issue:
    return Issue(
        code=code,
        message=message,
        line=line_number,
        severity=severity,
        column=column,
        excerpt=_excerpt(line),
    )


def _find_halfwidth_colon(line: str, line_number: int) -> Iterable[Issue]:
    pattern = re.compile(rf"(?:[{CJK_RE}][^\n:：]{{0,12}}:|:[^\n:：]{{0,12}}[{CJK_RE}])")
    for match in pattern.finditer(line):
        colon_index = line.find(":", match.start(), match.end())
        if colon_index >= 0:
            yield _make_issue(
                "HALFWIDTH_COLON_CN",
                "中文语境中发现半角冒号，建议核对是否应使用全角冒号。",
                line_number,
                colon_index + 1,
                line,
            )


def _has_cjk_near(line: str, index: int, window: int = 3) -> bool:
    start = max(0, index - window)
    end = min(len(line), index + window + 1)
    return bool(CJK_CHAR_RE.search(line[start:end]))


def _find_halfwidth_punctuation_in_cjk_context(line: str, line_number: int) -> Iterable[Issue]:
    for index, mark in enumerate(line):
        if mark not in HALFWIDTH_PUNCTUATION:
            continue
        if not _has_cjk_near(line, index):
            continue
        yield _make_issue(
            "HALFWIDTH_PUNCTUATION_CN",
            f"中文语境中发现半角{HALFWIDTH_PUNCTUATION[mark]}，建议核对是否应使用全角标点。",
            line_number,
            index + 1,
            line,
        )


def _find_straight_quotes(line: str, line_number: int) -> Iterable[Issue]:
    for match in re.finditer(r"""["']""", line):
        yield _make_issue(
            "STRAIGHT_QUOTE",
            "发现英文直引号，中文法律文书中通常应核对为规范中文引号。",
            line_number,
            match.start() + 1,
            line,
        )


def _find_consecutive_spaces(line: str, line_number: int) -> Iterable[Issue]:
    for match in re.finditer(r" {2,}", line):
        yield _make_issue(
            "CONSECUTIVE_SPACES",
            "发现连续半角空格，建议核对是否为误输入或缩进格式问题。",
            line_number,
            match.start() + 1,
            line,
        )


def _find_trailing_whitespace(line: str, line_number: int) -> Iterable[Issue]:
    stripped = line.rstrip(" \t")
    if stripped != line:
        yield _make_issue(
            "TRAILING_WHITESPACE",
            "发现行尾空格或制表符。",
            line_number,
            len(stripped) + 1,
            line,
        )


def _find_mixed_width_punctuation(line: str, line_number: int) -> Iterable[Issue]:
    punctuation_groups = (
        (("，",), (",",), "逗号"),
        (("。",), (".",), "句号"),
        (("；",), (";",), "分号"),
        (("：",), (":",), "冒号"),
        (("（", "）"), ("(", ")"), "括号"),
        (("“", "”"), ('"',), "双引号"),
        (("‘", "’"), ("'",), "单引号"),
    )
    mixed_names = [
        name
        for full_marks, half_marks, name in punctuation_groups
        if any(mark in line for mark in full_marks) and any(mark in line for mark in half_marks)
    ]
    if mixed_names:
        first_columns = [
            line.find(half_mark) + 1
            for full_marks, half_marks, _name in punctuation_groups
            if any(mark in line for mark in full_marks)
            for half_mark in half_marks
            if line.find(half_mark) >= 0
        ]
        yield _make_issue(
            "MIXED_WIDTH_PUNCTUATION",
            "同一行疑似存在全角/半角标点混用：" + "、".join(mixed_names) + "。",
            line_number,
            min(first_columns) if first_columns else 1,
            line,
        )


def _find_empty_brackets(line: str, line_number: int) -> Iterable[Issue]:
    patterns = (
        (re.compile(r"（[ \t\u3000]*）"), "空中文括号"),
        (re.compile(r"\([ \t\u3000]*\)"), "空英文括号"),
        (re.compile(r"《[ \t\u3000]*》"), "空书名号"),
    )
    for pattern, label in patterns:
        for match in pattern.finditer(line):
            yield _make_issue(
                "EMPTY_BRACKETS",
                f"发现{label}，建议核对是否遗漏内容或应删除占位符。",
                line_number,
                match.start() + 1,
                line,
            )


CHECKS: tuple[Callable[[str, int], Iterable[Issue]], ...] = (
    _find_trailing_whitespace,
    _find_consecutive_spaces,
    _find_halfwidth_colon,
    _find_halfwidth_punctuation_in_cjk_context,
    _find_straight_quotes,
    _find_mixed_width_punctuation,
    _find_empty_brackets,
)


def audit_text(text: str) -> list[Issue]:
    """Return formatting and punctuation issues without modifying text."""
    lines = text.splitlines() or [""]
    issues: list[Issue] = []
    for line_number, line in enumerate(lines, start=1):
        for check in CHECKS:
            issues.extend(check(line, line_number))
    return issues


def _read_input(input_text_or_file: str, require_file: bool = False) -> tuple[str, str]:
    candidate = Path(input_text_or_file)
    if candidate.is_file():
        return candidate.read_text(encoding="utf-8"), str(candidate)
    if require_file or "/" in input_text_or_file or "\\" in input_text_or_file:
        raise FileNotFoundError(f"Input file not found: {input_text_or_file}")
    return input_text_or_file, "direct text"


def _format_human_report(issues: list[Issue], source: str) -> str:
    if not issues:
        return f"Text audit: no issues found ({source})."

    lines = [f"Text audit: {len(issues)} issue(s) found ({source})."]
    for issue in issues:
        lines.append(
            f"- L{issue.line}:C{issue.column} [{issue.severity}] "
            f"{issue.code}: {issue.message}"
        )
        if issue.excerpt:
            lines.append(f"  > {issue.excerpt}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Audit Chinese legal text for punctuation and spacing format issues. "
            "The input may be a UTF-8 text file path or direct text."
        )
    )
    parser.add_argument("input_text_or_file", metavar="INPUT_TEXT_OR_FILE")
    parser.add_argument(
        "--json",
        action="store_true",
        help="write a structured JSON report instead of a human-readable report",
    )
    parser.add_argument(
        "--file",
        action="store_true",
        help="treat INPUT_TEXT_OR_FILE as a file path and fail if it does not exist",
    )
    parser.add_argument(
        "--no-excerpt",
        action="store_true",
        help="omit source text excerpts from the report. This is the default for legal documents.",
    )
    parser.add_argument(
        "--with-excerpt",
        action="store_true",
        help="include source text excerpts in reports. Use only for non-sensitive debugging.",
    )
    parser.add_argument(
        "--fail-on-issue",
        action="store_true",
        help="return exit code 1 when any issue is found",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        text, source = _read_input(args.input_text_or_file, require_file=args.file)
    except FileNotFoundError as exc:
        parser.error(str(exc))
    issues = audit_text(text)
    omit_excerpt = args.no_excerpt or not args.with_excerpt
    output_issues = [
        Issue(
            code=issue.code,
            message=issue.message,
            line=issue.line,
            severity=issue.severity,
            column=issue.column,
            excerpt="" if omit_excerpt else issue.excerpt,
        )
        for issue in issues
    ]

    if args.json:
        payload = {
            "source": source,
            "issue_count": len(output_issues),
            "issues": [asdict(issue) for issue in output_issues],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_format_human_report(output_issues, source))

    return 1 if args.fail_on_issue and issues else 0


if __name__ == "__main__":
    sys.exit(main())
