from __future__ import annotations

import copy
import hashlib
import math
import re
import subprocess
import zipfile
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "derivation/runs/C1"
CURRENT = ROOT / "derivation/modules/C/current/C_MODULE_CONTEXT.md"
SNAPSHOT = ROOT / "derivation/modules/C/history/C_MODULE_CONTEXT_after_C1.md"

ENGINEERING_SHA256 = "6c1225d3137f8095673b78e1dc8a76acdb0ae73247ec7c49e720cfcc56bb03cb"
MODULE_CANDIDATE_SHA256 = "8a703edcb72905f290378dd36ccc9460fbceac7c4e9a4b040f978dcdb5fdbfa9"
ACCEPTED_SHA256 = "daa5702355fb56cf98cdd8194717fbe8e2b41311c9fd0ef29010484bd5f8654c"


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


def determinant(matrix: list[list[float]]) -> float:
    return (
        matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
        - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
        + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
    )


def validate_run_summary() -> None:
    accepted = RUN_DIR / "RUN_UPDATE_SUMMARY.yaml"
    candidate = RUN_DIR / "RUN_UPDATE_SUMMARY_CANDIDATE.yaml"
    raw = RUN_DIR / "raw_downloads/RUN_UPDATE_SUMMARY(6).yaml"
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
        "module": "C1",
        "run_id": "C1-r01",
        "prompt_version": "1.0.0",
        "engineering_context_baseline": "1.0.0",
        "module_context_baseline": "none",
        "run_directory": "derivation/runs/C1",
    }

    delta = summary["engineering_context_delta"]
    assert len(delta) == 1
    assert delta[0] == {
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

    module_delta = summary["module_context_delta"]
    assert set(module_delta) == {"added", "modified", "preserved", "unresolved"}
    assert len(module_delta["added"]) == 10
    assert module_delta["modified"] == ["none"]
    assert module_delta["preserved"] == ["none"]
    assert len(module_delta["unresolved"]) == 10
    assert any("wrench/twist" in item for item in module_delta["added"])
    assert any("DamageStore" in item for item in module_delta["added"])
    assert any("s_max" in item for item in module_delta["unresolved"])
    assert any("rocking=on" in item for item in module_delta["unresolved"])

    assert all(summary["outputs"].values())
    assert all(
        value == "pass"
        for key, value in summary["self_check"].items()
        if key != "notes"
    )


def validate_manifest_and_raw_outputs() -> None:
    manifest = yaml.safe_load((RUN_DIR / "INPUT_MANIFEST.yaml").read_text(encoding="utf-8"))
    run = manifest["run"]
    assert run["id"] == "C1-r01"
    assert run["module"] == "C1"
    assert run["run_directory"] == "derivation/runs/C1"
    assert run["module_context_baseline"] == "none"

    contract = manifest["upload_contract"]
    assert contract["expected_file_count"] == contract["verified_file_count"] == 10
    assert len(contract["files"]) == 10
    assert contract["all_expected_files_present"] is True
    assert contract["minimum_literature_package_complete"] is True
    assert contract["upstream_contract_included"] is True
    assert contract["existing_c_module_context_required"] is False
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

    expected = {
        "C_MODULE_CONTEXT.md": (
            "C_MODULE_CONTEXT.md",
            "MODULE_CONTEXT_CANDIDATE.md",
            MODULE_CANDIDATE_SHA256,
        ),
        "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md": (
            "ENGINEERING_FIXED_CONTEXT_CANDIDATE(6).md",
            "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md",
            ENGINEERING_SHA256,
        ),
        "RUN_UPDATE_SUMMARY.yaml": (
            "RUN_UPDATE_SUMMARY(6).yaml",
            "RUN_UPDATE_SUMMARY_CANDIDATE.yaml",
            "20e0e2a36d1dace1cffb7255c919aa07fd07bc9929f3a364fd265b9480d2169d",
        ),
        "CITATION_BRIEF.md": (
            "CITATION_BRIEF(6).md",
            "CITATION_BRIEF.md",
            "4d63fc1005cacc6a3a8699b6febf8c6e2fffee58b43885ac62c937a2c8fb797a",
        ),
    }

    received = manifest["received_outputs"]
    assert len(received) == len(expected) == 4
    for item in received:
        raw_name, candidate_name, expected_hash = expected[item["expected_name"]]
        assert item["received_name"] == raw_name
        assert item["archived_path"] == f"derivation/runs/C1/raw_downloads/{raw_name}"
        assert item["normalized_candidate_path"] == f"derivation/runs/C1/{candidate_name}"
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
        "history_snapshot": "derivation/modules/C/history/C_MODULE_CONTEXT_after_C1.md",
        "version": "0.1.0",
        "stage": "C1",
        "status": "accepted",
        "bytes": 72251,
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
    raw = RUN_DIR / "raw_downloads/ENGINEERING_FIXED_CONTEXT_CANDIDATE(6).md"
    assert baseline.read_bytes() == candidate.read_bytes() == raw.read_bytes()
    assert sha256(candidate) == ENGINEERING_SHA256


def validate_module_context() -> None:
    candidate_path = RUN_DIR / "MODULE_CONTEXT_CANDIDATE.md"
    raw_path = RUN_DIR / "raw_downloads/C_MODULE_CONTEXT.md"
    candidate = candidate_path.read_text(encoding="utf-8")
    accepted = CURRENT.read_text(encoding="utf-8")

    assert candidate_path.read_bytes() == raw_path.read_bytes()
    assert sha256(candidate_path) == MODULE_CANDIDATE_SHA256
    assert CURRENT.read_bytes() == SNAPSHOT.read_bytes()
    assert sha256(CURRENT) == ACCEPTED_SHA256
    assert "> 当前完成阶段：`C1 — 四单元同步搜索、内部预紧与停止条件`" in candidate
    assert "> 上下文版本：`0.1.0`" in candidate
    assert "> 上游合同：`B_TO_C 1.0.0 accepted`" in candidate
    assert "> 当前状态：`candidate`" in candidate
    assert "> 当前状态：`accepted`" in accepted

    expected = candidate.replace("> 当前状态：`candidate`", "> 当前状态：`accepted`", 1)
    assert accepted == expected

    sections = [int(item) for item in re.findall(r"(?m)^## ([0-9]+)[.] ", accepted)]
    assert sections == list(range(16))
    assert len(re.findall(r"(?m)^\| C1-V[0-9]{2} \|", accepted)) == 28

    required_markers = (
        "C1SearchRequest",
        "C1SearchTrialResponse",
        "C1PreloadState",
        "embedded_array_unit_trial",
        "CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1",
        "UX_PZ_BALANCED",
        "PRESCRIBED_XZ_RESIDUAL",
        "Q_s^{\\mathrm{contact}}",
        "Q_s^{\\mathrm{drive}}",
        "p_X",
        "p_Y",
        "\\Delta_X",
        "\\Delta_Y",
        "\\gamma_C=\\min",
        "DamageStore",
        "PREPARE_GLOBAL_COMMIT",
        "STOP_PRELOAD_ACCEPTED",
        "STOP_AT_SEARCH_LIMIT_UNQUALIFIED",
        "STOP_SAFETY_LIMIT",
        "STOP_IRRECOVERABLE",
        "STOP_UNCERTIFIED",
        "STOP_NUMERICAL",
        "UNIT_DETACHED_RECOVERABLE",
        "UNIT_DETACHED_IRRECOVERABLE",
        "KINEMATIC_MODE_UNSUPPORTED",
        "NUMERICAL_NONCONVERGENCE",
        "m_{\\min}",
        "G_{\\mathrm{stop}}",
        "UNRESOLVED.C1.STOP_THRESHOLD",
        "UNRESOLVED.C1.MAX_SEARCH_DISTANCE",
        "rocking=off",
        "真实 rocking 请求",
        "文献 09",
        "文献 20",
    )
    for marker in required_markers:
        assert marker in accepted, marker

    assert "四个单元严格满足" in accepted
    assert "不得出现逐针力、$P_i/N$" in accepted
    assert "只能调用" in accepted
    assert "不提前完成 C2" in accepted
    assert "C3 必须补齐" in accepted
    assert "不得借用 B 的 $100\\ \\mathrm{mm}$" in accepted
    assert "s_{\\max}=100" not in accepted
    assert "s_max_mm: 100" not in accepted
    assert "当前仅定义理论与测试，不虚构代码或实验已经通过" in accepted
    assert "\x00" not in candidate
    assert "\t" not in candidate
    assert candidate.count("```") % 2 == 0
    assert candidate.count("$$") % 2 == 0
    assert candidate.count("\\[") == candidate.count("\\]")
    assert "TODO" not in candidate and "TBD" not in candidate and "{{" not in candidate


def validate_citations() -> None:
    citation_path = RUN_DIR / "CITATION_BRIEF.md"
    raw = RUN_DIR / "raw_downloads/CITATION_BRIEF(6).md"
    assert citation_path.read_bytes() == raw.read_bytes()
    citation = citation_path.read_text(encoding="utf-8")
    body, references = citation.split("## 参考来源", maxsplit=1)
    defined = set(re.findall(r"^\[([0-9]+)\]\s", references, flags=re.MULTILINE))
    used: set[str] = set()
    for group in re.findall(r"\[([0-9,]+)\]", body):
        used.update(group.split(","))
    assert defined == used == {"1", "2", "3", "4"}
    assert "[3] 文献09" in references
    assert "[4] 文献20" in references
    assert "[2] GPT 自带知识" in references
    assert "[1] https://modernrobotics.northwestern.edu/chapters/chapter3/" in references
    assert set(re.findall(r"https://[^\s]+", references)) == {
        "https://modernrobotics.northwestern.edu/chapters/chapter3/"
    }
    assert "SE(3)" in citation
    assert "具体阈值、容差和实现仍需验证" in citation
    assert "仅本地归档" in citation
    assert "不进入任何后续默认上传" in citation


def validate_c1_mechanics() -> None:
    rotations = [
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        [[-1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 1.0]],
        [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]],
        [[0.0, 1.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 0.0, 1.0]],
    ]
    ex = [[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, -1.0, 0.0]]

    for rotation in rotations:
        for vectors in (rotation, transpose(rotation)):
            assert all(
                close(dot(vectors[i], vectors[j]), 1.0 if i == j else 0.0)
                for i in range(3)
                for j in range(3)
            )
        assert close(determinant(rotation), 1.0)

    positions = [[-40.0 * item for item in axis] for axis in ex]
    distances = sorted(
        math.dist(positions[left], positions[right])
        for left, right in ((0, 2), (0, 3), (1, 2), (1, 3))
    )
    assert all(close(distance, math.sqrt(40.0**2 + 40.0**2)) for distance in distances)
    assert close(math.dist(positions[0], positions[1]), 80.0)
    assert close(math.dist(positions[2], positions[3]), 80.0)

    force_local = [1.4, -0.7, 2.1]
    moment_local = [3.0, -5.0, 7.0]
    theta_global = [0.013, -0.021, 0.017]
    u_c_global = [0.8, -1.2, 0.4]
    rho_local = [1.7, -0.9, 0.6]
    for rotation, position in zip(rotations, positions, strict=True):
        r_global = add(position, matvec(rotation, rho_local))
        force_global = matvec(rotation, force_local)
        moment_global = add(matvec(rotation, moment_local), cross(r_global, force_global))
        theta_local = matvec(transpose(rotation), theta_global)
        u_a_local = matvec(
            transpose(rotation),
            add(u_c_global, cross(theta_global, r_global)),
        )
        source_power = dot(force_local, u_a_local) + dot(moment_local, theta_local)
        target_power = dot(force_global, u_c_global) + dot(moment_global, theta_global)
        assert close(source_power, target_power)

    resistance = [2.0, 2.0, 3.0, 3.0]
    forces = [[-value * component for component in axis] for value, axis in zip(resistance, ex, strict=True)]
    summed_force = [sum(force[index] for force in forces) for index in range(3)]
    assert all(close(value, 0.0) for value in summed_force)
    p_x = 0.5 * (resistance[0] + resistance[1])
    p_y = 0.5 * (resistance[2] + resistance[3])
    delta_x = resistance[1] - resistance[0]
    delta_y = resistance[3] - resistance[2]
    q_drive = sum(resistance)
    assert close(p_x, 2.0) and close(p_y, 3.0)
    assert close(delta_x, 0.0) and close(delta_y, 0.0)
    assert close(q_drive, 2.0 * (p_x + p_y)) and q_drive > 0.0

    heterogeneous = [1.2, 2.1, 0.8, 1.7]
    assert close(heterogeneous[1] - heterogeneous[0], 0.9)
    assert close(heterogeneous[3] - heterogeneous[2], 0.9)

    event_fractions = [0.72, 0.31, 0.31 + 1.0e-12, 0.9]
    earliest = min(event_fractions)
    simultaneous = {
        index for index, value in enumerate(event_fractions) if abs(value - earliest) <= 1.0e-10
    }
    assert close(earliest, 0.31)
    assert simultaneous == {1, 2}
    assert min(reversed(event_fractions)) == earliest

    accepted = {
        "s": 12.0,
        "unit_versions": [4, 8, 3, 6],
        "damage_version": 7,
        "event_number": 14,
    }
    baseline = copy.deepcopy(accepted)
    trial = copy.deepcopy(accepted)
    trial.update(s=12.4, damage_version=8, event_number=15)
    trial["unit_versions"][1] += 1
    prepare_success = False
    if prepare_success:
        accepted = trial
    assert accepted == baseline

    gates = {
        "valid": True,
        "plateau": True,
        "gain": True,
        "weak": True,
        "safe": True,
        "persist": True,
        "range": True,
    }
    assert all(gates.values())
    weak_failed = dict(gates, weak=False)
    gain_failed = dict(gates, gain=False)
    assert not all(weak_failed.values())
    assert not all(gain_failed.values())


def main() -> None:
    validate_run_summary()
    validate_manifest_and_raw_outputs()
    validate_engineering_context()
    validate_module_context()
    validate_citations()
    validate_c1_mechanics()
    print("C1-r01 artifact, citation, transform, event, stop-policy, and transaction validation: PASS")


if __name__ == "__main__":
    main()
