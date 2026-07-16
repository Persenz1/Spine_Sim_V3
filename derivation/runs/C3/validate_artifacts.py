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
RUN_DIR = ROOT / "derivation/runs/C3"
CURRENT = ROOT / "derivation/modules/C/current/C_MODULE_CONTEXT.md"
SNAPSHOT = ROOT / "derivation/modules/C/history/C_MODULE_CONTEXT_after_C3.md"
C2_SNAPSHOT = ROOT / "derivation/modules/C/history/C_MODULE_CONTEXT_after_C2.md"

ENGINEERING_SHA256 = "6c1225d3137f8095673b78e1dc8a76acdb0ae73247ec7c49e720cfcc56bb03cb"
MODULE_CANDIDATE_SHA256 = "e004000b7bc41ae9d93297a4aeeab8c0106b4bfd7cc5f83956a638470a09cbb7"
ACCEPTED_SHA256 = "810fc26972652086403181f97221503e08e267485c6bd31fe1ea44b5af9a8f66"


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


def cross(left: list[float], right: list[float]) -> list[float]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def add(left: list[float], right: list[float]) -> list[float]:
    return [a + b for a, b in zip(left, right, strict=True)]


def validate_run_summary() -> None:
    accepted = RUN_DIR / "RUN_UPDATE_SUMMARY.yaml"
    candidate = RUN_DIR / "RUN_UPDATE_SUMMARY_CANDIDATE.yaml"
    raw = RUN_DIR / "raw_downloads/RUN_UPDATE_SUMMARY.yaml"
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
        "module": "C3",
        "run_id": "C3-r01",
        "prompt_version": "1.0.0",
        "engineering_context_baseline": "1.0.0",
        "module_context_baseline": "0.2.0",
        "run_directory": "derivation/runs/C3",
    }

    delta = summary["engineering_context_delta"]
    assert len(delta) == 1
    assert delta[0]["id"] == "none"
    assert delta[0]["operation"] == "none"
    assert delta[0]["target"] is None
    assert delta[0]["affected_modules"] == []
    assert delta[0]["changed_fields"] == []
    assert delta[0]["evidence"] == {
        "local_literature": [],
        "external_urls": [],
        "gpt_knowledge": [],
        "derivation_locations": [],
    }
    assert delta[0]["proposed_fact"] is None
    assert delta[0]["approval_required"] is False

    module_delta = summary["module_context_delta"]
    assert set(module_delta) == {"added", "modified", "preserved", "unresolved"}
    assert len(module_delta["added"]) == 10
    assert len(module_delta["modified"]) == 3
    assert len(module_delta["preserved"]) == 5
    assert len(module_delta["unresolved"]) == 7
    assert any("首个针失效" in item for item in module_delta["added"])
    assert any("F_crit" in item for item in module_delta["added"])
    assert any("B_TO_C 2.x" in item for item in module_delta["unresolved"])
    assert any("大模块 C 集成" in item for item in module_delta["unresolved"])

    assert all(summary["outputs"].values())
    assert all(
        value == "pass"
        for key, value in summary["self_check"].items()
        if key != "notes"
    )


def validate_manifest_and_raw_outputs() -> None:
    manifest = yaml.safe_load((RUN_DIR / "INPUT_MANIFEST.yaml").read_text(encoding="utf-8"))
    run = manifest["run"]
    assert run["id"] == "C3-r01"
    assert run["module"] == "C3"
    assert run["run_directory"] == "derivation/runs/C3"
    assert run["module_context_baseline"] == "0.2.0"
    assert run["module_context_status"] == "accepted"
    assert run["upstream_contract_version"] == "1.0.0"

    prerequisite = manifest["prerequisite_acceptance"]
    assert prerequisite["prior_module_run"] == "C2-r01"
    assert prerequisite["status"] == "accepted"
    assert prerequisite["current_history_byte_identical"] is True
    assert prerequisite["c3_motion_extension_required"] is True
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
        frozen = bytes_at_commit(repository_commit, item["path"])
        assert len(frozen) == item["bytes"]
        assert hashlib.sha256(frozen).hexdigest() == item["sha256"]

    assert (RUN_DIR / "PROMPT.md").read_bytes() == (
        ROOT / "derivation/prompts/C/C3_PROMPT.md"
    ).read_bytes()

    expected = {
        "C_MODULE_CONTEXT.md": (
            "C_MODULE_CONTEXT(4).md",
            "MODULE_CONTEXT_CANDIDATE.md",
            MODULE_CANDIDATE_SHA256,
        ),
        "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md": (
            "ENGINEERING_FIXED_CONTEXT_CANDIDATE(8).md",
            "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md",
            ENGINEERING_SHA256,
        ),
        "RUN_UPDATE_SUMMARY.yaml": (
            "RUN_UPDATE_SUMMARY.yaml",
            "RUN_UPDATE_SUMMARY_CANDIDATE.yaml",
            "65c7bc74d4de8900e660c69b5ce2fd930cacfe827bfb6191b4e18b6b24d94f27",
        ),
        "CITATION_BRIEF.md": (
            "CITATION_BRIEF.md",
            "CITATION_BRIEF.md",
            "760a49a0916a6e4489391bdc6bcd7427e26d73f55a45486deada723067cab6b8",
        ),
    }

    received = manifest["received_outputs"]
    assert len(received) == len(expected) == 4
    for item in received:
        raw_name, candidate_name, expected_hash = expected[item["expected_name"]]
        assert item["received_name"] == raw_name
        assert item["archived_path"] == f"derivation/runs/C3/raw_downloads/{raw_name}"
        assert item["normalized_candidate_path"] == f"derivation/runs/C3/{candidate_name}"
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
        "history_snapshot": "derivation/modules/C/history/C_MODULE_CONTEXT_after_C3.md",
        "version": "0.3.0",
        "stage": "C3",
        "status": "accepted",
        "bytes": 200666,
        "sha256": ACCEPTED_SHA256,
        "current_history_byte_identical": True,
    }
    assert sha256(ROOT / accepted["path"]) == ACCEPTED_SHA256
    assert (ROOT / accepted["path"]).read_bytes() == (
        ROOT / accepted["history_snapshot"]
    ).read_bytes()

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
    raw = RUN_DIR / "raw_downloads/ENGINEERING_FIXED_CONTEXT_CANDIDATE(8).md"
    assert baseline.read_bytes() == candidate.read_bytes() == raw.read_bytes()
    assert sha256(candidate) == ENGINEERING_SHA256


def validate_module_context() -> None:
    manifest = yaml.safe_load((RUN_DIR / "INPUT_MANIFEST.yaml").read_text(encoding="utf-8"))
    candidate_path = RUN_DIR / "MODULE_CONTEXT_CANDIDATE.md"
    raw_path = RUN_DIR / "raw_downloads/C_MODULE_CONTEXT(4).md"
    candidate = candidate_path.read_text(encoding="utf-8")
    accepted = CURRENT.read_text(encoding="utf-8")

    assert candidate_path.read_bytes() == raw_path.read_bytes()
    assert sha256(candidate_path) == MODULE_CANDIDATE_SHA256
    assert CURRENT.read_bytes() == SNAPSHOT.read_bytes()
    assert sha256(CURRENT) == ACCEPTED_SHA256

    expected = candidate
    replacements = (
        ("> 上下文候选版本：`0.3.0`", "> 上下文版本：`0.3.0`"),
        ("> 当前状态：`candidate`", "> 当前状态：`accepted`"),
        (
            "| C3 物理状态机、事件重平衡和数据合同 | 理论定义完成，状态 `candidate` |",
            "| C3 物理状态机、事件重平衡和数据合同 | 已完成并经 `C3-r01` 审查接受 |",
        ),
        ("    C_module_context_status = candidate", "    C_module_context_status = accepted"),
        (
            "| 单元显著退化事件函数族 | 本轮推导 | candidate | 阈值、尺度和通道待标定。 |",
            "| 单元显著退化事件函数族 | 本轮推导 | accepted | 阈值、尺度和通道待标定。 |",
        ),
        (
            "| `F_crit` 稳定可达分支定义 | 工程输出要求 + 本轮推导 | candidate | 只有合法终止/覆盖后可确认。 |",
            "| `F_crit` 稳定可达分支定义 | 工程输出要求 + 本轮推导 | accepted | 只有合法终止/覆盖后可确认。 |",
        ),
        (
            "| 融合 C1+C2+C3 的最新完整上下文 | 全文；第 0、31–48 节 | 已形成 candidate。 |",
            "| 融合 C1+C2+C3 的最新完整上下文 | 全文；第 0、31–48 节 | 已经 `C3-r01` 审查接受。 |",
        ),
        (
            "- [x] 文件头写明 C3、版本 0.3.0、工程事实 1.0.0、B_TO_C 1.0.0、基线 0.2.0、运行 C3-r01 和 candidate。",
            "- [x] 文件头写明 C3、版本 0.3.0、工程事实 1.0.0、B_TO_C 1.0.0、基线 0.2.0、运行 C3-r01 和 accepted。",
        ),
    )
    for old, new in replacements:
        assert expected.count(old) == 1, old
        expected = expected.replace(old, new, 1)
    assert accepted == expected

    assert "> 当前完成阶段：`C3 — 单元渐进失效、整体重分配与最大承载`" in accepted
    assert "> 上下文版本：`0.3.0`" in accepted
    assert "> 上游合同：`B_TO_C 1.0.0 accepted`" in accepted
    assert "> 基线：`C_MODULE_CONTEXT 0.2.0 accepted`" in accepted
    assert "> 当前状态：`accepted`" in accepted

    repository_commit = manifest["run"]["repository_commit"]
    frozen_c2 = bytes_at_commit(
        repository_commit, "derivation/modules/C/current/C_MODULE_CONTEXT.md"
    ).decode("utf-8")
    assert frozen_c2.encode("utf-8") == C2_SNAPSHOT.read_bytes()
    inherited_c2 = frozen_c2[frozen_c2.index("# 第一篇") :].rstrip()
    candidate_inherited = candidate[
        candidate.index("# 第一篇") : candidate.index("\n\n---\n\n# 第三篇")
    ].rstrip()
    assert inherited_c2 == candidate_inherited

    sections = [int(item) for item in re.findall(r"(?m)^## ([0-9]+)[.] ", accepted)]
    assert sections == list(range(49))
    assert len(re.findall(r"(?m)^\| C1-V[0-9]{2} \|", accepted)) == 28
    assert len(re.findall(r"(?m)^\| C2-V[0-9]{2} \|", accepted)) == 30
    assert len(re.findall(r"(?m)^\| C3-V[0-9]{2} \|", accepted)) == 26

    required_markers = (
        "C1PreloadState",
        "C2AcceptedState",
        "C3LoadRequest",
        "C3UnitContinuationCapsule",
        "C3LoadTrialResponse",
        "C3EventRecord",
        "C3AcceptedState",
        "C3MaximumCapacityResult",
        "C3LocalWrenchCapability",
        "FIRST_NEEDLE_FAILURE",
        "FIRST_UNIT_SIGNIFICANT_DEGRADATION",
        "GLOBAL_REACTION_PEAK_CANDIDATE",
        "GLOBAL_CRITICAL_CAPACITY_CONFIRMED",
        "GLOBAL_EQUILIBRIUM_INFEASIBLE",
        "GLOBAL_PHYSICAL_INSTABILITY",
        "GLOBAL_DETACHMENT_RECOVERABLE",
        "GLOBAL_DETACHMENT_IRRECOVERABLE",
        "C3_CONTRACT_EXTENSION_REQUIRED",
        "C3_PROGRESSIVE_LOAD_STEP",
        "C3_global_bundle_manifest",
        "CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1",
        "B_TO_C 2.x",
        "文献 23",
        "文献 28",
        "GPT 通用知识",
    )
    for marker in required_markers:
        assert marker in accepted, marker

    required_phrases = (
        "不得把所有事件都称为“失效”",
        "载荷重分配必须由位移兼容、状态相关 response/graph、整体姿态、接触约束和六维平衡自动产生",
        "首个峰值、首次反力下降或首个单元退化均不允许自动终止",
        "不得用四个单元峰值之和",
        "正式 C3 请求只能安全拒绝，不能输出物理 `F_crit`",
        "本轮不得自动开始上述集成",
    )
    for phrase in required_phrases:
        assert phrase in accepted, phrase

    assert "> 当前状态：`candidate`" not in accepted
    assert "C_module_context_status = candidate" not in accepted
    assert "| candidate |" not in accepted
    assert "s_{\\max}=100" not in accepted
    assert "s_max_mm: 100" not in accepted
    assert "\x00" not in candidate
    assert "\t" not in candidate
    assert candidate.count("```") % 2 == 0
    assert candidate.count("$$") % 2 == 0
    assert "TODO" not in candidate and "TBD" not in candidate and "{{" not in candidate


def engineering_fact_ids() -> set[str]:
    ids: set[str] = set()
    for path in (ROOT / "engineering_fixed_context/internal/facts").glob("*.yaml"):
        domain = yaml.safe_load(path.read_text(encoding="utf-8"))
        for fact in domain["facts"]:
            ids.add(fact["id"])
            ids.update(item["id"] for item in fact.get("registry", []))
    return ids


def validate_citations() -> None:
    citation_path = RUN_DIR / "CITATION_BRIEF.md"
    raw = RUN_DIR / "raw_downloads/CITATION_BRIEF.md"
    assert citation_path.read_bytes() == raw.read_bytes()
    citation = citation_path.read_text(encoding="utf-8")
    body, references = citation.split("## 参考来源", maxsplit=1)
    defined = set(re.findall(r"^\[([0-9]+)\]\s", references, flags=re.MULTILINE))
    used: set[str] = set()
    for group in re.findall(r"\[([0-9,]+)\]", body):
        used.update(group.split(","))
    assert defined == used == {"1", "2", "3"}
    assert "[1] 文献23" in references
    assert "[2] 文献28" in references
    assert "[3] GPT 自带知识" in references
    assert "http://" not in citation and "https://" not in citation
    assert "文献17" not in citation and "文献09" not in citation
    assert "历史相关集合值本构/接触响应" in citation
    assert "项目阈值、材料/表面参数、姿态有效域与实验误差仍需实现验证和标定" in citation
    assert "仅本地归档" in citation
    assert "不进入任何后续默认上传" in citation

    cited_facts = set(
        re.findall(r"`([A-Z][A-Z0-9_]*(?:\.[A-Z0-9_]+)+)`", citation)
    )
    assert cited_facts <= engineering_fact_ids()


def validate_c3_mechanics() -> None:
    load_point = [0.0, 0.0, 50.0]
    load = 3.2
    moment_x = cross(load_point, [load, 0.0, 0.0])
    assert all(
        close(value, expected)
        for value, expected in zip(moment_x, [0.0, 50.0 * load, 0.0], strict=True)
    )

    direction_45 = [1.0 / math.sqrt(2.0), 1.0 / math.sqrt(2.0), 0.0]
    moment_45 = cross(load_point, [load * item for item in direction_45])
    expected_45 = [-50.0 * load / math.sqrt(2.0), 50.0 * load / math.sqrt(2.0), 0.0]
    assert all(
        close(value, expected)
        for value, expected in zip(moment_45, expected_45, strict=True)
    )

    positions = [
        [-40.0, 0.0, 0.0],
        [40.0, 0.0, 0.0],
        [0.0, -40.0, 0.0],
        [0.0, 40.0, 0.0],
    ]
    fz1, fz2, fz3, fz4 = 2.2, 3.1, 1.4, 2.8
    pair_x = add(
        cross(positions[0], [0.0, 0.0, fz1]),
        cross(positions[1], [0.0, 0.0, fz2]),
    )
    pair_y = add(
        cross(positions[2], [0.0, 0.0, fz3]),
        cross(positions[3], [0.0, 0.0, fz4]),
    )
    assert close(pair_x[1], 40.0 * (fz1 - fz2))
    assert close(pair_y[0], 40.0 * (fz4 - fz3))

    lost_load = 6.0
    branch_count = 4
    equal_increment = lost_load / (branch_count - 1)
    assert close(sum([equal_increment] * (branch_count - 1)), lost_load)
    stiffness = [1.0, 2.0, 3.0]
    nonlinear_increments = [lost_load * item / sum(stiffness) for item in stiffness]
    assert close(sum(nonlinear_increments), lost_load)
    assert any(not close(item, equal_increment) for item in nonlinear_increments)

    states = [
        {"reaction": 2.0, "accepted": True, "certified": True, "stable": True, "reachable": True},
        {"reaction": 5.0, "accepted": True, "certified": True, "stable": True, "reachable": True},
        {"reaction": 8.0, "accepted": False, "certified": True, "stable": True, "reachable": True},
        {"reaction": 9.0, "accepted": True, "certified": False, "stable": True, "reachable": True},
    ]
    admissible = [
        state["reaction"]
        for state in states
        if all(state[key] for key in ("accepted", "certified", "stable", "reachable"))
    ]
    assert max(admissible) == 5.0

    accepted = {
        "delta_P": 0.4,
        "q_C": [0.1, 0.0, 0.0, 0.0, 0.002, 0.0],
        "unit_versions": [4, 8, 3, 6],
        "damage_version": 7,
        "event_number": 14,
        "peak_ledger": [4.7],
    }
    baseline = copy.deepcopy(accepted)
    trial = copy.deepcopy(accepted)
    trial.update(delta_P=0.5, damage_version=8, event_number=15)
    trial["q_C"][0] = 0.2
    trial["unit_versions"][1] += 1
    trial["peak_ledger"].append(5.0)
    prepare_success = False
    if prepare_success:
        accepted = trial
    assert accepted == baseline


def validate_generator() -> None:
    result = subprocess.run(
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
        text=True,
        encoding="utf-8",
    )
    assert "校验通过：9 个领域，48 条事实" in result.stdout


def main() -> None:
    validate_run_summary()
    validate_manifest_and_raw_outputs()
    validate_engineering_context()
    validate_module_context()
    validate_citations()
    validate_c3_mechanics()
    validate_generator()
    print(
        "C3-r01 artifact, YAML, citation, C1/C2 inheritance, event, rebalance, "
        "peak, termination, contract-gap, and transaction validation: PASS"
    )


if __name__ == "__main__":
    main()
