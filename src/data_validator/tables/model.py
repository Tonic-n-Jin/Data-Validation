"""Table schema model."""

from __future__ import annotations

from functools import cached_property
from typing import Any, ClassVar, Self

from pydantic import BaseModel, Field, ValidationError, create_model, model_validator

from data_validator._base import ACTIVE_FLAG, MODEL_CONFIG, ROW_CONFIG, Ident
from data_validator.columns.model import ColumnMeta
from data_validator.tables.declaration import TableDeclarationMeta
from data_validator.types.sql import SqlType
from data_validator.types.table_type import TableType


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
                column.sql_type.is_numeric and not (column.primary_key or column.references)
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
