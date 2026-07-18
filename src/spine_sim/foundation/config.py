"""Strict YAML 1.2-subset/JSON loading and immutable resolved configurations."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Any

import yaml
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode
from yaml.tokens import AliasToken, AnchorToken, TagToken

from .canonical import semantic_hash, source_file_hash
from .errors import AggregateValidationError, ValidationIssue
from .models import SourceIdentity
from .units import NormalizedQuantity, normalize_quantity, split_suffix_field

_JSON_NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\Z")
_AMBIGUOUS_PLAIN = re.compile(
    r"(?:yes|no|on|off|y|n|\.nan|[+-]?\.inf|[0-9]{4}-[0-9]{2}-[0-9]{2}(?:[Tt ].*)?)\Z",
    re.IGNORECASE,
)


class ConfigLayerLevel(IntEnum):
    L0_SCHEMA = 0
    L1_AUTHORITY = 1
    L2_DEV_POLICY = 2
    L2_ISOLATED = 20
    L3_RUN_BASE = 3
    L4_CASE_PATCH = 4
    L5_RUN_OVERRIDE = 5


class ParameterOwnership(StrEnum):
    FIXED_ENGINEERING = "FIXED_ENGINEERING"
    DESIGN_VARIABLE = "DESIGN_VARIABLE"
    DEV_PRIOR_UNCERTAINTY = "DEV_PRIOR_UNCERTAINTY"
    NUMERICAL_CONFIGURATION = "NUMERICAL_CONFIGURATION"
    RUN_AND_PLOT_CONFIGURATION = "RUN_AND_PLOT_CONFIGURATION"


@dataclass(frozen=True, slots=True)
class ConfigField:
    path: str
    expected_type: type[Any] | tuple[type[Any], ...]
    ownership: ParameterOwnership
    requirement_origin: str
    source_identity: SourceIdentity
    required: bool = True
    dimension: str | None = None
    locked: bool = False
    enum_values: tuple[Any, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    allow_children: bool = False


@dataclass(frozen=True, slots=True)
class ConfigSchema:
    schema_id: str
    version: str
    fields: tuple[ConfigField, ...]
    cross_validators: tuple[Callable[[Mapping[str, Any]], list[ValidationIssue]], ...] = ()

    def field_map(self) -> dict[str, ConfigField]:
        return {item.path: item for item in self.fields}


@dataclass(frozen=True, slots=True)
class ConfigLayer:
    level: ConfigLayerLevel
    source_id: str
    source_hash: str
    data: Mapping[str, Any]
    source_identity: SourceIdentity
    isolated_namespace: str | None = None


@dataclass(frozen=True, slots=True)
class OverrideStep:
    layer: str
    source_id: str
    source_hash: str
    field_path: str
    original_value: Any
    result_value: Any
    locked: bool


@dataclass(frozen=True, slots=True)
class ResolvedLeaf:
    path: str
    canonical_value: Any
    canonical_unit: str | None
    parameter_ownership: ParameterOwnership
    requirement_origin: str
    runtime_value_provenance: SourceIdentity
    source_file: str
    source_path: str
    source_hash: str
    original_value: Any
    original_unit: str | None
    override_chain: tuple[OverrideStep, ...]
    locked: bool
    schema_version: str

    def semantic_value(self) -> Any:
        if self.canonical_unit is None:
            return self.canonical_value
        return {"value": self.canonical_value, "unit": self.canonical_unit}


@dataclass(frozen=True, slots=True)
class ResolvedConfig:
    config_id: str
    schema_id: str
    schema_version: str
    values: Mapping[str, Any]
    leaves: tuple[ResolvedLeaf, ...]
    semantic_hash: str

    def as_manifest(self) -> dict[str, Any]:
        return {
            "config_id": self.config_id,
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "semantic_hash": self.semantic_hash,
            "values": self.values,
            "leaves": [
                {
                    "path": item.path,
                    "canonical_value": item.canonical_value,
                    "canonical_unit": item.canonical_unit,
                    "parameter_ownership": item.parameter_ownership.value,
                    "requirement_origin": item.requirement_origin,
                    "runtime_value_provenance": item.runtime_value_provenance.value,
                    "source_file": item.source_file,
                    "source_path": item.source_path,
                    "source_hash": item.source_hash,
                    "original_value": item.original_value,
                    "original_unit": item.original_unit,
                    "override_chain": [
                        {
                            "layer": step.layer,
                            "source_id": step.source_id,
                            "source_hash": step.source_hash,
                            "field_path": step.field_path,
                            "original_value": step.original_value,
                            "result_value": step.result_value,
                            "locked": step.locked,
                        }
                        for step in item.override_chain
                    ],
                    "locked": item.locked,
                    "schema_version": item.schema_version,
                }
                for item in self.leaves
            ],
        }


def _json_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    duplicates: list[str] = []
    for key, value in pairs:
        if key in output:
            duplicates.append(key)
        output[key] = value
    if duplicates:
        raise AggregateValidationError(
            [ValidationIssue("DUPLICATE_KEY", key, "duplicate JSON key") for key in duplicates]
        )
    return output


def _scalar_value(node: ScalarNode, path: str, issues: list[ValidationIssue]) -> Any:
    text = node.value
    if node.style is not None:
        return text
    lower = text.lower()
    if lower in {"null", "~"}:
        return None
    if lower == "true":
        return True
    if lower == "false":
        return False
    if _AMBIGUOUS_PLAIN.fullmatch(text):
        issues.append(
            ValidationIssue(
                "AMBIGUOUS_IMPLICIT_TYPE",
                path,
                "ambiguous plain scalar is forbidden by the strict YAML subset",
                original_value=text,
                suggestion="quote it as a string or use an explicit JSON-compatible scalar",
            )
        )
        return text
    if _JSON_NUMBER.fullmatch(text):
        value: int | float = float(text) if any(char in text for char in ".eE") else int(text)
        if isinstance(value, float) and not math.isfinite(value):
            issues.append(ValidationIssue("NONFINITE_NUMBER", path, "NaN/Inf is forbidden"))
        return value
    if re.fullmatch(r"[+-]?[0-9][0-9_]*", text) or re.fullmatch(r"0[xob][0-9a-fA-F]+", text):
        issues.append(
            ValidationIssue(
                "AMBIGUOUS_NUMERIC_LITERAL",
                path,
                "only JSON-compatible numeric literals are allowed",
                original_value=text,
            )
        )
    return text


def _node_to_value(node: Node, path: str, issues: list[ValidationIssue]) -> Any:
    if isinstance(node, ScalarNode):
        return _scalar_value(node, path, issues)
    if isinstance(node, SequenceNode):
        return [
            _node_to_value(child, f"{path}[{index}]", issues)
            for index, child in enumerate(node.value)
        ]
    if isinstance(node, MappingNode):
        result: dict[str, Any] = {}
        for key_node, value_node in node.value:
            if not isinstance(key_node, ScalarNode):
                issues.append(
                    ValidationIssue("NON_STRING_KEY", path, "mapping keys must be scalar strings")
                )
                continue
            key = key_node.value
            child_path = f"{path}.{key}" if path else key
            if key == "<<":
                issues.append(
                    ValidationIssue(
                        "YAML_MERGE_FORBIDDEN", child_path, "YAML merge keys are forbidden"
                    )
                )
                continue
            if key in result:
                issues.append(ValidationIssue("DUPLICATE_KEY", child_path, "duplicate YAML key"))
                continue
            result[key] = _node_to_value(value_node, child_path, issues)
        return result
    issues.append(
        ValidationIssue("UNSUPPORTED_YAML_NODE", path, f"unsupported node {type(node).__name__}")
    )
    return None


def load_strict_document(
    text: str, *, format_hint: str | None = None, source: str = "<memory>"
) -> dict[str, Any]:
    """Load JSON or the frozen strict YAML 1.2 subset with aggregated issues."""

    stripped = text.lstrip()
    is_json = format_hint == "json" or (format_hint is None and stripped.startswith(("{", "[")))
    if is_json:
        try:
            value = json.loads(
                text,
                object_pairs_hook=_json_pairs,
                parse_constant=lambda token: _raise_nonfinite(token),
            )
        except AggregateValidationError:
            raise
        except (json.JSONDecodeError, ValueError) as error:
            raise AggregateValidationError(
                [ValidationIssue("INVALID_JSON", "", str(error), source=source)]
            ) from error
    else:
        issues: list[ValidationIssue] = []
        try:
            for token in yaml.scan(text, Loader=yaml.BaseLoader):
                if isinstance(token, AnchorToken | AliasToken):
                    issues.append(
                        ValidationIssue(
                            "YAML_ANCHOR_ALIAS_FORBIDDEN",
                            "",
                            "anchors and aliases are forbidden",
                            source=source,
                        )
                    )
                elif isinstance(token, TagToken):
                    issues.append(
                        ValidationIssue(
                            "YAML_CUSTOM_TAG_FORBIDDEN",
                            "",
                            "custom tags are forbidden",
                            source=source,
                        )
                    )
            root = yaml.compose(text, Loader=yaml.BaseLoader)
        except yaml.YAMLError as error:
            raise AggregateValidationError(
                [ValidationIssue("INVALID_YAML", "", str(error), source=source)]
            ) from error
        if root is None:
            value = {}
        else:
            value = _node_to_value(root, "", issues)
        if issues:
            raise AggregateValidationError(issues)
    if not isinstance(value, dict):
        raise AggregateValidationError(
            [
                ValidationIssue(
                    "ROOT_NOT_MAPPING", "", "configuration root must be a mapping", source=source
                )
            ]
        )
    return value


def _raise_nonfinite(token: str) -> None:
    raise ValueError(f"non-finite JSON number is forbidden: {token}")


def load_strict_file(path: str | Path) -> tuple[dict[str, Any], str]:
    source_path = Path(path)
    text = source_path.read_text(encoding="utf-8")
    hint = "json" if source_path.suffix.lower() == ".json" else "yaml"
    return load_strict_document(text, format_hint=hint, source=str(source_path)), source_file_hash(
        source_path
    )


def materialize_cli_override_artifact(
    overrides: Mapping[str, Any], *, destination: str | Path, schema_version: str
) -> Path:
    """Write the immutable input artifact consumed as L5; never consult environment variables."""

    path = Path(destination)
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "artifact_kind": "RECORDED_RUN_OVERRIDE",
        "schema_version": schema_version,
        "overrides": dict(overrides),
    }
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    path.chmod(0o444)
    return path


def _flatten(value: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, item in value.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(item, Mapping):
            output.update(_flatten(item, path))
        else:
            output[path] = item
    return output


def _unflatten(leaves: Mapping[str, Any]) -> dict[str, Any]:
    root: dict[str, Any] = {}
    for path, value in leaves.items():
        target = root
        parts = path.split(".")
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value
    return root


def _normalize_layer_keys(
    data: Mapping[str, Any], field_map: Mapping[str, ConfigField]
) -> tuple[dict[str, Any], dict[str, tuple[str, str] | None]]:
    flattened: dict[str, Any] = {}

    def walk(value: Mapping[str, Any], prefix: str = "") -> None:
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else key
            if path in field_map:
                flattened[path] = item
            elif isinstance(item, Mapping):
                walk(item, path)
            else:
                flattened[path] = item

    walk(data)
    normalized: dict[str, Any] = {}
    suffix_info: dict[str, tuple[str, str] | None] = {}
    for path, value in flattened.items():
        if path in field_map:
            normalized[path] = value
            suffix_info[path] = None
            continue
        parent, _, leaf = path.rpartition(".")
        split = split_suffix_field(leaf)
        if split is not None:
            base, unit = split
            candidate = f"{parent}.{base}" if parent else base
            field_spec = field_map.get(candidate)
            if field_spec is not None and field_spec.dimension is not None:
                normalized[candidate] = {"value": value, "unit": unit}
                suffix_info[candidate] = (path, unit)
                continue
        normalized[path] = value
        suffix_info[path] = None
    return normalized, suffix_info


def resolve_config(
    schema: ConfigSchema, layers: tuple[ConfigLayer, ...] | list[ConfigLayer], *, config_kind: str
) -> ResolvedConfig:
    """Validate, normalize once, merge, and produce leaf-level source chains."""

    field_map = schema.field_map()
    issues: list[ValidationIssue] = []
    resolved_values: dict[str, Any] = {}
    leaf_meta: dict[str, dict[str, Any]] = {}
    previous_level = -1
    for layer in layers:
        ordering_level = 2 if layer.level is ConfigLayerLevel.L2_ISOLATED else int(layer.level)
        if ordering_level < previous_level:
            issues.append(
                ValidationIssue(
                    "LAYER_ORDER_INVALID",
                    "",
                    "configuration layers are not monotonic",
                    layer=layer.level.name,
                )
            )
        previous_level = ordering_level
        normalized_layer, suffix_info = _normalize_layer_keys(layer.data, field_map)
        for path, raw_value in normalized_layer.items():
            spec = field_map.get(path)
            if spec is None:
                issues.append(
                    ValidationIssue(
                        "UNKNOWN_KEY",
                        path,
                        "field is not declared by the configuration schema",
                        source=layer.source_id,
                        layer=layer.level.name,
                        original_value=raw_value,
                    )
                )
                continue
            if layer.level is ConfigLayerLevel.L2_ISOLATED:
                prefix = f"{layer.isolated_namespace}." if layer.isolated_namespace else ""
                if layer.source_identity not in {
                    SourceIdentity.PROPOSED_SUPPLEMENT,
                    SourceIdentity.VALIDATION_ONLY,
                } or not path.startswith(prefix):
                    issues.append(
                        ValidationIssue(
                            "ISOLATED_NAMESPACE_VIOLATION",
                            path,
                            "isolated L2 values must stay in their declared namespace",
                        )
                    )
                    continue
            canonical_value: Any = raw_value
            canonical_unit: str | None = None
            original_value: Any = raw_value
            original_unit: str | None = None
            if spec.dimension is not None:
                if not isinstance(raw_value, dict):
                    issues.append(
                        ValidationIssue(
                            "EXPLICIT_QUANTITY_REQUIRED",
                            path,
                            "dimensional fields require {value, unit}",
                            original_value=raw_value,
                        )
                    )
                    continue
                try:
                    suffix_used = suffix_info.get(path) is not None
                    quantity = normalize_quantity(
                        raw_value, expected_dimension=spec.dimension, suffix_adapter=suffix_used
                    )
                except Exception as error:
                    issues.append(
                        ValidationIssue(
                            "UNIT_VALIDATION_FAILED", path, str(error), original_value=raw_value
                        )
                    )
                    continue
                canonical_value = quantity.canonical_value
                canonical_unit = quantity.canonical_unit
                original_value = quantity.original_value
                original_unit = quantity.original_unit
            expected = spec.expected_type
            if isinstance(canonical_value, bool) and expected is not bool:
                valid_type = False
            else:
                valid_type = isinstance(canonical_value, expected)
            if not valid_type:
                issues.append(
                    ValidationIssue(
                        "TYPE_MISMATCH",
                        path,
                        f"expected {expected}, got {type(canonical_value).__name__}",
                        original_value=raw_value,
                    )
                )
                continue
            if isinstance(canonical_value, float) and not math.isfinite(canonical_value):
                issues.append(ValidationIssue("NONFINITE_NUMBER", path, "NaN/Inf is forbidden"))
                continue
            if spec.enum_values and canonical_value not in spec.enum_values:
                issues.append(
                    ValidationIssue(
                        "ENUM_VALUE_INVALID",
                        path,
                        f"expected one of {spec.enum_values}",
                        original_value=raw_value,
                    )
                )
                continue
            if spec.minimum is not None and canonical_value < spec.minimum:
                issues.append(
                    ValidationIssue(
                        "VALUE_BELOW_MINIMUM",
                        path,
                        f"minimum is {spec.minimum}",
                        original_value=raw_value,
                    )
                )
                continue
            if spec.maximum is not None and canonical_value > spec.maximum:
                issues.append(
                    ValidationIssue(
                        "VALUE_ABOVE_MAXIMUM",
                        path,
                        f"maximum is {spec.maximum}",
                        original_value=raw_value,
                    )
                )
                continue
            previous = resolved_values.get(path, _MISSING)
            if previous is not _MISSING and spec.locked and canonical_value != previous:
                issues.append(
                    ValidationIssue(
                        "LOCKED_FIELD_OVERRIDE",
                        path,
                        "locked authority value cannot be overridden",
                        source=layer.source_id,
                        layer=layer.level.name,
                        original_value=raw_value,
                    )
                )
                continue
            step = OverrideStep(
                layer=layer.level.name,
                source_id=layer.source_id,
                source_hash=layer.source_hash,
                field_path=path,
                original_value=raw_value,
                result_value=canonical_value,
                locked=spec.locked,
            )
            chain = (*leaf_meta.get(path, {}).get("chain", ()), step)
            resolved_values[path] = canonical_value
            leaf_meta[path] = {
                "canonical_unit": canonical_unit,
                "original_value": original_value,
                "original_unit": original_unit,
                "source_id": layer.source_id,
                "source_hash": layer.source_hash,
                "source_identity": layer.source_identity,
                "chain": chain,
            }
    for path, spec in field_map.items():
        if spec.required and path not in resolved_values:
            issues.append(
                ValidationIssue("REQUIRED_FIELD_MISSING", path, "required field is absent")
            )
    expanded = _unflatten(resolved_values)
    for validator in schema.cross_validators:
        issues.extend(validator(expanded))
    if issues:
        raise AggregateValidationError(issues)
    leaves = tuple(
        ResolvedLeaf(
            path=path,
            canonical_value=resolved_values[path],
            canonical_unit=leaf_meta[path]["canonical_unit"],
            parameter_ownership=field_map[path].ownership,
            requirement_origin=field_map[path].requirement_origin,
            runtime_value_provenance=leaf_meta[path]["source_identity"],
            source_file=leaf_meta[path]["source_id"],
            source_path=path,
            source_hash=leaf_meta[path]["source_hash"],
            original_value=leaf_meta[path]["original_value"],
            original_unit=leaf_meta[path]["original_unit"],
            override_chain=leaf_meta[path]["chain"],
            locked=field_map[path].locked,
            schema_version=schema.version,
        )
        for path in sorted(resolved_values)
    )
    semantic_values = {item.path: item.semantic_value() for item in leaves}
    digest = semantic_hash(
        {"schema_id": schema.schema_id, "schema_version": schema.version, "values": semantic_values}
    )
    return ResolvedConfig(
        config_id=f"{config_kind}:{digest}",
        schema_id=schema.schema_id,
        schema_version=schema.version,
        values=expanded,
        leaves=leaves,
        semantic_hash=digest,
    )


_MISSING = object()


def layer_from_file(
    path: str | Path,
    *,
    level: ConfigLayerLevel,
    source_identity: SourceIdentity,
    isolated_namespace: str | None = None,
) -> ConfigLayer:
    data, digest = load_strict_file(path)
    return ConfigLayer(level, str(Path(path)), digest, data, source_identity, isolated_namespace)


def quantity_audit_record(quantity: NormalizedQuantity) -> dict[str, Any]:
    return {
        "canonical_value": quantity.canonical_value,
        "canonical_unit": quantity.canonical_unit,
        "dimension": quantity.dimension,
        "original_value": quantity.original_value,
        "original_unit": quantity.original_unit,
        "converter_id": quantity.converter_id,
        "converter_version": quantity.converter_version,
        "suffix_adapter_id": quantity.suffix_adapter_id,
        "suffix_adapter_version": quantity.suffix_adapter_version,
    }
