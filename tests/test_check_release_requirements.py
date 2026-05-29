from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills" / "legal-document-format" / "scripts" / "check_release_requirements.py"


def load_module():
    spec = importlib.util.spec_from_file_location("check_release_requirements", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_core_mode_does_not_require_visual_tools():
    module = load_module()

    with patch.object(module, "find_soffice", return_value=None), patch.object(module.shutil, "which", return_value=None):
        report = module.build_report("core")

    assert report["status"] == "pass"
    visual_requirements = [item for item in report["requirements"] if item["name"] in {"soffice", "pdftoppm"}]
    assert visual_requirements
    assert all(item["required"] is False for item in visual_requirements)
    assert all(item["status"] == "skip" for item in visual_requirements)


def test_release_mode_requires_visual_tools():
    module = load_module()

    with patch.object(module, "find_soffice", return_value=None), patch.object(module.shutil, "which", return_value=None):
        report = module.build_report("release")

    assert report["status"] == "fail"
    assert report["blocking_failure_count"] == 2
    assert any(item["name"] == "soffice" and item["required"] for item in report["requirements"])
    assert any(item["name"] == "pdftoppm" and item["required"] for item in report["requirements"])


def test_cli_json_core_mode():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--mode", "core", "--json"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stderr
    assert '"mode": "core"' in result.stdout
    assert '"status": "pass"' in result.stdout


def test_help_and_executable_bit():
    result = subprocess.run(
        [str(SCRIPT), "--help"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0
    assert os.access(SCRIPT, os.X_OK)
    assert SCRIPT.stat().st_mode & stat.S_IXUSR
    assert "--mode" in result.stdout
