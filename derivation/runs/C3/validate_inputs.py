from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "derivation/runs/C3"
MANIFEST_PATH = RUN_DIR / "INPUT_MANIFEST.yaml"

EXPECTED_UPLOADS = [
    "engineering_fixed_context/engineering_fixed_context.md",
    "docs/extract/MECHANISM_MODULE_PLAN.md",
    "derivation/prompts/C/C3_PROMPT.md",
    "docs/derivation_workflow/templates/MODULE_CONTEXT_TEMPLATE.md",
    "docs/derivation_workflow/templates/ENGINEERING_FIXED_CONTEXT_CANDIDATE_TEMPLATE.md",
    "docs/derivation_workflow/templates/RUN_UPDATE_SUMMARY_TEMPLATE.yaml",
    "docs/derivation_workflow/templates/CITATION_BRIEF_TEMPLATE.md",
    "derivation/contracts/B_TO_C_CONTRACT.md",
    "derivation/modules/C/current/C_MODULE_CONTEXT.md",
    "docs/extract/机理提取/23_dual_rail_spiny_climbing_robot/23_dual_rail_spiny_climbing_robot.zip",
    "docs/extract/机理提取/28_loris_lightweight_free_climbing_robot/28_loris_lightweight_free_climbing_robot.zip",
]

EXPECTED_OUTPUTS = [
    "C_MODULE_CONTEXT.md",
    "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md",
    "RUN_UPDATE_SUMMARY.yaml",
    "CITATION_BRIEF.md",
]

ZIP_CONTENTS = {
    EXPECTED_UPLOADS[9]: [
        "evidence_card.md",
        "figures/fig07_p05_dual_rail_geometry.png",
        "figures/fig10_p08_track_load_distribution.png",
        "figures/fig13_p10_force_redistribution_validation.png",
    ],
    EXPECTED_UPLOADS[10]: [
        "evidence_card.md",
        "figures/fig02_p02_splayed_gripper_loading.png",
        "figures/fig03_p03_passive_wrist_pivot.png",
        "figures/fig05_p05_dig_force_margin.png",
    ],
}


def fail(message: str) -> None:
    raise SystemExit(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_manifest() -> dict:
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail("INPUT_MANIFEST.yaml 顶层必须是映射")
    return data


def git_blob(commit: str, relative_path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        fail(
            f"冻结提交缺少输入 {relative_path}: "
            f"{result.stderr.decode('utf-8', errors='replace').strip()}"
        )
    return result.stdout


def check_run_identity(manifest: dict) -> None:
    run = manifest["run"]
    expected = {
        "id": "C3-r01",
        "module": "C3",
        "run_directory": "derivation/runs/C3",
        "prompt_version": "1.0.0",
        "workflow_version": "1.3.4",
        "engineering_context_version": "1.0.0",
        "module_context_baseline": "0.2.0",
        "module_context_status": "accepted",
        "upstream_contract_version": "1.0.0",
        "upstream_contract_status": "accepted",
    }
    for key, value in expected.items():
        if run.get(key) != value:
            fail(f"运行身份不一致：{key}={run.get(key)!r}，期望 {value!r}")

    manifests = sorted((ROOT / "derivation/runs").glob("**/INPUT_MANIFEST.yaml"))
    c3_ids: list[tuple[str, str]] = []
    for path in manifests:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        run_data = data.get("run", {}) if isinstance(data, dict) else {}
        run_id = run_data.get("id") or run_data.get("run_id")
        if isinstance(run_id, str) and run_id.startswith("C3-r"):
            c3_ids.append((run_id, path.relative_to(ROOT).as_posix()))
    if c3_ids != [("C3-r01", "derivation/runs/C3/INPUT_MANIFEST.yaml")]:
        fail(f"C3 运行编号或目录不唯一：{c3_ids}")


def check_files_and_git_snapshot(manifest: dict) -> None:
    upload = manifest["upload_contract"]
    rows = upload["files"]
    paths = [row["path"] for row in rows]
    if paths != EXPECTED_UPLOADS:
        fail(f"manifest 上传顺序不一致：{paths}")
    if upload.get("expected_file_count") != 11 or upload.get("verified_file_count") != 11:
        fail("manifest 上传数量不是 11")

    commit = manifest["run"]["repository_commit"]
    head = subprocess.run(
        ["git", "rev-parse", commit],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if head.returncode != 0 or head.stdout.strip() != commit:
        fail(f"repository_commit 无法解析为完整提交：{commit}")

    for row in rows:
        relative = row["path"]
        path = ROOT / relative
        if not path.is_file():
            fail(f"缺少上传文件：{relative}")
        frozen = git_blob(commit, relative)
        if len(frozen) != row["bytes"]:
            fail(f"冻结提交中的字节数不一致：{relative}")
        if sha256_bytes(frozen) != row["sha256"]:
            fail(f"冻结提交中的 SHA-256 不一致：{relative}")


def check_prompt_and_archive(manifest: dict) -> None:
    prompt_path = ROOT / EXPECTED_UPLOADS[2]
    archive_path = RUN_DIR / "PROMPT.md"
    prompt = prompt_path.read_bytes()
    archive = archive_path.read_bytes()
    if prompt != archive:
        fail("正式提示词与运行归档 PROMPT.md 不逐字节一致")

    archive_row = manifest["prompt_archive"]
    if archive_row["path"] != "derivation/runs/C3/PROMPT.md":
        fail("prompt_archive.path 不正确")
    if archive_row["bytes"] != len(archive):
        fail("PROMPT.md 字节数与 manifest 不一致")
    if archive_row["sha256"] != sha256_bytes(archive):
        fail("PROMPT.md SHA-256 与 manifest 不一致")

    text = prompt.decode("utf-8")
    table_paths = re.findall(r"^\|\s*\d+\s*\|\s*`([^`]+)`\s*\|", text, re.MULTILINE)
    if table_paths != EXPECTED_UPLOADS:
        fail(f"提示词上传表与实际清单不一致：{table_paths}")

    required_tokens = [
        "C3-r01",
        "C_MODULE_CONTEXT 0.2.0",
        "上下文候选版本 `0.3.0`",
        "C3_CONTRACT_EXTENSION_REQUIRED",
        "FIRST_NEEDLE_FAILURE",
        "FIRST_UNIT_SIGNIFICANT_DEGRADATION",
        "GLOBAL_REACTION_PEAK_CANDIDATE",
        "GLOBAL_CRITICAL_CAPACITY_CONFIRMED",
        "F_{\\mathrm{crit}}",
        "C3MaximumCapacityResult",
        "不要输出额外第五份总结",
        "不执行大模块 C 集成",
    ]
    missing = [token for token in required_tokens if token not in text]
    if missing:
        fail(f"提示词缺少 C3 强制内容：{missing}")


def check_prerequisites(manifest: dict) -> None:
    prereq = manifest["prerequisite_acceptance"]
    report = ROOT / prereq["validation_report"]
    report_data = report.read_bytes()
    if len(report_data) != prereq["validation_report_bytes"]:
        fail("C2 验证报告字节数不一致")
    if sha256_bytes(report_data) != prereq["validation_report_sha256"]:
        fail("C2 验证报告 SHA-256 不一致")
    report_text = report_data.decode("utf-8")
    if "pass / accepted" not in report_text or "没有工程事实变化" not in report_text:
        fail("C2 验证报告未冻结为 pass / accepted 或存在未处理工程事实变化")

    repository_commit = manifest["run"]["repository_commit"]
    current = ROOT / prereq["current_module_context"]
    history = ROOT / prereq["history_snapshot"]
    if not current.is_file():
        fail("当前 C_MODULE_CONTEXT 文件不存在")
    current_data = git_blob(repository_commit, prereq["current_module_context"])
    history_data = history.read_bytes()
    if current_data != history_data:
        fail("C2 current 与 history 快照不逐字节一致")
    if len(current_data) != prereq["current_module_context_bytes"]:
        fail("当前 C_MODULE_CONTEXT 字节数不一致")
    if sha256_bytes(current_data) != prereq["current_module_context_sha256"]:
        fail("当前 C_MODULE_CONTEXT SHA-256 不一致")
    current_text = current_data.decode("utf-8")
    for token in (
        "当前完成阶段：`C2",
        "上下文版本：`0.2.0`",
        "当前状态：`accepted`",
        "C2_CONTRACT_EXTENSION_REQUIRED",
        "C3 必须从当前 `C2AcceptedState` 继续",
    ):
        if token not in current_text:
            fail(f"当前 C_MODULE_CONTEXT 缺少前置标识：{token}")

    contract = ROOT / prereq["public_contract"]
    contract_data = contract.read_bytes()
    if len(contract_data) != prereq["public_contract_bytes"]:
        fail("B_TO_C_CONTRACT 字节数不一致")
    if sha256_bytes(contract_data) != prereq["public_contract_sha256"]:
        fail("B_TO_C_CONTRACT SHA-256 不一致")
    contract_text = contract_data.decode("utf-8")
    for token in (
        "`contract_version` | `1.0.0`",
        "`status` | `accepted`",
        "KINEMATIC_MODE_UNSUPPORTED",
        "CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1",
        "full_unit_resolve_callback_requirement",
    ):
        if token not in contract_text:
            fail(f"B_TO_C_CONTRACT 缺少前置标识：{token}")


def check_literature_archives() -> None:
    for relative, expected_names in ZIP_CONTENTS.items():
        path = ROOT / relative
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad is not None:
                fail(f"文献包 CRC 失败：{relative}:{bad}")
            names = archive.namelist()
            if names != expected_names:
                fail(f"文献包内容不一致：{relative}:{names}")
            card = archive.read("evidence_card.md").decode("utf-8")
        if relative == EXPECTED_UPLOADS[9]:
            required = ("A Spiny Climbing Robot with Dual-Rail Mechanism", "七足到六足", "等刚度换载模型")
        else:
            required = ("LORIS: A Lightweight Free-Climbing Robot", "最大化最小附着裕度", "当前接触集合固定")
        for token in required:
            if token not in card:
                fail(f"文献包证据卡缺少预期内容：{relative}:{token}")


def check_outputs_and_generator(manifest: dict) -> None:
    expected = manifest["expected_outputs"]
    if expected.get("file_count") != 4 or expected.get("files") != EXPECTED_OUTPUTS:
        fail("网页端四个输出文件名不一致")

    result = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(ROOT / "engineering_fixed_context/internal/build_context.py"),
            "--check",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        fail(f"工程事实生成器校验失败：\n{result.stdout}")
    if "校验通过：9 个领域，48 条事实" not in result.stdout:
        fail(f"工程事实生成器输出异常：\n{result.stdout}")


def main() -> int:
    manifest = read_manifest()
    check_run_identity(manifest)
    check_files_and_git_snapshot(manifest)
    check_prompt_and_archive(manifest)
    check_prerequisites(manifest)
    check_literature_archives()
    check_outputs_and_generator(manifest)
    print("C3-r01 输入准备校验通过")
    print("- C2-r01、C_MODULE_CONTEXT 0.2.0 与 B_TO_C_CONTRACT 1.0.0 已接受且哈希一致")
    print("- 11 个上传文件的路径、顺序、字节数和 SHA-256 一致")
    print("- 冻结 Git 提交中的全部上传输入与 manifest 一致")
    print("- 正式提示词与运行归档副本逐字节一致")
    print("- 文献 23、28 压缩包结构、证据卡、关键图数量和 CRC 通过")
    print("- C3 对当前 B 合同缺口、渐进重平衡、稳定峰值和峰后终止的边界已显式冻结")
    print("- 网页输出严格为最新完整 C_MODULE_CONTEXT、工程事实候选、运行摘要和引用说明")
    print("- 工程事实生成器校验通过：9 个领域，48 条事实")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
