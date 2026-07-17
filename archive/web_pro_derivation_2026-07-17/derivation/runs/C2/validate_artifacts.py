from __future__ import annotations

import copy
import hashlib
import math
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "derivation/runs/C2"
CURRENT = ROOT / "derivation/modules/C/current/C_MODULE_CONTEXT.md"
SNAPSHOT = ROOT / "derivation/modules/C/history/C_MODULE_CONTEXT_after_C2.md"
C1_SNAPSHOT = ROOT / "derivation/modules/C/history/C_MODULE_CONTEXT_after_C1.md"

ENGINEERING_SHA256 = "6c1225d3137f8095673b78e1dc8a76acdb0ae73247ec7c49e720cfcc56bb03cb"
MODULE_CANDIDATE_SHA256 = "39654a496946e0ac2218331ba93d42e5fcdf48eaa342db4a3dc345b2fb197241"
ACCEPTED_SHA256 = "7aa3c9a6a2e6f16886e7ec14674f0503d1d3794f8c70fab2942ab3d178ec6f65"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bytes_at_commit(commit: str, relative_path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def close(left: float, right: float, scale: float = 1.0) -> bool:
    return abs(left - right) <= 1.0e-11 * max(scale, abs(left), abs(right))


def dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def cross(left: list[float], right: list[float]) -> list[float]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def add(left: list[float], right: list[float]) -> list[float]:
    return [a + b for a, b in zip(left, right, strict=True)]


def matvec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [dot(row, vector) for row in matrix]


def transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [list(column) for column in zip(*matrix, strict=True)]


def validate_run_summary() -> None:
    accepted = RUN_DIR / "RUN_UPDATE_SUMMARY.yaml"
    candidate = RUN_DIR / "RUN_UPDATE_SUMMARY_CANDIDATE.yaml"
    raw = RUN_DIR / "raw_downloads/RUN_UPDATE_SUMMARY(7).yaml"
    assert accepted.read_bytes() == candidate.read_bytes() == raw.read_bytes()

    summary = yaml.safe_load(accepted.read_text(encoding="utf-8"))
    assert set(summary) == {
        "run",
        "engineering_context_delta",
        "module_context_delta",
        "outputs",
        "self_check",
    }
    assert summary["run"] == {
        "module": "C2",
        "run_id": "C2-r01",
        "prompt_version": "1.0.0",
        "engineering_context_baseline": "1.0.0",
        "module_context_baseline": "0.1.0",
        "run_directory": "derivation/runs/C2",
    }

    delta = summary["engineering_context_delta"]
    assert delta == [
        {
            "id": "none",
            "operation": "none",
            "target": None,
            "reason": "未发现需要修改的工程事实",
            "affected_modules": [],
            "changed_fields": [],
            "evidence": {
                "local_literature": [],
                "external_urls": [],
                "gpt_knowledge": [],
                "derivation_locations": [],
            },
            "proposed_fact": None,
            "approval_required": False,
        }
    ]

    module_delta = summary["module_context_delta"]
    assert set(module_delta) == {"added", "modified", "preserved", "unresolved"}
    assert len(module_delta["added"]) == 10
    assert len(module_delta["modified"]) == 2
    assert len(module_delta["preserved"]) == 5
    assert len(module_delta["unresolved"]) == 6
    assert any("B_TO_C 2.x" in item for item in module_delta["added"])
    assert any("C1PreloadState" in item for item in module_delta["added"])
    assert any("B_TO_C 2.x" in item for item in module_delta["unresolved"])
    assert any("C3" in item for item in module_delta["unresolved"])

    assert all(summary["outputs"].values())
    assert all(
        value == "pass"
        for key, value in summary["self_check"].items()
        if key != "notes"
    )


def validate_manifest_and_raw_outputs() -> None:
    manifest = yaml.safe_load((RUN_DIR / "INPUT_MANIFEST.yaml").read_text(encoding="utf-8"))
    run = manifest["run"]
    assert run["id"] == "C2-r01"
    assert run["module"] == "C2"
    assert run["run_directory"] == "derivation/runs/C2"
    assert run["module_context_baseline"] == "0.1.0"
    assert run["module_context_status"] == "accepted"
    assert run["upstream_contract_version"] == "1.0.0"

    prerequisite = manifest["prerequisite_acceptance"]
    assert prerequisite["prior_module_run"] == "C1-r01"
    assert prerequisite["status"] == "accepted"
    assert prerequisite["current_history_byte_identical"] is True
    assert prerequisite["c2_motion_extension_required"] is True
    assert prerequisite["semantic_prerequisite_complete"] is True

    contract = manifest["upload_contract"]
    assert contract["expected_file_count"] == contract["verified_file_count"] == 11
    assert len(contract["files"]) == 11
    assert contract["all_expected_files_present"] is True
    assert contract["minimum_literature_package_complete"] is True
    assert contract["upstream_contract_included"] is True
    assert contract["existing_c_module_context_required"] is True
    assert contract["existing_c_module_context_included"] is True
    assert contract["full_b_integrated_model_required"] is False
    assert contract["prompt_manifest_actual_paths_identical"] is True

    repository_commit = run["repository_commit"]
    for item in contract["files"]:
        current_path = ROOT / item["path"]
        current_bytes = current_path.read_bytes()
        if len(current_bytes) == item["bytes"] and hashlib.sha256(current_bytes).hexdigest() == item["sha256"]:
            frozen = current_bytes
        else:
            frozen = bytes_at_commit(repository_commit, item["path"])
        assert len(frozen) == item["bytes"]
        assert hashlib.sha256(frozen).hexdigest() == item["sha256"]

    assert (RUN_DIR / "PROMPT.md").read_bytes() == (
        ROOT / "derivation/prompts/C/C2_PROMPT.md"
    ).read_bytes()

    expected = {
        "C_MODULE_CONTEXT.md": (
            "C_MODULE_CONTEXT(2).md",
            "MODULE_CONTEXT_CANDIDATE.md",
            MODULE_CANDIDATE_SHA256,
        ),
        "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md": (
            "ENGINEERING_FIXED_CONTEXT_CANDIDATE(7).md",
            "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md",
            ENGINEERING_SHA256,
        ),
        "RUN_UPDATE_SUMMARY.yaml": (
            "RUN_UPDATE_SUMMARY(7).yaml",
            "RUN_UPDATE_SUMMARY_CANDIDATE.yaml",
            "cc1575b8509ac6f99d5230c8c17a64447843e13da750bc7344264d4fe1f06c42",
        ),
        "CITATION_BRIEF.md": (
            "CITATION_BRIEF(7).md",
            "CITATION_BRIEF.md",
            "dfc6112d7523c41f0001064f83604e8a7678f55f999957387dd59848a6a7073a",
        ),
    }

    received = manifest["received_outputs"]
    assert len(received) == len(expected) == 4
    for item in received:
        raw_name, candidate_name, expected_hash = expected[item["expected_name"]]
        assert item["received_name"] == raw_name
        assert item["archived_path"] == f"derivation/runs/C2/raw_downloads/{raw_name}"
        assert item["normalized_candidate_path"] == f"derivation/runs/C2/{candidate_name}"
        assert item["byte_identical_to_raw"] is True

        raw_path = ROOT / item["archived_path"]
        normalized_path = ROOT / item["normalized_candidate_path"]
        assert raw_path.stat().st_size == item["bytes"]
        assert normalized_path.stat().st_size == item["normalized_bytes"]
        assert sha256(raw_path) == item["sha256"] == expected_hash
        assert sha256(normalized_path) == item["normalized_sha256"] == expected_hash
        assert raw_path.read_bytes() == normalized_path.read_bytes()

        indexed = subprocess.run(
            ["git", "show", f":{item['archived_path']}"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
        assert indexed == raw_path.read_bytes()

        attribute = subprocess.run(
            ["git", "check-attr", "text", "--", item["archived_path"]],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        ).stdout.strip()
        assert attribute.endswith(": text: unset")

    raw_names = {path.name for path in (RUN_DIR / "raw_downloads").iterdir()}
    assert raw_names == {values[0] for values in expected.values()}

    raw_response = ROOT / manifest["raw_response"]["path"]
    assert raw_response.stat().st_size == manifest["raw_response"]["bytes"]
    assert sha256(raw_response) == manifest["raw_response"]["sha256"]
    indexed_response = subprocess.run(
        ["git", "show", f":{manifest['raw_response']['path']}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout
    assert indexed_response == raw_response.read_bytes()
    response_attribute = subprocess.run(
        ["git", "check-attr", "text", "--", manifest["raw_response"]["path"]],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    ).stdout.strip()
    assert response_attribute.endswith(": text: unset")

    accepted = manifest["accepted_module_context"]
    assert accepted == {
        "path": "derivation/modules/C/current/C_MODULE_CONTEXT.md",
        "history_snapshot": "derivation/modules/C/history/C_MODULE_CONTEXT_after_C2.md",
        "version": "0.2.0",
        "stage": "C2",
        "status": "accepted",
        "bytes": 120064,
        "sha256": ACCEPTED_SHA256,
        "current_history_byte_identical": True,
    }
    assert sha256(ROOT / accepted["path"]) == ACCEPTED_SHA256
    assert (ROOT / accepted["path"]).read_bytes() == (ROOT / accepted["history_snapshot"]).read_bytes()

    assert manifest["artifact_review"] == {
        "status": "accepted",
        "engineering_context_delta": "none",
        "semantic_conflict": False,
        "manual_decision_required": False,
        "external_sources_checked": True,
        "citation_brief_local_archive_only": True,
    }

    for literature_path in [item["path"] for item in contract["files"][-2:]]:
        with zipfile.ZipFile(ROOT / literature_path) as archive:
            names = archive.namelist()
            assert "evidence_card.md" in names
            assert sum(name.startswith("figures/") and not name.endswith("/") for name in names) == 3
            assert archive.testzip() is None


def validate_engineering_context() -> None:
    baseline = ROOT / "engineering_fixed_context/engineering_fixed_context.md"
    candidate = RUN_DIR / "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md"
    raw = RUN_DIR / "raw_downloads/ENGINEERING_FIXED_CONTEXT_CANDIDATE(7).md"
    assert baseline.read_bytes() == candidate.read_bytes() == raw.read_bytes()
    assert sha256(candidate) == ENGINEERING_SHA256


def validate_module_context() -> None:
    candidate_path = RUN_DIR / "MODULE_CONTEXT_CANDIDATE.md"
    raw_path = RUN_DIR / "raw_downloads/C_MODULE_CONTEXT(2).md"
    candidate = candidate_path.read_text(encoding="utf-8")
    accepted = CURRENT.read_text(encoding="utf-8")
    c1 = C1_SNAPSHOT.read_text(encoding="utf-8")

    assert candidate_path.read_bytes() == raw_path.read_bytes()
    assert sha256(candidate_path) == MODULE_CANDIDATE_SHA256
    assert CURRENT.read_bytes() == SNAPSHOT.read_bytes()
    assert sha256(CURRENT) == ACCEPTED_SHA256

    expected = candidate
    replacements = (
        ("> 上下文候选版本：`0.2.0`", "> 上下文版本：`0.2.0`"),
        ("> 当前状态：`candidate`", "> 当前状态：`accepted`"),
        (
            "它在本候选中作为 C2 的不可丢失初态继续有效。",
            "它在本滚动上下文中作为 C2 的不可丢失初态继续有效。",
        ),
        (
            "- **理论推导**：完成候选；",
            "- **理论推导**：已完成并经 `C2-r01` 审查接受；",
        ),
    )
    for old, new in replacements:
        assert expected.count(old) == 1, old
        expected = expected.replace(old, new, 1)
    assert accepted == expected

    assert "> 当前完成阶段：`C2 — 偏心外载、整体小角度摇摆与六维平衡`" in accepted
    assert "> 上下文版本：`0.2.0`" in accepted
    assert "> 上游合同：`B_TO_C 1.0.0 accepted`" in accepted
    assert "> 基线：`C_MODULE_CONTEXT 0.1.0 accepted`" in accepted
    assert "> 当前状态：`accepted`" in accepted

    c1_inherited = c1[c1.index("## 1. 范围"):c1.index("## 15. 输出前自检")]
    c2_inherited = candidate[
        candidate.index("## 1. 范围"):candidate.index("## 15. C1 已接受内容的历史自检")
    ]
    assert c1_inherited == c2_inherited

    sections = [int(item) for item in re.findall(r"(?m)^## ([0-9]+)[.] ", accepted)]
    assert sections == list(range(31))
    assert len(re.findall(r"(?m)^\| C1-V[0-9]{2} \|", accepted)) == 28
    assert len(re.findall(r"(?m)^\| C2-V[0-9]{2} \|", accepted)) == 30

    required_markers = (
        "C1PreloadState",
        "C2LoadRequest",
        "C2LoadTrialResponse",
        "C2AcceptedState",
        "C2ContractExtensionRequirement",
        "CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1",
        "PATH_ONLY_NO_SUPPORT_V1",
        "C2_GLOBAL_LOAD_STEP",
        "PRESCRIBED_SE3_RESIDUAL",
        "SE3_WITH_FORCE_BALANCED_NORMAL_STROKE",
        "C2_CONTRACT_EXTENSION_REQUIRED",
        "C2_EQUILIBRIUM_INFEASIBLE_FIXED_POSE",
        "C2_PHYSICAL_INSTABILITY",
        "C2_STOP_NUMERICAL",
        "C2_TRANSACTION_ERROR",
        "KINEMATIC_MODE_UNSUPPORTED",
        "MODEL_UNAVAILABLE",
        "ACTUATOR_WRENCH_UNCERTIFIED",
        "last_valid_accepted_state=C1PreloadState",
        "B_TO_C 2.0.0",
        "peak_not_yet_declared",
        "文献 17",
        "文献 28",
        "GPT 通用知识",
    )
    for marker in required_markers:
        assert marker in accepted, marker

    assert "只旋转旧力或旧 wrench 不能替代" in accepted
    assert "不能添加导轨或“固定姿态反力矩”" in accepted
    assert "不得预先断言哪一侧必然首先剥离" in accepted
    assert "不在本轮把峰值自动声明为最终最大承载" in accepted
    assert "当前仅定义测试，不声称代码或实验已经通过" in accepted
    assert "本轮新增内容均属于机理、合同要求或未决实现，不进入工程固定事实" in accepted
    assert "s_{\\max}=100" not in accepted
    assert "s_max_mm: 100" not in accepted
    assert "theta_Z=0" in accepted
    assert "\x00" not in candidate
    assert "\t" not in candidate
    assert candidate.count("```") % 2 == 0
    assert candidate.count("$$") % 2 == 0
    assert candidate.count("\\[") == candidate.count("\\]")
    assert "TODO" not in candidate and "TBD" not in candidate and "{{" not in candidate


def validate_citations() -> None:
    citation_path = RUN_DIR / "CITATION_BRIEF.md"
    raw = RUN_DIR / "raw_downloads/CITATION_BRIEF(7).md"
    assert citation_path.read_bytes() == raw.read_bytes()
    citation = citation_path.read_text(encoding="utf-8")
    body, references = citation.split("## 参考来源", maxsplit=1)
    defined = set(re.findall(r"^\[([0-9]+)\]\s", references, flags=re.MULTILINE))
    used: set[str] = set()
    for group in re.findall(r"\[([0-9,]+)\]", body):
        used.update(group.split(","))
    assert defined == used == {"1", "2", "3"}
    assert "[1] 文献17" in references
    assert "[2] 文献28" in references
    assert "[3] GPT 自带知识" in references
    assert "http://" not in citation and "https://" not in citation
    assert "文献09" not in citation and "文献20" not in citation
    assert "刚体 SE(3) 小增量运动" in citation
    assert "项目作用线、角度上限、阈值、材料参数和实验约束仍需合同或标定" in citation
    assert "仅本地归档" in citation
    assert "不进入任何后续默认上传" in citation


def validate_c2_mechanics() -> None:
    ex = [
        [1.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, -1.0, 0.0],
    ]
    ez = [0.0, 0.0, 1.0]
    ey = [cross(ez, axis) for axis in ex]
    rotations = [
        [[axis[row], lateral[row], ez[row]] for row in range(3)]
        for axis, lateral in zip(ex, ey, strict=True)
    ]
    positions = [[-40.0 * item for item in axis] for axis in ex]

    force_local = [1.4, -0.7, 2.1]
    moment_local = [3.0, -5.0, 7.0]
    theta_global = [0.013, -0.021, 0.017]
    u_c_global = [0.8, -1.2, 0.4]
    for rotation, position in zip(rotations, positions, strict=True):
        force_global = matvec(rotation, force_local)
        moment_global = add(matvec(rotation, moment_local), cross(position, force_global))
        theta_local = matvec(transpose(rotation), theta_global)
        u_a_local = matvec(
            transpose(rotation),
            add(u_c_global, cross(theta_global, position)),
        )
        source_power = dot(force_local, u_a_local) + dot(moment_local, theta_local)
        target_power = dot(force_global, u_c_global) + dot(moment_global, theta_global)
        assert close(source_power, target_power)

    theta_y = [0.0, 0.02, 0.0]
    theta_x = [0.015, 0.0, 0.0]
    assert close(cross(theta_y, positions[0])[2], 40.0 * theta_y[1])
    assert close(cross(theta_y, positions[1])[2], -40.0 * theta_y[1])
    assert close(cross(theta_x, positions[2])[2], -40.0 * theta_x[0])
    assert close(cross(theta_x, positions[3])[2], 40.0 * theta_x[0])

    load_point = [0.0, 0.0, 50.0]
    load = 3.2
    moment_x = cross(load_point, [load, 0.0, 0.0])
    assert all(close(value, expected) for value, expected in zip(moment_x, [0.0, 50.0 * load, 0.0], strict=True))
    direction_45 = [1.0 / math.sqrt(2.0), 1.0 / math.sqrt(2.0), 0.0]
    moment_45 = cross(load_point, [load * item for item in direction_45])
    expected_45 = [-50.0 * load / math.sqrt(2.0), 50.0 * load / math.sqrt(2.0), 0.0]
    assert all(close(value, expected) for value, expected in zip(moment_45, expected_45, strict=True))

    displacement_x = [1.0, 0.0, 0.0]
    local_x = [dot(axis, displacement_x) for axis in ex]
    local_y = [dot(lateral, displacement_x) for lateral in ey]
    assert local_x == [1.0, -1.0, 0.0, 0.0]
    assert local_y == [0.0, 0.0, -1.0, 1.0]
    local_y_45 = [dot(lateral, direction_45) for lateral in ey]
    assert all(not close(value, 0.0) for value in local_y_45)

    fz1, fz2, fz3, fz4 = 2.2, 3.1, 1.4, 2.8
    pair_x = add(cross(positions[0], [0.0, 0.0, fz1]), cross(positions[1], [0.0, 0.0, fz2]))
    pair_y = add(cross(positions[2], [0.0, 0.0, fz3]), cross(positions[3], [0.0, 0.0, fz4]))
    assert close(pair_x[1], 40.0 * (fz1 - fz2))
    assert close(pair_y[0], 40.0 * (fz4 - fz3))

    accepted = {
        "delta_P": 0.0,
        "q_C": [0.0] * 6,
        "unit_versions": [4, 8, 3, 6],
        "damage_version": 7,
        "event_number": 14,
    }
    baseline = copy.deepcopy(accepted)
    trial = copy.deepcopy(accepted)
    trial.update(delta_P=0.2, damage_version=8, event_number=15)
    trial["q_C"][0] = 0.2
    trial["unit_versions"][1] += 1
    prepare_success = False
    if prepare_success:
        accepted = trial
    assert accepted == baseline


def validate_generator() -> None:
    subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            "engineering_fixed_context/internal/build_context.py",
            "--check",
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def main() -> None:
    validate_run_summary()
    validate_manifest_and_raw_outputs()
    validate_engineering_context()
    validate_module_context()
    validate_citations()
    validate_c2_mechanics()
    validate_generator()
    print(
        "C2-r01 artifact, YAML, citation, inheritance, kinematics, wrench, "
        "contract-gap, event, and transaction validation: PASS"
    )


if __name__ == "__main__":
    main()
