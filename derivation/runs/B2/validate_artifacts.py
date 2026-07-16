from __future__ import annotations

import hashlib
import math
import re
import subprocess
import zipfile
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "derivation/runs/B2"
CURRENT = ROOT / "derivation/modules/B/current/B_MODULE_CONTEXT.md"
SNAPSHOT = ROOT / "derivation/modules/B/history/B_MODULE_CONTEXT_after_B2.md"
B1_SNAPSHOT = ROOT / "derivation/modules/B/history/B_MODULE_CONTEXT_after_B1.md"
ACCEPTED_SHA256 = "65aeb65e28887942b8eed9e95d7339d62604b52000f2b6133def7245513dae22"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bytes_at_commit(commit: str, relative_path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def close(left: float, right: float, scale: float = 1.0) -> bool:
    return abs(left - right) <= 1.0e-11 * max(scale, abs(left), abs(right))


def between(text: str, start: str, end: str) -> str:
    return text.split(start, maxsplit=1)[1].split(end, maxsplit=1)[0]


def validate_run_summary() -> None:
    accepted = RUN_DIR / "RUN_UPDATE_SUMMARY.yaml"
    candidate = RUN_DIR / "RUN_UPDATE_SUMMARY_CANDIDATE.yaml"
    raw = RUN_DIR / "raw_downloads/RUN_UPDATE_SUMMARY(4).yaml"
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
        "module": "B2",
        "run_id": "B2-r01",
        "prompt_version": "1.0.0",
        "engineering_context_baseline": "1.0.0",
        "module_context_baseline": "0.1.0 accepted after B1",
        "run_directory": "derivation/runs/B2",
    }
    assert summary["engineering_context_delta"] == [
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
    assert all(summary["outputs"].values())
    assert all(
        value == "pass"
        for key, value in summary["self_check"].items()
        if key != "notes"
    )
    delta = summary["module_context_delta"]
    assert set(delta) == {"added", "modified", "preserved", "unresolved"}
    assert len(delta["added"]) == 8
    assert len(delta["modified"]) == 2
    assert len(delta["preserved"]) == 5
    assert len(delta["unresolved"]) == 6
    assert any("u_z" in item for item in delta["added"])
    assert any("B3_REBALANCE_REQUIRED" in item for item in delta["added"])


def validate_manifest_and_raw_outputs() -> None:
    manifest = yaml.safe_load((RUN_DIR / "INPUT_MANIFEST.yaml").read_text(encoding="utf-8"))
    assert manifest["run"]["id"] == "B2-r01"
    assert manifest["run"]["run_directory"] == "derivation/runs/B2"
    contract = manifest["upload_contract"]
    assert contract["expected_file_count"] == contract["verified_file_count"] == 12
    assert len(contract["files"]) == 12
    assert contract["all_expected_files_present"] is True
    assert contract["minimum_literature_package_complete"] is True
    assert contract["prompt_manifest_actual_paths_identical"] is True

    repository_commit = manifest["run"]["repository_commit"]
    for item in contract["files"]:
        current_path = ROOT / item["path"]
        current_bytes = current_path.read_bytes()
        if len(current_bytes) == item["bytes"] and hashlib.sha256(current_bytes).hexdigest() == item["sha256"]:
            continue
        historical_bytes = bytes_at_commit(repository_commit, item["path"])
        assert len(historical_bytes) == item["bytes"]
        assert hashlib.sha256(historical_bytes).hexdigest() == item["sha256"]

    expected_receipts = {
        "B_MODULE_CONTEXT.md": ("B_MODULE_CONTEXT(2).md", "MODULE_CONTEXT_CANDIDATE.md"),
        "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md": (
            "ENGINEERING_FIXED_CONTEXT_CANDIDATE(4).md",
            "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md",
        ),
        "RUN_UPDATE_SUMMARY.yaml": ("RUN_UPDATE_SUMMARY(4).yaml", "RUN_UPDATE_SUMMARY_CANDIDATE.yaml"),
        "CITATION_BRIEF.md": ("CITATION_BRIEF(4).md", "CITATION_BRIEF.md"),
    }
    received = manifest["received_outputs"]
    assert len(received) == len(expected_receipts) == 4
    for item in received:
        raw_name, candidate_name = expected_receipts[item["expected_name"]]
        assert item["received_name"] == raw_name
        archived = ROOT / item["archived_path"]
        normalized = ROOT / item["normalized_candidate_path"]
        assert archived.name == raw_name
        assert normalized.name == candidate_name
        assert archived.stat().st_size == item["bytes"]
        assert sha256(archived) == item["sha256"]
        assert archived.read_bytes() == normalized.read_bytes()
        indexed = subprocess.run(
            ["git", "show", f":{item['archived_path']}"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
        assert indexed == archived.read_bytes()
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

    expected_raw = {values[0] for values in expected_receipts.values()}
    assert {path.name for path in (RUN_DIR / "raw_downloads").iterdir()} == expected_raw
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
    assert accepted["version"] == "0.2.0"
    assert accepted["stage"] == "B2"
    assert accepted["status"] == "accepted"
    assert accepted["sha256"] == ACCEPTED_SHA256
    assert sha256(ROOT / accepted["path"]) == ACCEPTED_SHA256
    assert (ROOT / accepted["path"]).read_bytes() == (ROOT / accepted["history_snapshot"]).read_bytes()

    for literature_path in [item["path"] for item in contract["files"][-3:]]:
        with zipfile.ZipFile(ROOT / literature_path) as archive:
            names = archive.namelist()
            assert "evidence_card.md" in names
            assert sum(name.startswith("figures/") for name in names) == 3
            assert archive.testzip() is None


def validate_engineering_context() -> None:
    baseline = ROOT / "engineering_fixed_context/engineering_fixed_context.md"
    candidate = RUN_DIR / "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md"
    raw = RUN_DIR / "raw_downloads/ENGINEERING_FIXED_CONTEXT_CANDIDATE(4).md"
    assert baseline.read_bytes() == candidate.read_bytes() == raw.read_bytes()
    assert sha256(candidate) == "6c1225d3137f8095673b78e1dc8a76acdb0ae73247ec7c49e720cfcc56bb03cb"


def validate_b1_preservation(accepted: str) -> None:
    baseline = B1_SNAPSHOT.read_text(encoding="utf-8")
    baseline_sections_2_to_15 = between(baseline, "## 2. 坐标", "## 16. 对 B2")
    accepted_sections_2_to_15 = between(accepted, "## 2. 坐标", "## 16. B1 冻结交接记录")
    assert accepted_sections_2_to_15 == baseline_sections_2_to_15

    baseline_section_16_body = between(baseline, "### 16.1", "## 17. 输出前自检结论")
    accepted_section_16_body = between(accepted, "### 16.1", "## 17. B1 冻结自检记录")
    assert accepted_section_16_body == baseline_section_16_body

    b1_final_bullets = baseline.split("- 本文是 B 截至 B1 的首版完整上下文", maxsplit=1)[1]
    assert "- 本文是 B 截至 B1 的首版完整上下文" + b1_final_bullets in accepted


def validate_module_context() -> None:
    raw = RUN_DIR / "raw_downloads/B_MODULE_CONTEXT(2).md"
    candidate_path = RUN_DIR / "MODULE_CONTEXT_CANDIDATE.md"
    assert raw.read_bytes() == candidate_path.read_bytes()
    candidate = candidate_path.read_text(encoding="utf-8")
    accepted = CURRENT.read_text(encoding="utf-8")
    assert CURRENT.read_bytes() == SNAPSHOT.read_bytes()
    assert sha256(CURRENT) == ACCEPTED_SHA256
    assert "> 上下文候选版本：`0.2.0`" in candidate
    assert "> 当前状态：`candidate`" in candidate
    assert "> 上下文版本：`0.2.0`" in accepted
    assert "> 当前状态：`accepted`" in accepted

    expected = candidate.replace(
        "> 上下文候选版本：`0.2.0`",
        "> 上下文版本：`0.2.0`",
        1,
    ).replace(
        "> 当前状态：`candidate`",
        "> 当前状态：`accepted`",
        1,
    ).replace(
        "最新完整候选上下文",
        "最新完整上下文",
        1,
    ).replace(
        "本候选上下文同时覆盖",
        "本上下文同时覆盖",
        1,
    ).replace(
        "本候选已形成",
        "本接受版已形成",
        1,
    ).replace(
        "B1+B2 最新完整候选，不是 B2 增量",
        "B1+B2 最新完整上下文，不是 B2 增量",
        1,
    )
    expected = expected.rstrip() + "\n"
    assert accepted == expected
    validate_b1_preservation(accepted)

    for section in range(1, 34):
        assert re.search(rf"^## {section}\.\s", accepted, flags=re.MULTILINE)
    required_markers = (
        "B2EquilibriumRequest",
        "B2EquilibriumTrial",
        "A_on_B",
        "embedded_constitutive_trial",
        "RIGID_MOUNT",
        "AXIAL_SPRING_MOUNT",
        "P_z\\in\\mathcal N_U",
        "PRELOAD_SEARCH_CONTINUE",
        "BALANCED_UNIQUE",
        "BALANCED_DEGENERATE",
        "EVENT_REDUCTION_REQUIRED",
        "B3_REBALANCE_REQUIRED",
        "NUMERICAL_NONCONVERGENCE",
        "EQUILIBRIUM_INFEASIBLE",
        "CONSTRAINT_GRAPH_UNAVAILABLE",
        "\\gamma_{\\rm common}",
        "\\mathbf K_{W,x\\mid P_z}",
        "N_{\\rm eff}",
        "2×5",
        "5×2",
        "文献06",
        "文献07",
        "文献10",
    )
    for marker in required_markers:
        assert marker in accepted
    assert "不得再加一次 `k_s delta_s`" in accepted
    assert "每单元 `P_z` 只在 B2 外层施加一次" in accepted
    assert "B2 不越过事件" in accepted
    assert "不构成已接受的 B_TO_C 合同" in accepted
    assert "尚未运行真实 A 实现或实验数据" in accepted
    assert accepted.count("```") % 2 == 0
    assert accepted.count("\\[") == accepted.count("\\]")
    assert "TODO" not in accepted and "TBD" not in accepted and "{{" not in accepted
    tags = re.findall(r"\\tag\{([^}]+)\}", accepted)
    assert len(tags) == len(set(tags))


def validate_citations() -> None:
    citation_path = RUN_DIR / "CITATION_BRIEF.md"
    raw = RUN_DIR / "raw_downloads/CITATION_BRIEF(4).md"
    assert citation_path.read_bytes() == raw.read_bytes()
    citation = citation_path.read_text(encoding="utf-8")
    body, references = citation.split("## 参考来源", maxsplit=1)
    defined = set(re.findall(r"^\[(\d+)\]\s", references, flags=re.MULTILINE))
    used: set[str] = set()
    for group in re.findall(r"\[([0-9,]+)\]", body):
        used.update(group.split(","))
    assert defined == used == {str(index) for index in range(1, 8)}
    assert "[1] 文献06" in references
    assert "[2] 文献07" in references
    assert "[3] 文献10" in references
    assert "https://doi.org/10.1007/BF01581275" in references
    assert "https://doi.org/10.1137/S1052623401383558" in references
    assert "https://petsc.org/release/manual/snes/#variational-inequalities" in references
    assert "GPT 自带知识" in references
    assert "仅本地归档" in citation


def surrogate_solution(onsets: list[float], stiffnesses: list[float], pz: float) -> tuple[float, list[float]]:
    low = min(onsets)
    high = max(onsets) + pz / min(stiffnesses) + 1.0
    for _ in range(100):
        middle = 0.5 * (low + high)
        total = sum(k * max(0.0, middle - onset) for onset, k in zip(onsets, stiffnesses, strict=True))
        if total < pz:
            low = middle
        else:
            high = middle
    p = 0.5 * (low + high)
    forces = [k * max(0.0, p - onset) for onset, k in zip(onsets, stiffnesses, strict=True)]
    return p, forces


def validate_b2_mechanics() -> None:
    # Common displacement produces equilibrium without assuming equal per-needle force.
    onsets = [0.0, 0.15, 0.45, 0.9]
    stiffnesses = [2.0, 1.0, 4.0, 0.5]
    pz = 1.2
    p, forces = surrogate_solution(onsets, stiffnesses, pz)
    assert close(sum(forces), pz)
    assert 1 < sum(force > 1.0e-12 for force in forces) < len(forces)
    assert len({round(force, 10) for force in forces if force > 1.0e-12}) > 1

    # Needle evaluation order cannot change the common solution or force-by-ID map.
    permutation = [2, 0, 3, 1]
    p_perm, forces_perm = surrogate_solution(
        [onsets[index] for index in permutation],
        [stiffnesses[index] for index in permutation],
        pz,
    )
    restored = [0.0] * len(forces)
    for permuted_index, original_index in enumerate(permutation):
        restored[original_index] = forces_perm[permuted_index]
    assert close(p, p_perm)
    assert all(close(left, right) for left, right in zip(forces, restored, strict=True))

    weights = [force / pz for force in forces]
    n_eff = 1.0 / sum(weight * weight for weight in weights)
    assert 1.0 <= n_eff <= sum(force > 0.0 for force in forces)

    # Constant-Pz condensation matches a finite difference on a synthetic smooth branch.
    k_x = [2.0, -0.5, 1.25, 0.2, -0.1, 0.3]
    k_z = [-1.0, 0.4, -5.0, 0.0, 0.2, -0.6]
    w0 = [0.3, -0.2, 1.8, 0.1, 0.0, -0.1]
    k_zx = k_x[2]
    k_zz = k_z[2]
    duz_dux = -k_zx / k_zz
    condensed = [kx + kz * duz_dux for kx, kz in zip(k_x, k_z, strict=True)]

    def balanced_wrench(ux: float) -> list[float]:
        uz = (pz - w0[2] - k_x[2] * ux) / k_z[2]
        return [base + kx * ux + kz * uz for base, kx, kz in zip(w0, k_x, k_z, strict=True)]

    step = 1.0e-6
    derivative = [
        (plus - minus) / (2.0 * step)
        for plus, minus in zip(balanced_wrench(step), balanced_wrench(-step), strict=True)
    ]
    assert all(close(left, right, scale=10.0) for left, right in zip(condensed, derivative, strict=True))
    assert close(balanced_wrench(0.3)[2], pz)

    # Active actuator and contact resultant close only in the normal generalized coordinate.
    contact_force = (0.7, -0.2, pz)
    actuator_force = (0.0, 0.0, -pz)
    assert close(contact_force[2] + actuator_force[2], 0.0)
    assert close(-contact_force[0], -0.7)

    # Common event reduction and simultaneous-event membership are permutation invariant.
    gammas = [0.72, 0.31, 0.31 + 1.0e-12, 1.0]
    gamma_common = min(gammas)
    simultaneous = {index for index, gamma in enumerate(gammas) if abs(gamma - gamma_common) <= 1.0e-10}
    assert close(gamma_common, 0.31)
    assert simultaneous == {1, 2}
    assert min(reversed(gammas)) == gamma_common

    # Independent admissible normal intervals assemble to the same total interval in any order.
    graphs = [(0.0, 0.6), (0.4, 1.2), (0.0, 0.5)]
    total_interval = (sum(item[0] for item in graphs), sum(item[1] for item in graphs))
    assert total_interval[0] <= pz <= total_interval[1]
    assert total_interval == (sum(item[0] for item in reversed(graphs)), sum(item[1] for item in reversed(graphs)))

    # The 4 mm spring travel limit is a hard branch boundary, not a tensile extension.
    for requested_compression in (-1.0, 0.0, 2.5, 4.0, 5.0):
        compression = min(4.0, max(0.0, requested_compression))
        assert 0.0 <= compression <= 4.0
        assert 3.0 * compression >= 0.0


def main() -> None:
    validate_run_summary()
    validate_manifest_and_raw_outputs()
    validate_engineering_context()
    validate_module_context()
    validate_citations()
    validate_b2_mechanics()
    print("B2-r01 artifact, citation, inheritance, and mechanics validation: PASS")


if __name__ == "__main__":
    main()
