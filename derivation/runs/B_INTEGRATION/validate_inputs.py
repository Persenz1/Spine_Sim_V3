from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "derivation/runs/B_INTEGRATION"
MANIFEST_PATH = RUN_DIR / "INPUT_MANIFEST.yaml"
PROMPT_PATH = ROOT / "derivation/prompts/B/B_INTEGRATION_PROMPT.md"
CURRENT_CONTEXT = ROOT / "derivation/modules/B/current/B_MODULE_CONTEXT.md"
B3_SNAPSHOT = ROOT / "derivation/modules/B/history/B_MODULE_CONTEXT_after_B3.md"


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
    assert run["id"] == "B_INTEGRATION-r01"
    assert run["task"] == "B_INTEGRATION"
    assert run["module"] == "B"
    assert run["run_directory"] == "derivation/runs/B_INTEGRATION"
    assert run["prompt_version"] == "1.0.0"
    assert run["workflow_version"] == "1.3.4"
    assert run["engineering_context_version"] == "1.0.0"
    assert run["upstream_contract_version"] == "A_TO_B 1.0.0 accepted"
    assert run["module_context_baseline"] == "0.3.0"
    assert run["module_context_status"] == "accepted"

    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    assert "> 运行编号：B_INTEGRATION-r01" in prompt
    assert "> 提示词版本：1.0.0" in prompt
    assert "> 工程事实基线：engineering_fixed_context 1.0.0" in prompt
    assert "B_MODULE_CONTEXT 0.3.0，状态 accepted" in prompt
    assert "A_TO_B 1.0.0 accepted" in prompt


def validate_submodules(manifest: dict) -> None:
    acceptance = manifest["submodule_acceptance"]
    assert acceptance["all_three_submodules_accepted"] is True
    assert acceptance["latest_context_contains_B1_B2_B3"] is True
    assert acceptance["latest_context_matches_after_B3_snapshot"] is True
    assert acceptance["upstream_A_TO_B_inherited"] is True

    stages = acceptance["stages"]
    assert [item["task"] for item in stages] == ["B1", "B2", "B3"]
    expected_hashes = {
        "B1": "a4b9ae655fdabb82b72dffadfa3b6f0024cbba225120b51c26e96c201261616a",
        "B2": "65aeb65e28887942b8eed9e95d7339d62604b52000f2b6133def7245513dae22",
        "B3": "35e072fc730e2e74edc1d2c3cdc392382566b0b9ee2a2edd4947585038c4bc21",
    }
    for item in stages:
        snapshot = ROOT / item["snapshot"]
        report = (ROOT / item["validation_report"]).read_text(encoding="utf-8")
        assert item["status"] == "accepted"
        assert item["accepted_sha256"] == expected_hashes[item["task"]]
        assert sha256_bytes(snapshot.read_bytes()) == item["accepted_sha256"]
        assert "accepted" in report and "pass" in report

    assert CURRENT_CONTEXT.read_bytes() == B3_SNAPSHOT.read_bytes()
    current = CURRENT_CONTEXT.read_text(encoding="utf-8")
    assert "当前完成阶段：`B3`" in current
    assert "上下文版本：`0.3.0`" in current
    assert "当前状态：`accepted`" in current
    assert "B1：阵列几何、共同运动与柔顺拓扑" in current
    assert "B2：恒定法向主动推力下的活动接触集与载荷共享" in current
    assert "B3：失效重分配、连续再挂接与单元能力输出" in current
    assert "上游合同：`A_TO_B 1.0.0 accepted`" in current


def validate_upload_contract(manifest: dict) -> None:
    contract = manifest["upload_contract"]
    records = contract["files"]
    expected_paths = [
        "engineering_fixed_context/engineering_fixed_context.md",
        "derivation/modules/B/current/B_MODULE_CONTEXT.md",
        "derivation/prompts/B/B_INTEGRATION_PROMPT.md",
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
    assert outputs["file_count"] == 2
    assert outputs["files"] == ["B_INTEGRATED_MODEL.md", "B_TO_C_CONTRACT.md"]
    assert outputs["contract_embedded_in_integrated_model"] is True
    assert outputs["submodule_four_file_protocol_forbidden"] is True

    prompt = prompt_content.decode("utf-8")
    assert "### 8.1 B_INTEGRATED_MODEL.md" in prompt
    assert "### 8.2 B_TO_C_CONTRACT.md" in prompt
    assert "只上传以下 3 个文件" in prompt
    assert "按以下顺序输出 2 个独立、可下载文件" in prompt
    assert "合同正文必须与 `B_INTEGRATED_MODEL.md` 的公共 B→C 接口章节逐字一致" in prompt
    assert "intrinsic/embedded array-unit trial" in prompt
    assert "standalone continuous unit driver" in prompt
    assert "C 的四单元全局步接受后" in prompt
    assert "rocking=on" in prompt
    assert "KINEMATIC_MODE_UNSUPPORTED" in prompt
    assert "不要输出第三个总结文件、工程事实候选、RUN_UPDATE_SUMMARY 或 CITATION_BRIEF" in prompt


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
    print("B_INTEGRATION-r01 输入准备校验通过")
    print("- B1、B2、B3 接受快照和验证报告一致")
    print("- 最新 B_MODULE_CONTEXT 与 after_B3 快照一致并继承 A_TO_B 1.0.0")
    print("- 3 个上传文件的路径、顺序、字节数和 SHA-256 一致")
    print("- 冻结 Git 提交中的 3 个输入与 manifest 一致")
    print("- 正式提示词与运行归档副本逐字一致")
    print("- 输出严格为 B_INTEGRATED_MODEL.md 和 B_TO_C_CONTRACT.md")
    print("- 工程事实 1.0.0 生成器校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
