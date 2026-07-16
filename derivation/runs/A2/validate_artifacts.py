from __future__ import annotations

import hashlib
import math
import re
import subprocess
import zipfile
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "derivation/runs/A2"
CURRENT = ROOT / "derivation/modules/A/current/A_MODULE_CONTEXT.md"
SNAPSHOT = ROOT / "derivation/modules/A/history/A_MODULE_CONTEXT_after_A2.md"
A1_SNAPSHOT = ROOT / "derivation/modules/A/history/A_MODULE_CONTEXT_after_A1.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bytes_at_commit(commit: str, relative_path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    return result.stdout


def close(left: float, right: float, scale: float = 1.0) -> bool:
    return abs(left - right) <= 1.0e-10 * max(scale, abs(left), abs(right))


def mat_transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [list(row) for row in zip(*matrix, strict=True)]


def mat_multiply(left: list[list[float]], right: list[list[float]]) -> list[list[float]]:
    right_t = mat_transpose(right)
    return [[sum(a * b for a, b in zip(row, col, strict=True)) for col in right_t] for row in left]


def quadratic(vector: list[float], matrix: list[list[float]]) -> float:
    return sum(vector[i] * matrix[i][j] * vector[j] for i in range(len(vector)) for j in range(len(vector)))


def cholesky_positive_definite(matrix: list[list[float]]) -> None:
    size = len(matrix)
    factor = [[0.0] * size for _ in range(size)]
    for i in range(size):
        for j in range(i + 1):
            remainder = matrix[i][j] - sum(factor[i][k] * factor[j][k] for k in range(j))
            if i == j:
                assert remainder > 0.0
                factor[i][j] = math.sqrt(remainder)
            else:
                factor[i][j] = remainder / factor[j][j]


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
        "module": "A2",
        "run_id": "A2-r01",
        "prompt_version": "1.0.0",
        "engineering_context_baseline": "1.0.0",
        "module_context_baseline": "0.1.0",
        "run_directory": "derivation/runs/A2",
    }
    deltas = summary["engineering_context_delta"]
    assert len(deltas) == 1
    delta = deltas[0]
    assert delta == {
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
    assert all(summary["outputs"].values())
    assert all(value == "pass" for key, value in summary["self_check"].items() if key != "notes")


def validate_manifest_and_raw_outputs() -> None:
    manifest = yaml.safe_load((RUN_DIR / "INPUT_MANIFEST.yaml").read_text(encoding="utf-8"))
    assert manifest["run"]["id"] == "A2-r01"
    assert manifest["run"]["run_directory"] == "derivation/runs/A2"
    contract = manifest["upload_contract"]
    assert contract["expected_file_count"] == contract["verified_file_count"] == 10
    assert len(contract["files"]) == 10
    assert contract["all_expected_files_present"] is True
    assert contract["minimum_literature_package_complete"] is True
    repository_commit = manifest["run"]["repository_commit"]
    for item in contract["files"]:
        current_bytes = (ROOT / item["path"]).read_bytes()
        if len(current_bytes) == item["bytes"] and hashlib.sha256(current_bytes).hexdigest() == item["sha256"]:
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
        assert archived.read_bytes() == normalized.read_bytes()

    with zipfile.ZipFile(ROOT / contract["files"][8]["path"]) as archive:
        assert any(name.endswith("evidence_card.md") for name in archive.namelist())
        assert archive.testzip() is None
    with zipfile.ZipFile(ROOT / contract["files"][9]["path"]) as archive:
        assert any(name.endswith("evidence_card.md") for name in archive.namelist())
        assert archive.testzip() is None


def validate_engineering_context() -> None:
    baseline = ROOT / "engineering_fixed_context/engineering_fixed_context.md"
    candidate = RUN_DIR / "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md"
    assert baseline.read_bytes() == candidate.read_bytes()
    assert sha256(candidate) == "6c1225d3137f8095673b78e1dc8a76acdb0ae73247ec7c49e720cfcc56bb03cb"


def validate_module_context() -> None:
    candidate = (RUN_DIR / "MODULE_CONTEXT_CANDIDATE.md").read_text(encoding="utf-8")
    current = CURRENT.read_text(encoding="utf-8")
    a1 = A1_SNAPSHOT.read_text(encoding="utf-8")
    assert CURRENT.read_bytes() == SNAPSHOT.read_bytes()
    assert "> 当前完成阶段：`A2`" in current
    assert "> 上下文版本：`0.2.0`" in current
    assert "> 当前状态：`accepted`" in current
    assert "> 当前状态：`candidate`" in candidate

    a1_lines = a1.splitlines()
    candidate_lines = candidate.splitlines()
    current_lines = current.splitlines()
    assert candidate_lines[13 : len(a1_lines)] == a1_lines[13:]
    assert current_lines[13 : len(a1_lines)] == a1_lines[13:]

    for section in range(1, 26):
        assert re.search(rf"^## {section}\.", current, flags=re.MULTILINE)
    assert "# A2：单边接触、摩擦稳定与结构柔顺加载" in current
    assert "\\boldsymbol\\chi_j\\in\\mathcal L_3" in current
    assert "\\mathbf C_b=" in current
    assert "`PRELOAD_INFEASIBLE`" in current
    assert "\\frac{\\tan\\phi-\\mu}{1+\\mu\\tan\\phi}" in current
    assert "它不表示任意较小 $F$ 都满足完整摩擦锥" in current
    assert current.count("```") % 2 == 0
    assert sum(line.strip() == "$$" for line in current.splitlines()) % 2 == 0


def validate_citations() -> None:
    citation = (RUN_DIR / "CITATION_BRIEF.md").read_text(encoding="utf-8")
    body, references = citation.split("## 参考来源", maxsplit=1)
    defined = set(re.findall(r"^\[(\d+)\]\s", references, flags=re.MULTILINE))
    used: set[str] = set()
    for group in re.findall(r"\[([0-9,]+)\]", body):
        used.update(group.split(","))
    assert defined == used == {str(index) for index in range(1, 7)}
    assert "[3] 文献01" in references
    assert "[5] 文献07" in references
    assert "https://arxiv.org/pdf/2101.11763" in references
    assert "https://epubs.siam.org/doi/10.1137/060671061" in references
    assert "https://ocw.mit.edu/" in references
    assert "仅本地归档" in citation


def validate_mechanics() -> None:
    mu = 0.6
    lambda_n = 2.0
    slip = (0.3, 0.4)
    slip_norm = math.hypot(*slip)
    lambda_t = tuple(-mu * lambda_n * value / slip_norm for value in slip)
    chi = (mu * lambda_n, *lambda_t)
    psi = (slip_norm, *slip)
    assert close(math.hypot(*chi[1:]), chi[0])
    assert close(math.hypot(*psi[1:]), psi[0])
    assert close(sum(a * b for a, b in zip(chi, psi, strict=True)), 0.0)

    phi = 0.3
    normal_load = 0.5
    ratio = (math.tan(phi) + mu) / (1.0 - mu * math.tan(phi))
    drag = normal_load * ratio
    normal_reaction = drag * math.sin(phi) + normal_load * math.cos(phi)
    tangential_reaction = -drag * math.cos(phi) + normal_load * math.sin(phi)
    assert close(tangential_reaction, -mu * normal_reaction)

    phi = 0.8
    lower_ratio = (math.tan(phi) - mu) / (1.0 + mu * math.tan(phi))
    drag = normal_load * lower_ratio
    normal_reaction = drag * math.sin(phi) + normal_load * math.cos(phi)
    tangential_reaction = -drag * math.cos(phi) + normal_load * math.sin(phi)
    assert close(tangential_reaction, mu * normal_reaction)

    locking_mu = 0.8
    locking_phi = 1.1
    assert math.cos(locking_phi) - locking_mu * math.sin(locking_phi) < 0.0
    locking_lower = (math.tan(locking_phi) - locking_mu) / (
        1.0 + locking_mu * math.tan(locking_phi)
    )
    below_drag = 0.5 * normal_load * locking_lower
    below_normal = below_drag * math.sin(locking_phi) + normal_load * math.cos(locking_phi)
    below_tangent = -below_drag * math.cos(locking_phi) + normal_load * math.sin(locking_phi)
    assert below_tangent > locking_mu * below_normal
    above_drag = 2.0 * normal_load
    above_normal = above_drag * math.sin(locking_phi) + normal_load * math.cos(locking_phi)
    above_tangent = -above_drag * math.cos(locking_phi) + normal_load * math.sin(locking_phi)
    assert abs(above_tangent) <= locking_mu * above_normal

    young = 210000.0
    poisson = 0.3
    diameter = 0.8
    length = 4.0
    area = math.pi * diameter**2 / 4.0
    second_moment = math.pi * diameter**4 / 64.0
    polar_moment = math.pi * diameter**4 / 32.0
    shear = young / (2.0 * (1.0 + poisson))
    p_parallel = [[1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    p_perp = [[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    skew = [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]]

    def combine(first: float, left: list[list[float]], second: float, right: list[list[float]]) -> list[list[float]]:
        return [[first * left[i][j] + second * right[i][j] for j in range(3)] for i in range(3)]

    c11 = combine(length / (young * area), p_parallel, length**3 / (3.0 * young * second_moment), p_perp)
    c12 = [[-length**2 * value / (2.0 * young * second_moment) for value in row] for row in skew]
    c21 = [[length**2 * value / (2.0 * young * second_moment) for value in row] for row in skew]
    c22 = combine(length / (shear * polar_moment), p_parallel, length / (young * second_moment), p_perp)
    compliance = [c11[i] + c12[i] for i in range(3)] + [c21[i] + c22[i] for i in range(3)]
    assert all(close(compliance[i][j], compliance[j][i]) for i in range(6) for j in range(6))
    cholesky_positive_definite(compliance)

    radius = [0.0, 0.05, -0.02]
    radius_skew = [[0.0, -radius[2], radius[1]], [radius[2], 0.0, -radius[0]], [-radius[1], radius[0], 0.0]]
    point_jacobian = [
        [1.0, 0.0, 0.0, *[-value for value in radius_skew[0]]],
        [0.0, 1.0, 0.0, *[-value for value in radius_skew[1]]],
        [0.0, 0.0, 1.0, *[-value for value in radius_skew[2]]],
    ]
    point_compliance = mat_multiply(mat_multiply(point_jacobian, compliance), mat_transpose(point_jacobian))
    assert quadratic([1.0, -0.4, 0.2], point_compliance) > 0.0


def main() -> None:
    validate_run_summary()
    validate_manifest_and_raw_outputs()
    validate_engineering_context()
    validate_module_context()
    validate_citations()
    validate_mechanics()
    print("A2-r01 artifact and mechanics validation: PASS")


if __name__ == "__main__":
    main()
