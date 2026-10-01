"""Table schema model."""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, ClassVar, Self

from pydantic import BaseModel, ValidationError, model_validator

from data_validator._base import MODEL_CONFIG, Ident
from data_validator.columns.model import ColumnMeta
from data_validator.registry import UnknownTypeError
from data_validator.rows.engine import build_report, validate_records
from data_validator.rows.factory import build_row_model
from data_validator.tables import builtins as _builtins  # noqa: F401  (registers built-ins)
from data_validator.tables.declaration import TableDeclarationMeta
from data_validator.tables.specs import TABLE_TYPES, TableTypeKey, get_table_type_spec

if TYPE_CHECKING:
    from data_validator.rows.report import ValidationReport


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
        return build_row_model(self.name, self.columns)

    def validate_rows(self, records: list[dict[str, Any]]) -> ValidationReport:
        return build_report(*validate_records(self.row_model, records))

    def validate_rows_legacy(
        self, records: list[dict[str, Any]]
    ) -> tuple[list[BaseModel], list[tuple[int, ValidationError]]]:
        """Return the pre-structured-report validation result shape."""
        return validate_records(self.row_model, records)
