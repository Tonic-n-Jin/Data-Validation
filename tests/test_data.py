from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import ClassVar

import pytest
from pydantic import ValidationError

from data_validator import (
    ColumnMeta,
    ColumnType,
    PrimaryKeyColumn,
    SqlType,
    TableMeta,
    TableType,
    ValidationReport,
)


def test_python_mappings_and_type_families() -> None:
    assert SqlType.BIT.python_type is bool
    assert SqlType.DECIMAL.python_type is Decimal
    assert SqlType.NUMERIC.is_numeric
    assert SqlType.NVARCHAR.is_string
    assert SqlType.DATETIME2.is_temporal
    assert SqlType.BIT.is_boolean
    assert SqlType.DECIMAL.supports_precision_scale
    assert not SqlType.INT.supports_precision_scale


def test_column_type_defaults_and_invariants() -> None:
    primary_key = ColumnMeta(name="id", sql_type=SqlType.INT, column_type=ColumnType.PRIMARY_KEY)
    assert primary_key.primary_key
    assert primary_key.indexed
    assert not primary_key.nullable

    with pytest.raises(ValidationError):
        ColumnMeta(
            name="missing_reference",
            sql_type=SqlType.INT,
            column_type=ColumnType.FOREIGN_KEY,
        )
    with pytest.raises(ValidationError):
        ColumnMeta(
            name="bad_identity",
            sql_type=SqlType.NVARCHAR,
            column_type=ColumnType.IDENTITY,
        )
    with pytest.raises(ValidationError):
        ColumnMeta(
            name="generated_id",
            sql_type=SqlType.INT,
            column_type=ColumnType.IDENTITY,
            default=1,
        )
    identity = ColumnMeta(
        name="generated_id",
        sql_type=SqlType.BIGINT,
        column_type=ColumnType.IDENTITY,
        default=1,
        allow_manual_default=True,
    )
    assert identity.default == 1
    assert PrimaryKeyColumn(name="alternate_id", sql_type=SqlType.INT).primary_key


def test_metadata_constraints_compile_into_row_model() -> None:
    table = TableMeta(
        name="stg_measurements",
        table_type=TableType.STAGING,
        columns=(
            ColumnMeta(
                name="code",
                sql_type=SqlType.NVARCHAR,
                nullable=False,
                max_length=3,
                regex_pattern=r"^[A-Z]+$",
                allowed_values=frozenset({"ABC", "DEF"}),
                is_sensitive=True,
            ),
            ColumnMeta(
                name="amount",
                sql_type=SqlType.DECIMAL,
                nullable=False,
                precision=5,
                scale=2,
                min_value=Decimal("1.00"),
                max_value=Decimal("99.99"),
            ),
            ColumnMeta(
                name="observed_on",
                sql_type=SqlType.DATE,
                nullable=False,
                min_value=date(2024, 1, 1),
                max_value=date(2024, 12, 31),
            ),
        ),
    )
    row = table.row_model.model_validate(
        {
            "code": "ABC",
            "amount": "12.50",
            "observed_on": date(2024, 6, 1),
        }
    )
    assert row.amount == Decimal("12.50")
    for invalid in (
        {"code": "TOOLONG", "amount": "12.50", "observed_on": date(2024, 6, 1)},
        {"code": "XYZ", "amount": "12.50", "observed_on": date(2024, 6, 1)},
        {"code": "ABC", "amount": "100.00", "observed_on": date(2024, 6, 1)},
        {"code": "ABC", "amount": "12.345", "observed_on": date(2024, 6, 1)},
        {"code": "ABC", "amount": "12.50", "observed_on": date(2025, 1, 1)},
    ):
        with pytest.raises(ValidationError):
            table.row_model.model_validate(invalid)


def test_system_date_uses_utc_datetime_factory() -> None:
    table = TableMeta(
        name="stg_audit",
        table_type=TableType.STAGING,
        columns=(
            ColumnMeta(
                name="loaded_at",
                sql_type=SqlType.DATETIME2,
                column_type=ColumnType.SYSTEM_DATE,
            ),
        ),
    )
    row = table.row_model.model_validate({})
    assert isinstance(row.loaded_at, datetime)
    assert row.loaded_at.tzinfo == timezone.utc


def test_active_list_is_scaffolded_and_defaulted() -> None:
    table = TableMeta(name="al_region", table_type=TableType.ACTIVE_LIST)
    assert [column.name for column in table.columns] == ["region", "is_active"]
    assert table.columns[0].column_type == ColumnType.PRIMARY_KEY
    row = table.row_model.model_validate({"region": "north"})
    assert row.is_active


def test_dimension_fact_and_junction_rules() -> None:
    dimension = TableMeta(
        name="dim_customer",
        table_type=TableType.DIMENSION,
        columns=(
            ColumnMeta(
                name="customer_id",
                sql_type=SqlType.INT,
                column_type=ColumnType.PRIMARY_KEY,
            ),
            ColumnMeta(name="name", sql_type=SqlType.NVARCHAR),
        ),
    )
    fact = TableMeta(
        name="fact_sales",
        table_type=TableType.FACT,
        columns=(
            ColumnMeta(
                name="customer_id",
                sql_type=SqlType.INT,
                column_type=ColumnType.FOREIGN_KEY,
                references="dim_customer.customer_id",
            ),
            ColumnMeta(name="amount", sql_type=SqlType.DECIMAL),
        ),
    )
    junction = TableMeta(
        name="jct_customer_region",
        table_type=TableType.JUNCTION,
        columns=(
            ColumnMeta(
                name="customer_id",
                sql_type=SqlType.INT,
                column_type=ColumnType.COMPOSITE_KEY,
                references="dim_customer.customer_id",
            ),
            ColumnMeta(
                name="region_id",
                sql_type=SqlType.INT,
                column_type=ColumnType.COMPOSITE_KEY,
                references="al_region.region",
            ),
        ),
    )
    assert len(dimension.pk) == 1
    assert fact.table_type == TableType.FACT
    assert len(junction.pk) == 2


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


def test_structured_report_and_legacy_validation_result() -> None:
    table = TableMeta(
        name="stg_measurements",
        table_type=TableType.STAGING,
        columns=(ColumnMeta(name="amount", sql_type=SqlType.DECIMAL, nullable=False),),
    )
    records = [{"amount": "12.50"}, {"amount": "not-a-number"}, {"extra": 1}]
    report = table.validate_rows(records)
    assert isinstance(report, ValidationReport)
    assert report.valid_count == 1
    assert report.invalid_count == 2
    assert [error.row_index for error in report.invalid_rows] == [1, 2]
    assert report.invalid_rows[0].errors[0].field == ("amount",)

    valid_rows, invalid_rows = table.validate_rows_legacy(records)
    assert len(valid_rows) == 1
    assert [index for index, _ in invalid_rows] == [1, 2]
