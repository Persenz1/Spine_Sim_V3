from __future__ import annotations

import hashlib
import subprocess
import zipfile
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = ROOT / "derivation/runs/A2/INPUT_MANIFEST.yaml"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_manifest() -> dict:
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("INPUT_MANIFEST.yaml 顶层必须是映射")
    return data


def prompt_upload_paths(prompt: str) -> list[str]:
    paths: list[str] = []
    for line in prompt.splitlines():
        cells = line.split("|")
        if len(cells) < 4 or not cells[1].strip().isdigit():
            continue
        path_cell = cells[2].strip()
        if not (path_cell.startswith("`") and path_cell.endswith("`")):
            raise ValueError(f"上传表路径未使用反引号：{line}")
        paths.append(path_cell[1:-1])
    return paths


def git_blob(commit: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def main() -> int:
    manifest = read_manifest()
    run = manifest["run"]
    contract = manifest["upload_contract"]
    records = contract["files"]

    assert run["id"] == "A2-r01"
    assert run["module"] == "A2"
    assert run["run_directory"] == "derivation/runs/A2"
    assert run["prompt_version"] == "1.0.0"
    assert run["engineering_context_version"] == "1.0.0"
    assert run["module_context_baseline"] == "0.1.0"
    assert run["module_context_status"] == "accepted"
    assert contract["expected_file_count"] == 10
    assert contract["verified_file_count"] == 10
    assert len(records) == 10
    assert contract["all_expected_files_present"] is True
    assert contract["minimum_literature_package_complete"] is True

    paths = [record["path"] for record in records]
    if len(paths) != len(set(paths)):
        raise ValueError("上传清单存在重复路径")

    current_mismatches: list[str] = []
    for record in records:
        path = ROOT / record["path"]
        if not path.is_file():
            raise FileNotFoundError(path)
        content = path.read_bytes()
        if len(content) != record["bytes"] or sha256_bytes(content) != record["sha256"]:
            current_mismatches.append(record["path"])

    prompt_path = ROOT / "derivation/prompts/A/A2_PROMPT.md"
    prompt = prompt_path.read_text(encoding="utf-8")
    table_paths = prompt_upload_paths(prompt)
    if table_paths != paths:
        raise ValueError(f"提示词上传表与 manifest 不一致：{table_paths!r} != {paths!r}")

    archive_record = manifest["prompt_archive"]
    archive_path = ROOT / archive_record["path"]
    archive_content = archive_path.read_bytes()
    if len(archive_content) != archive_record["bytes"]:
        raise ValueError("PROMPT.md 归档字节数不一致")
    if sha256_bytes(archive_content) != archive_record["sha256"]:
        raise ValueError("PROMPT.md 归档哈希不一致")
    if archive_content != prompt_path.read_bytes():
        raise ValueError("PROMPT.md 与正式 A2_PROMPT.md 不一致")

    commit = run["repository_commit"]
    subprocess.run(
        ["git", "rev-parse", "--verify", f"{commit}^{{commit}}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for record in records:
        committed = git_blob(commit, record["path"])
        if len(committed) != record["bytes"]:
            raise ValueError(f"冻结提交中的字节数不一致：{record['path']}")
        if sha256_bytes(committed) != record["sha256"]:
            raise ValueError(f"冻结提交中的 SHA-256 不一致：{record['path']}")

    for literature_path in paths[-2:]:
        with zipfile.ZipFile(ROOT / literature_path) as archive:
            names = archive.namelist()
            if "evidence_card.md" not in names:
                raise ValueError(f"文献包缺少 evidence_card.md：{literature_path}")
            if not any(name.startswith("figures/") for name in names):
                raise ValueError(f"文献包缺少关键图：{literature_path}")
            bad_member = archive.testzip()
            if bad_member is not None:
                raise ValueError(f"文献包 CRC 失败：{literature_path}:{bad_member}")

    required_outputs = (
        "A_MODULE_CONTEXT.md",
        "ENGINEERING_FIXED_CONTEXT_CANDIDATE.md",
        "RUN_UPDATE_SUMMARY.yaml",
        "CITATION_BRIEF.md",
    )
    for output in required_outputs:
        if f"### 10.{required_outputs.index(output) + 1} `{output}`" not in prompt:
            raise ValueError(f"提示词缺少固定输出章节：{output}")

    print("A2-r01 输入校验通过")
    print("- 10 个上传文件的路径和顺序一致")
    print("- 正式提示词与运行归档副本一致")
    print("- 冻结 Git 提交中的全部上传输入与 manifest 一致")
    if current_mismatches:
        print(f"- 当前工作区已有 {len(current_mismatches)} 个滚动输入升级；旧运行从冻结提交复验")
    else:
        print("- 当前工作区上传输入的字节数和 SHA-256 仍与 manifest 一致")
    print("- 文献 01、07 压缩包结构和 CRC 通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
