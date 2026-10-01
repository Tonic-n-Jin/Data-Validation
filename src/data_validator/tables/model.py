"""Table schema model."""

from __future__ import annotations

from functools import cached_property
from typing import Any, ClassVar, Self

from pydantic import BaseModel, Field, ValidationError, create_model, model_validator

from data_validator._base import MODEL_CONFIG, ROW_CONFIG, Ident
from data_validator.columns.model import ColumnMeta
from data_validator.registry import UnknownTypeError
from data_validator.tables import builtins as _builtins  # noqa: F401  (registers built-ins)
from data_validator.tables.declaration import TableDeclarationMeta
from data_validator.tables.specs import TABLE_TYPES, TableTypeKey, get_table_type_spec


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
    table_type: TableTypeKey
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
        table_type, table_name = data.get("table_type"), data.get("name")
        if (
            not data.get("columns")
            and isinstance(table_type, str)
            and table_type in TABLE_TYPES
            and isinstance(table_name, str)
        ):
            scaffold = get_table_type_spec(table_type).scaffold
            if scaffold is not None:
                data["columns"] = scaffold(table_name)
        return data

    @model_validator(mode="after")
    def _apply_table_type_rules(self) -> Self:
        try:
            spec = get_table_type_spec(self.table_type)
        except UnknownTypeError as error:
            raise ValueError(str(error)) from error
        errors: list[str] = []
        if not self.name.startswith(spec.prefix):
            errors.append(f"name must start with '{spec.prefix}'")
        if len({column.name for column in self.columns}) != len(self.columns):
            errors.append("duplicate column names")
        errors.extend(spec.rules(self))
        if errors:
            raise ValueError(f"{self.name}: " + "; ".join(errors))
        return self

    @property
    def pk(self) -> tuple[ColumnMeta, ...]:
        return tuple(column for column in self.columns if column.primary_key)

    @cached_property
    def row_model(self) -> type[BaseModel]:
        field_definitions: dict[str, Any] = {
            column.name: (column.annotation(), column.field_info()) for column in self.columns
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
