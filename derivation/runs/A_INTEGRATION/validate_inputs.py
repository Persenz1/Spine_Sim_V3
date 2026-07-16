from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "derivation/runs/A_INTEGRATION"
MANIFEST_PATH = RUN_DIR / "INPUT_MANIFEST.yaml"
PROMPT_PATH = ROOT / "derivation/prompts/A/A_INTEGRATION_PROMPT.md"
CURRENT_CONTEXT = ROOT / "derivation/modules/A/current/A_MODULE_CONTEXT.md"
A3_SNAPSHOT = ROOT / "derivation/modules/A/history/A_MODULE_CONTEXT_after_A3.md"


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
    assert run["id"] == "A_INTEGRATION-r01"
    assert run["task"] == "A_INTEGRATION"
    assert run["module"] == "A"
    assert run["run_directory"] == "derivation/runs/A_INTEGRATION"
    assert run["prompt_version"] == "1.0.0"
    assert run["workflow_version"] == "1.3.4"
    assert run["engineering_context_version"] == "1.0.0"
    assert run["module_context_baseline"] == "0.3.0"
    assert run["module_context_status"] == "accepted"

    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    assert "> 运行编号：A_INTEGRATION-r01" in prompt
    assert "> 提示词版本：1.0.0" in prompt
    assert "> 工程事实基线：engineering_fixed_context 1.0.0" in prompt
    assert "A_MODULE_CONTEXT 0.3.0，状态 accepted" in prompt


def validate_submodules(manifest: dict) -> None:
    acceptance = manifest["submodule_acceptance"]
    assert acceptance["all_three_submodules_accepted"] is True
    assert acceptance["latest_context_contains_A1_A2_A3"] is True
    assert acceptance["latest_context_matches_after_A3_snapshot"] is True

    stages = acceptance["stages"]
    assert [item["task"] for item in stages] == ["A1", "A2", "A3"]
    expected_hashes = {
        "A1": "9a14d472e87bd9cb230abf1ad835cbf546771b38cdf5e797091dd02231821e9e",
        "A2": "09ca48fdd68779005ad504c722538bfce477b0b60cf4ee554295f4a85366ce6a",
        "A3": "cca6febc359cf30f2c0454e375f010222da5c642b43316bb7a5f712cdf2da898",
    }
    for item in stages:
        snapshot = ROOT / item["snapshot"]
        report = (ROOT / item["validation_report"]).read_text(encoding="utf-8")
        assert item["status"] == "accepted"
        assert item["accepted_sha256"] == expected_hashes[item["task"]]
        assert sha256_bytes(snapshot.read_bytes()) == item["accepted_sha256"]
        assert "accepted" in report or "接受" in report

    assert CURRENT_CONTEXT.read_bytes() == A3_SNAPSHOT.read_bytes()
    current = CURRENT_CONTEXT.read_text(encoding="utf-8")
    assert "当前完成阶段" in current and "A3" in current
    assert "上下文版本" in current and "0.3.0" in current
    assert "当前状态" in current and "accepted" in current
    assert "# A2：单边接触、摩擦稳定与结构柔顺加载" in current
    assert "# A3：滑移、局部材料失效、脱离与再挂接" in current


def validate_upload_contract(manifest: dict) -> None:
    contract = manifest["upload_contract"]
    records = contract["files"]
    expected_paths = [
        "engineering_fixed_context/engineering_fixed_context.md",
        "derivation/modules/A/current/A_MODULE_CONTEXT.md",
        "derivation/prompts/A/A_INTEGRATION_PROMPT.md",
    ]
    assert contract["expected_file_count"] == 3
    assert contract["verified_file_count"] == 3
    assert len(records) == 3
    assert contract["all_expected_files_present"] is True
    assert contract["default_module_integration_inputs_complete"] is True
    assert contract["prompt_manifest_actual_paths_identical"] is True
    assert contract["additional_audit_inputs_required"] is False
    assert contract["historical_snapshots_uploaded"] is False
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
    assert outputs["file_count"] == 2
    assert outputs["files"] == ["A_INTEGRATED_MODEL.md", "A_TO_B_CONTRACT.md"]
    assert outputs["contract_embedded_in_integrated_model"] is True
    assert outputs["submodule_four_file_protocol_forbidden"] is True

    prompt = prompt_content.decode("utf-8")
    assert "### 8.1 A_INTEGRATED_MODEL.md" in prompt
    assert "### 8.2 A_TO_B_CONTRACT.md" in prompt
    assert "只上传以下 3 个文件" in prompt
    assert "按以下顺序输出 2 个独立、可下载文件" in prompt
    assert "合同正文必须与 A_INTEGRATED_MODEL 的公共接口章节逐字一致" in prompt
    assert "intrinsic_single_spine_kernel" in prompt
    assert "standalone_single_spine_driver" in prompt
    assert "不得把单刺独立验证的 0.5 N 复制成阵列内每根针" in prompt


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
    print("A_INTEGRATION-r01 输入准备校验通过")
    print("- A1、A2、A3 接受快照和验证报告一致")
    print("- 最新 A_MODULE_CONTEXT 与 after_A3 快照一致")
    print("- 3 个上传文件的路径、顺序、字节数和 SHA-256 一致")
    print("- 冻结 Git 提交中的 3 个输入与 manifest 一致")
    print("- 正式提示词与运行归档副本逐字一致")
    print("- 输出严格为 A_INTEGRATED_MODEL.md 和 A_TO_B_CONTRACT.md")
    print("- 工程事实 1.0.0 生成器校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
