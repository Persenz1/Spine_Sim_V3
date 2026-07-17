from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml


CONTEXT_DIR = Path(__file__).resolve().parent
ROOT = CONTEXT_DIR.parent.parent
MANIFEST_PATH = CONTEXT_DIR / "manifest.yaml"
SCHEMA_PATH = CONTEXT_DIR / "schema.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: YAML 顶层必须是映射")
    return data


def require_fields(data: dict[str, Any], fields: list[str], location: str) -> None:
    missing = [field for field in fields if field not in data]
    if missing:
        raise ValueError(f"{location}: 缺少字段 {', '.join(missing)}")


def validate_and_load() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = load_yaml(MANIFEST_PATH)
    schema = load_yaml(SCHEMA_PATH)
    require_fields(manifest, ["context", "status_labels", "scope_labels", "fact_files"], str(MANIFEST_PATH))

    allowed_statuses = set(schema["allowed_statuses"])
    allowed_scopes = set(schema["allowed_scopes"])
    id_pattern = re.compile(schema["id_rules"]["pattern"])
    domain_required = schema["required_domain_fields"]
    fact_required = schema["required_fact_fields"]
    known_ids: set[str] = set()
    known_domain_ids: set[str] = set()
    known_domain_orders: set[int] = set()
    covered_baseline_sections: set[str] = set()
    domains: list[dict[str, Any]] = []

    for relative_path in manifest["fact_files"]:
        path = CONTEXT_DIR / relative_path
        domain = load_yaml(path)
        require_fields(domain, domain_required, str(path))
        if not isinstance(domain["facts"], list):
            raise ValueError(f"{path}: facts 必须是列表")
        if domain["id"] in known_domain_ids:
            raise ValueError(f"{path}: 重复领域 ID {domain['id']}")
        known_domain_ids.add(domain["id"])
        if domain["order"] in known_domain_orders:
            raise ValueError(f"{path}: 重复领域顺序 {domain['order']}")
        known_domain_orders.add(domain["order"])
        known_fact_orders: set[int] = set()

        for index, fact in enumerate(domain["facts"], start=1):
            location = f"{path}:facts[{index}]"
            if not isinstance(fact, dict):
                raise ValueError(f"{location}: 事实必须是映射")
            require_fields(fact, fact_required, location)

            if fact["order"] in known_fact_orders:
                raise ValueError(f"{location}: 领域内重复事实顺序 {fact['order']}")
            known_fact_orders.add(fact["order"])

            fact_id = fact["id"]
            if not isinstance(fact_id, str) or not id_pattern.fullmatch(fact_id):
                raise ValueError(f"{location}: 非法事实 ID {fact_id!r}")
            if fact_id in known_ids:
                raise ValueError(f"{location}: 重复事实 ID {fact_id}")
            known_ids.add(fact_id)

            if fact["status"] not in allowed_statuses:
                raise ValueError(f"{location}: 非法状态 {fact['status']!r}")
            if not isinstance(fact["scopes"], list) or not fact["scopes"]:
                raise ValueError(f"{location}: scopes 必须是非空列表")
            unknown_scopes = set(fact["scopes"]) - allowed_scopes
            if unknown_scopes:
                raise ValueError(f"{location}: 非法作用域 {sorted(unknown_scopes)}")
            if any(isinstance(item, bool) for item in _walk_values(fact.get("value"))):
                raise ValueError(f"{location}: value 中不允许隐式布尔值；模型开关请显式写为引号字符串")

            for key in ("definitions", "equations", "requirements", "constraints", "notes", "registry"):
                if key in fact and not isinstance(fact[key], list):
                    raise ValueError(f"{location}: {key} 必须是列表")
            for item_index, item in enumerate(fact.get("definitions", []), start=1):
                if not isinstance(item, dict):
                    raise ValueError(f"{location}.definitions[{item_index}]: 必须是映射")
                require_fields(item, ["term", "meaning"], f"{location}.definitions[{item_index}]")
            for item_index, item in enumerate(fact.get("equations", []), start=1):
                if not isinstance(item, dict):
                    raise ValueError(f"{location}.equations[{item_index}]: 必须是映射")
                require_fields(item, ["latex"], f"{location}.equations[{item_index}]")
            for item_index, item in enumerate(fact.get("registry", []), start=1):
                registry_location = f"{location}.registry[{item_index}]"
                if not isinstance(item, dict):
                    raise ValueError(f"{registry_location}: 必须是映射")
                require_fields(item, ["id", "topic"], registry_location)
                registry_id = item["id"]
                if not isinstance(registry_id, str) or not id_pattern.fullmatch(registry_id):
                    raise ValueError(f"{registry_location}: 非法登记 ID {registry_id!r}")
                if registry_id in known_ids:
                    raise ValueError(f"{registry_location}: 重复事实或登记 ID {registry_id}")
                known_ids.add(registry_id)

            provenance = fact["provenance"]
            if not isinstance(provenance, dict):
                raise ValueError(f"{location}: provenance 必须是映射")
            require_fields(provenance, ["type", "source", "section"], f"{location}.provenance")
            source_path = ROOT / provenance["source"]
            if not source_path.exists():
                raise ValueError(f"{location}: 来源文件不存在 {provenance['source']}")
            if provenance["source"] == manifest["context"]["source_document"]:
                covered_baseline_sections.add(str(provenance["section"]))

        domains.append(domain)

    expected_sections = set(str(item) for item in manifest.get("baseline_sections", []))
    missing_sections = expected_sections - covered_baseline_sections
    if missing_sections:
        raise ValueError(f"基线章节未覆盖：{sorted(missing_sections)}")

    domains.sort(key=lambda item: item["order"])
    return manifest, domains


def _walk_values(value: Any):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_values(item)
    else:
        yield value


def scalar(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "是" if value else "否"
    return str(value)


def render_value(value: Any, unit: str | None) -> list[str]:
    suffix = f" {unit}" if unit else ""
    if isinstance(value, list):
        return [f"- 取值：{', '.join(scalar(item) for item in value)}{suffix}"]
    if isinstance(value, dict):
        lines = ["- 取值："]
        for key, item in value.items():
            if isinstance(item, list):
                rendered = ", ".join(scalar(entry) for entry in item)
            else:
                rendered = scalar(item)
            lines.append(f"  - {key}：{rendered}{suffix}")
        return lines
    return [f"- 取值：{scalar(value)}{suffix}"]


def render_fact(fact: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    status = manifest["status_labels"][fact["status"]]
    scopes = "、".join(manifest["scope_labels"][scope] for scope in fact["scopes"])
    lines = [f"### {fact['id']} — {fact['title']}", "", f"- 状态：{status}", f"- 适用范围：{scopes}"]
    if "symbol" in fact:
        lines.append(f"- 符号：${fact['symbol']}$")
    if "value" in fact:
        lines.extend(render_value(fact["value"], fact.get("unit")))
    lines.extend(["", fact["summary"].strip(), ""])

    if fact.get("definitions"):
        lines.extend(["定义：", "", "| 名称 | 含义 |", "|---|---|"])
        for item in fact["definitions"]:
            lines.append(f"| {item['term']} | {item['meaning']} |")
        lines.append("")

    if fact.get("equations"):
        lines.extend(["工程表达：", ""])
        for equation in fact["equations"]:
            if equation.get("label"):
                lines.append(f"- {equation['label']}")
                lines.append("")
            lines.extend(["$$", equation["latex"].strip(), "$$", ""])
            if equation.get("description"):
                lines.extend([equation["description"].strip(), ""])

    for label, key in (("必须满足", "requirements"), ("约束", "constraints"), ("说明", "notes")):
        if fact.get(key):
            lines.extend([f"{label}：", ""])
            lines.extend(f"- {item}" for item in fact[key])
            lines.append("")

    if fact.get("registry"):
        lines.extend(["登记项：", "", "| 编号 | 项目 | 作用域 | 说明 |", "|---|---|---|---|"])
        for item in fact["registry"]:
            lines.append(
                f"| {item['id']} | {item['topic']} | {item.get('scope', '—')} | {item.get('note', '—')} |"
            )
        lines.append("")

    source = fact["provenance"]
    lines.extend(
        [
            f"> 来源：{source['source']}，第 {source['section']} 节；来源类型：{source['type']}。",
            "",
        ]
    )
    return lines


def render_document(manifest: dict[str, Any], domains: list[dict[str, Any]]) -> str:
    context = manifest["context"]
    lines = [
        f"# {context['title']}",
        "",
        f"> 版本：`{context['version']}`",
        f"> 状态：`{context['status']}`",
        "> 本文件由 `engineering_fixed_context/internal/facts/*.yaml` 单向生成，是供人工审阅和网页端上传的完整工程事实视图。",
        "> 它只定义工程事实、边界、工况、接口要求和未决参数；具体机理实现属于 `RESULT` 与 `MODULE_CONTEXT`。",
        "",
        "## 阅读与修改规则",
        "",
        context["description"],
        "",
        "- “已固定”表示当前正式基线，后续理论或代码不得静默改写；允许经显式说明、差异审查和人工确认后升级版本。",
        "- “范围/集合已固定”不代表其内部离散点或标定值已经全部确定。",
        "- “接口能力已固定”只约束程序必须提供的能力，不预先指定机理算法。",
        "- “尚未固定”表示必须保留为参数或待标定项，禁止擅自硬编码唯一值。",
        "- 修改结构化事实后运行 `conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --write` 重新生成本文件。",
        "",
        "## 状态图例",
        "",
        "| 状态 | 含义 |",
        "|---|---|",
    ]
    for key, label in manifest["status_labels"].items():
        lines.append(f"| `{key}` | {label} |")
    lines.extend(["", "## 领域导航", ""])
    for domain in domains:
        lines.append(f"- [{domain['order']}. {domain['title']}](#domain-{domain['order']})")
    lines.append("")

    for domain in domains:
        lines.extend([f'<a id="domain-{domain["order"]}"></a>', "", f"## {domain['order']}. {domain['title']}", ""])
        if domain.get("description"):
            lines.extend([domain["description"].strip(), ""])
        for fact in sorted(domain["facts"], key=lambda item: item["order"]):
            lines.extend(render_fact(fact, manifest))

    lines.extend(
        [
            "## 结构化源与生成信息",
            "",
            f"- 事实库标识：`{context['id']}`",
            f"- 结构化源目录：`engineering_fixed_context/internal/facts/`",
            f"- 原始基线：`{context['source_document']}`",
            "- 正式修改流程：提出语义变更说明 → 审查差异 → 人工确认 → 更新 YAML → 校验并重新生成。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="校验并生成工程固定上下文")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="校验 YAML 和已生成 Markdown")
    mode.add_argument("--write", action="store_true", help="写入 engineering_fixed_context.md")
    args = parser.parse_args()

    manifest, domains = validate_and_load()
    rendered = render_document(manifest, domains)
    output_path = ROOT / manifest["context"]["generated_document"]

    if args.write:
        output_path.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"已生成 {output_path}")
        return 0

    if not output_path.exists():
        raise SystemExit(f"缺少生成文件：{output_path}")
    current = output_path.read_text(encoding="utf-8")
    if current != rendered:
        raise SystemExit("engineering_fixed_context.md 与 YAML 事实库不一致，请运行 --write")
    print(f"校验通过：{len(domains)} 个领域，{sum(len(item['facts']) for item in domains)} 条事实")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
