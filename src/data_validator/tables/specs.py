"""Table type specs and the registry that resolves `TableMeta.table_type`."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated

from pydantic import AfterValidator

from data_validator.registry import Registry, UnknownTypeError
from data_validator.types.table_type import TableType

if TYPE_CHECKING:
    from data_validator.columns.model import ColumnMeta
    from data_validator.tables.model import TableMeta

TableRules = Callable[["TableMeta"], Sequence[str]]
TableScaffold = Callable[[str], "tuple[ColumnMeta, ...]"]
_IDENT_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _no_rules(table: TableMeta) -> Sequence[str]:
    return ()


@dataclass(frozen=True, slots=True)
class TableTypeSpec:
    """Behavior attached to a table type key.

    `rules` returns structural error messages for a built table. `scaffold`, when
    set, generates columns for a table declared without any.
    """

    key: str
    prefix: str
    rules: TableRules = _no_rules
    scaffold: TableScaffold | None = None

    def __post_init__(self) -> None:
        if not _IDENT_PATTERN.match(self.key):
            raise ValueError(f"table type key '{self.key}' must be an identifier")
        if not _IDENT_PATTERN.match(self.prefix):
            raise ValueError(f"table prefix '{self.prefix}' must start a valid identifier")

    def strip_prefix(self, table_name: str) -> str:
        return table_name.removeprefix(self.prefix)


TABLE_TYPES: Registry[TableTypeSpec] = Registry("table type")


def register_table_type(spec: TableTypeSpec, *, replace: bool = False) -> TableTypeSpec:
    return TABLE_TYPES.register(spec.key, spec, replace=replace)


def unregister_table_type(key: str) -> TableTypeSpec:
    return TABLE_TYPES.unregister(key)


def get_table_type_spec(key: str) -> TableTypeSpec:
    return TABLE_TYPES.get(key)


def _resolve_table_type(value: str) -> str:
    try:
        TABLE_TYPES.get(value)
    except UnknownTypeError as error:
        raise ValueError(str(error)) from error
    try:
        return TableType(value)
    except ValueError:
        return value


TableTypeKey = Annotated[str, AfterValidator(_resolve_table_type)]
"""A registered table type key; built-in keys are normalized to `TableType` members."""
