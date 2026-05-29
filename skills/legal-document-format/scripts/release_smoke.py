#!/usr/bin/env python3
"""Run the V2 release smoke gate for the legal document format skill."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
STEP_TIMEOUT_SECONDS = 300
PARALLEL_RENDER_TIMEOUT_SECONDS = 240


@dataclass
class StepResult:
    name: str
    status: str
    command: list[str]
    returncode: int
    detail: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the repository V2 release smoke gate.")
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip pytest. Use only when test dependencies are intentionally unavailable.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write a structured JSON report.",
    )
    return parser


def run_step(name: str, command: list[str]) -> StepResult:
    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=STEP_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        return StepResult(name=name, status="fail", command=command, returncode=124, detail=f"timed out after {exc.timeout}s")
    except OSError as exc:
        return StepResult(name=name, status="fail", command=command, returncode=127, detail=f"could not start command: {exc}")
    detail = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    return StepResult(
        name=name,
        status="pass" if result.returncode == 0 else "fail",
        command=command,
        returncode=result.returncode,
        detail=detail,
    )


def pytest_python() -> str:
    configured = REPO_ROOT / ".venv" / "bin" / "python"
    if configured.exists():
        return str(configured)
    return sys.executable


def run_parallel_render_step(docx_path: Path, output_root: Path, worker_count: int = 3) -> StepResult:
    commands = [
        [
            str(SCRIPT_DIR / "render_docx.sh"),
            str(docx_path),
            str(output_root / f"parallel-render-{index}"),
        ]
        for index in range(worker_count)
    ]
    processes = []
    for command in commands:
        try:
            processes.append(
                subprocess.Popen(
                    command,
                    cwd=REPO_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
            )
        except OSError as exc:
            for process in processes:
                process.kill()
            return StepResult(
                name="parallel_render_docx",
                status="fail",
                command=["parallel", *commands[0]],
                returncode=127,
                detail=f"could not start parallel render: {exc}",
            )
    outputs = []
    try:
        for process in processes:
            outputs.append(process.communicate(timeout=PARALLEL_RENDER_TIMEOUT_SECONDS)[0])
    except subprocess.TimeoutExpired:
        for process in processes:
            process.kill()
        outputs = [process.communicate()[0] for process in processes]
        return StepResult(
            name="parallel_render_docx",
            status="fail",
            command=["parallel", *commands[0]],
            returncode=124,
            detail=f"parallel render timed out after {PARALLEL_RENDER_TIMEOUT_SECONDS}s",
        )
    failures = [
        (index, process.returncode, outputs[index].strip().splitlines()[-1] if outputs[index].strip() else "")
        for index, process in enumerate(processes)
        if process.returncode != 0
    ]
    if failures:
        detail = "; ".join(f"worker {index} rc={code}: {message}" for index, code, message in failures)
        return StepResult(
            name="parallel_render_docx",
            status="fail",
            command=["parallel", *commands[0]],
            returncode=1,
            detail=detail,
        )
    return StepResult(
        name="parallel_render_docx",
        status="pass",
        command=["parallel", *commands[0]],
        returncode=0,
        detail=f"{worker_count} isolated LibreOffice renders passed",
    )


def run_release_smoke(skip_tests: bool) -> dict[str, object]:
    steps: list[StepResult] = []
    py_files = sorted(str(path.relative_to(REPO_ROOT)) for path in [*SCRIPT_DIR.glob("*.py"), *(REPO_ROOT / "tests").glob("*.py")])

    steps.append(
        run_step(
            "release_requirements",
            [str(SCRIPT_DIR / "check_release_requirements.py"), "--mode", "release"],
        )
    )
    steps.append(run_step("render_script_syntax", ["bash", "-n", str(SCRIPT_DIR / "render_docx.sh")]))
    steps.append(run_step("python_compile", [sys.executable, "-m", "py_compile", *py_files]))

    with tempfile.TemporaryDirectory(prefix="wenge-release-") as tmp:
        tmp_path = Path(tmp)
        template_path = tmp_path / "template.docx"
        replacements_path = tmp_path / "replacements.json"
        docx_path = tmp_path / "generated.docx"
        rendered_path = tmp_path / "rendered"
        replacements_path.write_text(
            json.dumps({"TITLE": "Synthetic DOCX 示例文书", "CASE_NO": "SYNTHETIC-CASE-NO-0001"}, ensure_ascii=False),
            encoding="utf-8",
        )
        steps.append(
            run_step(
                "synthetic_template_docx",
                [str(SCRIPT_DIR / "make_synthetic_docx.py"), str(template_path), "--title", "{{TITLE}}", "--case-no", "{{CASE_NO}}"],
            )
        )
        steps.append(
            run_step(
                "template_apply",
                [str(SCRIPT_DIR / "apply_docx_template.py"), str(template_path), str(docx_path), "--replacements-json", str(replacements_path), "--json"],
            )
        )
        steps.append(
            run_step(
                "template_parity",
                [str(SCRIPT_DIR / "compare_docx_template_parity.py"), str(template_path), str(docx_path), "--json"],
            )
        )
        steps.append(run_step("render_docx", [str(SCRIPT_DIR / "render_docx.sh"), str(docx_path), str(rendered_path)]))
        steps.append(run_parallel_render_step(docx_path, tmp_path))
        png_dir = rendered_path / "png"
        steps.append(
            run_step(
                "format_gate_require_visual",
                [
                    str(SCRIPT_DIR / "format_gate.py"),
                    "--text",
                    "申请人认为，本案事实清楚。",
                    "--docx",
                    str(docx_path),
                    "--baseline-png",
                    str(png_dir),
                    "--candidate-png",
                    str(png_dir),
                    "--require-visual",
                    "--fail-on-warning",
                    "--json",
                    "--no-excerpt",
                ],
            )
        )

    if not skip_tests:
        steps.append(run_step("pytest", [pytest_python(), "-m", "pytest", "-q"]))

    failed = [step for step in steps if step.status != "pass"]
    return {
        "status": "pass" if not failed else "fail",
        "step_count": len(steps),
        "failure_count": len(failed),
        "steps": [asdict(step) for step in steps],
    }


def format_human_report(report: dict[str, object]) -> str:
    lines = [
        "V2 Release Smoke Gate",
        "",
        f"Status: {str(report['status']).upper()}",
        f"Steps: {report['step_count']} (failures={report['failure_count']})",
        "",
        "Step Details:",
    ]
    for step in report["steps"]:  # type: ignore[index]
        lines.append(f"- {step['name']}: {step['status'].upper()} rc={step['returncode']} {step['detail']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = run_release_smoke(skip_tests=args.skip_tests)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_human_report(report))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
