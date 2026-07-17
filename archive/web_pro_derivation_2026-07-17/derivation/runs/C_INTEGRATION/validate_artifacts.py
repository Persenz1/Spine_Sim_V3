from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "derivation/runs/C_INTEGRATION"
RAW_DOWNLOAD = RUN_DIR / "raw_downloads/C_INTEGRATED_MODEL.md"
CANDIDATE = RUN_DIR / "C_INTEGRATED_MODEL_CANDIDATE.md"
FINAL = ROOT / "derivation/modules/C/final/C_INTEGRATED_MODEL.md"
ENGINEERING_CONTEXT = ROOT / "engineering_fixed_context/engineering_fixed_context.md"
MODULE_CONTEXT = ROOT / "derivation/modules/C/current/C_MODULE_CONTEXT.md"
C3_SNAPSHOT = ROOT / "derivation/modules/C/history/C_MODULE_CONTEXT_after_C3.md"
UPSTREAM_CONTRACT = ROOT / "derivation/contracts/B_TO_C_CONTRACT.md"
OFFICIAL_PROMPT = ROOT / "derivation/prompts/C/C_INTEGRATION_PROMPT.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)


def accepted_transform(candidate: str) -> str:
    transformed = candidate
    replacements = (
        ("> 模型版本：`1.0.0-candidate`  ", "> 模型版本：`1.0.0`  "),
        ("> 状态：`candidate`  ", "> 状态：`accepted`  "),
        (
            "any trial stage\n"
            "  -> UNCERTIFIED_STOPPED\n"
            "  -> NUMERICAL_OR_TRANSACTION_STOPPED",
            "any trial stage\n"
            "  -> {UNCERTIFIED_STOPPED | NUMERICAL_OR_TRANSACTION_STOPPED}",
        ),
        ("  C_model_version = 1.0.0-candidate", "  C_model_version = 1.0.0"),
        (
            "认证等级是累积证据标签，不替代主状态。当前候选至少满足 "
            "`C_THEORY_INTEGRATED`；在 B 1.0 下不满足 "
            "`C_ECCENTRIC_LOAD_CONTRACT_SUPPORTED`，也不满足数值或实验验证等级。",
            "认证等级是累积证据标签，不替代主状态。当前正式模型满足 "
            "`C_THEORY_INTEGRATED`；在 B 1.0 下不满足 "
            "`C_ECCENTRIC_LOAD_CONTRACT_SUPPORTED`，也不满足数值或实验验证等级。",
        ),
        ("## 20. 候选模型完成判据核对", "## 20. 正式模型完成判据核对"),
        ("`C_INTEGRATED_MODEL 1.0.0-candidate`", "`C_INTEGRATED_MODEL 1.0.0`"),
    )
    for old, new in replacements:
        transformed = replace_once(transformed, old, new)
    return transformed


def validate_manifest_and_archives() -> None:
    manifest = yaml.safe_load(
        (RUN_DIR / "INPUT_MANIFEST.yaml").read_text(encoding="utf-8")
    )
    assert manifest["run"]["id"] == "C_INTEGRATION-r01"
    assert manifest["run"]["task"] == "C_INTEGRATION"
    assert manifest["run"]["run_directory"] == "derivation/runs/C_INTEGRATION"
    assert manifest["run"]["repository_commit"] == (
        "0c66baa71a6f14380e9cb3e6cbbbade33c77d5db"
    )
    assert manifest["expected_outputs"]["files"] == ["C_INTEGRATED_MODEL.md"]
    assert manifest["expected_outputs"]["separate_downstream_contract_required"] is False
    assert manifest["expected_outputs"]["submodule_four_file_protocol_forbidden"] is True

    received = manifest["received_outputs"]
    assert len(received) == 1
    item = received[0]
    assert item["name"] == "C_INTEGRATED_MODEL.md"
    assert item["bytes"] == RAW_DOWNLOAD.stat().st_size == 110864
    assert item["sha256"] == sha256(RAW_DOWNLOAD) == (
        "65fc8b40e9dfde0bcf47842bd37535b5f3a56cad6dd31d49510208642e832043"
    )
    assert RAW_DOWNLOAD.read_bytes() == CANDIDATE.read_bytes()
    assert item["byte_identical_candidate_copy"] is True

    raw_response = manifest["raw_response"]
    raw_response_path = ROOT / raw_response["path"]
    assert raw_response["attachment_only_marker"] is True
    assert raw_response_path.stat().st_size == raw_response["bytes"] == 7
    assert sha256(raw_response_path) == raw_response["sha256"] == (
        "0871e777e5359cd18464698fdcc6982c6d14146444d170d477e33f28095a56f8"
    )
    assert raw_response_path.read_text(encoding="utf-8") == "产物\n"

    accepted = manifest["accepted_outputs"]
    assert accepted["status"] == "accepted"
    assert accepted["candidate_to_accepted_repairs_only"] is True
    assert accepted["engineering_context_changed"] is False
    assert accepted["upstream_contract_changed"] is False
    assert accepted["engineering_or_physics_decision_required"] is False
    assert accepted["separate_history_snapshot_required"] is False
    assert accepted["next_module_or_global_integration_started"] is False
    final_item = accepted["files"][0]
    assert final_item["path"] == "derivation/modules/C/final/C_INTEGRATED_MODEL.md"
    assert FINAL.stat().st_size == final_item["bytes"] == 110832
    assert sha256(FINAL) == final_item["sha256"] == (
        "8439835281ed61344de106082f8e6826c9a993d8767fb7845633510cdfe5b589"
    )

    assert (RUN_DIR / "MECHANICAL_FIXES.md").is_file()
    assert (RUN_DIR / "VALIDATION_REPORT.md").is_file()
    assert sorted(path.name for path in RAW_DOWNLOAD.parent.iterdir()) == [
        "C_INTEGRATED_MODEL.md"
    ]
    assert sorted(path.name for path in FINAL.parent.iterdir()) == [
        "C_INTEGRATED_MODEL.md"
    ]
    forbidden_names = (
        "RUN_UPDATE_SUMMARY.yaml",
        "CITATION_BRIEF.md",
        "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md",
        "C_TO_SYSTEM_CONTRACT.md",
    )
    for name in forbidden_names:
        assert not (RUN_DIR / name).exists()
        assert not (FINAL.parent / name).exists()


def validate_frozen_authorities() -> None:
    assert sha256(ENGINEERING_CONTEXT) == (
        "6c1225d3137f8095673b78e1dc8a76acdb0ae73247ec7c49e720cfcc56bb03cb"
    )
    assert sha256(MODULE_CONTEXT) == (
        "810fc26972652086403181f97221503e08e267485c6bd31fe1ea44b5af9a8f66"
    )
    assert MODULE_CONTEXT.read_bytes() == C3_SNAPSHOT.read_bytes()
    assert sha256(UPSTREAM_CONTRACT) == (
        "fc9dd4504f1c6b0650361bbf289fdfdfc18ae1a01834887a3bf40bc09478c894"
    )
    assert sha256(OFFICIAL_PROMPT) == (
        "21b7722090921ad08185ff0fe23a37e9ac60a117ddc6b7bda2dbd756b34ef3f1"
    )
    assert OFFICIAL_PROMPT.read_bytes() == (RUN_DIR / "PROMPT.md").read_bytes()


def validate_candidate_to_accepted_relation() -> None:
    candidate = CANDIDATE.read_text(encoding="utf-8")
    final = FINAL.read_text(encoding="utf-8")
    assert accepted_transform(candidate) == final
    assert "> 模型版本：`1.0.0-candidate`" in candidate
    assert "> 状态：`candidate`" in candidate
    assert "> 模型版本：`1.0.0`" in final
    assert "> 状态：`accepted`" in final
    assert "C_model_version = 1.0.0-candidate" in candidate
    assert "C_model_version = 1.0.0" in final
    assert (
        "UNCERTIFIED_STOPPED\n  -> NUMERICAL_OR_TRANSACTION_STOPPED" in candidate
    )
    assert (
        "{UNCERTIFIED_STOPPED | NUMERICAL_OR_TRANSACTION_STOPPED}" in final
    )


def validate_structure_and_format() -> None:
    final = FINAL.read_text(encoding="utf-8")
    for section in range(0, 22):
        assert re.search(rf"^## {section}\. ", final, flags=re.MULTILINE), section
    lines = final.splitlines()
    assert sum(line == "\\[" for line in lines) == sum(
        line == "\\]" for line in lines
    )
    assert final.count("\\(") == final.count("\\)")
    fence_lines = [line for line in final.splitlines() if line.startswith("```")]
    assert len(fence_lines) % 2 == 0
    assert not re.search(r"\b(?:TODO|TBD|FIXME)\b", final, flags=re.IGNORECASE)

    algorithm = re.findall(r"^\s*(\d+)\. [A-Z][A-Z0-9_]+$", final, flags=re.MULTILINE)
    assert [int(item) for item in algorithm] == list(range(1, 22))


def validate_submodule_inheritance_and_integration() -> None:
    final = FINAL.read_text(encoding="utf-8")
    required_markers = (
        # C1: synchronous search, preload acceptance and stop gates
        "C1PreloadState",
        "u_{x_1}=u_{x_2}=u_{x_3}=u_{x_4}=s",
        "Q_s^{\\rm drive}",
        "G_{\\rm stop}",
        "C_PRELOAD_ACCEPTED_LOCKED",
        "s_{\\max}",
        "STOP_AT_SEARCH_LIMIT_UNQUALIFIED",
        # C2: pose, full wrench equilibrium, stability and coverage audit
        "C2AcceptedState",
        "\\Delta\\boldsymbol\\xi_{A_i}^{i}",
        "\\mathbf W_i^{G,C}=\\mathbf J_i^{\\mathsf T}",
        "C_PHYSICAL_EQUILIBRIUM_INFEASIBLE",
        "C_PHYSICAL_INSTABILITY",
        "rocking=off",
        "rocking=on",
        # C3: degradation, rebalance, peak and capacity semantics
        "C3AcceptedState",
        "C3MaximumCapacityResult",
        "CMaximumCapacityResult",
        "FIRST_NEEDLE_FAILURE",
        "FIRST_UNIT_SIGNIFICANT_DEGRADATION",
        "GLOBAL_REACTION_PEAK_CANDIDATE",
        "F_{\\rm crit}",
        "C_DETACHMENT_RECOVERABLE",
        "C_DETACHMENT_IRRECOVERABLE",
        # Cross-stage state, damage, event and transaction closure
        "CAcceptedState",
        "all_status_codes",
        "CTransactionBundle",
        "DamageStore fixed point",
        "SIMULTANEOUS_EVENT_GROUPING",
        "SAME_POSITION_CASCADE",
        "ATOMIC_COMMIT_OR_ROLLBACK",
        "prepare_tokens",
        "global_commit_token",
        "idempotency",
    )
    for marker in required_markers:
        assert marker in final, marker

    assert final.index("4. MOTION_CONTRACT_COVERAGE_AUDIT") < final.index(
        "6. FOUR_SIDE_EFFECT_FREE_B_TRIALS"
    )
    assert "events/work/curve/peak advanced = false" in final
    assert "事件后四单元重分配" in final
    assert "不均分、不用固定权重" in final


def validate_symbols_units_work_and_deduplication() -> None:
    final = FINAL.read_text(encoding="utf-8")
    required = (
        "A_on_B",
        "CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1",
        "N·mm",
        "N/mm",
        "wrench–twist 功不变",
        "ideal_generalized_force_work",
        "certified_relative_actuator_work",
        "unavailable_reason",
        "dW_{P_i}^{\\rm ideal}",
        "dW_{P_i}^{\\rm certified}",
        "rocking 是允许刚体自由度，不是弹性元件",
        "\\eta_i",
        "C 不建第二套接触",
        "C 不加等效梁",
        "C 不均分、不用固定权重",
        "不相加、不取最大、不按顺序覆盖",
    )
    for marker in required:
        assert marker in final, marker

    load_table = re.search(
        r"### 6\.2 载荷所有权\n(.*?)\n### 6\.3", final, flags=re.DOTALL
    )
    assert load_table
    assert "B 返回 contact-only wrench" in load_table.group(1)
    assert "\\(P_i\\) 作为 B 控制输入" in load_table.group(1)
    assert "加载器" in load_table.group(1)
    assert "未授权模式乘子" in load_table.group(1)


def validate_contract_boundary_and_interfaces() -> None:
    final = FINAL.read_text(encoding="utf-8")
    required = (
        "B_TO_C 1.0.0 accepted",
        "C_CONTRACT_EXTENSION_REQUIRED",
        "\\bigcap_{i=1}^{4}\\mathcal V_i",
        "\\operatorname{span}\\{\\mathbf E_Z\\}",
        "四单元均需要局部 y 运动",
        "B 2.x 最小扩展要求",
        "本节是版本化扩展要求，不是已接受合同",
        "CSystemRequest",
        "CSystemResponse",
        "CCertificationLevel",
        "C_ECCENTRIC_LOAD_CONTRACT_EXTENSION_REQUIRED",
        "C_ECCENTRIC_LOAD_CONTRACT_SUPPORTED",
        "面向实验的公共输出与对齐",
        "时间为 `unavailable`",
    )
    for marker in required:
        assert marker in final, marker

    gap_section = re.search(
        r"### 12\.5 统一安全拒绝\n(.*?)\n## 13\.", final, flags=re.DOTALL
    )
    assert gap_section
    for marker in (
        "保留 last-valid accepted state",
        "不调用降阶替代",
        "不推进",
        "\\(F_{\\rm crit}=0\\)",
        "物理无平衡",
        "物理失稳",
        "不可恢复脱附",
    ):
        assert marker in gap_section.group(1), marker


def validate_unresolved_and_scope_boundaries() -> None:
    final = FINAL.read_text(encoding="utf-8")
    required = (
        "UNRESOLVED.C1.STOP_THRESHOLD",
        "UNRESOLVED.C1.MAX_SEARCH_DISTANCE",
        "UNRESOLVED.NUMERICS.EVENT_STEPS",
        "UNRESOLVED.STOCHASTIC.SAMPLE_COUNT",
        "UNRESOLVED.VALIDATION.ERROR_TOLERANCE",
        "UNRESOLVED.METRIC.BINARY_SUCCESS",
        "UNRESOLVED.METRIC.COMPOSITE_SCORE",
        "不得自动沿用 A/B 单刺/阵列直线拖拽的",
        "不修改 A/B 正式模型",
        "不定义二元抓附成功",
        "未开始全局 A/B/C 集成",
    )
    for marker in required:
        assert marker in final, marker


def dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def mat_vec(matrix: tuple[tuple[float, ...], ...], vector: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(dot(row, vector) for row in matrix)


def transpose(matrix: tuple[tuple[float, ...], ...]) -> tuple[tuple[float, ...], ...]:
    return tuple(tuple(matrix[row][col] for row in range(len(matrix))) for col in range(len(matrix[0])))


def determinant3(matrix: tuple[tuple[float, ...], ...]) -> float:
    a, b, c = matrix
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )


def add(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(x + y for x, y in zip(a, b, strict=True))


def scale(value: float, vector: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(value * item for item in vector)


def close(a: float, b: float, tol: float = 1.0e-12) -> None:
    assert math.isclose(a, b, rel_tol=tol, abs_tol=tol), (a, b)


def validate_mathematical_regressions() -> None:
    ex = (1.0, 0.0, 0.0)
    ey = (0.0, 1.0, 0.0)
    ez = (0.0, 0.0, 1.0)
    unit_axes = (
        (ex, ey),
        (scale(-1.0, ex), scale(-1.0, ey)),
        (ey, scale(-1.0, ex)),
        (scale(-1.0, ey), ex),
    )
    rotations = tuple(
        tuple(tuple(axis[row] for axis in (axis_x, axis_y, ez)) for row in range(3))
        for axis_x, axis_y in unit_axes
    )
    for rotation in rotations:
        close(determinant3(rotation), 1.0)
        columns = transpose(rotation)
        for index, column in enumerate(columns):
            close(dot(column, column), 1.0)
            for other in range(index):
                close(dot(column, columns[other]), 0.0)

    load_offset = scale(50.0, ez)
    close(dot(cross(load_offset, ex), ey), 50.0)
    direction_45 = scale(1.0 / math.sqrt(2.0), add(ex, ey))
    moment_45 = cross(load_offset, direction_45)
    close(moment_45[0], -50.0 / math.sqrt(2.0))
    close(moment_45[1], 50.0 / math.sqrt(2.0))

    for displacement, expected_x, expected_y in (
        (ex, (1.0, -1.0, 0.0, 0.0), (0.0, 0.0, -1.0, 1.0)),
        (
            direction_45,
            tuple(value / math.sqrt(2.0) for value in (1.0, -1.0, 1.0, -1.0)),
            tuple(value / math.sqrt(2.0) for value in (1.0, -1.0, -1.0, 1.0)),
        ),
    ):
        for index, (axis_x, axis_y) in enumerate(unit_axes):
            close(dot(axis_x, displacement), expected_x[index])
            close(dot(axis_y, displacement), expected_y[index])

    points = (
        scale(-40.0, ex),
        scale(40.0, ex),
        scale(-40.0, ey),
        scale(40.0, ey),
    )
    rocking = ((0.0, 1.0, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 0.0))
    expected_z = (40.0, -40.0, -40.0, 40.0)
    for theta, point, expected in zip(rocking, points, expected_z, strict=True):
        close(cross(theta, point)[2], expected)

    rotation = rotations[2]
    rotation_t = transpose(rotation)
    r = (-40.0, 3.0, 5.0)
    local_force = (1.2, -0.7, 2.1)
    local_moment = (3.0, 4.0, -2.0)
    v_c = (0.2, -0.5, 0.8)
    omega = (0.01, -0.02, 0.03)
    global_force = mat_vec(rotation, local_force)
    global_moment = add(mat_vec(rotation, local_moment), cross(r, global_force))
    local_v = mat_vec(rotation_t, add(v_c, cross(omega, r)))
    local_omega = mat_vec(rotation_t, omega)
    local_power = dot(local_force, local_v) + dot(local_moment, local_omega)
    global_power = dot(global_force, v_c) + dot(global_moment, omega)
    close(local_power, global_power)


def main() -> int:
    validate_manifest_and_archives()
    validate_frozen_authorities()
    validate_candidate_to_accepted_relation()
    validate_structure_and_format()
    validate_submodule_inheritance_and_integration()
    validate_symbols_units_work_and_deduplication()
    validate_contract_boundary_and_interfaces()
    validate_unresolved_and_scope_boundaries()
    validate_mathematical_regressions()
    print("C_INTEGRATION-r01 产物校验通过")
    print("- 网页原件与候选副本逐字节一致，原始响应已归档")
    print("- 候选到正式版只有身份转正和无歧义异常分支符号修复")
    print("- C1、C2、C3 状态、方程、事件、损伤、稳定性和能力机理已继承")
    print("- 坐标、wrench、单位、功方向、柔顺/载荷/失效去重和数学回归通过")
    print("- 事件优先级、共享损伤 fixed point、21 步算法和原子事务闭合")
    print("- B 1.0 运动覆盖缺口、零历史推进安全拒绝和 B 2.x 未接受边界已保留")
    print("- 工程事实、C 上下文、B_TO_C 合同和正式提示词未改动")
    print("- 输出严格为 C_INTEGRATED_MODEL.md，未启动下一模块或全局集成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
