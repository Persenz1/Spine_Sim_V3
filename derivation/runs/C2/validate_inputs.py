from __future__ import annotations

import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = ROOT / "derivation/runs/C2/INPUT_MANIFEST.yaml"

EXPECTED_UPLOADS = (
    "engineering_fixed_context/engineering_fixed_context.md",
    "docs/extract/MECHANISM_MODULE_PLAN.md",
    "derivation/prompts/C/C2_PROMPT.md",
    "docs/derivation_workflow/templates/MODULE_CONTEXT_TEMPLATE.md",
    "docs/derivation_workflow/templates/ENGINEERING_FIXED_CONTEXT_CANDIDATE_TEMPLATE.md",
    "docs/derivation_workflow/templates/RUN_UPDATE_SUMMARY_TEMPLATE.yaml",
    "docs/derivation_workflow/templates/CITATION_BRIEF_TEMPLATE.md",
    "derivation/contracts/B_TO_C_CONTRACT.md",
    "derivation/modules/C/current/C_MODULE_CONTEXT.md",
    "docs/extract/机理提取/17_beetle_claw_mechanical_gripper/17_beetle_claw_mechanical_gripper.zip",
    "docs/extract/机理提取/28_loris_lightweight_free_climbing_robot/28_loris_lightweight_free_climbing_robot.zip",
)

EXPECTED_LITERATURE = EXPECTED_UPLOADS[-2:]

EXPECTED_OUTPUTS = (
    "C_MODULE_CONTEXT.md",
    "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md",
    "RUN_UPDATE_SUMMARY.yaml",
    "CITATION_BRIEF.md",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_manifest() -> dict:
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("INPUT_MANIFEST.yaml 顶层必须是映射")
    return data


def prompt_upload_paths(prompt: str) -> list[str]:
    paths: list[str] = []
    for line in prompt.splitlines():
        cells = line.split("|")
        if len(cells) < 4 or not cells[1].strip().isdigit():
            continue
        path_cell = cells[2].strip()
        if not (path_cell.startswith("`") and path_cell.endswith("`")):
            raise ValueError(f"上传表路径未使用反引号：{line}")
        paths.append(path_cell[1:-1])
    return paths


def git_blob(commit: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


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

    assert run["id"] == "C2-r01"
    assert run["module"] == "C2"
    assert run["prepared_on"] == "2026-07-17"
    assert run["run_directory"] == "derivation/runs/C2"
    assert run["prompt_version"] == "1.0.0"
    assert run["workflow_version"] == "1.3.4"
    assert run["engineering_context_version"] == "1.0.0"
    assert run["module_context_baseline"] == "0.1.0"
    assert run["module_context_status"] == "accepted"
    assert run["upstream_contract_version"] == "1.0.0"
    assert run["upstream_contract_status"] == "accepted"

    assert prerequisite["prior_module_run"] == "C1-r01"
    assert prerequisite["status"] == "accepted"
    assert prerequisite["current_module_context_version"] == "0.1.0"
    assert prerequisite["current_module_context_stage"] == "C1"
    assert prerequisite["current_module_context_status"] == "accepted"
    assert prerequisite["current_history_byte_identical"] is True
    assert prerequisite["public_contract_version"] == "1.0.0"
    assert prerequisite["public_contract_status"] == "accepted"
    assert prerequisite["c2_motion_extension_required"] is True
    assert prerequisite["semantic_prerequisite_complete"] is True

    assert contract["expected_file_count"] == len(EXPECTED_UPLOADS)
    assert contract["verified_file_count"] == len(EXPECTED_UPLOADS)
    assert len(records) == len(EXPECTED_UPLOADS)
    assert contract["all_expected_files_present"] is True
    assert contract["minimum_literature_package_complete"] is True
    assert contract["upstream_contract_included"] is True
    assert contract["existing_c_module_context_required"] is True
    assert contract["existing_c_module_context_included"] is True
    assert contract["full_b_integrated_model_required"] is False
    assert contract["prompt_manifest_actual_paths_identical"] is True

    paths = tuple(record["path"] for record in records)
    if paths != EXPECTED_UPLOADS:
        raise ValueError(f"manifest 上传路径或顺序错误：{paths!r}")
    if len(paths) != len(set(paths)):
        raise ValueError("上传清单存在重复路径")
    if sum(path.endswith(".zip") for path in paths) != 2:
        raise ValueError("C2 最小文献包必须恰为 2 个 zip")
    if "derivation/modules/B/final/B_INTEGRATED_MODEL.md" in paths:
        raise ValueError("C2 默认上传清单不得包含完整 B 集成模型")
    if "derivation/modules/C/current/C_MODULE_CONTEXT.md" not in paths:
        raise ValueError("C2 必须上传 C1 accepted 完整 C_MODULE_CONTEXT")
    for forbidden_literature in ("18_", "19_", "29_"):
        if any(Path(path).name.startswith(forbidden_literature) for path in paths):
            raise ValueError(f"C2 默认上传清单误含备用文献：{forbidden_literature}")

    for record in records:
        verify_record(
            ROOT / record["path"],
            record["bytes"],
            record["sha256"],
            f"上传输入 {record['path']}",
        )

    prompt_path = ROOT / "derivation/prompts/C/C2_PROMPT.md"
    prompt_bytes = prompt_path.read_bytes()
    prompt = prompt_bytes.decode("utf-8")
    table_paths = tuple(prompt_upload_paths(prompt))
    if table_paths != EXPECTED_UPLOADS:
        raise ValueError(f"提示词上传表与正式清单不一致：{table_paths!r}")
    if "本轮网页端任务必须按下表顺序上传 **11 个文件**" not in prompt:
        raise ValueError("提示词没有冻结 11 文件上传合同")
    for required_identity in (
        "> 模块：`C2`",
        "> 运行编号：`C2-r01`",
        "> 实际运行目录：`derivation/runs/C2`",
        "> 提示词版本：`1.0.0`",
        "> C 模块上下文基线：`C_MODULE_CONTEXT 0.1.0`，阶段 `C1`，状态 `accepted`",
    ):
        if required_identity not in prompt:
            raise ValueError(f"提示词缺少运行身份：{required_identity}")
    for required_content in (
        "钩爪式爬壁机器人",
        "C1PreloadState",
        "CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1",
        "KINEMATIC_MODE_UNSUPPORTED",
        "B_TO_C` 最小扩展要求",
        "50F N·mm",
        "rocking=off/on",
        "C2AcceptedState",
    ):
        if required_content not in prompt:
            raise ValueError(f"提示词缺少 C2 强制内容：{required_content}")
    if prompt.count("$$") % 2:
        raise ValueError("提示词显示数学定界符不闭合")
    if prompt.count("```") % 2:
        raise ValueError("提示词代码围栏不闭合")

    archive_record = manifest["prompt_archive"]
    assert archive_record["matches_uploaded_prompt"] is True
    archive_content = verify_record(
        ROOT / archive_record["path"],
        archive_record["bytes"],
        archive_record["sha256"],
        "PROMPT.md 归档",
    )
    if archive_content != prompt_bytes:
        raise ValueError("PROMPT.md 与正式 C2_PROMPT.md 不是逐字节一致")

    commit = run["repository_commit"]
    subprocess.run(
        ["git", "rev-parse", "--verify", f"{commit}^{{commit}}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for record in records:
        committed = git_blob(commit, record["path"])
        if len(committed) != record["bytes"]:
            raise ValueError(f"冻结提交中的字节数不一致：{record['path']}")
        if sha256_bytes(committed) != record["sha256"]:
            raise ValueError(f"冻结提交中的 SHA-256 不一致：{record['path']}")

    report_content = verify_record(
        ROOT / prerequisite["validation_report"],
        prerequisite["validation_report_bytes"],
        prerequisite["validation_report_sha256"],
        "C1 验证报告",
    ).decode("utf-8")
    if "`pass / accepted`" not in report_content:
        raise ValueError("C1 验证报告未确认 pass / accepted")

    current_context = verify_record(
        ROOT / prerequisite["current_module_context"],
        prerequisite["current_module_context_bytes"],
        prerequisite["current_module_context_sha256"],
        "C1 accepted 当前上下文",
    ).decode("utf-8")
    history_context = verify_record(
        ROOT / prerequisite["history_snapshot"],
        prerequisite["history_snapshot_bytes"],
        prerequisite["history_snapshot_sha256"],
        "C1 历史快照",
    )
    if current_context.encode("utf-8") != history_context:
        raise ValueError("C1 current 与 after_C1 历史快照不一致")
    for marker in (
        "当前完成阶段：`C1",
        "上下文版本：`0.1.0`",
        "当前状态：`accepted`",
        "C1PreloadState",
        "当前 B 不认证真实 rocking",
        "KINEMATIC_MODE_UNSUPPORTED",
    ):
        if marker not in current_context:
            raise ValueError(f"C1 accepted 上下文缺少冻结标记：{marker}")

    public_contract = verify_record(
        ROOT / prerequisite["public_contract"],
        prerequisite["public_contract_bytes"],
        prerequisite["public_contract_sha256"],
        "B_TO_C 正式合同",
    ).decode("utf-8")
    for marker in (
        "| `contract_version` | `1.0.0` |",
        "| `status` | `accepted` |",
        "embedded_array_unit_trial(request)",
        "CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1",
        "当前 B 不认证局部 y 平移",
        "rocking=on",
        "KINEMATIC_MODE_UNSUPPORTED",
    ):
        if marker not in public_contract:
            raise ValueError(f"B_TO_C 合同缺少冻结标记：{marker}")

    for literature_path in EXPECTED_LITERATURE:
        with zipfile.ZipFile(ROOT / literature_path) as archive:
            names = archive.namelist()
            if "evidence_card.md" not in names:
                raise ValueError(f"文献包缺少 evidence_card.md：{literature_path}")
            figures = [name for name in names if name.startswith("figures/") and not name.endswith("/")]
            if len(figures) != 3:
                raise ValueError(f"文献包关键图数量不是 3：{literature_path}:{figures!r}")
            unexpected = [name for name in names if name != "evidence_card.md" and name not in figures]
            if unexpected:
                raise ValueError(f"文献包存在未记录内容：{literature_path}:{unexpected!r}")
            bad_member = archive.testzip()
            if bad_member is not None:
                raise ValueError(f"文献包 CRC 失败：{literature_path}:{bad_member}")

    assert outputs["file_count"] == len(EXPECTED_OUTPUTS)
    if tuple(outputs["files"]) != EXPECTED_OUTPUTS:
        raise ValueError("manifest 的网页输出文件名或顺序错误")
    for index, output in enumerate(EXPECTED_OUTPUTS, start=1):
        if f"### 10.{index} `{output}`" not in prompt:
            raise ValueError(f"提示词缺少固定输出章节：{output}")

    for key in (
        "engineering_context_generator_check",
        "c1_acceptance_validation",
        "upstream_contract_validation",
        "prompt_archive_byte_identical",
        "git_snapshot_hashes_verified",
        "upload_order_verified",
        "literature_zip_crc_verified",
        "output_contract_verified",
        "c2_motion_contract_gap_explicit",
    ):
        if preparation[key] not in (True, "pass"):
            raise ValueError(f"准备校验未通过：{key}={preparation[key]!r}")

    build_output = run_python_check(
        "engineering_fixed_context/internal/build_context.py", "--check"
    )
    c1_input_output = run_python_check("derivation/runs/C1/validate_inputs.py")
    c1_artifact_output = run_python_check("derivation/runs/C1/validate_artifacts.py")

    print("C2-r01 输入准备校验通过")
    print("- C1-r01、C_MODULE_CONTEXT 0.1.0 与 B_TO_C_CONTRACT 1.0.0 已接受且哈希一致")
    print("- 11 个上传文件的路径、顺序、字节数和 SHA-256 一致")
    print("- 冻结 Git 提交中的全部上传输入与 manifest 一致")
    print("- 正式提示词与运行归档副本逐字节一致")
    print("- 文献 17、28 压缩包结构、关键图数量和 CRC 通过")
    print("- C2 所需局部 y/姿态运动与当前 B 合同缺口已显式冻结")
    print("- 网页输出严格为最新完整 C_MODULE_CONTEXT、工程事实候选、运行摘要和引用说明")
    print(f"- {build_output}")
    print(f"- C1 输入复验：{c1_input_output.splitlines()[0]}")
    print(f"- C1 产物复验：{c1_artifact_output.splitlines()[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
