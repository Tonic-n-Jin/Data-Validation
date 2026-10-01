"""Column metadata models."""

# Pydantic models are frozen, but Pyright still treats narrowed Literal field
# overrides as mutable/invariant.
# pyright: reportIncompatibleVariableOverride=false

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from operator import gt
from typing import Any, Literal, Self

from pydantic import BaseModel, Field, model_validator

from data_validator._base import MODEL_CONFIG, Ident, Reference
from data_validator.columns.annotations import build_annotation, build_field_info
from data_validator.columns.specs import COLUMN_TYPES, ColumnTypeKey, get_column_type_spec
from data_validator.registry import UnknownTypeError
from data_validator.types.column_type import ColumnType
from data_validator.types.sql import SqlType


class ColumnMeta(BaseModel):
    """Metadata and runtime validation rules for one physical column."""

    model_config = MODEL_CONFIG

    name: Ident
    sql_type: SqlType
    column_type: ColumnTypeKey = ColumnType.MISCELLANEOUS
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
        if isinstance(raw_type, str) and raw_type in COLUMN_TYPES:
            return get_column_type_spec(raw_type).apply_defaults(data)
        return data

    @model_validator(mode="after")
    def _validate_metadata(self) -> Self:
        if self.primary_key and self.nullable:
            raise ValueError(f"PK '{self.name}' cannot be nullable")
        if self.references and not (self.column_type == ColumnType.FOREIGN_KEY or self.primary_key):
            raise ValueError(f"Column '{self.name}' has references; use FOREIGN_KEY or a key type")
        if self.max_length is not None and not self.sql_type.is_string:
            raise ValueError("max_length is only valid for string SQL types")
        if self.regex_pattern is not None and not self.sql_type.is_string:
            raise ValueError("regex_pattern is only valid for string SQL types")
        if (
            self.precision is not None or self.scale is not None
        ) and not self.sql_type.supports_precision_scale:
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
                raise ValueError("min_value and max_value must be mutually comparable") from error
            if bounds_are_reversed:
                raise ValueError("min_value cannot exceed max_value")
        try:
            spec = get_column_type_spec(self.column_type)
        except UnknownTypeError as error:
            raise ValueError(str(error)) from error
        violation = spec.check(self)
        if violation:
            raise ValueError(f"{self.column_type} column '{self.name}' {violation}")
        return self

    def annotation(self) -> Any:
        """Build a Pydantic-compatible constrained annotation for this column."""
        return build_annotation(self)

    def field_info(self) -> Any:
        return build_field_info(self)


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
