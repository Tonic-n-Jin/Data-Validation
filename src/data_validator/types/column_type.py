"""Built-in column type keys."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any

from data_validator.types.sql import SqlType

if TYPE_CHECKING:
    from data_validator.columns.model import ColumnMeta


class ColumnType(StrEnum):
    PRIMARY_KEY = "primary_key"
    FOREIGN_KEY = "foreign_key"
    IDENTITY = "identity"
    COMPOSITE_KEY = "composite_key"
    SYSTEM_DATE = "system_date"
    MISCELLANEOUS = "miscellaneous"

    def defaults(self, values: dict[str, Any]) -> dict[str, Any]:
        values = dict(values)
        if self in {ColumnType.PRIMARY_KEY, ColumnType.COMPOSITE_KEY}:
            values.setdefault("primary_key", True)
            values.setdefault("nullable", False)
            values.setdefault("indexed", True)
        elif self is ColumnType.SYSTEM_DATE:
            values.setdefault("nullable", False)
            values.setdefault("auto_utc", True)
        return values

    def violation(self, column: ColumnMeta) -> str | None:
        if self in {ColumnType.PRIMARY_KEY, ColumnType.COMPOSITE_KEY}:
            if not column.primary_key or column.nullable or not column.indexed:
                return "must be a non-nullable indexed primary key"
        if self is ColumnType.FOREIGN_KEY and not column.references:
            return "requires a references target"
        if self is ColumnType.IDENTITY:
            if column.sql_type not in {SqlType.INT, SqlType.BIGINT}:
                return "requires INT or BIGINT"
            if column.default is not None and not column.allow_manual_default:
                return "disallows a manual default without allow_manual_default=True"
        if self is ColumnType.SYSTEM_DATE:
            if column.sql_type not in {SqlType.DATE, SqlType.DATETIME2}:
                return "requires DATE or DATETIME2"
        return None
