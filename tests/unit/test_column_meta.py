from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from data_validator import ColumnMeta, SqlType


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"sql_type": SqlType.INT, "max_length": 5}, "max_length is only valid"),
        ({"sql_type": SqlType.INT, "regex_pattern": "^a$"}, "regex_pattern is only valid"),
        ({"sql_type": SqlType.INT, "precision": 5}, "precision and scale are only valid"),
        ({"sql_type": SqlType.DECIMAL, "scale": 2}, "scale requires precision"),
        ({"sql_type": SqlType.DECIMAL, "precision": 2, "scale": 3}, "scale cannot exceed"),
        ({"sql_type": SqlType.NVARCHAR, "min_value": 1}, "require numeric or temporal"),
        ({"sql_type": SqlType.INT, "min_value": 5, "max_value": 1}, "cannot exceed max_value"),
        (
            {"sql_type": SqlType.DATE, "min_value": date(2024, 1, 1), "max_value": Decimal(1)},
            "mutually comparable",
        ),
        ({"sql_type": SqlType.INT, "references": "dim_a.a"}, "has references"),
        ({"sql_type": SqlType.INT, "primary_key": True}, "cannot be nullable"),
    ],
)
def test_invalid_metadata_is_rejected(overrides: dict[str, Any], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        ColumnMeta(name="col", **overrides)


@pytest.mark.parametrize("name", ["1col", "has space", "x" * 129])
def test_column_names_must_be_identifiers(name: str) -> None:
    with pytest.raises(ValidationError):
        ColumnMeta(name=name, sql_type=SqlType.INT)


def test_column_meta_is_frozen_and_rejects_unknown_fields() -> None:
    column = ColumnMeta(name="col", sql_type=SqlType.INT)
    with pytest.raises(ValidationError):
        column.nullable = False  # type: ignore[misc]
    with pytest.raises(ValidationError):
        ColumnMeta(name="col", sql_type=SqlType.INT, unknown=True)  # type: ignore[call-arg]
