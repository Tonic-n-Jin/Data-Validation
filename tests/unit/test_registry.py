from __future__ import annotations

import pytest

from data_validator import ColumnTypeSpec, TableTypeSpec, UnknownTypeError
from data_validator.registry import Registry


def test_register_get_and_unregister() -> None:
    registry: Registry[int] = Registry("widget")
    registry.register("a", 1)
    assert registry.get("a") == 1
    assert "a" in registry
    assert registry.keys() == ("a",)
    assert registry.unregister("a") == 1
    assert "a" not in registry


def test_duplicate_registration_requires_replace() -> None:
    registry: Registry[int] = Registry("widget")
    registry.register("a", 1)
    with pytest.raises(ValueError, match="already registered"):
        registry.register("a", 2)
    registry.register("a", 2, replace=True)
    assert registry.get("a") == 2


@pytest.mark.parametrize("operation", ["get", "unregister"])
def test_unknown_key_lists_registered_keys(operation: str) -> None:
    registry: Registry[int] = Registry("widget")
    registry.register("a", 1)
    with pytest.raises(UnknownTypeError, match="unknown widget 'b'; registered: a"):
        getattr(registry, operation)("b")


def test_snapshot_and_restore() -> None:
    registry: Registry[int] = Registry("widget")
    registry.register("a", 1)
    snapshot = registry.snapshot()
    registry.register("b", 2)
    registry.restore(snapshot)
    assert registry.keys() == ("a",)


@pytest.mark.parametrize("key", ["", "1abc", "has space", "dash-key"])
def test_spec_keys_must_be_identifiers(key: str) -> None:
    with pytest.raises(ValueError, match="must be an identifier"):
        ColumnTypeSpec(key)
    with pytest.raises(ValueError, match="must be an identifier"):
        TableTypeSpec(key, "x_")


def test_table_prefix_must_start_an_identifier() -> None:
    with pytest.raises(ValueError, match="prefix"):
        TableTypeSpec("snapshot", "9_")
