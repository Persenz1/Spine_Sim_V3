from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = ROOT / "derivation/runs/B3/INPUT_MANIFEST.yaml"

EXPECTED_UPLOADS = (
    "engineering_fixed_context/engineering_fixed_context.md",
    "docs/extract/MECHANISM_MODULE_PLAN.md",
    "derivation/prompts/B/B3_PROMPT.md",
    "docs/derivation_workflow/templates/MODULE_CONTEXT_TEMPLATE.md",
    "docs/derivation_workflow/templates/ENGINEERING_FIXED_CONTEXT_CANDIDATE_TEMPLATE.md",
    "docs/derivation_workflow/templates/RUN_UPDATE_SUMMARY_TEMPLATE.yaml",
    "docs/derivation_workflow/templates/CITATION_BRIEF_TEMPLATE.md",
    "derivation/contracts/A_TO_B_CONTRACT.md",
    "derivation/modules/B/current/B_MODULE_CONTEXT.md",
    "docs/extract/机理提取/03_compliant_directional_suspensions/03_compliant_directional_suspensions.zip",
    "docs/extract/机理提取/09_stochastic_compliant_spine_arrays/09_stochastic_compliant_spine_arrays.zip",
    "docs/extract/机理提取/21_underactuated_adaptive_microspines_gripper/21_underactuated_adaptive_microspines_gripper.zip",
)

EXPECTED_LITERATURE = EXPECTED_UPLOADS[-3:]
EXPECTED_OUTPUTS = (
    "B_MODULE_CONTEXT.md",
    "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md",
    "RUN_UPDATE_SUMMARY.yaml",
    "CITATION_BRIEF.md",
)


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def read_manifest() -> dict:
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("INPUT_MANIFEST.yaml 顶层必须是映射")
    return data


def git_blob(commit: str, relative_path: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{commit}:{relative_path}"], cwd=ROOT
    )


def verify_record(path: Path, expected_bytes: int, expected_sha256: str, label: str) -> bytes:
    if not path.is_file():
        raise FileNotFoundError(path)
    content = path.read_bytes()
    if len(content) != expected_bytes:
        raise ValueError(f"{label} 字节数不一致：{len(content)} != {expected_bytes}")
    digest = sha256_bytes(content)
    if digest != expected_sha256:
        raise ValueError(f"{label} SHA-256 不一致：{digest} != {expected_sha256}")
    return content


def verify_frozen_record(
    commit: str,
    relative_path: str,
    expected_bytes: int,
    expected_sha256: str,
    label: str,
) -> bytes:
    path = ROOT / relative_path
    if path.is_file():
        content = path.read_bytes()
        if len(content) == expected_bytes and sha256_bytes(content) == expected_sha256:
            return content
    content = git_blob(commit, relative_path)
    if len(content) != expected_bytes:
        raise ValueError(f"{label} 冻结字节数不一致：{len(content)} != {expected_bytes}")
    digest = sha256_bytes(content)
    if digest != expected_sha256:
        raise ValueError(f"{label} 冻结 SHA-256 不一致：{digest} != {expected_sha256}")
    return content


def prompt_upload_paths(prompt: str) -> tuple[str, ...]:
    start = prompt.index("## 3. 网页端必须上传的文件清单与完整阅读要求")
    end = prompt.index("不要补传", start)
    block = prompt[start:end]
    paths: list[str] = []
    pattern = re.compile(r"^\|\s*\d+\s*\|\s*([^|]+?)\s*\|", re.MULTILINE)
    for match in pattern.finditer(block):
        paths.append(match.group(1).strip().strip("`"))
    return tuple(paths)


def run_python_check(relative_script: str, *args: str) -> str:
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(ROOT / relative_script), *args],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def main() -> int:
    manifest = read_manifest()
    run = manifest["run"]
    prerequisite = manifest["prerequisite_acceptance"]
    contract = manifest["upload_contract"]
    records = contract["files"]
    outputs = manifest["expected_outputs"]
    preparation = manifest["preparation_validation"]
    commit = run["repository_commit"]

    assert run["id"] == "B3-r01"
    assert run["module"] == "B3"
    assert run["prepared_on"] == "2026-07-16"
    assert run["run_directory"] == "derivation/runs/B3"
    assert run["prompt_version"] == "1.0.0"
    assert run["workflow_version"] == "1.3.4"
    assert run["engineering_context_version"] == "1.0.0"
    assert run["module_context_baseline"] == "0.2.0"
    assert run["module_context_status"] == "accepted"
    assert run["upstream_contract_version"] == "1.0.0"
    assert run["upstream_contract_status"] == "accepted"

    assert prerequisite["prior_module_run"] == "B2-r01"
    assert prerequisite["status"] == "accepted"
    assert prerequisite["current_module_context_version"] == "0.2.0"
    assert prerequisite["current_module_context_stage"] == "B2"
    assert prerequisite["current_module_context_status"] == "accepted"
    assert prerequisite["current_history_byte_identical"] is True
    assert prerequisite["public_contract_version"] == "1.0.0"
    assert prerequisite["public_contract_status"] == "accepted"
    assert prerequisite["semantic_prerequisite_complete"] is True

    assert contract["expected_file_count"] == len(EXPECTED_UPLOADS)
    assert contract["verified_file_count"] == len(EXPECTED_UPLOADS)
    assert len(records) == len(EXPECTED_UPLOADS)
    assert contract["all_expected_files_present"] is True
    assert contract["minimum_literature_package_complete"] is True
    assert contract["upstream_contract_included"] is True
    assert contract["existing_b_module_context_required"] is True
    assert contract["existing_b_module_context_included"] is True
    assert contract["full_a_integrated_model_required"] is False
    assert contract["prompt_manifest_actual_paths_identical"] is True

    paths = tuple(record["path"] for record in records)
    if paths != EXPECTED_UPLOADS:
        raise ValueError(f"manifest 上传路径或顺序错误：{paths!r}")
    if len(paths) != len(set(paths)):
        raise ValueError("上传清单存在重复路径")
    if sum(path.endswith(".zip") for path in paths) != 3:
        raise ValueError("B3 最小文献包必须恰为 3 个 zip")
    forbidden = {
        "derivation/modules/A/final/A_INTEGRATED_MODEL.md",
        "derivation/runs/B2/CITATION_BRIEF.md",
    }
    if forbidden.intersection(paths):
        raise ValueError("B3 默认上传清单包含禁止的历史或完整 A 集成输入")

    subprocess.run(
        ["git", "rev-parse", "--verify", f"{commit}^{{commit}}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for record in records:
        frozen = verify_frozen_record(
            commit,
            record["path"],
            record["bytes"],
            record["sha256"],
            f"上传输入 {record['path']}",
        )
        committed = git_blob(commit, record["path"])
        if committed != frozen:
            raise ValueError(f"冻结提交与已验证输入不一致：{record['path']}")

    prompt_path = ROOT / "derivation/prompts/B/B3_PROMPT.md"
    prompt_bytes = prompt_path.read_bytes()
    prompt = prompt_bytes.decode("utf-8")
    if prompt_upload_paths(prompt) != EXPECTED_UPLOADS:
        raise ValueError("提示词上传表、manifest 和实际上传顺序不一致")
    if "本轮网页端必须按下表顺序上传 12 个文件" not in prompt:
        raise ValueError("提示词没有冻结 12 文件上传合同")
    for marker in (
        "> 模块：B3",
        "> 运行编号：B3-r01",
        "> 实际运行目录：derivation/runs/B3",
        "> 提示词版本：1.0.0",
        "> B 模块上下文基线：B_MODULE_CONTEXT 0.2.0，完成阶段 B2，状态 accepted",
        "共享损伤记忆与多针冲突",
        "100 mm 连续拖拽历史",
        "不得执行 B 大模块集成",
    ):
        if marker not in prompt:
            raise ValueError(f"提示词缺少 B3 强制内容：{marker}")

    archive_record = manifest["prompt_archive"]
    assert archive_record["matches_uploaded_prompt"] is True
    archive = verify_record(
        ROOT / archive_record["path"],
        archive_record["bytes"],
        archive_record["sha256"],
        "PROMPT.md 归档",
    )
    if archive != prompt_bytes:
        raise ValueError("PROMPT.md 与正式 B3_PROMPT.md 不是逐字节一致")

    validation_report = verify_record(
        ROOT / prerequisite["validation_report"],
        prerequisite["validation_report_bytes"],
        prerequisite["validation_report_sha256"],
        "B2 验证报告",
    ).decode("utf-8")
    if "pass / accepted" not in validation_report:
        raise ValueError("B2 验证报告未确认 pass / accepted")

    current_context = verify_record(
        ROOT / prerequisite["current_module_context"],
        prerequisite["current_module_context_bytes"],
        prerequisite["current_module_context_sha256"],
        "B2 接受上下文",
    )
    history_context = verify_record(
        ROOT / prerequisite["history_snapshot"],
        prerequisite["history_snapshot_bytes"],
        prerequisite["history_snapshot_sha256"],
        "B2 历史快照",
    )
    if current_context != history_context:
        raise ValueError("当前 B 上下文与 B2 历史快照不一致")
    current_text = current_context.decode("utf-8")
    for marker in (
        "当前完成阶段",
        "B2",
        "上下文版本",
        "0.2.0",
        "当前状态",
        "accepted",
        "B3_REBALANCE_REQUIRED",
        "B2EquilibriumTrial",
    ):
        if marker not in current_text:
            raise ValueError(f"B2 接受上下文缺少前置标记：{marker}")

    public_contract = verify_record(
        ROOT / prerequisite["public_contract"],
        prerequisite["public_contract_bytes"],
        prerequisite["public_contract_sha256"],
        "A_TO_B 正式合同",
    ).decode("utf-8")
    for marker in (
        "contract_version",
        "1.0.0",
        "status",
        "accepted",
        "embedded_constitutive_trial",
        "prepare_atomic_commit",
        "commit_atomic",
        "DAMAGE_CONFLICT_REQUIRES_RESOLVE",
    ):
        if marker not in public_contract:
            raise ValueError(f"A_TO_B 合同缺少冻结标记：{marker}")

    for literature_path in EXPECTED_LITERATURE:
        with zipfile.ZipFile(ROOT / literature_path) as archive_zip:
            names = archive_zip.namelist()
            if "evidence_card.md" not in names:
                raise ValueError(f"文献包缺少 evidence_card.md：{literature_path}")
            figures = [
                name
                for name in names
                if name.startswith("figures/") and not name.endswith("/")
            ]
            if len(figures) != 3:
                raise ValueError(f"文献包关键图数量不是 3：{literature_path}:{figures!r}")
            unexpected = [
                name
                for name in names
                if name != "evidence_card.md" and name not in figures
            ]
            if unexpected:
                raise ValueError(f"文献包存在未记录内容：{literature_path}:{unexpected!r}")
            bad_member = archive_zip.testzip()
            if bad_member is not None:
                raise ValueError(f"文献包 CRC 失败：{literature_path}:{bad_member}")

    assert outputs["file_count"] == len(EXPECTED_OUTPUTS)
    if tuple(outputs["files"]) != EXPECTED_OUTPUTS:
        raise ValueError("manifest 的网页输出文件名或顺序错误")
    for index, output in enumerate(EXPECTED_OUTPUTS, start=1):
        if f"### 11.{index} {output}" not in prompt:
            raise ValueError(f"提示词缺少固定输出章节：{output}")

    for key in (
        "engineering_context_generator_check",
        "b2_input_validation",
        "b2_artifact_acceptance_validation",
        "upstream_contract_validation",
        "prompt_archive_byte_identical",
        "git_snapshot_hashes_verified",
        "upload_order_verified",
        "literature_zip_crc_verified",
        "output_contract_verified",
        "no_run_directory_collision",
    ):
        if preparation[key] not in (True, "pass"):
            raise ValueError(f"准备校验未通过：{key}={preparation[key]!r}")

    build_output = run_python_check(
        "engineering_fixed_context/internal/build_context.py", "--check"
    )
    b2_input_output = run_python_check("derivation/runs/B2/validate_inputs.py")
    b2_artifact_output = run_python_check("derivation/runs/B2/validate_artifacts.py")

    print("B3-r01 输入准备校验通过")
    print("- B2-r01、B_MODULE_CONTEXT 0.2.0 和 A_TO_B_CONTRACT 1.0.0 已接受且哈希一致")
    print("- 12 个上传文件的路径、顺序、字节数和 SHA-256 一致")
    print("- 冻结 Git 提交中的全部上传输入与 manifest 一致")
    print("- 正式提示词与运行归档副本逐字节一致")
    print("- 文献 03、09、21 压缩包结构、关键图数量和 CRC 通过")
    print("- 网页输出严格为 B_MODULE_CONTEXT、工程事实候选、运行摘要和引用说明")
    print(f"- {build_output}")
    print(f"- B2 输入复验：{b2_input_output.splitlines()[0]}")
    print(f"- B2 接受复验：{b2_artifact_output.splitlines()[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
