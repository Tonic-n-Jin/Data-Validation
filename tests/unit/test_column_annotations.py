from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from data_validator import ColumnMeta, ColumnType, SqlType

CODE = ColumnMeta(
    name="code",
    sql_type=SqlType.NVARCHAR,
    nullable=False,
    max_length=3,
    regex_pattern=r"^[A-Z]+$",
    allowed_values=frozenset({"ABC", "DEF"}),
    is_sensitive=True,
)
AMOUNT = ColumnMeta(
    name="amount",
    sql_type=SqlType.DECIMAL,
    nullable=False,
    precision=5,
    scale=2,
    min_value=Decimal("1.00"),
    max_value=Decimal("99.99"),
)
OBSERVED_ON = ColumnMeta(
    name="observed_on",
    sql_type=SqlType.DATE,
    nullable=False,
    min_value=date(2024, 1, 1),
    max_value=date(2024, 12, 31),
)


def adapter(column: ColumnMeta) -> TypeAdapter[Any]:
    return TypeAdapter(column.annotation())


def test_valid_values_pass() -> None:
    assert adapter(CODE).validate_python("ABC") == "ABC"
    assert adapter(AMOUNT).validate_python("12.50") == Decimal("12.50")
    assert adapter(OBSERVED_ON).validate_python(date(2024, 6, 1)) == date(2024, 6, 1)


@pytest.mark.parametrize(
    ("column", "value"),
    [
        (CODE, "TOOLONG"),
        (CODE, "abc"),
        (CODE, "XYZ"),
        (AMOUNT, "100.00"),
        (AMOUNT, "12.345"),
        (AMOUNT, "not-a-number"),
        (AMOUNT, "NaN"),
        (OBSERVED_ON, date(2025, 1, 1)),
    ],
)
def test_constraint_violations_fail(column: ColumnMeta, value: Any) -> None:
    with pytest.raises(ValidationError):
        adapter(column).validate_python(value)


def test_nullable_columns_accept_none() -> None:
    column = ColumnMeta(name="note", sql_type=SqlType.NVARCHAR)
    assert adapter(column).validate_python(None) is None
    with pytest.raises(ValidationError):
        adapter(CODE).validate_python(None)


def test_field_info_defaults() -> None:
    assert ColumnMeta(name="note", sql_type=SqlType.NVARCHAR).field_info().default is None
    assert ColumnMeta(name="flag", sql_type=SqlType.BIT, default=True).field_info().default is True
    assert CODE.field_info().is_required()
    loaded_on = ColumnMeta(
        name="loaded_on", sql_type=SqlType.DATE, column_type=ColumnType.SYSTEM_DATE
    )
    assert loaded_on.field_info().default_factory == date.today
    loaded_at = ColumnMeta(
        name="loaded_at", sql_type=SqlType.DATETIME2, column_type=ColumnType.SYSTEM_DATE
    )
    produced = loaded_at.field_info().default_factory()
    assert isinstance(produced, datetime)
