from __future__ import annotations

import pytest
from pydantic import ValidationError

from data_validator import (
    ColumnMeta,
    ColumnType,
    ColumnTypeSpec,
    PrimaryKeyColumn,
    SqlType,
    get_column_type_spec,
)


def test_column_type_defaults_and_invariants() -> None:
    primary_key = ColumnMeta(name="id", sql_type=SqlType.INT, column_type=ColumnType.PRIMARY_KEY)
    assert primary_key.primary_key
    assert primary_key.indexed
    assert not primary_key.nullable

    with pytest.raises(ValidationError):
        ColumnMeta(
            name="missing_reference",
            sql_type=SqlType.INT,
            column_type=ColumnType.FOREIGN_KEY,
        )
    with pytest.raises(ValidationError):
        ColumnMeta(
            name="bad_identity",
            sql_type=SqlType.NVARCHAR,
            column_type=ColumnType.IDENTITY,
        )
    with pytest.raises(ValidationError):
        ColumnMeta(
            name="generated_id",
            sql_type=SqlType.INT,
            column_type=ColumnType.IDENTITY,
            default=1,
        )
    identity = ColumnMeta(
        name="generated_id",
        sql_type=SqlType.BIGINT,
        column_type=ColumnType.IDENTITY,
        default=1,
        allow_manual_default=True,
    )
    assert identity.default == 1
    assert PrimaryKeyColumn(name="alternate_id", sql_type=SqlType.INT).primary_key


def test_system_date_defaults_and_type_check() -> None:
    column = ColumnMeta(
        name="loaded_at", sql_type=SqlType.DATETIME2, column_type=ColumnType.SYSTEM_DATE
    )
    assert column.auto_utc
    assert not column.nullable
    with pytest.raises(ValidationError, match="requires DATE or DATETIME2"):
        ColumnMeta(name="loaded_at", sql_type=SqlType.INT, column_type=ColumnType.SYSTEM_DATE)


def test_explicit_values_override_spec_defaults() -> None:
    with pytest.raises(ValidationError, match="cannot be nullable"):
        ColumnMeta(
            name="id", sql_type=SqlType.INT, column_type=ColumnType.PRIMARY_KEY, nullable=True
        )


def test_built_in_keys_resolve_to_enum_members() -> None:
    column = ColumnMeta(name="id", sql_type=SqlType.INT, column_type="primary_key")
    assert column.column_type is ColumnType.PRIMARY_KEY


def test_unknown_column_type_is_rejected() -> None:
    with pytest.raises(ValidationError, match="unknown column type 'surrogate'"):
        ColumnMeta(name="id", sql_type=SqlType.INT, column_type="surrogate")


def test_every_built_in_column_type_is_registered() -> None:
    for column_type in ColumnType:
        assert get_column_type_spec(column_type).key == column_type


def test_spec_defaults_are_read_only() -> None:
    spec = ColumnTypeSpec("audit", {"nullable": False})
    with pytest.raises(TypeError):
        spec.defaults["nullable"] = True  # type: ignore[index]
