from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from functools import cached_property
from typing import Annotated, Any, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    create_model,
    model_validator,
)


class SqlType(StrEnum):
    BIT = "bit"
    INT = "int"
    BIGINT = "bigint"
    DECIMAL = "decimal"
    VARCHAR = "varchar"
    NVARCHAR = "nvarchar"
    DATE = "date"
    DATETIME2 = "datetime2"

    @property
    def python_type(self) -> type:
        return _PY_TYPES[self]

    @property
    def is_numeric(self) -> bool:
        return self in {SqlType.INT, SqlType.BIGINT, SqlType.DECIMAL}


_PY_TYPES = {
    SqlType.BIT: bool,
    SqlType.INT: int,
    SqlType.BIGINT: int,
    SqlType.DECIMAL: Decimal,
    SqlType.VARCHAR: str,
    SqlType.NVARCHAR: str,
    SqlType.DATE: date,
    SqlType.DATETIME2: datetime,
}

Ident = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z_][A-Za-z0-9_]*$", max_length=128),
]

ACTIVE_FLAG = "is_active"


class ColumnMeta(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: Ident
    sql_type: SqlType
    nullable: bool = True
    primary_key: bool = False
    references: str | None = None
    default: Any = None
    max_length: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _pk_not_null(self) -> Self:
        if self.primary_key and self.nullable:
            raise ValueError(f"PK '{self.name}' cannot be nullable")
        return self

    def annotation(self) -> Any:
        t = self.sql_type.python_type
        if t is str and self.max_length:
            t = Annotated[str, StringConstraints(max_length=self.max_length)]
        return t | None if self.nullable else t


def _single_pk(table: TableMeta) -> str | None:
    if len(table.pk) != 1:
        return f"needs exactly 1 PK, has {len(table.pk)}"
    return None


def _has_attribute(table: TableMeta) -> str | None:
    if all(column.primary_key for column in table.columns):
        return "needs a non-key column"
    return None


def _has_fk(table: TableMeta) -> str | None:
    if not any(column.references for column in table.columns):
        return "needs an FK column"
    return None


def _has_measure(table: TableMeta) -> str | None:
    if not any(
        column.sql_type.is_numeric
        and not (column.primary_key or column.references)
        for column in table.columns
    ):
        return "needs a numeric measure"
    return None


def _composite_fk_pk(table: TableMeta) -> str | None:
    if len(table.pk) < 2 or not all(column.references for column in table.pk):
        return "PK must be 2+ FK columns"
    return None


def _active_list_shape(table: TableMeta) -> str | None:
    pk_name = table.table_type.strip_prefix(table.name)
    flag = next((column for column in table.columns if column.name == ACTIVE_FLAG), None)
    if (
        len(table.columns) != 2
        or not table.pk
        or table.pk[0].name != pk_name
    ):
        return f"must be exactly ({pk_name} PK, {ACTIVE_FLAG})"
    if (
        flag is None
        or flag.sql_type is not SqlType.BIT
        or flag.nullable
        or flag.default != 1
    ):
        return f"{ACTIVE_FLAG} must be BIT NOT NULL DEFAULT 1"
    return None


class TableType(StrEnum):
    ACTIVE_LIST = ("active_list", "al_", (_single_pk, _active_list_shape))
    LOOKUP = ("lookup", "lu_", (_single_pk, _has_attribute))
    DIMENSION = ("dimension", "dim_", (_single_pk, _has_attribute))
    FACT = ("fact", "fact_", (_has_fk, _has_measure))
    JUNCTION = ("junction", "jct_", (_composite_fk_pk,))
    STAGING = ("staging", "stg_", ())

    def __new__(cls, value: str, prefix: str, rules: tuple) -> Self:
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.prefix = prefix
        obj.rules = rules
        return obj

    def strip_prefix(self, table_name: str) -> str:
        return table_name.removeprefix(self.prefix)

    def scaffold(self, table_name: str) -> list[dict[str, Any]] | None:
        match self:
            case TableType.ACTIVE_LIST:
                return [
                    {
                        "name": self.strip_prefix(table_name),
                        "sql_type": "nvarchar",
                        "max_length": 100,
                        "primary_key": True,
                        "nullable": False,
                    },
                    {
                        "name": ACTIVE_FLAG,
                        "sql_type": "bit",
                        "nullable": False,
                        "default": True,
                    },
                ]
            case _:
                return None


class TableMeta(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: Ident
    table_type: TableType
    columns: tuple[ColumnMeta, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def _scaffold(cls, data: Any) -> Any:
        if isinstance(data, dict) and not data.get("columns"):
            try:
                table_type = TableType(data.get("table_type"))
            except ValueError:
                return data
            table_name = data.get("name")
            if not isinstance(table_name, str):
                table_name = ""
            columns = table_type.scaffold(table_name)
            if columns is not None:
                data = {**data, "columns": columns}
        return data

    @model_validator(mode="after")
    def _apply_type_rules(self) -> Self:
        errors = []
        if not self.name.startswith(self.table_type.prefix):
            errors.append(f"name must start with '{self.table_type.prefix}'")
        if len({column.name for column in self.columns}) != len(self.columns):
            errors.append("duplicate column names")
        errors.extend(
            message
            for rule in self.table_type.rules
            if (message := rule(self))
        )
        if errors:
            raise ValueError(f"{self.name}: " + "; ".join(errors))
        return self

    @property
    def pk(self) -> tuple[ColumnMeta, ...]:
        return tuple(column for column in self.columns if column.primary_key)

    @cached_property
    def row_model(self) -> type[BaseModel]:
        fields = {
            column.name: (
                column.annotation(),
                column.default
                if column.default is not None
                else (None if column.nullable else ...),
            )
            for column in self.columns
        }
        return create_model(
            f"{self.name}_row",
            __config__=ConfigDict(extra="forbid"),
            **fields,
        )

    def validate_rows(
        self, records: list[dict[str, Any]]
    ) -> tuple[list[BaseModel], list[tuple[int, ValidationError]]]:
        good = []
        bad = []
        for index, record in enumerate(records):
            try:
                good.append(self.row_model.model_validate(record))
            except ValidationError as error:
                bad.append((index, error))
        return good, bad
