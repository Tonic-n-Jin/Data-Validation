from __future__ import annotations

from typing import ClassVar

import pytest
from pydantic import ValidationError

from data_validator import ColumnMeta, ColumnType, SqlType, TableMeta, TableType


def test_annotated_class_declaration_uses_same_rules() -> None:
    class Customer(TableMeta):
        name: str = "dim_customer"
        table_type: TableType = TableType.DIMENSION
        customer_id: ClassVar[ColumnMeta] = ColumnMeta(
            name="customer_id",
            sql_type=SqlType.INT,
            column_type=ColumnType.PRIMARY_KEY,
        )
        label: ClassVar[ColumnMeta] = ColumnMeta(
            name="label", sql_type=SqlType.NVARCHAR, max_length=50
        )

    schema = Customer()
    assert [column.name for column in schema.columns] == ["customer_id", "label"]


def test_declared_columns_are_inherited() -> None:
    class Base(TableMeta):
        customer_id: ClassVar[ColumnMeta] = ColumnMeta(
            name="customer_id", sql_type=SqlType.INT, column_type=ColumnType.PRIMARY_KEY
        )

    class Customer(Base):
        name: str = "dim_customer"
        table_type: TableType = TableType.DIMENSION
        label: ClassVar[ColumnMeta] = ColumnMeta(name="label", sql_type=SqlType.NVARCHAR)

    assert [column.name for column in Customer().columns] == ["customer_id", "label"]


def test_declared_tables_enforce_table_rules() -> None:
    class Broken(TableMeta):
        name: str = "dim_broken"
        table_type: TableType = TableType.DIMENSION
        label: ClassVar[ColumnMeta] = ColumnMeta(name="label", sql_type=SqlType.NVARCHAR)

    with pytest.raises(ValidationError, match="needs exactly 1 PK"):
        Broken()
