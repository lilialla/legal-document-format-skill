from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "skills" / "legal-document-format" / "scripts" / "audit_text.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_text", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_audit_detects_core_punctuation_and_spacing_rules():
    audit_text = load_audit_module()
    sample = '申请人: 张三, 李四  \n被申请人（公司)称："同意"。\n案由：《》'

    issues = audit_text.audit_text(sample)
    codes = {issue.code for issue in issues}

    assert "HALFWIDTH_COLON_CN" in codes
    assert "HALFWIDTH_PUNCTUATION_CN" in codes
    assert "STRAIGHT_QUOTE" in codes
    assert "CONSECUTIVE_SPACES" in codes
    assert "TRAILING_WHITESPACE" in codes
    assert "MIXED_WIDTH_PUNCTUATION" in codes
    assert "EMPTY_BRACKETS" in codes
    assert all(issue.line >= 1 for issue in issues)
    assert all(issue.severity for issue in issues)
    assert all(issue.message for issue in issues)


def test_audit_allows_clean_chinese_legal_text():
    audit_text = load_audit_module()
    sample = "一、事实与理由\n申请人认为，本案事实清楚，证据充分。\n被申请人称：“已履行义务”。"

    assert audit_text.audit_text(sample) == []


def test_json_cli_accepts_file_input(tmp_path):
    input_file = tmp_path / "sample.txt"
    input_file.write_text("申请人: 张三\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(input_file), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["source"] == str(input_file)
    assert payload["issue_count"] >= 1
    assert payload["issues"][0]["code"]
    assert payload["issues"][0]["line"] == 1
    assert payload["issues"][0]["severity"]


def test_json_cli_can_omit_excerpts_for_sensitive_text(tmp_path):
    input_file = tmp_path / "sample.txt"
    input_file.write_text("申请人: 张三\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(input_file), "--json", "--no-excerpt"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["issue_count"] >= 1
    assert all(issue["excerpt"] == "" for issue in payload["issues"])


def test_cli_reports_missing_path_instead_of_treating_as_text(tmp_path):
    missing = tmp_path / "missing.txt"

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(missing), "--json"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "Input file not found" in result.stderr


def test_cli_accepts_direct_text_with_dots():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "合同第1.2条约定：履行期限。", "--json"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["source"] == "direct text"


def test_file_flag_requires_existing_file():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "missing.txt", "--file"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "Input file not found" in result.stderr


def test_cli_can_fail_on_issue():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "申请人: 张三", "--fail-on-issue"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "HALFWIDTH_COLON_CN" in result.stdout


def test_human_cli_accepts_direct_text():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "申请人: 张三"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Text audit:" in result.stdout
    assert "HALFWIDTH_COLON_CN" in result.stdout


def test_cli_help_and_executable_bit():
    result = subprocess.run(
        [str(SCRIPT_PATH), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert os.access(SCRIPT_PATH, os.X_OK)
    assert "INPUT_TEXT_OR_FILE" in result.stdout
    assert "--json" in result.stdout
    assert "--file" in result.stdout
    assert "--no-excerpt" in result.stdout
