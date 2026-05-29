from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills" / "legal-document-format" / "scripts" / "release_smoke.py"


def load_module():
    spec = importlib.util.spec_from_file_location("release_smoke", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_release_smoke_reports_failure_when_a_step_fails():
    module = load_module()

    def fake_run_step(name: str, command: list[str]):
        status = "fail" if name == "render_docx" else "pass"
        return module.StepResult(name=name, status=status, command=command, returncode=1 if status == "fail" else 0, detail=name)

    with patch.object(module, "run_step", side_effect=fake_run_step), patch.object(
        module,
        "run_parallel_render_step",
        return_value=module.StepResult("parallel_render_docx", "pass", ["parallel"], 0, "ok"),
    ):
        report = module.run_release_smoke(skip_tests=True)

    assert report["status"] == "fail"
    assert report["failure_count"] == 1
    assert any(step["name"] == "format_gate_require_visual" for step in report["steps"])


def test_release_smoke_skip_tests_omits_pytest_step():
    module = load_module()

    with patch.object(
        module,
        "run_step",
        side_effect=lambda name, command: module.StepResult(name, "pass", command, 0, name),
    ), patch.object(
        module,
        "run_parallel_render_step",
        return_value=module.StepResult("parallel_render_docx", "pass", ["parallel"], 0, "ok"),
    ):
        report = module.run_release_smoke(skip_tests=True)

    assert report["status"] == "pass"
    assert all(step["name"] != "pytest" for step in report["steps"])
    assert any(step["name"] == "parallel_render_docx" for step in report["steps"])


def test_release_smoke_uses_repo_venv_for_pytest_when_available():
    module = load_module()
    expected = REPO_ROOT / ".venv" / "bin" / "python"

    if expected.exists():
        assert module.pytest_python() == str(expected)
    else:
        assert module.pytest_python() == sys.executable


def test_run_step_returns_structured_timeout():
    module = load_module()

    with patch.object(module.subprocess, "run", side_effect=subprocess.TimeoutExpired(["cmd"], 1)):
        result = module.run_step("slow", ["cmd"])

    assert result.status == "fail"
    assert result.returncode == 124
    assert "timed out" in result.detail


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
    assert "--skip-tests" in result.stdout
