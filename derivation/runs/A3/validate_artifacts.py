from __future__ import annotations

import hashlib
import math
import re
import subprocess
import zipfile
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "derivation/runs/A3"
CURRENT = ROOT / "derivation/modules/A/current/A_MODULE_CONTEXT.md"
SNAPSHOT = ROOT / "derivation/modules/A/history/A_MODULE_CONTEXT_after_A3.md"
A2_SNAPSHOT = ROOT / "derivation/modules/A/history/A_MODULE_CONTEXT_after_A2.md"


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
    return abs(left - right) <= 1.0e-10 * max(scale, abs(left), abs(right))


def validate_run_summary() -> None:
    summary_path = RUN_DIR / "RUN_UPDATE_SUMMARY.yaml"
    candidate_path = RUN_DIR / "RUN_UPDATE_SUMMARY_CANDIDATE.yaml"
    assert summary_path.read_bytes() == candidate_path.read_bytes()
    summary = yaml.safe_load(summary_path.read_text(encoding="utf-8"))
    assert set(summary) == {
        "run",
        "engineering_context_delta",
        "module_context_delta",
        "outputs",
        "self_check",
    }
    assert summary["run"] == {
        "module": "A3",
        "run_id": "A3-r01",
        "prompt_version": "1.0.0",
        "engineering_context_baseline": "1.0.0",
        "module_context_baseline": "0.2.0",
        "run_directory": "derivation/runs/A3",
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


def validate_manifest_and_raw_outputs() -> None:
    manifest = yaml.safe_load((RUN_DIR / "INPUT_MANIFEST.yaml").read_text(encoding="utf-8"))
    assert manifest["run"]["id"] == "A3-r01"
    assert manifest["run"]["run_directory"] == "derivation/runs/A3"
    contract = manifest["upload_contract"]
    assert contract["expected_file_count"] == contract["verified_file_count"] == 12
    assert len(contract["files"]) == 12
    assert contract["all_expected_files_present"] is True
    assert contract["minimum_literature_package_complete"] is True
    assert contract["prompt_manifest_actual_paths_identical"] is True

    repository_commit = manifest["run"]["repository_commit"]
    for item in contract["files"]:
        current_bytes = (ROOT / item["path"]).read_bytes()
        if (
            len(current_bytes) == item["bytes"]
            and hashlib.sha256(current_bytes).hexdigest() == item["sha256"]
        ):
            continue
        historical_bytes = bytes_at_commit(repository_commit, item["path"])
        assert len(historical_bytes) == item["bytes"]
        assert hashlib.sha256(historical_bytes).hexdigest() == item["sha256"]

    received = manifest["received_outputs"]
    assert len(received) == 4
    for item in received:
        archived = ROOT / item["archived_path"]
        normalized = ROOT / item["normalized_candidate_path"]
        assert archived.is_file() and normalized.is_file()
        assert archived.stat().st_size == item["bytes"]
        assert sha256(archived) == item["sha256"]

    exact_working_copies = received[:3]
    for item in exact_working_copies:
        assert (ROOT / item["archived_path"]).read_bytes() == (
            ROOT / item["normalized_candidate_path"]
        ).read_bytes()

    raw_citation = ROOT / received[3]["archived_path"]
    final_citation = ROOT / received[3]["normalized_candidate_path"]
    assert raw_citation.read_bytes() != final_citation.read_bytes()
    assert "www.civil.northwestern.edu" in raw_citation.read_text(encoding="utf-8")
    assert "link.springer.com/article/10.1007/BF02486267" in final_citation.read_text(
        encoding="utf-8"
    )
    assert (RUN_DIR / "RAW_RESPONSE.md").read_text(encoding="utf-8").strip() == "执行任务2"

    literature_paths = [item["path"] for item in contract["files"][-4:]]
    for literature_path in literature_paths:
        with zipfile.ZipFile(ROOT / literature_path) as archive:
            names = archive.namelist()
            assert "evidence_card.md" in names
            assert sum(name.startswith("figures/") for name in names) == 3
            assert archive.testzip() is None


def validate_engineering_context() -> None:
    baseline = ROOT / "engineering_fixed_context/engineering_fixed_context.md"
    candidate = RUN_DIR / "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md"
    assert baseline.read_bytes() == candidate.read_bytes()
    assert sha256(candidate) == "6c1225d3137f8095673b78e1dc8a76acdb0ae73247ec7c49e720cfcc56bb03cb"


def trim_trailing_separators(lines: list[str]) -> list[str]:
    trimmed = list(lines)
    while trimmed and trimmed[-1].strip() in {"", "---"}:
        trimmed.pop()
    return trimmed


def validate_module_context() -> None:
    candidate_path = RUN_DIR / "MODULE_CONTEXT_CANDIDATE.md"
    candidate = candidate_path.read_text(encoding="utf-8")
    accepted = CURRENT.read_text(encoding="utf-8")
    a2 = A2_SNAPSHOT.read_text(encoding="utf-8")

    assert CURRENT.read_bytes() == SNAPSHOT.read_bytes()
    assert sha256(candidate_path) == "a6d47ea5617464a15ddee09faa25ed039a6a13098391e2b35e021f493402630c"
    assert "> 当前完成阶段：`A3`" in candidate
    assert "> 上下文版本：`0.3.0`" in candidate
    assert "> 当前状态：`candidate`" in candidate
    assert "> 当前状态：`accepted`" in accepted

    a2_lines = a2.splitlines()
    candidate_lines = candidate.splitlines()
    a2_body = a2_lines[a2_lines.index("## 1. 范围、目标与不可越界边界") :]
    candidate_body_start = candidate_lines.index("## 1. 范围、目标与不可越界边界")
    a3_start = candidate_lines.index("# A3：滑移、局部材料失效、脱离与再挂接")
    candidate_a1_a2 = trim_trailing_separators(candidate_lines[candidate_body_start:a3_start])
    assert candidate_a1_a2 == trim_trailing_separators(a2_body)

    for section in range(1, 39):
        assert re.search(rf"^## {section}\.", accepted, flags=re.MULTILINE)
    required_markers = (
        "`CRITICAL_SLIP`",
        "SLIDING_CONTACT",
        "\\tag{A3-GEO}",
        "\\tag{A3-MC}",
        "\\tag{A3-ENERGY}",
        "\\tag{A3-NEEDLE-VM}",
        "\\tag{A3-RES}",
        "SEPARATED_SEARCH",
        "REATTACHED_LOAD",
        "SingleSpineTrialResponse",
        "A_MODULE_CONTEXT_after_A3.md",
    )
    for marker in required_markers[:-1]:
        assert marker in accepted
    assert "A_INTEGRATED_MODEL.md" in accepted
    assert "本轮不输出 `A_INTEGRATED_MODEL.md`" in accepted
    assert "多根针的共同背板平衡" in accepted
    assert "\\Phi_{M,k}=r_{M,k}-1" in accepted
    assert "未完成该标定时，$\\Phi_M$ 不进入" in accepted
    assert "\\mathbf Q_m" not in accepted
    assert "\\mathbf R_{m,k},\\mathbb H_k" in accepted
    assert "www.civil.northwestern.edu/people/bazant/PDFs/Papers/157.pdf" not in accepted
    assert "https://link.springer.com/article/10.1007/BF02486267" in accepted
    assert accepted.count("```") % 2 == 0
    assert sum(line.strip() == "$$" for line in accepted.splitlines()) % 2 == 0

    tags = re.findall(r"\\tag\{([^}]+)\}", accepted)
    assert len(tags) == len(set(tags))


def validate_citations() -> None:
    citation = (RUN_DIR / "CITATION_BRIEF.md").read_text(encoding="utf-8")
    body, references = citation.split("## 参考来源", maxsplit=1)
    defined = set(re.findall(r"^\[(\d+)\]\s", references, flags=re.MULTILINE))
    used: set[str] = set()
    for group in re.findall(r"\[([0-9,]+)\]", body):
        used.update(group.split(","))
    assert defined == used == {str(index) for index in range(1, 8)}
    assert "[2] 文献15" in references
    assert "[3] 文献14" in references
    assert "[6] 文献05" in references
    assert "[7] 文献03" in references
    assert "https://link.springer.com/article/10.1007/BF02486267" in references
    assert "https://ntrs.nasa.gov/api/citations/20020053651/downloads/20020053651.pdf" in references
    assert "GPT 自带知识" in references
    assert "仅本地归档" in citation


def validate_mechanics() -> None:
    # A3-STRESS: the stress proxy must reproduce the aggregated wall traction.
    normal = (0.0, 0.0, 1.0)
    tangent = (0.3, -0.2, 0.0)
    compression = 0.5
    area = 0.1
    sigma = [[0.0] * 3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            sigma[i][j] = (
                -compression * normal[i] * normal[j]
                - tangent[i] * normal[j]
                - normal[i] * tangent[j]
            ) / area
    traction = tuple(sum(sigma[i][j] * normal[j] for j in range(3)) for i in range(3))
    expected = tuple((-compression * normal[i] - tangent[i]) / area for i in range(3))
    assert all(close(left, right) for left, right in zip(traction, expected, strict=True))

    # A3-MC: a point built from the classical principal-stress surface has Phi=0.
    cohesion = 0.8
    phi = 0.45
    sigma_iii = -2.0
    sigma_i = (
        2.0 * cohesion * math.cos(phi) + sigma_iii * (1.0 - math.sin(phi))
    ) / (1.0 + math.sin(phi))
    phi_mc = (
        sigma_i * (1.0 + math.sin(phi)) / (2.0 * cohesion * math.cos(phi))
        - sigma_iii * (1.0 - math.sin(phi)) / (2.0 * cohesion * math.cos(phi))
        - 1.0
    )
    assert close(phi_mc, 0.0)

    # A3-SOFT/A3-ENERGY: endpoints and complete-softening energy close exactly.
    residual = 0.2
    peak_traction = 5.0
    fracture_energy = 0.1
    patch_area = 0.03
    delta_f = 2.0 * fracture_energy / ((1.0 - residual) * peak_traction)
    q0 = residual + (1.0 - residual) * max(1.0 - 0.0 / delta_f, 0.0)
    qf = residual + (1.0 - residual) * max(1.0 - delta_f / delta_f, 0.0)
    dissipation = (
        patch_area
        * (1.0 - residual)
        * peak_traction
        * (delta_f - delta_f**2 / (2.0 * delta_f))
    )
    assert close(q0, 1.0)
    assert close(qf, residual)
    assert close(dissipation, patch_area * fracture_energy)

    # A3-DPROJ: elastic and active-softening KKT states are exact roots.
    scale = 0.7
    elastic_increment = 0.0
    elastic_r_minus_q = -0.2
    elastic_residual = elastic_increment - max(
        0.0, elastic_increment + scale * elastic_r_minus_q
    )
    active_increment = 0.04
    active_r_minus_q = 0.0
    active_residual = active_increment - max(
        0.0, active_increment + scale * active_r_minus_q
    )
    invalid_residual = 0.0 - max(0.0, scale * 0.1)
    assert close(elastic_residual, 0.0)
    assert close(active_residual, 0.0)
    assert not close(invalid_residual, 0.0)

    # A3-SLIP: translation plus the corresponding sphere rotation gives zero slip.
    radius = 0.1
    speed = 2.0
    center_velocity = (speed, 0.0, 0.0)
    omega = (0.0, speed / radius, 0.0)
    contact_arm = (0.0, 0.0, -radius)
    omega_cross_arm = (
        omega[1] * contact_arm[2] - omega[2] * contact_arm[1],
        omega[2] * contact_arm[0] - omega[0] * contact_arm[2],
        omega[0] * contact_arm[1] - omega[1] * contact_arm[0],
    )
    slip_velocity = tuple(
        center_velocity[i] + omega_cross_arm[i] for i in range(3)
    )
    assert all(close(value, 0.0) for value in slip_velocity)

    # A3-NEEDLE: circular-section identities and stress bounds remain positive.
    diameter = 0.8
    section_area = math.pi * diameter**2 / 4.0
    second_moment = math.pi * diameter**4 / 64.0
    polar_moment = math.pi * diameter**4 / 32.0
    assert close(polar_moment, 2.0 * second_moment)
    sigma_ab = 1.2 / section_area + (diameter / 2.0) * math.hypot(0.3, 0.4) / second_moment
    tau_t = abs(0.05) * (diameter / 2.0) / polar_moment
    tau_v = 4.0 * math.hypot(0.1, 0.2) / (3.0 * section_area)
    sigma_vm = math.sqrt(sigma_ab**2 + 3.0 * (tau_t + tau_v) ** 2)
    assert sigma_vm >= sigma_ab > 0.0


def main() -> None:
    validate_run_summary()
    validate_manifest_and_raw_outputs()
    validate_engineering_context()
    validate_module_context()
    validate_citations()
    validate_mechanics()
    print("A3-r01 artifact, citation, and mechanics validation: PASS")


if __name__ == "__main__":
    main()
