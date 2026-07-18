from __future__ import annotations

import json

import pytest

from spine_sim.foundation.canonical import semantic_hash
from spine_sim.foundation.config import (
    ConfigField,
    ConfigLayer,
    ConfigLayerLevel,
    ConfigSchema,
    ParameterOwnership,
    load_strict_document,
    materialize_cli_override_artifact,
    resolve_config,
)
from spine_sim.foundation.errors import AggregateValidationError
from spine_sim.foundation.models import SourceIdentity


def _layer(level: ConfigLayerLevel, data: dict[str, object], name: str = "layer") -> ConfigLayer:
    return ConfigLayer(level, name, semantic_hash(data), data, SourceIdentity.DEV_POLICY)


@pytest.mark.parametrize(
    ("text", "code"),
    [
        ("a: 1\na: 2\n", "DUPLICATE_KEY"),
        ("base: &base {a: 1}\ncopy: *base\n", "YAML_ANCHOR_ALIAS_FORBIDDEN"),
        ("a: !custom value\n", "YAML_CUSTOM_TAG_FORBIDDEN"),
        ("a: 2026-07-18\n", "AMBIGUOUS_IMPLICIT_TYPE"),
        ("a: yes\n", "AMBIGUOUS_IMPLICIT_TYPE"),
        ("a: 01\n", "AMBIGUOUS_NUMERIC_LITERAL"),
        ("base: {a: 1}\nvalue: {<<: {a: 2}}\n", "YAML_MERGE_FORBIDDEN"),
    ],
)
def test_strict_yaml_rejections(text: str, code: str) -> None:
    with pytest.raises(AggregateValidationError) as captured:
        load_strict_document(text, format_hint="yaml")
    assert code in {issue.code for issue in captured.value.issues}


def test_strict_yaml_json_compatible_scalars() -> None:
    assert load_strict_document("a: true\nb: null\nc: 1.25\nd: plain\n") == {
        "a": True,
        "b": None,
        "c": 1.25,
        "d": "plain",
    }


def test_strict_json_duplicate_and_nonfinite() -> None:
    with pytest.raises(AggregateValidationError):
        load_strict_document('{"a": 1, "a": 2}', format_hint="json")
    with pytest.raises(AggregateValidationError):
        load_strict_document('{"a": NaN}', format_hint="json")


def test_suffix_adapter_and_explicit_quantity_have_same_semantic_hash() -> None:
    schema = ConfigSchema(
        "units",
        "1.0.0",
        (
            ConfigField(
                "tip_radius",
                float,
                ParameterOwnership.DESIGN_VARIABLE,
                "test",
                SourceIdentity.FIXED_ENGINEERING,
                dimension="length",
            ),
        ),
    )
    explicit = resolve_config(
        schema,
        (_layer(ConfigLayerLevel.L3_RUN_BASE, {"tip_radius": {"value": 50, "unit": "um"}}),),
        config_kind="case",
    )
    suffix = resolve_config(
        schema,
        (_layer(ConfigLayerLevel.L3_RUN_BASE, {"tip_radius_mm": 0.05}),),
        config_kind="case",
    )
    assert explicit.semantic_hash == suffix.semantic_hash
    assert explicit.values["tip_radius"] == pytest.approx(0.05)
    assert explicit.leaves[0].original_unit == "um"
    assert suffix.leaves[0].original_unit == "mm"


def test_layer_merge_list_replace_null_and_source_chain() -> None:
    schema = ConfigSchema(
        "merge",
        "1.0.0",
        (
            ConfigField(
                "map.a",
                int,
                ParameterOwnership.RUN_AND_PLOT_CONFIGURATION,
                "test",
                SourceIdentity.DEV_POLICY,
            ),
            ConfigField(
                "map.b",
                (str, type(None)),
                ParameterOwnership.RUN_AND_PLOT_CONFIGURATION,
                "test",
                SourceIdentity.DEV_POLICY,
            ),
            ConfigField(
                "items",
                list,
                ParameterOwnership.RUN_AND_PLOT_CONFIGURATION,
                "test",
                SourceIdentity.DEV_POLICY,
            ),
        ),
    )
    result = resolve_config(
        schema,
        (
            _layer(
                ConfigLayerLevel.L3_RUN_BASE,
                {"map": {"a": 1, "b": "kept"}, "items": [1, 2]},
                "base",
            ),
            _layer(ConfigLayerLevel.L4_CASE_PATCH, {"map": {"b": None}, "items": [3]}, "case"),
        ),
        config_kind="case",
    )
    assert result.values == {"items": [3], "map": {"a": 1, "b": None}}
    item_leaf = next(item for item in result.leaves if item.path == "items")
    assert [step.source_id for step in item_leaf.override_chain] == ["base", "case"]


def test_locked_override_and_aggregated_unknown_missing() -> None:
    schema = ConfigSchema(
        "locked",
        "1.0.0",
        (
            ConfigField(
                "fixed",
                int,
                ParameterOwnership.FIXED_ENGINEERING,
                "test",
                SourceIdentity.FIXED_ENGINEERING,
                locked=True,
            ),
            ConfigField(
                "required",
                str,
                ParameterOwnership.RUN_AND_PLOT_CONFIGURATION,
                "test",
                SourceIdentity.DEV_POLICY,
            ),
        ),
    )
    layers = (
        _layer(ConfigLayerLevel.L1_AUTHORITY, {"fixed": 1}, "authority"),
        _layer(ConfigLayerLevel.L3_RUN_BASE, {"fixed": 2, "unknown": 3}, "run"),
    )
    with pytest.raises(AggregateValidationError) as captured:
        resolve_config(schema, layers, config_kind="run")
    assert {item.code for item in captured.value.issues} >= {
        "LOCKED_FIELD_OVERRIDE",
        "UNKNOWN_KEY",
        "REQUIRED_FIELD_MISSING",
    }


def test_cli_override_is_materialized_without_environment_read(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "override.json"  # type: ignore[operator]
    monkeypatch.setenv("PHYSICAL_VALUE", "999")
    materialize_cli_override_artifact({"value": 3}, destination=path, schema_version="1.0.0")
    payload = json.loads(path.read_text())
    assert payload["overrides"] == {"value": 3}
    assert "999" not in path.read_text()
