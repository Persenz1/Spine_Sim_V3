from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "derivation/runs/A1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bytes_at_commit(commit: str, relative_path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    return result.stdout


def validate_run_summary() -> None:
    summary = yaml.safe_load((RUN_DIR / "RUN_UPDATE_SUMMARY.yaml").read_text(encoding="utf-8"))
    assert set(summary) == {
        "run",
        "engineering_context_delta",
        "module_context_delta",
        "outputs",
        "self_check",
    }
    assert summary["run"] == {
        "module": "A1",
        "prompt_version": "1.2.0",
        "engineering_context_baseline": "1.0.0",
        "module_context_baseline": "none",
        "run_directory": "derivation/runs/A1",
    }
    deltas = summary["engineering_context_delta"]
    assert len(deltas) == 1
    delta = deltas[0]
    assert delta["id"] == "none"
    assert delta["operation"] == "none"
    assert delta["target"] is None
    assert delta["affected_modules"] == []
    assert delta["changed_fields"] == []
    assert all(value == [] for value in delta["evidence"].values())
    assert delta["proposed_fact"] is None
    assert delta["approval_required"] is False
    assert all(
        value == "pass"
        for key, value in summary["self_check"].items()
        if key != "notes"
    )


def validate_manifest() -> None:
    manifest = yaml.safe_load((RUN_DIR / "INPUT_MANIFEST.yaml").read_text(encoding="utf-8"))
    contract = manifest["upload_contract"]
    assert contract["expected_file_count"] == 11
    assert contract["verified_file_count"] == 11
    assert len(contract["files"]) == 11
    assert contract["all_expected_files_present"] is True
    assert contract["minimum_literature_package_complete"] is True
    repository_commit = manifest["run"]["repository_commit"]
    for item in contract["files"]:
        path = ROOT / item["path"]
        assert path.is_file(), path
        current_bytes = path.read_bytes()
        if len(current_bytes) == item["bytes"] and hashlib.sha256(current_bytes).hexdigest() == item["sha256"]:
            continue
        historical_bytes = bytes_at_commit(repository_commit, item["path"])
        assert len(historical_bytes) == item["bytes"], path
        assert hashlib.sha256(historical_bytes).hexdigest() == item["sha256"], path

    for item in manifest["received_outputs"]:
        path = ROOT / item["archived_path"]
        assert path.is_file(), path
        assert path.stat().st_size == item["bytes"], path
        assert sha256(path) == item["sha256"], path


def validate_markdown() -> None:
    candidate = (RUN_DIR / "MODULE_CONTEXT_CANDIDATE.md").read_text(encoding="utf-8")
    assert candidate.count("```") % 2 == 0
    assert sum(line.strip() == "$$" for line in candidate.splitlines()) % 2 == 0

    required_sections = [
        "## 1. 范围、目标与不可越界边界",
        "## 2. 坐标、几何对象、符号与单位",
        "## 3. 输入、输出、状态与统一数据合同",
        "## 4. 地形生成与导入机理",
        "## 5. 实测表面预处理与质量门槛",
        "## 6. 有限球形针尖可达性",
        "## 7. 完整针体与安装结构的禁止碰撞",
        "## 8. 首次接触与方向性几何候选",
        "## 9. 事件函数、可变步长与数值算法",
        "## 10. 模型选择、参数证据与标定状态",
        "## 11. 验证、收敛、完成判据与当前状态",
        "## 12. 对 A2/A3 的交接合同",
    ]
    assert all(section in candidate for section in required_sections)

    citation = (RUN_DIR / "CITATION_BRIEF.md").read_text(encoding="utf-8")
    body, references = citation.split("## 参考来源", maxsplit=1)
    defined = set(re.findall(r"^\[(\d+)\]\s", references, flags=re.MULTILINE))
    used: set[str] = set()
    for group in re.findall(r"\[([0-9,]+)\]", body):
        used.update(group.split(","))
    assert defined == used == {str(index) for index in range(1, 13)}


def validate_archive_and_acceptance() -> None:
    baseline = ROOT / "engineering_fixed_context/engineering_fixed_context.md"
    engineering_candidate = RUN_DIR / "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md"
    assert baseline.read_bytes() == engineering_candidate.read_bytes()

    prompt = ROOT / "derivation/prompts/A/A1_PROMPT.md"
    archived_prompt = RUN_DIR / "PROMPT.md"
    assert prompt.read_bytes() == archived_prompt.read_bytes()

    snapshot = ROOT / "derivation/modules/A/history/A_MODULE_CONTEXT_after_A1.md"
    current = ROOT / "derivation/modules/A/current/A_MODULE_CONTEXT.md"
    assert sha256(snapshot) == "9a14d472e87bd9cb230abf1ad835cbf546771b38cdf5e797091dd02231821e9e"
    accepted = snapshot.read_text(encoding="utf-8")
    assert "> 当前状态：`accepted`" in accepted
    assert "q_e(\\mathbf q)=\\sqrt{{\\mathbf q'}^\\mathsf T\\mathbf A\\mathbf q'}." in accepted
    rolled = current.read_text(encoding="utf-8")
    assert "> 当前状态：`accepted`" in rolled
    assert "## 1. 范围、目标与不可越界边界" in rolled


def main() -> None:
    validate_run_summary()
    validate_manifest()
    validate_markdown()
    validate_archive_and_acceptance()
    print("A1-r01 artifact validation: PASS")


if __name__ == "__main__":
    main()
