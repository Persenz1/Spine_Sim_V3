from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import yaml


RUN_DIR = Path(__file__).resolve().parent
ROOT = RUN_DIR.parents[2]
MANIFEST = RUN_DIR / "INPUT_MANIFEST.yaml"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def marker_block(text: str, begin: str, end: str) -> str:
    start = text.index(begin)
    finish = text.index(end, start) + len(end)
    return text[start:finish]


def git_blob(commit: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def main() -> None:
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    run = manifest["run"]
    assert run["id"] == "SYSTEM_INTEGRATION-r01"
    assert run["task"] == "SYSTEM_INTEGRATION"
    assert run["run_directory"] == "derivation/runs/SYSTEM_INTEGRATION"
    assert run["prompt_version"] == "1.0.0"
    assert run["workflow_version"] == "1.3.4"
    assert run["engineering_context_version"] == "1.0.0"

    prompt_archive = manifest["prompt_archive"]
    archived_prompt = ROOT / prompt_archive["path"]
    formal_prompt = ROOT / "derivation/prompts/SYSTEM_INTEGRATION_PROMPT.md"
    assert archived_prompt.read_bytes() == formal_prompt.read_bytes()
    assert len(archived_prompt.read_bytes()) == prompt_archive["bytes"]
    assert sha256(archived_prompt.read_bytes()) == prompt_archive["sha256"]
    assert prompt_archive["matches_uploaded_prompt"] is True

    upload = manifest["upload_contract"]
    assert upload["expected_file_count"] == 5
    assert upload["verified_file_count"] == 5
    assert upload["no_additional_evidence_required"] is True
    assert [item["upload_order"] for item in upload["files"]] == [1, 2, 3, 4, 5]

    commit = run["repository_commit"]
    for item in upload["files"]:
        path = ROOT / item["path"]
        data = path.read_bytes()
        assert len(data) == item["bytes"], item["path"]
        assert sha256(data) == item["sha256"], item["path"]
        assert git_blob(commit, item["path"]) == data, item["path"]

    models = manifest["module_acceptance"]["models"]
    assert manifest["module_acceptance"]["all_modules_formally_integrated_and_accepted"] is True
    assert [item["module"] for item in models] == ["A", "B", "C"]
    for item in models:
        assert item["model_version"] == "1.0.0"
        assert item["status"] == "accepted"
        text = (ROOT / item["path"]).read_text(encoding="utf-8")
        assert "accepted" in text[:2000]

    a_begin = "<!-- BEGIN A_TO_B_PUBLIC_CONTRACT -->"
    a_end = "<!-- END A_TO_B_PUBLIC_CONTRACT -->"
    b_begin = "<!-- BEGIN B_TO_C_PUBLIC_CONTRACT -->"
    b_end = "<!-- END B_TO_C_PUBLIC_CONTRACT -->"
    a_standalone = (ROOT / "derivation/contracts/A_TO_B_CONTRACT.md").read_text(encoding="utf-8")
    a_integrated = (ROOT / "derivation/modules/A/final/A_INTEGRATED_MODEL.md").read_text(encoding="utf-8")
    b_standalone = (ROOT / "derivation/contracts/B_TO_C_CONTRACT.md").read_text(encoding="utf-8")
    b_integrated = (ROOT / "derivation/modules/B/final/B_INTEGRATED_MODEL.md").read_text(encoding="utf-8")
    assert marker_block(a_standalone, a_begin, a_end) == marker_block(a_integrated, a_begin, a_end)
    assert marker_block(b_standalone, b_begin, b_end) == marker_block(b_integrated, b_begin, b_end)

    expected = manifest["expected_outputs"]
    assert expected["file_count"] == 1
    assert expected["files"] == ["SYSTEM_INTEGRATED_MODEL.md"]
    assert expected["submodule_four_file_protocol_applies"] is False
    assert expected["require_engineering_fact_candidates"] is False
    assert expected["require_run_update_summary"] is False
    assert expected["require_citation_brief"] is False

    print("SYSTEM_INTEGRATION input validation: pass")


if __name__ == "__main__":
    main()
