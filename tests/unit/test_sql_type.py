from __future__ import annotations

from decimal import Decimal

from data_validator import SqlType


def test_python_mappings_and_type_families() -> None:
    assert SqlType.BIT.python_type is bool
    assert SqlType.DECIMAL.python_type is Decimal
    assert SqlType.NUMERIC.is_numeric
    assert SqlType.NVARCHAR.is_string
    assert SqlType.DATETIME2.is_temporal
    assert SqlType.BIT.is_boolean
    assert SqlType.DECIMAL.supports_precision_scale
    assert not SqlType.INT.supports_precision_scale


def test_every_sql_type_has_a_python_type() -> None:
    for sql_type in SqlType:
        assert isinstance(sql_type.python_type, type)
