"""Strict, declarative data warehouse schema and runtime row validation."""

from data_validator._base import ACTIVE_FLAG, Ident, Reference
from data_validator.columns.model import (
    ColumnMeta,
    CompositeKeyColumn,
    ForeignKeyColumn,
    IdentityColumn,
    PrimaryKeyColumn,
    SystemDateColumn,
)
from data_validator.tables.declaration import TableDeclarationMeta
from data_validator.tables.model import (
    FieldError,
    RowValidationError,
    TableMeta,
    ValidationReport,
)
from data_validator.types.column_type import ColumnType
from data_validator.types.sql import SqlType
from data_validator.types.table_type import TableType

__version__ = "0.2.0"

__all__ = [
    "ACTIVE_FLAG",
    "ColumnMeta",
    "ColumnType",
    "CompositeKeyColumn",
    "FieldError",
    "ForeignKeyColumn",
    "Ident",
    "IdentityColumn",
    "PrimaryKeyColumn",
    "Reference",
    "RowValidationError",
    "SqlType",
    "SystemDateColumn",
    "TableDeclarationMeta",
    "TableMeta",
    "TableType",
    "ValidationReport",
    "__version__",
]
