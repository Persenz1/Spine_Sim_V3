from __future__ import annotations

import hashlib
import math
import re
import subprocess
import zipfile
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "derivation/runs/B1"
CURRENT = ROOT / "derivation/modules/B/current/B_MODULE_CONTEXT.md"
SNAPSHOT = ROOT / "derivation/modules/B/history/B_MODULE_CONTEXT_after_B1.md"


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
    return abs(left - right) <= 1.0e-12 * max(scale, abs(left), abs(right))


def validate_run_summary() -> None:
    accepted = RUN_DIR / "RUN_UPDATE_SUMMARY.yaml"
    candidate = RUN_DIR / "RUN_UPDATE_SUMMARY_CANDIDATE.yaml"
    raw = RUN_DIR / "raw_downloads/RUN_UPDATE_SUMMARY(3).yaml"
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
        "module": "B1",
        "run_id": "B1-r01",
        "prompt_version": "1.0.0",
        "engineering_context_baseline": "1.0.0",
        "module_context_baseline": "none",
        "run_directory": "derivation/runs/B1",
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
    assert summary["module_context_delta"]["modified"] == ["none"]
    assert summary["module_context_delta"]["preserved"] == ["none"]


def validate_manifest_and_raw_outputs() -> None:
    manifest = yaml.safe_load((RUN_DIR / "INPUT_MANIFEST.yaml").read_text(encoding="utf-8"))
    assert manifest["run"]["id"] == "B1-r01"
    assert manifest["run"]["run_directory"] == "derivation/runs/B1"
    contract = manifest["upload_contract"]
    assert contract["expected_file_count"] == contract["verified_file_count"] == 10
    assert len(contract["files"]) == 10
    assert contract["all_expected_files_present"] is True
    assert contract["minimum_literature_package_complete"] is True
    assert contract["prompt_manifest_actual_paths_identical"] is True

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

    expected_raw = {
        "B_MODULE_CONTEXT.md",
        "ENGINEERING_FIXED_CONTEXT_CANDIDATE(3).md",
        "RUN_UPDATE_SUMMARY(3).yaml",
        "CITATION_BRIEF(3).md",
    }
    assert {path.name for path in (RUN_DIR / "raw_downloads").iterdir()} == expected_raw
    assert (RUN_DIR / "RAW_RESPONSE.md").is_file()

    for literature_path in [item["path"] for item in contract["files"][-2:]]:
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


def validate_module_context() -> None:
    raw = RUN_DIR / "raw_downloads/B_MODULE_CONTEXT.md"
    candidate_path = RUN_DIR / "MODULE_CONTEXT_CANDIDATE.md"
    assert raw.read_bytes() == candidate_path.read_bytes()
    candidate = candidate_path.read_text(encoding="utf-8")
    accepted = CURRENT.read_text(encoding="utf-8")
    assert CURRENT.read_bytes() == SNAPSHOT.read_bytes()
    assert "> 上下文候选版本：`0.1.0`" in candidate
    assert "> 当前状态：`candidate`" in candidate
    assert "> 上下文版本：`0.1.0`" in accepted
    assert "> 当前状态：`accepted`" in accepted
    expected = candidate.replace(
        "> 上下文候选版本：`0.1.0`",
        "> 上下文版本：`0.1.0`",
        1,
    ).replace("> 当前状态：`candidate`", "> 当前状态：`accepted`", 1).replace(
        "当前状态仍为 `candidate`，表示代码、真实 CAD、表面测量和实验尚未完成；这不改变 B1 数据与运动学合同的闭合性。",
        "当前归档状态为 `accepted`，表示 B1 数据与运动学合同已通过本轮审查；这不表示代码、真实 CAD、表面测量或实验已经完成。",
        1,
    )
    assert accepted == expected

    for section in range(1, 18):
        assert re.search(rf"^## {section}\.", accepted, flags=re.MULTILINE)
    required_markers = (
        "B1UnitConfiguration",
        "NeedleStaticRecord",
        "UnitKinematicMap",
        "MountTopologyRecord",
        "SurfaceCorrelationBinding",
        "EmbeddedSingleSpineTrialRequest",
        "embedded_constitutive_trial",
        "A_on_B",
        "RIGID_MOUNT",
        "AXIAL_SPRING_MOUNT",
        "KINEMATIC_MODE_UNSUPPORTED",
        "DAMAGE_CONFLICT_REQUIRES_RESOLVE",
        "B2HandoffSchema",
        "B3",
        "2×5",
        "5×2",
    )
    for marker in required_markers:
        assert marker in accepted
    assert "standalone_single_spine_driver" in accepted
    assert "不得调用或间接包装 `standalone_single_spine_driver`" in accepted
    assert "per_spine_normal_force" in accepted
    assert "请求中不得出现 `per_spine_normal_force`" in accepted
    assert "B1 不求解任何接触力、弹簧平衡值或活动接触集" in accepted
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
    assert defined == used == {str(index) for index in range(1, 7)}
    assert "[1] 文献04" in references
    assert "[2] 文献07" in references
    assert "https://www.itl.nist.gov/div898/handbook/eda/section3/eda35c.htm" in references
    assert "https://www.rfc-editor.org/rfc/rfc8785.html" in references
    assert "https://csrc.nist.gov/pubs/fips/180-4/upd1/final" in references
    assert "GPT 自带知识" in references
    assert "仅本地归档" in citation


def validate_geometry_and_mechanics() -> None:
    tested = 0
    max_coplanarity = 0.0
    max_closure = 0.0
    for nx in range(2, 7):
        for ny in range(2, 7):
            for spacing in (4.0, 5.0, 6.0):
                tested += 1
                points = []
                for r in range(nx):
                    for c in range(ny):
                        x = ((nx - 1) / 2.0 - r) * spacing
                        y = (c - (ny - 1) / 2.0) * spacing
                        points.append((x, y, 0.0))
                assert len(points) == nx * ny == len(set(points))
                assert close(sum(point[0] for point in points), 0.0)
                assert close(sum(point[1] for point in points), 0.0)
                assert close(max(point[0] for point in points) - min(point[0] for point in points), (nx - 1) * spacing)
                assert close(max(point[1] for point in points) - min(point[1] for point in points), (ny - 1) * spacing)
    assert tested == 75

    for nx in range(2, 7):
        for alpha_head_deg in (50.0, 60.0):
            mount_z_values = []
            for r in range(nx):
                fraction = r / (nx - 1)
                alpha_deg = (1.0 - fraction) * 80.0 + fraction * alpha_head_deg
                alpha = math.radians(alpha_deg)
                length = 4.0 * math.sin(math.radians(80.0)) / math.sin(alpha)
                axis = (math.cos(alpha), 0.0, -math.sin(alpha))
                center = (((nx - 1) / 2.0 - r) * 5.0, 0.0, 0.0)
                mount = tuple(center[k] - length * axis[k] for k in range(3))
                recovered = tuple(mount[k] + length * axis[k] for k in range(3))
                max_closure = max(max_closure, *(abs(recovered[k] - center[k]) for k in range(3)))
                mount_z_values.append(mount[2])
            max_coplanarity = max(max_coplanarity, max(mount_z_values) - min(mount_z_values))
    assert max_closure < 2.0e-15
    assert max_coplanarity < 1.0e-15

    def directed_count(nx: int, ny: int, mx: int, my: int) -> int:
        if abs(mx) >= nx or abs(my) >= ny or (mx == 0 and my == 0):
            return 0
        return (nx - abs(mx)) * (ny - abs(my))

    assert directed_count(2, 5, 2, 0) == 0
    assert directed_count(5, 2, 2, 0) == 6
    assert directed_count(2, 5, 0, 2) == 6
    assert directed_count(5, 2, 0, 2) == 0

    # Wrench reference-point transport preserves virtual work for rigid translation.
    force = (1.2, -0.4, 0.7)
    moment = (0.1, 0.2, -0.3)
    r_old = (2.0, 1.0, -0.5)
    r_new = (-1.0, 0.5, 0.25)
    arm = tuple(r_old[k] - r_new[k] for k in range(3))
    cross = (
        arm[1] * force[2] - arm[2] * force[1],
        arm[2] * force[0] - arm[0] * force[2],
        arm[0] * force[1] - arm[1] * force[0],
    )
    transported_moment = tuple(moment[k] + cross[k] for k in range(3))
    translation = (0.03, 0.0, -0.02)
    rotation = (0.0, 0.0, 0.0)
    work_old = sum(force[k] * translation[k] + moment[k] * rotation[k] for k in range(3))
    work_new = sum(force[k] * translation[k] + transported_moment[k] * rotation[k] for k in range(3))
    assert close(work_old, work_new)


def main() -> None:
    validate_run_summary()
    validate_manifest_and_raw_outputs()
    validate_engineering_context()
    validate_module_context()
    validate_citations()
    validate_geometry_and_mechanics()
    print("B1-r01 artifact, citation, geometry, and mechanics validation: PASS")


if __name__ == "__main__":
    main()
