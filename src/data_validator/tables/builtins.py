"""Built-in table type rules and scaffolding, registered on import."""

from __future__ import annotations

from typing import TYPE_CHECKING

from data_validator._base import ACTIVE_FLAG
from data_validator.columns.model import ColumnMeta
from data_validator.tables.specs import TableTypeSpec, register_table_type
from data_validator.types.column_type import ColumnType
from data_validator.types.sql import SqlType
from data_validator.types.table_type import TableType

if TYPE_CHECKING:
    from data_validator.tables.model import TableMeta


def active_list_scaffold(table_name: str) -> tuple[ColumnMeta, ...]:
    return (
        ColumnMeta(
            name=TableType.ACTIVE_LIST.strip_prefix(table_name),
            sql_type=SqlType.NVARCHAR,
            column_type=ColumnType.PRIMARY_KEY,
            max_length=100,
        ),
        ColumnMeta(name=ACTIVE_FLAG, sql_type=SqlType.BIT, nullable=False, default=True),
    )


def active_list_rules(table: TableMeta) -> list[str]:
    expected_pk = TableType.ACTIVE_LIST.strip_prefix(table.name)
    if len(table.columns) != 2 or len(table.pk) != 1 or table.pk[0].name != expected_pk:
        return [f"must be exactly ({expected_pk} PK, {ACTIVE_FLAG})"]
    flag = next((column for column in table.columns if column.name == ACTIVE_FLAG), None)
    if (
        flag is None
        or flag.sql_type is not SqlType.BIT
        or flag.nullable
        or flag.default is not True
    ):
        return [f"{ACTIVE_FLAG} must be BIT NOT NULL DEFAULT True"]
    return []


def keyed_entity_rules(table: TableMeta) -> list[str]:
    if len(table.pk) != 1:
        return [f"needs exactly 1 PK, has {len(table.pk)}"]
    if all(column.primary_key for column in table.columns):
        return ["needs a non-key column"]
    return []


def fact_rules(table: TableMeta) -> list[str]:
    errors = []
    if not any(column.references for column in table.columns):
        errors.append("needs an FK column")
    if not any(
        column.sql_type.is_numeric and not (column.primary_key or column.references)
        for column in table.columns
    ):
        errors.append("needs a numeric measure")
    return errors


def junction_rules(table: TableMeta) -> list[str]:
    if len(table.pk) < 2 or not all(column.references for column in table.pk):
        return ["PK must be 2+ FK columns"]
    return []


for _spec in (
    TableTypeSpec(
        TableType.ACTIVE_LIST,
        TableType.ACTIVE_LIST.prefix,
        active_list_rules,
        active_list_scaffold,
    ),
    TableTypeSpec(TableType.LOOKUP, TableType.LOOKUP.prefix, keyed_entity_rules),
    TableTypeSpec(TableType.DIMENSION, TableType.DIMENSION.prefix, keyed_entity_rules),
    TableTypeSpec(TableType.FACT, TableType.FACT.prefix, fact_rules),
    TableTypeSpec(TableType.JUNCTION, TableType.JUNCTION.prefix, junction_rules),
    TableTypeSpec(TableType.STAGING, TableType.STAGING.prefix),
):
    register_table_type(_spec)
