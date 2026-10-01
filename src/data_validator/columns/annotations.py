"""Compile column metadata into Pydantic field annotations and defaults."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Annotated, Any

from pydantic import AfterValidator, BeforeValidator, Field, StringConstraints

from data_validator.columns.constraints import (
    allowed_values_validator,
    decimal_precision_validator,
    parse_decimal,
    utc_now,
)
from data_validator.types.sql import SqlType

if TYPE_CHECKING:
    from data_validator.columns.model import ColumnMeta


def build_annotation(column: ColumnMeta) -> Any:
    """Build a Pydantic-compatible constrained annotation for one column."""
    base = column.sql_type.python_type
    metadata: list[Any] = []
    if column.sql_type.is_string:
        metadata.append(
            StringConstraints(max_length=column.max_length, pattern=column.regex_pattern)
        )
    if column.sql_type.supports_precision_scale:
        metadata.append(BeforeValidator(parse_decimal))
        if column.precision is not None:
            metadata.append(
                AfterValidator(decimal_precision_validator(column.precision, column.scale or 0))
            )
    if column.min_value is not None or column.max_value is not None:
        metadata.append(Field(ge=column.min_value, le=column.max_value))
    if column.allowed_values is not None:
        metadata.append(AfterValidator(allowed_values_validator(column.allowed_values)))
    annotation: Any = Annotated[base, *metadata] if metadata else base
    return annotation | None if column.nullable else annotation


def build_field_info(column: ColumnMeta) -> Any:
    """Choose the row-model default for one column."""
    if column.auto_utc:
        factory = utc_now if column.sql_type is SqlType.DATETIME2 else date.today
        return Field(default_factory=factory, description=column.description)
    if column.default is not None:
        return Field(default=column.default, description=column.description)
    if column.nullable:
        return Field(default=None, description=column.description)
    return Field(..., description=column.description)
