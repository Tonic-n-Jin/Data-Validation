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
from data_validator.columns.specs import (
    ColumnTypeSpec,
    get_column_type_spec,
    register_column_type,
    unregister_column_type,
)
from data_validator.registry import UnknownTypeError
from data_validator.rows.report import FieldError, RowValidationError, ValidationReport
from data_validator.tables.declaration import TableDeclarationMeta
from data_validator.tables.model import TableMeta
from data_validator.tables.specs import (
    TableTypeSpec,
    get_table_type_spec,
    register_table_type,
    unregister_table_type,
)
from data_validator.types.column_type import ColumnType
from data_validator.types.sql import SqlType
from data_validator.types.table_type import TableType

__version__ = "0.2.0"

__all__ = [
    "ACTIVE_FLAG",
    "ColumnMeta",
    "ColumnType",
    "ColumnTypeSpec",
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
    "TableTypeSpec",
    "UnknownTypeError",
    "ValidationReport",
    "__version__",
    "get_column_type_spec",
    "get_table_type_spec",
    "register_column_type",
    "register_table_type",
    "unregister_column_type",
    "unregister_table_type",
]
