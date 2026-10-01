"""Built-in table type keys and their naming prefixes."""

from __future__ import annotations

from enum import StrEnum


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


_PREFIXES: dict[TableType, str] = {
    TableType.ACTIVE_LIST: "al_",
    TableType.LOOKUP: "lu_",
    TableType.DIMENSION: "dim_",
    TableType.FACT: "fact_",
    TableType.JUNCTION: "jct_",
    TableType.STAGING: "stg_",
}
