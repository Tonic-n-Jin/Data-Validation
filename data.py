"""Strict, declarative data warehouse schema and runtime row validation."""

# Pylance suppressions:
# Pydantic models are frozen, but Pyright still treats narrowed Literal field
# overrides as mutable/invariant.
# pyright: reportIncompatibleVariableOverride=false

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from functools import cached_property
from operator import gt
from typing import Annotated, Any, ClassVar, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    create_model,
    model_validator,
)
from pydantic._internal._model_construction import ModelMetaclass

MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=False)
ROW_CONFIG = ConfigDict(
    frozen=True, extra="forbid", arbitrary_types_allowed=False, strict=True
)
Ident = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z_][A-Za-z0-9_]*$", max_length=128),
]
Reference = Annotated[
    str,
    StringConstraints(
        pattern=r"^[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*$",
        max_length=257,
    ),
]
ACTIVE_FLAG = "is_active"


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


class ColumnMeta(BaseModel):
    """Metadata and runtime validation rules for one physical column."""

    model_config = MODEL_CONFIG

    name: Ident
    sql_type: SqlType
    column_type: ColumnType = ColumnType.MISCELLANEOUS
    nullable: bool = True
    primary_key: bool = False
    indexed: bool = False
    references: Reference | None = None
    default: Any = None
    allow_manual_default: bool = False
    auto_utc: bool = False
    max_length: int | None = Field(default=None, gt=0)
    precision: int | None = Field(default=None, ge=1, le=38)
    scale: int | None = Field(default=None, ge=0, le=38)
    min_value: int | float | Decimal | date | datetime | None = None
    max_value: int | float | Decimal | date | datetime | None = None
    regex_pattern: str | None = None
    allowed_values: frozenset[Any] | None = None
    description: str | None = Field(default=None, max_length=1_000)
    is_sensitive: bool = False

    @model_validator(mode="before")
    @classmethod
    def _apply_column_type_defaults(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        raw_type = data.get("column_type", cls.model_fields["column_type"].default)
        try:
            return ColumnType(raw_type).defaults(data)
        except ValueError:
            return data

    @model_validator(mode="after")
    def _validate_metadata(self) -> Self:
        if self.primary_key and self.nullable:
            raise ValueError(f"PK '{self.name}' cannot be nullable")
        if self.references and not (
            self.column_type is ColumnType.FOREIGN_KEY or self.primary_key
        ):
            raise ValueError(
                f"Column '{self.name}' has references; use FOREIGN_KEY or a key type"
            )
        if self.max_length is not None and not self.sql_type.is_string:
            raise ValueError("max_length is only valid for string SQL types")
        if self.regex_pattern is not None and not self.sql_type.is_string:
            raise ValueError("regex_pattern is only valid for string SQL types")
        if (self.precision is not None or self.scale is not None) and not (
            self.sql_type.supports_precision_scale
        ):
            raise ValueError("precision and scale are only valid for DECIMAL or NUMERIC")
        if self.scale is not None and self.precision is None:
            raise ValueError("scale requires precision")
        if self.precision is not None and self.scale is not None and self.scale > self.precision:
            raise ValueError("scale cannot exceed precision")
        if (self.min_value is not None or self.max_value is not None) and not (
            self.sql_type.is_numeric or self.sql_type.is_temporal
        ):
            raise ValueError("min_value and max_value require numeric or temporal types")
        if self.min_value is not None and self.max_value is not None:
            try:
                bounds_are_reversed = gt(self.min_value, self.max_value)
            except TypeError as error:
                raise ValueError(
                    "min_value and max_value must be mutually comparable"
                ) from error
            if bounds_are_reversed:
                raise ValueError("min_value cannot exceed max_value")
        violation = self.column_type.violation(self)
        if violation:
            raise ValueError(f"{self.column_type.value} column '{self.name}' {violation}")
        return self

    def annotation(self) -> Any:
        """Build a Pydantic-compatible constrained annotation for this column."""
        base = self.sql_type.python_type
        metadata: list[Any] = []
        if self.sql_type.is_string:
            metadata.append(
                StringConstraints(
                    max_length=self.max_length, pattern=self.regex_pattern
                )
            )
        if self.sql_type in {SqlType.DECIMAL, SqlType.NUMERIC}:
            metadata.append(BeforeValidator(_parse_decimal))
            if self.precision is not None:
                metadata.append(
                    AfterValidator(
                        _decimal_precision_validator(self.precision, self.scale or 0)
                    )
                )
        if self.min_value is not None or self.max_value is not None:
            metadata.append(Field(ge=self.min_value, le=self.max_value))
        if self.allowed_values is not None:
            metadata.append(AfterValidator(_allowed_values_validator(self.allowed_values)))
        annotation: Any = Annotated[base, *metadata] if metadata else base
        return annotation | None if self.nullable else annotation

    def field_info(self) -> Any:
        if self.auto_utc:
            factory = _utc_now if self.sql_type is SqlType.DATETIME2 else date.today
            return Field(default_factory=factory, description=self.description)
        if self.default is not None:
            return Field(default=self.default, description=self.description)
        if self.nullable:
            return Field(default=None, description=self.description)
        return Field(..., description=self.description)


class PrimaryKeyColumn(ColumnMeta):
    column_type: Literal[ColumnType.PRIMARY_KEY] = ColumnType.PRIMARY_KEY


class ForeignKeyColumn(ColumnMeta):
    column_type: Literal[ColumnType.FOREIGN_KEY] = ColumnType.FOREIGN_KEY


class IdentityColumn(ColumnMeta):
    column_type: Literal[ColumnType.IDENTITY] = ColumnType.IDENTITY


class CompositeKeyColumn(ColumnMeta):
    column_type: Literal[ColumnType.COMPOSITE_KEY] = ColumnType.COMPOSITE_KEY


class SystemDateColumn(ColumnMeta):
    column_type: Literal[ColumnType.SYSTEM_DATE] = ColumnType.SYSTEM_DATE


def _parse_decimal(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return Decimal(value)
        except InvalidOperation as error:
            raise ValueError("must be a valid decimal value") from error
    return value


def _decimal_precision_validator(precision: int, scale: int):
    def validate(value: Decimal) -> Decimal:
        if not value.is_finite():
            raise ValueError("must be a finite decimal value")
        digits = value.as_tuple().digits
        exponent = value.as_tuple().exponent
        if not isinstance(exponent, int):
            raise ValueError("must be a finite decimal value")
        decimals = max(-exponent, 0)
        integer_digits = len(digits) - decimals
        if decimals > scale or integer_digits + decimals > precision:
            raise ValueError(
                f"must fit DECIMAL({precision}, {scale}); received {value}"
            )
        return value

    return validate


def _allowed_values_validator(allowed_values: frozenset[Any]):
    def validate(value: Any) -> Any:
        if value not in allowed_values:
            raise ValueError(f"must be one of {sorted(map(str, allowed_values))}")
        return value

    return validate


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TableType(StrEnum):
    ACTIVE_LIST = "active_list"
    LOOKUP = "lookup"
    DIMENSION = "dimension"
    FACT = "fact"
    JUNCTION = "junction"
    STAGING = "staging"

    @property
    def prefix(self) -> str:
        return {
            TableType.ACTIVE_LIST: "al_",
            TableType.LOOKUP: "lu_",
            TableType.DIMENSION: "dim_",
            TableType.FACT: "fact_",
            TableType.JUNCTION: "jct_",
            TableType.STAGING: "stg_",
        }[self]

    def strip_prefix(self, table_name: str) -> str:
        return table_name.removeprefix(self.prefix)

    def scaffold(self, table_name: str) -> tuple[ColumnMeta, ...]:
        if self is not TableType.ACTIVE_LIST:
            return ()
        return (
            ColumnMeta(
                name=self.strip_prefix(table_name),
                sql_type=SqlType.NVARCHAR,
                column_type=ColumnType.PRIMARY_KEY,
                max_length=100,
            ),
            ColumnMeta(
                name=ACTIVE_FLAG,
                sql_type=SqlType.BIT,
                nullable=False,
                default=True,
            ),
        )


class TableDeclarationMeta(ModelMetaclass):
    """Collect `ColumnMeta` class attributes into an annotated table declaration."""

    def __new__(
        mcls, name: str, bases: tuple[type[Any], ...], namespace: dict[str, Any], **kwargs: Any
    ) -> type[Any]:
        declared = tuple(
            value for value in namespace.values() if isinstance(value, ColumnMeta)
        )
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        inherited = tuple(
            column
            for base in bases
            for column in getattr(base, "__declared_columns__", ())
        )
        cls.__declared_columns__ = inherited + declared
        return cls


class FieldError(BaseModel):
    model_config = MODEL_CONFIG

    field: tuple[str | int, ...]
    message: str
    error_type: str


class RowValidationError(BaseModel):
    model_config = MODEL_CONFIG

    row_index: int = Field(ge=0)
    errors: tuple[FieldError, ...]


class ValidationReport(BaseModel):
    model_config = MODEL_CONFIG

    valid_rows: tuple[BaseModel, ...]
    invalid_rows: tuple[RowValidationError, ...]

    @property
    def valid_count(self) -> int:
        return len(self.valid_rows)

    @property
    def invalid_count(self) -> int:
        return len(self.invalid_rows)


class TableMeta(BaseModel, metaclass=TableDeclarationMeta):
    """A table schema that can be built directly or declared as a Python class."""

    model_config = MODEL_CONFIG

    name: Ident
    table_type: TableType
    columns: tuple[ColumnMeta, ...] = ()
    __declared_columns__: ClassVar[tuple[ColumnMeta, ...]] = ()

    @model_validator(mode="before")
    @classmethod
    def _scaffold_or_declare(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if not data.get("columns") and cls.__declared_columns__:
            data["columns"] = cls.__declared_columns__
        if not data.get("columns"):
            try:
                table_type = TableType(data.get("table_type"))
            except ValueError:
                return data
            table_name = data.get("name")
            if isinstance(table_name, str):
                columns = table_type.scaffold(table_name)
                if columns:
                    data["columns"] = columns
        return data

    @model_validator(mode="after")
    def _apply_table_type_rules(self) -> Self:
        errors: list[str] = []
        if not self.name.startswith(self.table_type.prefix):
            errors.append(f"name must start with '{self.table_type.prefix}'")
        if len({column.name for column in self.columns}) != len(self.columns):
            errors.append("duplicate column names")
        errors.extend(self._type_rule_errors())
        if errors:
            raise ValueError(f"{self.name}: " + "; ".join(errors))
        return self

    def _type_rule_errors(self) -> list[str]:
        if self.table_type is TableType.ACTIVE_LIST:
            expected_pk = self.table_type.strip_prefix(self.name)
            if len(self.columns) != 2 or len(self.pk) != 1 or self.pk[0].name != expected_pk:
                return [f"must be exactly ({expected_pk} PK, {ACTIVE_FLAG})"]
            flag = next((column for column in self.columns if column.name == ACTIVE_FLAG), None)
            if (
                flag is None
                or flag.sql_type is not SqlType.BIT
                or flag.nullable
                or flag.default is not True
            ):
                return [f"{ACTIVE_FLAG} must be BIT NOT NULL DEFAULT True"]
        if self.table_type in {TableType.LOOKUP, TableType.DIMENSION}:
            if len(self.pk) != 1:
                return [f"needs exactly 1 PK, has {len(self.pk)}"]
            if all(column.primary_key for column in self.columns):
                return ["needs a non-key column"]
        if self.table_type is TableType.FACT:
            errors = []
            if not any(column.references for column in self.columns):
                errors.append("needs an FK column")
            if not any(
                column.sql_type.is_numeric
                and not (column.primary_key or column.references)
                for column in self.columns
            ):
                errors.append("needs a numeric measure")
            return errors
        if self.table_type is TableType.JUNCTION and (
            len(self.pk) < 2 or not all(column.references for column in self.pk)
        ):
            return ["PK must be 2+ FK columns"]
        return []

    @property
    def pk(self) -> tuple[ColumnMeta, ...]:
        return tuple(column for column in self.columns if column.primary_key)

    @cached_property
    def row_model(self) -> type[BaseModel]:
        field_definitions: dict[str, Any] = {
            column.name: (column.annotation(), column.field_info())
            for column in self.columns
        }
        return create_model(
            f"{''.join(part.title() for part in self.name.split('_'))}Row",
            __config__=ROW_CONFIG,
            **field_definitions,
        )

    def validate_rows(self, records: list[dict[str, Any]]) -> ValidationReport:
        valid_rows, invalid_rows = self._validate_rows(records)
        return ValidationReport(
            valid_rows=tuple(valid_rows),
            invalid_rows=tuple(
                RowValidationError(
                    row_index=index,
                    errors=tuple(
                        FieldError(
                            field=tuple(error["loc"]),
                            message=error["msg"],
                            error_type=error["type"],
                        )
                        for error in validation_error.errors()
                    ),
                )
                for index, validation_error in invalid_rows
            ),
        )

    def validate_rows_legacy(
        self, records: list[dict[str, Any]]
    ) -> tuple[list[BaseModel], list[tuple[int, ValidationError]]]:
        """Return the pre-structured-report validation result shape."""
        return self._validate_rows(records)

    def _validate_rows(
        self, records: list[dict[str, Any]]
    ) -> tuple[list[BaseModel], list[tuple[int, ValidationError]]]:
        valid_rows: list[BaseModel] = []
        invalid_rows: list[tuple[int, ValidationError]] = []
        for row_index, record in enumerate(records):
            try:
                valid_rows.append(self.row_model.model_validate(record))
            except ValidationError as error:
                invalid_rows.append((row_index, error))
        return valid_rows, invalid_rows


__all__ = [
    "ACTIVE_FLAG",
    "ColumnMeta",
    "ColumnType",
    "CompositeKeyColumn",
    "FieldError",
    "ForeignKeyColumn",
    "IdentityColumn",
    "Ident",
    "PrimaryKeyColumn",
    "RowValidationError",
    "SqlType",
    "SystemDateColumn",
    "TableDeclarationMeta",
    "TableMeta",
    "TableType",
    "ValidationReport",
]
