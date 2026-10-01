"""Column type specs and the registry that resolves `ColumnMeta.column_type`."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Annotated, Any

from pydantic import AfterValidator

from data_validator.registry import Registry, UnknownTypeError
from data_validator.types.column_type import ColumnType
from data_validator.types.sql import SqlType

if TYPE_CHECKING:
    from data_validator.columns.model import ColumnMeta

ColumnCheck = Callable[["ColumnMeta"], "str | None"]
_KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _no_check(column: ColumnMeta) -> str | None:
    return None


@dataclass(frozen=True, slots=True)
class ColumnTypeSpec:
    """Behavior attached to a column type key.

    `defaults` are applied with `setdefault` before a column is validated, and
    `check` returns a violation message (or None) once it is built.
    """

    key: str
    defaults: Mapping[str, Any] = field(default_factory=dict)
    check: ColumnCheck = _no_check

    def __post_init__(self) -> None:
        if not _KEY_PATTERN.match(self.key):
            raise ValueError(f"column type key '{self.key}' must be an identifier")
        object.__setattr__(self, "defaults", MappingProxyType(dict(self.defaults)))

    def apply_defaults(self, values: dict[str, Any]) -> dict[str, Any]:
        values = dict(values)
        for name, value in self.defaults.items():
            values.setdefault(name, value)
        return values


COLUMN_TYPES: Registry[ColumnTypeSpec] = Registry("column type")


def register_column_type(spec: ColumnTypeSpec, *, replace: bool = False) -> ColumnTypeSpec:
    return COLUMN_TYPES.register(spec.key, spec, replace=replace)


def unregister_column_type(key: str) -> ColumnTypeSpec:
    return COLUMN_TYPES.unregister(key)


def get_column_type_spec(key: str) -> ColumnTypeSpec:
    return COLUMN_TYPES.get(key)


def _resolve_column_type(value: str) -> str:
    try:
        COLUMN_TYPES.get(value)
    except UnknownTypeError as error:
        raise ValueError(str(error)) from error
    try:
        return ColumnType(value)
    except ValueError:
        return value


ColumnTypeKey = Annotated[str, AfterValidator(_resolve_column_type)]
"""A registered column type key; built-in keys are normalized to `ColumnType` members."""


def _check_key(column: ColumnMeta) -> str | None:
    if not column.primary_key or column.nullable or not column.indexed:
        return "must be a non-nullable indexed primary key"
    return None


def _check_foreign_key(column: ColumnMeta) -> str | None:
    return None if column.references else "requires a references target"


def _check_identity(column: ColumnMeta) -> str | None:
    if column.sql_type not in {SqlType.INT, SqlType.BIGINT}:
        return "requires INT or BIGINT"
    if column.default is not None and not column.allow_manual_default:
        return "disallows a manual default without allow_manual_default=True"
    return None


def _check_system_date(column: ColumnMeta) -> str | None:
    if column.sql_type not in {SqlType.DATE, SqlType.DATETIME2}:
        return "requires DATE or DATETIME2"
    return None


_KEY_DEFAULTS = {"primary_key": True, "nullable": False, "indexed": True}

for _spec in (
    ColumnTypeSpec(ColumnType.PRIMARY_KEY, _KEY_DEFAULTS, _check_key),
    ColumnTypeSpec(ColumnType.FOREIGN_KEY, check=_check_foreign_key),
    ColumnTypeSpec(ColumnType.IDENTITY, check=_check_identity),
    ColumnTypeSpec(ColumnType.COMPOSITE_KEY, _KEY_DEFAULTS, _check_key),
    ColumnTypeSpec(
        ColumnType.SYSTEM_DATE, {"nullable": False, "auto_utc": True}, _check_system_date
    ),
    ColumnTypeSpec(ColumnType.MISCELLANEOUS),
):
    register_column_type(_spec)
