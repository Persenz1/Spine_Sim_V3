from __future__ import annotations

import hashlib
import math
from pathlib import Path

import yaml


RUN_DIR = Path(__file__).resolve().parent
ROOT = RUN_DIR.parents[2]
CANDIDATE = RUN_DIR / "SYSTEM_INTEGRATED_MODEL_CANDIDATE.md"
RAW = RUN_DIR / "raw_downloads/SYSTEM_INTEGRATED_MODEL.md"
FINAL = ROOT / "derivation/system/SYSTEM_INTEGRATED_MODEL.md"
MANIFEST = RUN_DIR / "INPUT_MANIFEST.yaml"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def accepted_transform(candidate: str) -> str:
    transformed = candidate
    transformed = transformed.replace(
        "> 规范状态：系统理论与接口集成完成；代码、数值和实验未认证  ",
        "> 状态：`accepted`（系统理论与接口集成完成；代码、数值和实验未认证）  ",
        1,
    )
    for old, new in (
        ("`engineering_fixed_context(13).md`", "`engineering_fixed_context.md`"),
        ("`A_INTEGRATED_MODEL(1).md`", "`A_INTEGRATED_MODEL.md`"),
        ("`B_INTEGRATED_MODEL(1).md`", "`B_INTEGRATED_MODEL.md`"),
        ("`C_INTEGRATED_MODEL(1).md`", "`C_INTEGRATED_MODEL.md`"),
    ):
        transformed = transformed.replace(old, new, 1)

    standalone_anchor = """```text
StandaloneValidationRecord:
"""
    standalone_schema = """```text
StandaloneValidationRequest:
  profile = A_SINGLE_SPINE | B_ARRAY_UNIT
  independent_run_id
  immutable_surface_geometry_parameter_bindings
  standalone_accepted_state_handle_optional
  independent_DamageStore_branch
  path_control_and_requested_raw_outputs
  deterministic_replay_request
```

```text
StandaloneValidationRecord:
"""
    transformed = transformed.replace(standalone_anchor, standalone_schema, 1)
    transformed = transformed.replace(
        "全部针 `A_on_B` 运输到 `O_A` 后的 contact-only 和",
        "全部针 `A_on_B` 运输到 `O_A` 后的 contact-only 净和",
        1,
    )

    transport_anchor = """}
\\]

整爪 contact-only wrench 为
"""
    transport_clarification = """}
\\]

其中 `S_i` 是 B 响应显式声明的源表达坐标；在当前静态安装的 B 1.0 局部坐标响应中，`S_i=\\mathcal F_{A_i}` 且 `\\mathbf R_{G S_i}=\\mathbf R_{Gi}`。若响应声明其他源坐标，必须使用同一版本的显式变换，不能靠名称推断。

整爪 contact-only wrench 为
"""
    transformed = transformed.replace(transport_anchor, transport_clarification, 1)

    transformed = transformed.replace(
        "以下伪代码规定调用顺序和事务边界，不规定编程语言。",
        "以下伪代码规定调用顺序和事务边界，不规定编程语言。`SYSTEM_EXECUTE` 是内部调度门面，其输入是互斥并集 `ExecutionRequest = SystemRequest | StandaloneValidationRequest`：第 14.1 节的公开 `SystemRequest` 只能选择 `C_SYSTEM_MAIN_PATH`，A/B standalone 必须使用第 5.2 节的 `StandaloneValidationRequest`，且不得携带或推进 C 的 `SystemAcceptedState`。",
        1,
    )
    transformed = transformed.replace(
        "FUNCTION SYSTEM_EXECUTE(request, accepted_or_validation_state):",
        "FUNCTION SYSTEM_EXECUTE(execution_request, accepted_or_validation_state):",
        1,
    )
    transformed = transformed.replace(
        "  0. SELECT_EXECUTION_PROFILE\n     - profile ∈",
        "  0. SELECT_EXECUTION_PROFILE\n     - 按请求 schema 令 request=execution_request，并拒绝跨 schema 字段。\n     - profile ∈",
        1,
    )

    terminal_anchor = """| `TRANSACTION_ERROR` | prepare/commit/持久化失败 | 非物理结论 | 否 | rollback/幂等重试 |

## 21. 全局最早事件、同时组和级联
"""
    terminal_clarification = """| `TRANSACTION_ERROR` | prepare/commit/持久化失败 | 非物理结论 | 否 | rollback/幂等重试 |

本表中的“终止状态可提交”只允许提交满足第 47 节全部 accepted 不变量的最后有效状态、合法事件点/边界状态及其终止证据账本；不可行平衡 trial、失稳一侧 trial 或其他不满足 accepted 不变量的候选本身绝不得提交为物理状态。若终止只在越界一侧得到证明，保留 last-valid accepted state，并以独立 terminal evidence/ledger 记录终止分类。

## 21. 全局最早事件、同时组和级联
"""
    transformed = transformed.replace(terminal_anchor, terminal_clarification, 1)
    return transformed


def dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def validate_power_transport() -> None:
    force = (1.7, -0.4, 2.2)
    moment_at_source = (0.3, 1.1, -0.8)
    r_source_from_target = (12.0, -7.0, 3.0)
    v_target = (-0.2, 0.5, 0.1)
    omega = (0.01, -0.03, 0.02)
    v_source = tuple(
        value + increment
        for value, increment in zip(v_target, cross(omega, r_source_from_target), strict=True)
    )
    moment_at_target = tuple(
        value + increment
        for value, increment in zip(moment_at_source, cross(r_source_from_target, force), strict=True)
    )
    source_power = dot(force, v_source) + dot(moment_at_source, omega)
    target_power = dot(force, v_target) + dot(moment_at_target, omega)
    assert math.isclose(source_power, target_power, rel_tol=1e-12, abs_tol=1e-12)


def main() -> None:
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    raw = RAW.read_bytes()
    candidate = CANDIDATE.read_bytes()
    final_bytes = FINAL.read_bytes()
    assert raw == candidate

    received = manifest["received_outputs"][0]
    assert received["name"] == "SYSTEM_INTEGRATED_MODEL.md"
    assert len(raw) == received["bytes"]
    assert sha256(raw) == received["sha256"]
    assert received["byte_identical_candidate_copy"] is True
    assert (RUN_DIR / "RAW_RESPONSE.md").read_text(encoding="utf-8") == "产物\n"

    accepted = manifest["accepted_outputs"]
    assert accepted["status"] == "accepted"
    assert accepted["candidate_to_accepted_repairs_only"] is True
    assert accepted["engineering_context_changed"] is False
    assert accepted["A_B_C_models_or_contracts_changed"] is False
    assert accepted["engineering_or_physics_decision_required"] is False
    item = accepted["files"][0]
    assert item["path"] == "derivation/system/SYSTEM_INTEGRATED_MODEL.md"
    assert len(final_bytes) == item["bytes"]
    assert sha256(final_bytes) == item["sha256"]

    candidate_text = candidate.decode("utf-8")
    final = final_bytes.decode("utf-8")
    assert accepted_transform(candidate_text) == final
    assert "> 状态：`accepted`" in final[:500]
    assert "engineering_fixed_context(13).md" not in final
    assert "INTEGRATED_MODEL(1).md" not in final

    required = (
        "# 第一篇：系统对象、范围与闭合等级",
        "# 第二篇：完整依赖链与所有权",
        "# 第三篇：全局状态、对象和变量字典",
        "# 第四篇：坐标、参考点、单位、作用—反作用与功",
        "# 第五篇：模块接口与全局 schema",
        "# 第六篇：统一阶段、残量/graph 与单步算法",
        "# 第七篇：事件、优先级、终止和恢复",
        "# 第八篇：物理去重审计与实验原始输出合同",
        "# 第九篇：全局验证矩阵",
        "# 第十篇：未决问题、风险与实现交接",
        "# 第十一篇：系统闭合结论与强制自检",
        "A_TO_B 1.0.0 accepted",
        "B_TO_C 1.0.0 accepted",
        "C_CONTRACT_EXTENSION_REQUIRED",
        "C_ECCENTRIC_CONTRACT_SUPPORTED = false",
        "accepted_delta_P_increment = 0",
        "DamageStore_advanced = false",
        "F_crit_confirmed = false",
        "ExecutionRequest = SystemRequest | StandaloneValidationRequest",
        "terminal evidence/ledger",
        "## 37. 最小实现验收包",
        "## 38. 未决问题登记",
        "## 48. 输出前强制自检结果",
        "## 49. 最终规范结论",
    )
    for token in required:
        assert token in final, token

    fence_open = False
    for line in final.splitlines():
        if line.startswith("```"):
            fence_open = not fence_open
    assert fence_open is False
    assert final.count("\\[") == final.count("\\]")
    assert final.count("$$") % 2 == 0
    for forbidden in ("RUN_UPDATE_SUMMARY", "CITATION_BRIEF", "ENGINEERING_FACT_CANDIDATES"):
        assert forbidden not in final

    validate_power_transport()
    print("SYSTEM_INTEGRATION artifact validation: pass")


if __name__ == "__main__":
    main()
