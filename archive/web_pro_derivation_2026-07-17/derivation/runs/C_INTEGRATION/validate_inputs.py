from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "derivation/runs/C_INTEGRATION"
MANIFEST_PATH = RUN_DIR / "INPUT_MANIFEST.yaml"
PROMPT_PATH = ROOT / "derivation/prompts/C/C_INTEGRATION_PROMPT.md"
CURRENT_CONTEXT = ROOT / "derivation/modules/C/current/C_MODULE_CONTEXT.md"
C3_SNAPSHOT = ROOT / "derivation/modules/C/history/C_MODULE_CONTEXT_after_C3.md"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_manifest() -> dict:
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("INPUT_MANIFEST.yaml 顶层必须是映射")
    return data


def git_blob(commit: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def prompt_upload_paths(prompt: str) -> list[str]:
    paths: list[str] = []
    for line in prompt.splitlines():
        cells = line.split("|")
        if len(cells) < 4 or not cells[1].strip().isdigit():
            continue
        paths.append(cells[2].strip())
    return paths


def validate_identity(manifest: dict) -> None:
    run = manifest["run"]
    assert run["id"] == "C_INTEGRATION-r01"
    assert run["task"] == "C_INTEGRATION"
    assert run["module"] == "C"
    assert run["run_directory"] == "derivation/runs/C_INTEGRATION"
    assert run["prompt_version"] == "1.0.0"
    assert run["workflow_version"] == "1.3.4"
    assert run["engineering_context_version"] == "1.0.0"
    assert run["upstream_contract_version"] == "B_TO_C 1.0.0 accepted"
    assert run["module_context_baseline"] == "0.3.0"
    assert run["module_context_status"] == "accepted"

    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    assert "> 运行编号：C_INTEGRATION-r01" in prompt
    assert "> 提示词版本：1.0.0" in prompt
    assert "> 工程事实基线：engineering_fixed_context 1.0.0" in prompt
    assert "C_MODULE_CONTEXT 0.3.0，状态 accepted" in prompt
    assert "B_TO_C 1.0.0 accepted" in prompt


def validate_submodules(manifest: dict) -> None:
    acceptance = manifest["submodule_acceptance"]
    assert acceptance["all_three_submodules_accepted"] is True
    assert acceptance["latest_context_contains_C1_C2_C3"] is True
    assert acceptance["latest_context_matches_after_C3_snapshot"] is True
    assert acceptance["upstream_B_TO_C_inherited"] is True
    assert acceptance["upstream_motion_coverage_gap_preserved"] is True

    stages = acceptance["stages"]
    assert [item["task"] for item in stages] == ["C1", "C2", "C3"]
    expected_hashes = {
        "C1": "daa5702355fb56cf98cdd8194717fbe8e2b41311c9fd0ef29010484bd5f8654c",
        "C2": "7aa3c9a6a2e6f16886e7ec14674f0503d1d3794f8c70fab2942ab3d178ec6f65",
        "C3": "810fc26972652086403181f97221503e08e267485c6bd31fe1ea44b5af9a8f66",
    }
    for item in stages:
        snapshot = ROOT / item["snapshot"]
        report = (ROOT / item["validation_report"]).read_text(encoding="utf-8")
        assert item["status"] == "accepted"
        assert item["accepted_sha256"] == expected_hashes[item["task"]]
        assert sha256_bytes(snapshot.read_bytes()) == item["accepted_sha256"]
        assert "accepted" in report and "pass" in report

    assert CURRENT_CONTEXT.read_bytes() == C3_SNAPSHOT.read_bytes()
    current = CURRENT_CONTEXT.read_text(encoding="utf-8")
    assert "当前完成阶段：`C3" in current
    assert "上下文版本：`0.3.0`" in current
    assert "当前状态：`accepted`" in current
    assert "第一篇：C1" in current
    assert "第二篇：C2" in current
    assert "第三篇：C3" in current
    assert "上游合同：`B_TO_C 1.0.0 accepted`" in current
    assert "C3_CONTRACT_EXTENSION_REQUIRED" in current


def validate_upload_contract(manifest: dict) -> None:
    contract = manifest["upload_contract"]
    records = contract["files"]
    expected_paths = [
        "engineering_fixed_context/engineering_fixed_context.md",
        "derivation/modules/C/current/C_MODULE_CONTEXT.md",
        "derivation/prompts/C/C_INTEGRATION_PROMPT.md",
    ]
    assert contract["expected_file_count"] == 3
    assert contract["verified_file_count"] == 3
    assert len(records) == 3
    assert contract["all_expected_files_present"] is True
    assert contract["default_module_integration_inputs_complete"] is True
    assert contract["prompt_manifest_actual_paths_identical"] is True
    assert contract["additional_audit_inputs_required"] is False
    assert contract["historical_snapshots_uploaded"] is False
    assert contract["upstream_contract_uploaded_separately"] is False
    assert contract["upstream_integrated_model_uploaded"] is False
    assert contract["literature_packages_uploaded"] is False
    assert contract["citation_briefs_uploaded"] is False
    assert [record["path"] for record in records] == expected_paths

    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    assert prompt_upload_paths(prompt) == expected_paths

    commit = manifest["run"]["repository_commit"]
    subprocess.run(
        ["git", "rev-parse", "--verify", f"{commit}^{{commit}}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    for record in records:
        path = ROOT / record["path"]
        content = path.read_bytes()
        assert len(content) == record["bytes"]
        assert sha256_bytes(content) == record["sha256"]
        committed = git_blob(commit, record["path"])
        assert len(committed) == record["bytes"]
        assert sha256_bytes(committed) == record["sha256"]


def validate_prompt_archive_and_outputs(manifest: dict) -> None:
    archive = manifest["prompt_archive"]
    archived_content = (ROOT / archive["path"]).read_bytes()
    prompt_content = PROMPT_PATH.read_bytes()
    assert archive["matches_uploaded_prompt"] is True
    assert len(archived_content) == archive["bytes"]
    assert sha256_bytes(archived_content) == archive["sha256"]
    assert archived_content == prompt_content

    outputs = manifest["expected_outputs"]
    assert outputs["file_count"] == 1
    assert outputs["files"] == ["C_INTEGRATED_MODEL.md"]
    assert outputs["separate_downstream_contract_required"] is False
    assert outputs["public_upstream_downstream_experiment_interfaces_embedded"] is True
    assert outputs["submodule_four_file_protocol_forbidden"] is True

    prompt = prompt_content.decode("utf-8")
    assert "### 8.1 C_INTEGRATED_MODEL.md" in prompt
    assert "只上传以下 3 个文件" in prompt
    assert "只输出 1 个独立、可下载文件" in prompt
    assert "不要输出第二个合同文件" in prompt
    assert "C_CONTRACT_EXTENSION_REQUIRED" in prompt
    assert "B_TO_C 2.x" in prompt
    assert "C1 理想 `-P_i du_zi`" in prompt
    assert "物理事件路径优先级和摘要状态优先级分别定义" in prompt
    assert "不要输出第二个合同文件、总结文件、工程事实候选、RUN_UPDATE_SUMMARY 或 CITATION_BRIEF" in prompt


def validate_engineering_context() -> None:
    subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(ROOT / "engineering_fixed_context/internal/build_context.py"),
            "--check",
        ],
        cwd=ROOT,
        check=True,
    )


def main() -> int:
    manifest = load_manifest()
    validate_identity(manifest)
    validate_submodules(manifest)
    validate_upload_contract(manifest)
    validate_prompt_archive_and_outputs(manifest)
    validate_engineering_context()
    print("C_INTEGRATION-r01 输入准备校验通过")
    print("- C1、C2、C3 接受快照和验证报告一致")
    print("- 最新 C_MODULE_CONTEXT 与 after_C3 快照一致并继承 B_TO_C 1.0.0")
    print("- B 1.0 运动覆盖缺口和正式加载安全拒绝要求已保留")
    print("- 3 个上传文件的路径、顺序、字节数和 SHA-256 一致")
    print("- 冻结 Git 提交中的 3 个输入与 manifest 一致")
    print("- 正式提示词与运行归档副本逐字一致")
    print("- 输出严格为 C_INTEGRATED_MODEL.md")
    print("- 工程事实 1.0.0 生成器校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
