from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "derivation/runs/B_INTEGRATION"
MODEL = ROOT / "derivation/modules/B/final/B_INTEGRATED_MODEL.md"
CONTRACT = ROOT / "derivation/contracts/B_TO_C_CONTRACT.md"
ENGINEERING_CONTEXT = ROOT / "engineering_fixed_context/engineering_fixed_context.md"
MODULE_CONTEXT = ROOT / "derivation/modules/B/current/B_MODULE_CONTEXT.md"
PUBLIC_BLOCK_PATTERN = re.compile(
    r"(<!-- BEGIN B_TO_C_PUBLIC_CONTRACT -->\n.*?\n"
    r"<!-- END B_TO_C_PUBLIC_CONTRACT -->)",
    flags=re.DOTALL,
)
PUBLIC_BODY_PATTERN = re.compile(
    r"<!-- BEGIN B_TO_C_PUBLIC_CONTRACT -->\n(.*?)\n"
    r"<!-- END B_TO_C_PUBLIC_CONTRACT -->",
    flags=re.DOTALL,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def marked_public_block(text: str) -> str:
    matches = PUBLIC_BLOCK_PATTERN.findall(text.replace("\r\n", "\n"))
    assert len(matches) == 1
    return matches[0]


def public_body(text: str) -> str:
    matches = PUBLIC_BODY_PATTERN.findall(text.replace("\r\n", "\n"))
    assert len(matches) == 1
    return matches[0]


def accepted_transform(text: str, *, model: bool) -> str:
    transformed = text.replace("1.0.0-candidate", "1.0.0")
    transformed = transformed.replace(
        "| `status` | `candidate` |", "| `status` | `accepted` |"
    )
    transformed = transformed.replace(
        "3. 候选合同不等于代码、材料参数、真实 CAD 或实验已经验证。",
        "3. 本已接受的理论/数据合同不等于代码、材料参数、真实 CAD 或实验已经验证。",
    )
    transformed = transformed.replace("不属于本候选版本", "不属于本版本")
    transformed = transformed.replace(
        "以下测试是合同接受前的最低验证要求；本候选文件只冻结测试定义，不声称实现已通过。",
        "以下测试是合同实现验收前的最低验证要求；本已接受文件只冻结测试定义，不声称实现已通过。",
    )
    if model:
        transformed = transformed.replace(
            "| 状态 | `candidate` |", "| 状态 | `accepted` |"
        )
        transformed = transformed.replace(
            "- 理论/数据合同：`candidate`；",
            "- 理论/数据合同：`accepted`；",
        )
        transformed = transformed.replace(
            "| 集成坐标/事务/schema | candidate | 由本文件和公共合同冻结候选 |",
            "| 集成坐标/事务/schema | accepted | 由本文件和公共合同正式冻结 |",
        )
        transformed = transformed.replace("本候选集成已关闭", "本正式集成已关闭")
    else:
        transformed = transformed.replace(
            "| `status` | `candidate` |", "| `status` | `accepted` |"
        )
    return transformed


def validate_manifest_and_archives() -> None:
    manifest = yaml.safe_load(
        (RUN_DIR / "INPUT_MANIFEST.yaml").read_text(encoding="utf-8")
    )
    assert manifest["run"]["id"] == "B_INTEGRATION-r01"
    assert manifest["run"]["run_directory"] == "derivation/runs/B_INTEGRATION"
    assert manifest["run"]["repository_commit"] == (
        "f9d6ada7b77d70ce7e5c13fb9b41dc7d485bd0e4"
    )
    assert manifest["expected_outputs"]["files"] == [
        "B_INTEGRATED_MODEL.md",
        "B_TO_C_CONTRACT.md",
    ]

    expected_raw = {
        "B_INTEGRATED_MODEL.md": (
            116527,
            "5ba0e978cba199b99e4390bf4226b579f2e485468ce9a1b1cd29c70e13ecba3a",
        ),
        "B_TO_C_CONTRACT.md": (
            39631,
            "fbf20fd33128490ea59f0edfe0a835ccddf0024ed3ba92da5ff4e82af1b2b847",
        ),
    }
    for item in manifest["received_outputs"]:
        raw = ROOT / item["archived_path"]
        candidate = ROOT / item["normalized_candidate_path"]
        expected_bytes, expected_hash = expected_raw[item["name"]]
        assert raw.is_file() and candidate.is_file()
        assert raw.stat().st_size == item["bytes"] == expected_bytes
        assert sha256(raw) == item["sha256"] == expected_hash
        assert raw.read_bytes() == candidate.read_bytes()
        assert item["byte_identical_candidate_copy"] is True

    response = manifest["raw_response"]
    response_path = ROOT / response["path"]
    assert response_path.stat().st_size == response["bytes"] == 1438
    assert sha256(response_path) == response["sha256"]
    response_text = response_path.read_text(encoding="utf-8")
    assert "B_INTEGRATED_MODEL.md" in response_text
    assert "B_TO_C_CONTRACT.md" in response_text
    assert "c4bfbdf2fbbf7ba5f9e827939d2e1023b23fb8a2a92be0fb5fe59cd0b289c823" in response_text

    candidate_model = (RUN_DIR / "B_INTEGRATED_MODEL_CANDIDATE.md").read_text(
        encoding="utf-8"
    )
    candidate_contract = (RUN_DIR / "B_TO_C_CONTRACT_CANDIDATE.md").read_text(
        encoding="utf-8"
    )
    candidate_block = marked_public_block(candidate_model)
    assert candidate_block == marked_public_block(candidate_contract)
    expected_candidate_block_hash = manifest[
        "candidate_public_contract_marked_block_sha256"
    ]
    assert expected_candidate_block_hash == (
        "c4bfbdf2fbbf7ba5f9e827939d2e1023b23fb8a2a92be0fb5fe59cd0b289c823"
    )
    assert (
        hashlib.sha256(candidate_block.encode("utf-8")).hexdigest()
        == expected_candidate_block_hash
    )

    accepted = manifest["accepted_outputs"]
    assert accepted["status"] == "accepted"
    assert accepted["candidate_to_accepted_repairs_only"] is True
    assert accepted["engineering_context_changed"] is False
    assert accepted["engineering_or_physics_decision_required"] is False
    assert accepted["next_module_started"] is False
    for item in accepted["files"]:
        path = ROOT / item["path"]
        assert path.stat().st_size == item["bytes"]
        assert sha256(path) == item["sha256"]

    final_block = marked_public_block(MODEL.read_text(encoding="utf-8"))
    assert final_block == marked_public_block(CONTRACT.read_text(encoding="utf-8"))
    expected_final_block_hash = accepted[
        "accepted_public_contract_marked_block_sha256"
    ]
    assert expected_final_block_hash == (
        "caa451e79c890723ed1c7c7a969dd461c6273751bc2c8a533e8ccf90e6324201"
    )
    assert hashlib.sha256(final_block.encode("utf-8")).hexdigest() == (
        expected_final_block_hash
    )

    assert (RUN_DIR / "MECHANICAL_FIXES.md").is_file()
    assert (RUN_DIR / "VALIDATION_REPORT.md").is_file()


def validate_candidate_to_accepted_relation() -> None:
    candidate_model = (RUN_DIR / "B_INTEGRATED_MODEL_CANDIDATE.md").read_text(
        encoding="utf-8"
    )
    candidate_contract = (RUN_DIR / "B_TO_C_CONTRACT_CANDIDATE.md").read_text(
        encoding="utf-8"
    )
    final_model = MODEL.read_text(encoding="utf-8")
    final_contract = CONTRACT.read_text(encoding="utf-8")
    assert accepted_transform(candidate_model, model=True) == final_model
    assert accepted_transform(candidate_contract, model=False) == final_contract


def validate_model_and_contract() -> None:
    model = MODEL.read_text(encoding="utf-8")
    contract = CONTRACT.read_text(encoding="utf-8")
    candidate_model = (RUN_DIR / "B_INTEGRATED_MODEL_CANDIDATE.md").read_text(
        encoding="utf-8"
    )
    candidate_contract = (RUN_DIR / "B_TO_C_CONTRACT_CANDIDATE.md").read_text(
        encoding="utf-8"
    )

    assert "| 模型版本 | `1.0.0` |" in model
    assert "| 状态 | `accepted` |" in model
    assert "| `contract_version` | `1.0.0` |" in contract
    assert "| `status` | `accepted` |" in contract
    assert "1.0.0-candidate" not in model
    assert "1.0.0-candidate" not in contract
    assert "| 状态 | `candidate` |" in candidate_model
    assert "| `status` | `candidate` |" in candidate_contract
    assert public_body(model) == public_body(contract)
    assert public_body(candidate_model) == public_body(candidate_contract)

    for section in range(1, 13):
        assert re.search(rf"^## {section}\. ", model, flags=re.MULTILINE)
    for section in range(0, 15):
        assert re.search(rf"^### {section}\. ", public_body(contract), flags=re.MULTILINE)

    required_model_markers = (
        "B1UnitConfiguration",
        "NeedleStaticRecord",
        "SurfaceRealization/A1QueryHandle",
        "\\mathbf c^0_{rc}",
        "\\mathbf b^0_{rc}=\\mathbf c^0_{rc}-L_{rc}\\mathbf a_{rc}",
        "L_r\\sin\\alpha_r=4\\sin80^\\circ",
        "2×5",
        "5×2",
        "G4/G8/G_radius",
        "embedded_constitutive_trial",
        "UX_PZ_BALANCED",
        "PRESCRIBED_XZ_RESIDUAL",
        "r_z=\\mathbf E_Z^{\\mathsf T}\\mathbf F_U-P_z",
        "\\mathcal N_U",
        "BALANCED_DEGENERATE",
        "\\mathbf K_{W,x\\mid P_z}",
        "PRE_EVENT_LIMIT_TRIAL",
        "EVENT_POINT_TRIAL",
        "POST_EVENT_SIDE_TRIAL",
        "FINAL_COMMIT_CANDIDATE",
        "DamageStore",
        "i\\sim_D j",
        "CASCADE_STABILIZED",
        "\\Delta\\mathbf W_i",
        "REENGAGED",
        "standalone continuous unit driver",
        "C embedded unit trial",
        "prepare/commit/rollback",
        "100\\ {\\rm mm}",
        "1\\ {\\rm mm/s}",
        "UnitCapabilityState",
        "full_unit_resolve_callback_requirement",
        "KINEMATIC_MODE_UNSUPPORTED",
        "CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1",
    )
    for marker in required_model_markers:
        assert marker in model, marker

    required_contract_markers = (
        "embedded_array_unit_trial",
        "standalone_continuous_unit_driver",
        "prepare_embedded_unit_commit",
        "commit_global_B_bundle",
        "rollback_embedded_unit_trial",
        "A_on_B",
        "contact_only_wrench",
        "active_normal_actuator",
        "control_reactions",
        "constraints",
        "resultant_central_axis",
        "normal_resultant_graph_handle",
        "suggested_common_increment_fraction",
        "full_unit_resolve_callback_requirement",
        "cross_unit_conflict_signature",
        "global_bundle_manifest",
        "KINEMATIC_MODE_UNSUPPORTED",
        "DAMAGE_CONFLICT_UNRESOLVED",
        "NUMERICAL_NONCONVERGENCE",
        "PHYSICAL_INSTABILITY",
    )
    for marker in required_contract_markers:
        assert marker in contract, marker

    assert "P_i/N" in contract and "不得" in contract
    assert "不得把真实转动投影成 x/z 平移" in contract
    assert "大有限刚度" in contract
    assert "数值残量、积分误差和浮点归约误差必须单列" in contract

    for text in (model, contract):
        assert text.count("```") % 2 == 0
        display_open = re.findall(r"(?<!\\)\\\[", text)
        display_close = re.findall(r"(?<!\\)\\\]", text)
        inline_open = re.findall(r"(?<!\\)\\\(", text)
        inline_close = re.findall(r"(?<!\\)\\\)", text)
        assert len(display_open) == len(display_close)
        assert len(inline_open) == len(inline_close)
        assert re.search(r"\b(?:TODO|TBD|FIXME|PLACEHOLDER)\b", text) is None

    module_context = MODULE_CONTEXT.read_text(encoding="utf-8")
    assert "当前状态：`accepted`" in module_context
    assert "B1：阵列几何、共同运动与柔顺拓扑" in module_context
    assert "B2：恒定法向主动推力下的活动接触集与载荷共享" in module_context
    assert "B3：失效重分配、连续再挂接与单元能力输出" in module_context

    unresolved_topics = (
        "弹簧刚度离散点",
        "单元 \\(P_z\\) 离散点",
        "砂纸目数集合",
        "随机样本数",
        "二元成功阈值/综合评分",
        "高碳钢 E、屈服、断裂",
        "摩擦系数",
        "局部接触刚度",
        "局部强度和损伤演化",
        "回差、位置/角度误差",
        "刚性 graph 数据结构",
        "初始/最小/最大位移步长",
        "峰值持续比例",
        "`rocking=on` 真实转动",
        "C 搜索停止阈值",
        "A/B 实现级自动测试",
    )
    for topic in unresolved_topics:
        assert topic in model, topic

    engineering = ENGINEERING_CONTEXT.read_text(encoding="utf-8")
    assert "UNRESOLVED.REGISTRY.GLOBAL" in engineering
    assert "SCOPE.FIRST_RELEASE.EXCLUSIONS" in engineering


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


def validate_mechanics() -> None:
    # All formal grids retain count, spacing, centroid and transpose identity.
    for nx in range(2, 7):
        for ny in range(2, 7):
            for spacing in (4.0, 5.0, 6.0):
                points = [
                    (
                        ((nx - 1) / 2.0 - row) * spacing,
                        (column - (ny - 1) / 2.0) * spacing,
                    )
                    for row in range(nx)
                    for column in range(ny)
                ]
                assert len(points) == nx * ny == len(set(points))
                assert close(sum(point[0] for point in points), 0.0)
                assert close(sum(point[1] for point in points), 0.0)
                assert close(max(point[0] for point in points) - min(point[0] for point in points), (nx - 1) * spacing)
                assert close(max(point[1] for point in points) - min(point[1] for point in points), (ny - 1) * spacing)

    # Both prescribed gradients satisfy the exact exposed-length compensation.
    target_projection = 4.0 * math.sin(math.radians(80.0))
    for nx in range(2, 7):
        for alpha_head in (50.0, 60.0):
            for row in range(nx):
                fraction = row / (nx - 1)
                alpha = (1.0 - fraction) * 80.0 + fraction * alpha_head
                length = target_projection / math.sin(math.radians(alpha))
                assert close(length * math.sin(math.radians(alpha)), target_projection)

    # Engineering inputs convert exactly once to the public internal units.
    assert close(50.0 / 1000.0, 0.05)
    assert close(100.0 / 1000.0, 0.1)
    assert close(2000.0 / 1000.0, 2.0)

    # Wrench/twist reference transport preserves scalar work.
    force = (1.2, -0.7, 0.5)
    moment_o = (0.3, 0.8, -0.4)
    r_o = (2.0, -1.0, 0.5)
    r_op = (-0.5, 1.5, 2.0)
    dr_o = (0.04, -0.02, 0.01)
    dtheta = (0.005, -0.003, 0.004)
    moment_op = add(moment_o, cross(subtract(r_o, r_op), force))
    dr_op = add(dr_o, cross(dtheta, subtract(r_op, r_o)))
    assert close(
        dot(force, dr_o) + dot(moment_o, dtheta),
        dot(force, dr_op) + dot(moment_op, dtheta),
    )

    # The constant-thrust condensed tangent preserves the normal residual.
    k_zx, k_zz = 0.7, -3.5
    du_x = 0.02
    du_z = -(k_zx / k_zz) * du_x
    assert close(k_zx * du_x + k_zz * du_z, 0.0)
    k_w_x = (2.0, -0.4, 0.8)
    k_w_z = (-0.3, 1.2, 0.5)
    condensed = tuple(
        x - z * k_zx / k_zz for x, z in zip(k_w_x, k_w_z, strict=True)
    )
    direct = tuple(
        x * du_x + z * du_z for x, z in zip(k_w_x, k_w_z, strict=True)
    )
    assert all(
        close(actual, slope * du_x)
        for actual, slope in zip(direct, condensed, strict=True)
    )

    # Positive active thrust does positive work during wallward motion.
    thrust, du_z_wallward = 1.4, -0.03
    assert -thrust * du_z_wallward > 0.0

    # Spring interior and hard-stop branches satisfy the stated complementarity.
    stiffness = 0.8
    delta_interior, lambda_interior = 2.5, 0.0
    force_interior = stiffness * delta_interior + lambda_interior
    assert 0.0 <= delta_interior <= 4.0 and force_interior >= 0.0
    assert close(lambda_interior * (4.0 - delta_interior), 0.0)
    delta_stop, lambda_stop = 4.0, 1.1
    force_stop = stiffness * delta_stop + lambda_stop
    assert force_stop >= 0.0 and close(lambda_stop * (4.0 - delta_stop), 0.0)

    # Event reduction and damage-conflict relation are order independent.
    fractions = [1.0, 0.73, 0.41, 0.88]
    assert min(fractions) == min(reversed(fractions)) == 0.41
    read_a, write_a, kernel_a = {1, 2}, {3}, {3, 4}
    read_b, write_b, kernel_b = {3}, {5}, {4, 5}
    conflict_ab = bool(
        write_a & write_b
        or kernel_a & kernel_b
        or write_a & read_b
        or write_b & read_a
    )
    conflict_ba = bool(
        write_b & write_a
        or kernel_b & kernel_a
        or write_b & read_a
        or write_a & read_b
    )
    assert conflict_ab and conflict_ab == conflict_ba


def main() -> None:
    validate_manifest_and_archives()
    validate_candidate_to_accepted_relation()
    validate_model_and_contract()
    validate_mechanics()
    print("B_INTEGRATION-r01 artifact, contract, and mechanics validation: PASS")


if __name__ == "__main__":
    main()
