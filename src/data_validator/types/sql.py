"""SQL type keys and their Python type mapping."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum


class SqlType(StrEnum):
    BIT = "bit"
    SMALLINT = "smallint"
    INT = "int"
    BIGINT = "bigint"
    DECIMAL = "decimal"
    NUMERIC = "numeric"
    FLOAT = "float"
    VARCHAR = "varchar"
    NVARCHAR = "nvarchar"
    CHAR = "char"
    NCHAR = "nchar"
    DATE = "date"
    DATETIME2 = "datetime2"

    @property
    def python_type(self) -> type:
        return _PYTHON_TYPES[self]

    @property
    def is_numeric(self) -> bool:
        return self in {
            SqlType.SMALLINT,
            SqlType.INT,
            SqlType.BIGINT,
            SqlType.DECIMAL,
            SqlType.NUMERIC,
            SqlType.FLOAT,
        }

    @property
    def is_string(self) -> bool:
        return self in {
            SqlType.VARCHAR,
            SqlType.NVARCHAR,
            SqlType.CHAR,
            SqlType.NCHAR,
        }

    @property
    def is_temporal(self) -> bool:
        return self in {SqlType.DATE, SqlType.DATETIME2}

    @property
    def is_boolean(self) -> bool:
        return self is SqlType.BIT

    @property
    def supports_precision_scale(self) -> bool:
        return self in {SqlType.DECIMAL, SqlType.NUMERIC}


_PYTHON_TYPES: dict[SqlType, type] = {
    SqlType.BIT: bool,
    SqlType.SMALLINT: int,
    SqlType.INT: int,
    SqlType.BIGINT: int,
    SqlType.DECIMAL: Decimal,
    SqlType.NUMERIC: Decimal,
    SqlType.FLOAT: float,
    SqlType.VARCHAR: str,
    SqlType.NVARCHAR: str,
    SqlType.CHAR: str,
    SqlType.NCHAR: str,
    SqlType.DATE: date,
    SqlType.DATETIME2: datetime,
}
