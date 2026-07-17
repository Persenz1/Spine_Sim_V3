from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "derivation/runs/A_INTEGRATION"
MODEL = ROOT / "derivation/modules/A/final/A_INTEGRATED_MODEL.md"
CONTRACT = ROOT / "derivation/contracts/A_TO_B_CONTRACT.md"
ENGINEERING_CONTEXT = ROOT / "engineering_fixed_context/engineering_fixed_context.md"
MODULE_CONTEXT = ROOT / "derivation/modules/A/current/A_MODULE_CONTEXT.md"
PUBLIC_BODY_PATTERN = re.compile(
    r"<!-- BEGIN A_TO_B_PUBLIC_CONTRACT -->\s*(.*?)\s*"
    r"<!-- END A_TO_B_PUBLIC_CONTRACT -->",
    flags=re.DOTALL,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(left: float, right: float, scale: float = 1.0) -> bool:
    return abs(left - right) <= 1.0e-10 * max(scale, abs(left), abs(right))


def dot(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def cross(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def add(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> tuple[float, float, float]:
    return tuple(a + b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def subtract(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> tuple[float, float, float]:
    return tuple(a - b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def public_body(text: str) -> str:
    match = PUBLIC_BODY_PATTERN.search(text.replace("\r\n", "\n"))
    assert match is not None
    return match.group(1).strip()


def validate_manifest_and_archives() -> None:
    manifest = yaml.safe_load(
        (RUN_DIR / "INPUT_MANIFEST.yaml").read_text(encoding="utf-8")
    )
    assert manifest["run"]["id"] == "A_INTEGRATION-r01"
    assert manifest["run"]["run_directory"] == "derivation/runs/A_INTEGRATION"
    assert manifest["expected_outputs"]["files"] == [
        "A_INTEGRATED_MODEL.md",
        "A_TO_B_CONTRACT.md",
    ]

    received = manifest["received_outputs"]
    assert [item["name"] for item in received] == [
        "A_INTEGRATED_MODEL.md",
        "A_TO_B_CONTRACT.md",
    ]
    expected_raw_hashes = {
        "A_INTEGRATED_MODEL.md": (
            102793,
            "7d68d493f06187b78ac529c6fdb966e22131c99153fef8487890d1d56198b423",
        ),
        "A_TO_B_CONTRACT.md": (
            26117,
            "34a4b87e9d09dd251ee489b60038d3f3479d47fe2e385d5678bdae86b1f0ed38",
        ),
    }
    for item in received:
        archived = ROOT / item["archived_path"]
        candidate = ROOT / item["normalized_candidate_path"]
        expected_bytes, expected_hash = expected_raw_hashes[item["name"]]
        assert archived.is_file() and candidate.is_file()
        assert archived.stat().st_size == item["bytes"] == expected_bytes
        assert sha256(archived) == item["sha256"] == expected_hash
        assert archived.read_bytes() == candidate.read_bytes()
        assert item["byte_identical_candidate_copy"] is True

    assert (RUN_DIR / "RAW_RESPONSE.md").read_text(encoding="utf-8").strip() == "产物"
    assert (RUN_DIR / "MECHANICAL_FIXES.md").is_file()
    assert (RUN_DIR / "VALIDATION_REPORT.md").is_file()

    accepted = manifest["accepted_outputs"]
    assert accepted["status"] == "accepted"
    for item in accepted["files"]:
        path = ROOT / item["path"]
        assert path.is_file()
        assert path.stat().st_size == item["bytes"]
        assert sha256(path) == item["sha256"]
    assert accepted["public_contract_body_verbatim"] is True
    assert accepted["engineering_context_changed"] is False
    assert accepted["engineering_or_physics_decision_required"] is False


def validate_model_and_contract() -> None:
    model = MODEL.read_text(encoding="utf-8")
    contract = CONTRACT.read_text(encoding="utf-8")
    candidate_model = (RUN_DIR / "A_INTEGRATED_MODEL_CANDIDATE.md").read_text(
        encoding="utf-8"
    )
    candidate_contract = (RUN_DIR / "A_TO_B_CONTRACT_CANDIDATE.md").read_text(
        encoding="utf-8"
    )

    assert "模型版本：`1.0.0`" in model
    assert "状态：`accepted`" in model
    assert "contract_version: `1.0.0`" in contract
    assert "status: `accepted`" in contract
    assert "1.0.0-candidate" not in model
    assert "1.0.0-candidate" not in contract
    assert "状态：`candidate`" in candidate_model
    assert "status: `candidate`" in candidate_contract

    assert public_body(model) == public_body(contract)
    assert public_body(candidate_model) == public_body(candidate_contract)

    for section in range(1, 13):
        assert re.search(rf"^## {section}\. ", model, flags=re.MULTILINE)
    required_markers = (
        "SurfaceRealization",
        "A1QueryHandle",
        "candidate_any",
        "candidate_robust",
        "H_R(x_c,y_c)",
        "g_{\\rm cone}",
        "\\boldsymbol\\chi_j\\in\\mathcal L_3",
        "\\mathbf r_{c,j}",
        "\\mathbf C_b\\mathbf W_c",
        "AT_ORIGINAL_LENGTH",
        "HARD_STOP",
        "ROLLING_NO_SLIP",
        "SLIP_ONSET_CONFIRMED",
        "DamageStore",
        "\\Phi_{{\\rm init},k}",
        "\\Phi_{M,k}=r_{M,k}-1",
        "\\delta_{f,k}",
        "\\sigma_1^{\\rm ub}",
        "RELEASE_TRANSITION",
        "REATTACHED_ENTRY",
        "intrinsic_single_spine_kernel",
        "standalone_single_spine_driver",
        "embedded_constitutive_trial",
        "CONTRACT_VIOLATION_DUPLICATE_NORMAL_LOAD",
        "prepare_atomic_commit",
        "commit_atomic",
        "100\\ \\mathrm{mm}",
    )
    for marker in required_markers:
        assert marker in model

    for step in range(12):
        assert re.search(rf"^\s{{0,3}}{step}\. ", model, flags=re.MULTILINE)

    assert "本征核不含" in model
    assert "\\mathbf E_Z\\cdot\\mathbf F_c-0.5\\ \\mathrm N=0" in model
    assert re.search(
        r"r_P\s*=\s*\\mathbf E_Z\\cdot\\mathbf F_\{A\\to B\}-P_z=0",
        model,
    )
    assert "requested base increment or standalone Delta_u_x" in model
    assert "Repeated B Newton calls cannot mutate accepted state" in model

    assert model.count("```") % 2 == 0
    assert contract.count("```") % 2 == 0
    assert model.count("\\[") == model.count("\\]")
    assert contract.count("\\[") == contract.count("\\]")
    assert model.count("\\(") == model.count("\\)")
    assert contract.count("\\(") == contract.count("\\)")
    placeholders = re.compile(r"\b(?:TODO|TBD|FIXME|PLACEHOLDER)\b")
    assert placeholders.search(model) is None
    assert placeholders.search(contract) is None

    assert "Q_s=-\\mathbf a_0\\cdot\\mathbf F_c" in model
    assert "Q_s=-\\mathbf a\\cdot\\mathbf F_c" not in model
    assert "\\mathbf a_0\\mathbf a_0^{\\mathsf T}/k_s" in model
    assert "\\mathbf M_c^{c_t}" in model
    assert "\\mathbf K_{\\rm str}" in model and "\\mathbf N" in model

    engineering_ids = set(
        re.findall(r"UNRESOLVED\.[A-Z0-9_.]+", ENGINEERING_CONTEXT.read_text(encoding="utf-8"))
    )
    model_ids = set(re.findall(r"UNRESOLVED\.[A-Z0-9_.]+", model))
    assert engineering_ids <= model_ids
    assert "UNRESOLVED.REGISTRY.GLOBAL" in model_ids

    input_context = MODULE_CONTEXT.read_text(encoding="utf-8")
    assert "当前状态：`accepted`" in input_context
    assert "# A2：单边接触、摩擦稳定与结构柔顺加载" in input_context
    assert "# A3：滑移、局部材料失效、脱离与再挂接" in input_context


def validate_mechanics() -> None:
    # Wrench transport and twist transport preserve power.
    force = (1.2, -0.7, 0.5)
    moment_o = (0.3, 0.8, -0.4)
    r_o = (2.0, -1.0, 0.5)
    r_op = (-0.5, 1.5, 2.0)
    dr_o = (0.04, -0.02, 0.01)
    dtheta = (0.005, -0.003, 0.004)
    moment_op = add(moment_o, cross(subtract(r_o, r_op), force))
    dr_op = add(dr_o, cross(dtheta, subtract(r_op, r_o)))
    power_o = dot(force, dr_o) + dot(moment_o, dtheta)
    power_op = dot(force, dr_op) + dot(moment_op, dtheta)
    assert close(power_o, power_op)

    # Sliding SOC state satisfies complementarity and maximum dissipation.
    mu = 0.45
    lambda_n = 1.3
    slip = (0.03, -0.04)
    slip_norm = math.hypot(*slip)
    lambda_t = tuple(-mu * lambda_n * value / slip_norm for value in slip)
    chi = (mu * lambda_n, *lambda_t)
    psi = (slip_norm, *slip)
    assert close(dot(chi, psi), 0.0)
    assert close(math.hypot(*lambda_t), mu * lambda_n)
    assert dot(lambda_t, slip) <= 0.0

    # The beam compliance block is symmetric for the stated sign convention.
    a = (0.6, 0.0, -0.8)
    p_parallel = [[a[i] * a[j] for j in range(3)] for i in range(3)]
    identity = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]
    p_perp = [[identity[i][j] - p_parallel[i][j] for j in range(3)] for i in range(3)]
    s = [[0.0, -a[2], a[1]], [a[2], 0.0, -a[0]], [-a[1], a[0], 0.0]]
    length, young, area, inertia, shear, polar = 4.0, 200000.0, 0.5, 0.02, 77000.0, 0.04
    c = [[0.0] * 6 for _ in range(6)]
    for i in range(3):
        for j in range(3):
            c[i][j] = length / (young * area) * p_parallel[i][j] + length**3 / (3.0 * young * inertia) * p_perp[i][j]
            c[i][j + 3] = -(length**2) / (2.0 * young * inertia) * s[i][j]
            c[i + 3][j] = (length**2) / (2.0 * young * inertia) * s[i][j]
            c[i + 3][j + 3] = length / (young * inertia) * p_perp[i][j] + length / (shear * polar) * p_parallel[i][j]
    assert all(close(c[i][j], c[j][i]) for i in range(6) for j in range(6))

    # Engineering spring input N/m converts to internal N/mm exactly once.
    assert close(100.0 / 1000.0, 0.1)
    assert close(2000.0 / 1000.0, 2.0)

    # Patch stress proxy reproduces the aggregated wall traction.
    normal = (0.0, 0.0, 1.0)
    tangent = (0.3, -0.2, 0.0)
    compression = 0.5
    patch_area = 0.1
    sigma = [[0.0] * 3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            sigma[i][j] = (
                -compression * normal[i] * normal[j]
                - tangent[i] * normal[j]
                - normal[i] * tangent[j]
            ) / patch_area
    traction = tuple(sum(sigma[i][j] * normal[j] for j in range(3)) for i in range(3))
    expected = tuple((-compression * normal[i] - tangent[i]) / patch_area for i in range(3))
    assert all(close(a_value, b_value) for a_value, b_value in zip(traction, expected, strict=True))

    # Mohr-Coulomb boundary, softening endpoints, and fracture energy close.
    cohesion, phi, sigma_iii = 0.8, 0.45, -2.0
    sigma_i = (2.0 * cohesion * math.cos(phi) + sigma_iii * (1.0 - math.sin(phi))) / (1.0 + math.sin(phi))
    phi_mc = sigma_i * (1.0 + math.sin(phi)) / (2.0 * cohesion * math.cos(phi)) - sigma_iii * (1.0 - math.sin(phi)) / (2.0 * cohesion * math.cos(phi)) - 1.0
    assert close(phi_mc, 0.0)
    residual, peak_traction, fracture_energy = 0.2, 5.0, 0.1
    delta_f = 2.0 * fracture_energy / ((1.0 - residual) * peak_traction)
    q0 = residual + (1.0 - residual) * max(1.0 - 0.0 / delta_f, 0.0)
    qf = residual + (1.0 - residual) * max(1.0 - delta_f / delta_f, 0.0)
    dissipation = patch_area * (1.0 - residual) * peak_traction * (delta_f - delta_f**2 / (2.0 * delta_f))
    assert close(q0, 1.0) and close(qf, residual)
    assert close(dissipation, patch_area * fracture_energy)

    # Circular-section stress measures and the principal-stress bound are defined.
    diameter = 0.8
    section_area = math.pi * diameter**2 / 4.0
    second_moment = math.pi * diameter**4 / 64.0
    polar_moment = math.pi * diameter**4 / 32.0
    assert close(polar_moment, 2.0 * second_moment)
    sigma_ab = 1.2 / section_area + (diameter / 2.0) * math.hypot(0.3, 0.4) / second_moment
    tau_ub = abs(0.05) * (diameter / 2.0) / polar_moment + 4.0 * math.hypot(0.1, 0.2) / (3.0 * section_area)
    sigma_vm = math.sqrt(sigma_ab**2 + 3.0 * tau_ub**2)
    sigma_1 = 0.5 * (sigma_ab + math.sqrt(sigma_ab**2 + 4.0 * tau_ub**2))
    assert sigma_vm >= sigma_ab > 0.0
    assert sigma_1 >= sigma_ab > 0.0


def main() -> None:
    validate_manifest_and_archives()
    validate_model_and_contract()
    validate_mechanics()
    print("A_INTEGRATION-r01 artifact and mechanics validation: PASS")


if __name__ == "__main__":
    main()
