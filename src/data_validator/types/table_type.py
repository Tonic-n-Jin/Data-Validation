"""Built-in table type keys and their naming prefixes."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from data_validator._base import ACTIVE_FLAG
from data_validator.types.column_type import ColumnType
from data_validator.types.sql import SqlType

if TYPE_CHECKING:
    from data_validator.columns.model import ColumnMeta


class TableType(StrEnum):
    ACTIVE_LIST = "active_list"
    LOOKUP = "lookup"
    DIMENSION = "dimension"
    FACT = "fact"
    JUNCTION = "junction"
    STAGING = "staging"

    @property
    def prefix(self) -> str:
        return _PREFIXES[self]

    def strip_prefix(self, table_name: str) -> str:
        return table_name.removeprefix(self.prefix)

    def scaffold(self, table_name: str) -> tuple[ColumnMeta, ...]:
        # Temporary lazy import; scaffolding moves to the table-type registry.
        from data_validator.columns.model import ColumnMeta

        if self is not TableType.ACTIVE_LIST:
            return ()
        return (
            ColumnMeta(
                name=self.strip_prefix(table_name),
                sql_type=SqlType.NVARCHAR,
                column_type=ColumnType.PRIMARY_KEY,
                max_length=100,
            ),
            ColumnMeta(name=ACTIVE_FLAG, sql_type=SqlType.BIT, nullable=False, default=True),
        )


_PREFIXES: dict[TableType, str] = {
    TableType.ACTIVE_LIST: "al_",
    TableType.LOOKUP: "lu_",
    TableType.DIMENSION: "dim_",
    TableType.FACT: "fact_",
    TableType.JUNCTION: "jct_",
    TableType.STAGING: "stg_",
}
