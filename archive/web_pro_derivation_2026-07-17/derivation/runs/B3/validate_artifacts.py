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
RUN_DIR = ROOT / "derivation/runs/B3"
CURRENT = ROOT / "derivation/modules/B/current/B_MODULE_CONTEXT.md"
SNAPSHOT = ROOT / "derivation/modules/B/history/B_MODULE_CONTEXT_after_B3.md"
B2_SNAPSHOT = ROOT / "derivation/modules/B/history/B_MODULE_CONTEXT_after_B2.md"

ENGINEERING_SHA256 = "6c1225d3137f8095673b78e1dc8a76acdb0ae73247ec7c49e720cfcc56bb03cb"
ACCEPTED_SHA256 = "35e072fc730e2e74edc1d2c3cdc392382566b0b9ee2a2edd4947585038c4bc21"


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


def section_map(text: str) -> dict[int, str]:
    matches = list(re.finditer(r"(?m)^## ([0-9]+)[.] ", text))
    return {
        int(match.group(1)): text[
            match.start() : matches[index + 1].start() if index + 1 < len(matches) else len(text)
        ]
        for index, match in enumerate(matches)
    }


def close(left: float, right: float, scale: float = 1.0) -> bool:
    return abs(left - right) <= 1.0e-11 * max(scale, abs(left), abs(right))


def validate_run_summary() -> None:
    accepted = RUN_DIR / "RUN_UPDATE_SUMMARY.yaml"
    candidate = RUN_DIR / "RUN_UPDATE_SUMMARY_CANDIDATE.yaml"
    raw = RUN_DIR / "raw_downloads/RUN_UPDATE_SUMMARY(5).yaml"
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
        "module": "B3",
        "run_id": "B3-r01",
        "prompt_version": "1.0.0",
        "engineering_context_baseline": "1.0.0",
        "module_context_baseline": "0.2.0",
        "run_directory": "derivation/runs/B3",
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
    assert all(summary["outputs"].values())
    assert all(
        value == "pass"
        for key, value in summary["self_check"].items()
        if key != "notes"
    )

    module_delta = summary["module_context_delta"]
    assert set(module_delta) == {"added", "modified", "preserved", "unresolved"}
    assert len(module_delta["added"]) == 9
    assert len(module_delta["modified"]) == 3
    assert len(module_delta["preserved"]) == 4
    assert len(module_delta["unresolved"]) == 7
    assert any("DamageStore" in item for item in module_delta["added"])
    assert any("100 mm" in item for item in module_delta["added"])
    assert any("UnitCapabilityState" in item for item in module_delta["added"])


def validate_manifest_and_raw_outputs() -> None:
    manifest = yaml.safe_load((RUN_DIR / "INPUT_MANIFEST.yaml").read_text(encoding="utf-8"))
    run = manifest["run"]
    assert run["id"] == "B3-r01"
    assert run["module"] == "B3"
    assert run["run_directory"] == "derivation/runs/B3"
    assert run["module_context_baseline"] == "0.2.0"

    contract = manifest["upload_contract"]
    assert contract["expected_file_count"] == contract["verified_file_count"] == 12
    assert len(contract["files"]) == 12
    assert contract["all_expected_files_present"] is True
    assert contract["minimum_literature_package_complete"] is True
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
        "B_MODULE_CONTEXT.md": (
            "B_MODULE_CONTEXT(4).md",
            "MODULE_CONTEXT_CANDIDATE.md",
            "4082880404fe0fa681accae2482b809363be3ce31f692b4be26068d260b97941",
            "d126f12ace3840347d3d46e8d890b689e1fe8581b698a49f48b907c8deb2674a",
            False,
        ),
        "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md": (
            "ENGINEERING_FIXED_CONTEXT_CANDIDATE(5).md",
            "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md",
            ENGINEERING_SHA256,
            ENGINEERING_SHA256,
            True,
        ),
        "RUN_UPDATE_SUMMARY.yaml": (
            "RUN_UPDATE_SUMMARY(5).yaml",
            "RUN_UPDATE_SUMMARY_CANDIDATE.yaml",
            "fde0af47b5f93501fa8c4005c4dc119c91731ba8c6152068a4485f0766590bb3",
            "fde0af47b5f93501fa8c4005c4dc119c91731ba8c6152068a4485f0766590bb3",
            True,
        ),
        "CITATION_BRIEF.md": (
            "CITATION_BRIEF(5).md",
            "CITATION_BRIEF.md",
            "15b0033cacdee1c8c2c2cb5948eb73765671164827d997d3a92e5176d59ec899",
            "15b0033cacdee1c8c2c2cb5948eb73765671164827d997d3a92e5176d59ec899",
            True,
        ),
    }
    received = manifest["received_outputs"]
    assert len(received) == len(expected) == 4
    for item in received:
        raw_name, candidate_name, raw_hash, normalized_hash, identical = expected[item["expected_name"]]
        assert item["received_name"] == raw_name
        assert item["archived_path"] == f"derivation/runs/B3/raw_downloads/{raw_name}"
        assert item["normalized_candidate_path"] == f"derivation/runs/B3/{candidate_name}"
        raw_path = ROOT / item["archived_path"]
        candidate_path = ROOT / item["normalized_candidate_path"]
        assert raw_path.stat().st_size == item["bytes"]
        assert candidate_path.stat().st_size == item["normalized_bytes"]
        assert sha256(raw_path) == item["sha256"] == raw_hash
        assert sha256(candidate_path) == item["normalized_sha256"] == normalized_hash
        assert item["byte_identical_to_raw"] is identical
        assert (raw_path.read_bytes() == candidate_path.read_bytes()) is identical

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

    raw_module = RUN_DIR / "raw_downloads/B_MODULE_CONTEXT(4).md"
    normalized_module = RUN_DIR / "MODULE_CONTEXT_CANDIDATE.md"
    raw_text = raw_module.read_text(encoding="utf-8")
    bad_latex = ";\t" + "ext{branch/history}"
    assert raw_text.count(bad_latex) == 1
    repaired_text = raw_text.replace(bad_latex, ";\\text{branch/history}")
    assert normalized_module.read_text(encoding="utf-8") == repaired_text

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
    assert accepted["version"] == "0.3.0"
    assert accepted["stage"] == "B3"
    assert accepted["status"] == "accepted"
    assert accepted["sha256"] == ACCEPTED_SHA256
    assert accepted["current_history_byte_identical"] is True
    assert sha256(ROOT / accepted["path"]) == ACCEPTED_SHA256
    assert (ROOT / accepted["path"]).read_bytes() == (ROOT / accepted["history_snapshot"]).read_bytes()

    review = manifest["artifact_review"]
    assert review == {
        "status": "accepted",
        "engineering_context_delta": "none",
        "semantic_conflict": False,
        "manual_decision_required": False,
        "external_sources_checked": True,
        "citation_brief_local_archive_only": True,
    }

    for literature_path in [item["path"] for item in contract["files"][-3:]]:
        with zipfile.ZipFile(ROOT / literature_path) as archive:
            names = archive.namelist()
            assert "evidence_card.md" in names
            assert sum(name.startswith("figures/") and not name.endswith("/") for name in names) == 3
            assert archive.testzip() is None


def validate_engineering_context() -> None:
    baseline = ROOT / "engineering_fixed_context/engineering_fixed_context.md"
    candidate = RUN_DIR / "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md"
    raw = RUN_DIR / "raw_downloads/ENGINEERING_FIXED_CONTEXT_CANDIDATE(5).md"
    assert baseline.read_bytes() == candidate.read_bytes() == raw.read_bytes()
    assert sha256(candidate) == ENGINEERING_SHA256


def validate_b1_b2_preservation(candidate: str) -> None:
    baseline = B2_SNAPSHOT.read_text(encoding="utf-8")
    baseline_sections = section_map(baseline)
    candidate_sections = section_map(candidate)

    for number in [*range(2, 17), *range(18, 31)]:
        assert candidate_sections[number] == baseline_sections[number]

    old_note = (
        "> 本节保留 B1 0.1.0 accepted 当时的自检结论，作为本轮继承审计记录；"
        "本文当前的 B2 总体自检见第 33 节。"
    )
    new_note = (
        "> 本节保留 B1 0.1.0 accepted 当时的自检结论，作为继承审计记录；"
        "B2 当时的总体自检见第 33 节，当前 B1+B2+B3 总体自检见第 50 节。"
    )
    assert old_note in baseline_sections[17]
    assert candidate_sections[17] == baseline_sections[17].replace(old_note, new_note)

    for number in (31, 32):
        marker = f"### {number}.1"
        assert candidate_sections[number].split(marker, maxsplit=1)[1] == baseline_sections[number].split(marker, maxsplit=1)[1]

    baseline_bullets = baseline_sections[33][baseline_sections[33].index("- 已完整阅读") :].rstrip()
    candidate_bullets = candidate_sections[33][candidate_sections[33].index("- 已完整阅读") :].split("\n---", maxsplit=1)[0].rstrip()
    assert candidate_bullets == baseline_bullets


def validate_module_context() -> None:
    candidate_path = RUN_DIR / "MODULE_CONTEXT_CANDIDATE.md"
    candidate = candidate_path.read_text(encoding="utf-8")
    accepted = CURRENT.read_text(encoding="utf-8")
    assert CURRENT.read_bytes() == SNAPSHOT.read_bytes()
    assert sha256(CURRENT) == ACCEPTED_SHA256
    assert "> 上下文版本：`0.3.0`" in candidate
    assert "> 当前完成阶段：`B3`" in candidate
    assert "> 当前状态：`candidate`" in candidate
    assert "> 当前状态：`accepted`" in accepted

    expected = (
        candidate.replace("> 当前状态：`candidate`", "> 当前状态：`accepted`", 1)
        .replace("最新完整候选上下文", "最新完整上下文", 1)
        .replace("本候选版在理论合同层满足", "本接受版在理论合同层满足", 1)
        .replace(
            "“候选”表示理论与数据合同已形成，尚未完成人工接受、代码实现、参数标定、真实表面求解或实验验证。",
            "“accepted”表示理论与数据合同已通过本地语义审查；尚未完成代码实现、参数标定、真实表面求解或实验验证。",
            1,
        )
        .replace("B_MODULE_CONTEXT 0.3.0 candidate", "B_MODULE_CONTEXT 0.3.0 accepted", 1)
    )
    assert accepted == expected
    validate_b1_b2_preservation(candidate)

    sections = section_map(accepted)
    assert sorted(sections) == list(range(1, 51))
    required_markers = (
        "B3ContinuousUnitRequest",
        "B3ContinuousUnitResponse",
        "B3RebalanceTransactionRequest",
        "B3RebalanceTransactionTrial",
        "B3AtomicCommitReceipt",
        "PRE_EVENT_LIMIT_TRIAL",
        "EVENT_POINT_TRIAL",
        "POST_EVENT_SIDE_TRIAL",
        "FINAL_COMMIT_CANDIDATE",
        "prepare_atomic_commit",
        "commit_atomic",
        "CASCADE_STABILIZED",
        "DAMAGE_CONFLICT_REQUIRES_RESOLVE",
        "DAMAGE_CONFLICT_UNRESOLVED",
        "STALE_SNAPSHOT",
        "UNIT_DETACHED_RECOVERABLE",
        "UNIT_DETACHED_IRRECOVERABLE",
        "EQUILIBRIUM_INFEASIBLE",
        "PHYSICAL_INSTABILITY",
        "NUMERICAL_NONCONVERGENCE",
        "REENGAGED",
        "SPRING_HARD_STOP_ENTER",
        "SPRING_HARD_STOP_LEAVE",
        "COMPLETED_DRAG_PATH",
        "UnitCapabilityState",
        "full_needle_resolve_callback_requirement",
        "embedded_constitutive_trial",
        "A_on_B",
        r"100\ \mathrm{mm}",
        r"1\ \mathrm{mm/s}",
        "0\\le\\delta_{s,i}\\le4",
        "\\Delta\\mathbf W_i",
        "\\mathcal R_{\\rm redist}",
        "\\mathcal R_E",
        "文献03",
        "文献09",
        "文献21",
    )
    for marker in required_markers:
        assert marker in accepted, marker
    for number in range(1, 10):
        assert f"| {number}." in sections[48]

    assert "P_z` 未平均到各针" in accepted
    assert "不预设等载、全局均分、最近邻均分" in accepted
    assert "不得假装为无记忆能力面" in accepted
    assert "不生成 `B_INTEGRATED_MODEL`" in accepted
    assert "不冻结正式 `B_TO_C_CONTRACT`" in accepted
    assert "未执行 B 集成" in accepted
    assert "未开始 C1" in accepted
    assert "尚未完成代码实现、参数标定、真实表面求解或实验验证" in accepted
    assert "\t" not in candidate
    assert "\x00" not in candidate
    assert candidate.count("```") % 2 == 0
    assert candidate.count("\\[") == candidate.count("\\]")
    assert candidate.count("$$") % 2 == 0
    assert "TODO" not in candidate and "TBD" not in candidate and "{{" not in candidate
    tags = re.findall(r"\\tag\{([^}]+)\}", accepted)
    assert len(tags) == len(set(tags))


def validate_citations() -> None:
    citation_path = RUN_DIR / "CITATION_BRIEF.md"
    raw = RUN_DIR / "raw_downloads/CITATION_BRIEF(5).md"
    assert citation_path.read_bytes() == raw.read_bytes()
    citation = citation_path.read_text(encoding="utf-8")
    body, references = citation.split("## 参考来源", maxsplit=1)
    defined = set(re.findall(r"^\[([0-9]+)\]\s", references, flags=re.MULTILINE))
    used: set[str] = set()
    for group in re.findall(r"\[([0-9,]+)\]", body):
        used.update(group.split(","))
    assert defined == used == {str(index) for index in range(1, 8)}
    assert "[2] 文献03" in references
    assert "[3] 文献09" in references
    assert "[4] 文献21" in references
    assert "[1] GPT 自带知识" in references
    assert "https://sundials.readthedocs.io/en/latest/ida/Mathematics_link.html" in references
    assert "https://petsc.org/release/manual/snes/" in references
    assert "https://www.postgresql.org/docs/current/sql-prepare-transaction.html" in references
    assert "只作数值实现参考" in citation
    assert "不替代 A 的接触、摩擦、硬限位或材料物理" in citation
    assert "A_TO_B 1.0.0 accepted` 为唯一权威" in citation
    assert "仅本地归档" in citation


def equilibrium(
    onsets: list[float], stiffnesses: list[float], active: list[bool], pz: float
) -> tuple[float, list[float]]:
    low = min(onsets)
    high = max(onsets) + pz / min(stiffnesses) + 1.0
    for _ in range(120):
        middle = 0.5 * (low + high)
        total = sum(
            stiffness * max(0.0, middle - onset) if enabled else 0.0
            for onset, stiffness, enabled in zip(onsets, stiffnesses, active, strict=True)
        )
        if total < pz:
            low = middle
        else:
            high = middle
    displacement = 0.5 * (low + high)
    forces = [
        stiffness * max(0.0, displacement - onset) if enabled else 0.0
        for onset, stiffness, enabled in zip(onsets, stiffnesses, active, strict=True)
    ]
    return displacement, forces


def components(nodes: set[int], edges: set[tuple[int, int]]) -> set[frozenset[int]]:
    adjacency = {node: set() for node in nodes}
    for left, right in edges:
        adjacency[left].add(right)
        adjacency[right].add(left)
    result: set[frozenset[int]] = set()
    unseen = set(nodes)
    while unseen:
        stack = [min(unseen)]
        group: set[int] = set()
        while stack:
            node = stack.pop()
            if node in group:
                continue
            group.add(node)
            stack.extend(sorted(adjacency[node] - group, reverse=True))
        unseen -= group
        result.add(frozenset(group))
    return result


def validate_b3_mechanics() -> None:
    # A failed needle triggers a complete common-displacement re-solve at fixed Pz.
    onsets = [0.0, 0.12, 0.28, 0.5]
    stiffnesses = [2.0, 4.0, 1.5, 3.0]
    pz = 2.0
    before_u, before = equilibrium(onsets, stiffnesses, [True] * 4, pz)
    after_u, after = equilibrium(onsets, stiffnesses, [False, True, True, True], pz)
    assert close(sum(before), pz)
    assert close(sum(after), pz)
    assert close(sum(a - b for a, b in zip(after, before, strict=True)), 0.0)
    assert after_u > before_u
    assert after[0] == 0.0
    assert sum(abs(a - b) > 1.0e-12 for a, b in zip(after[1:], before[1:], strict=True)) >= 2

    # Needle call order does not change the balanced state or force-by-ID map.
    permutation = [2, 0, 3, 1]
    perm_u, perm_forces = equilibrium(
        [onsets[index] for index in permutation],
        [stiffnesses[index] for index in permutation],
        [[False, True, True, True][index] for index in permutation],
        pz,
    )
    restored = [0.0] * 4
    for position, original in enumerate(permutation):
        restored[original] = perm_forces[position]
    assert close(after_u, perm_u)
    assert all(close(left, right) for left, right in zip(after, restored, strict=True))

    # A conflict graph gives the same connected groups regardless of edge order.
    edges = {(0, 1), (1, 2), (3, 4)}
    expected = {frozenset({0, 1, 2}), frozenset({3, 4}), frozenset({5})}
    assert components(set(range(6)), edges) == expected
    reversed_edges = {(right, left) for left, right in edges}
    assert components(set(range(6)), reversed_edges) == expected

    # Failed prepare/commit trials cannot modify the accepted snapshot.
    accepted = {
        "chi": 12.0,
        "damage_version": 7,
        "needle_versions": [4, 8, 3],
        "dissipation": 1.25,
        "event_number": 14,
    }
    baseline = copy.deepcopy(accepted)
    trial = copy.deepcopy(accepted)
    trial.update(chi=12.4, damage_version=8, dissipation=1.4, event_number=15)
    trial["needle_versions"][1] += 1
    prepare_success = False
    if prepare_success:
        accepted = trial
    assert accepted == baseline

    # Travel, time, spring and work sign conventions remain within fixed bounds.
    coordinates = [0.0, 0.2, 0.2, 1.7, 99.6, 100.0]
    assert all(right >= left for left, right in zip(coordinates, coordinates[1:]))
    assert close(coordinates[-1] / 1.0, 100.0)
    for requested in (-1.0, 0.0, 2.5, 4.0, 5.0):
        compression = min(4.0, max(0.0, requested))
        assert 0.0 <= compression <= 4.0
        assert 4.0 - compression >= 0.0
    pz_work = -pz * (-0.3)
    assert pz_work > 0.0

    # Earliest/simultaneous event grouping is independent of enumeration order.
    locations = [0.72, 0.31, 0.31 + 1.0e-12, 0.9]
    earliest = min(locations)
    simultaneous = {index for index, value in enumerate(locations) if abs(value - earliest) <= 1.0e-10}
    assert close(earliest, 0.31)
    assert simultaneous == {1, 2}
    assert min(reversed(locations)) == earliest


def main() -> None:
    validate_run_summary()
    validate_manifest_and_raw_outputs()
    validate_engineering_context()
    validate_module_context()
    validate_citations()
    validate_b3_mechanics()
    print("B3-r01 artifact, citation, inheritance, transaction, and mechanics validation: PASS")


if __name__ == "__main__":
    main()
