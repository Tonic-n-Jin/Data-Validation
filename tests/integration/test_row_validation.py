from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from data_validator import ColumnMeta, ColumnType, SqlType, TableMeta, TableType, ValidationReport


@pytest.fixture
def measurements() -> TableMeta:
    return TableMeta(
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


def test_metadata_constraints_compile_into_row_model(measurements: TableMeta) -> None:
    row = measurements.row_model.model_validate(
        {"code": "ABC", "amount": "12.50", "observed_on": date(2024, 6, 1)}
    )
    assert row.amount == Decimal("12.50")  # type: ignore[attr-defined]
    assert measurements.row_model.__name__ == "StgMeasurementsRow"


@pytest.mark.parametrize(
    "invalid",
    [
        {"code": "TOOLONG", "amount": "12.50", "observed_on": date(2024, 6, 1)},
        {"code": "XYZ", "amount": "12.50", "observed_on": date(2024, 6, 1)},
        {"code": "ABC", "amount": "100.00", "observed_on": date(2024, 6, 1)},
        {"code": "ABC", "amount": "12.345", "observed_on": date(2024, 6, 1)},
        {"code": "ABC", "amount": "12.50", "observed_on": date(2025, 1, 1)},
        {"code": "ABC", "amount": "12.50", "observed_on": "2024-06-01"},
        {"code": "ABC", "amount": "12.50", "observed_on": date(2024, 6, 1), "extra": 1},
    ],
)
def test_row_model_rejects_invalid_records(
    measurements: TableMeta, invalid: dict[str, Any]
) -> None:
    with pytest.raises(ValidationError):
        measurements.row_model.model_validate(invalid)


def test_row_model_is_strict_and_frozen() -> None:
    table = TableMeta(
        name="stg_counts",
        table_type=TableType.STAGING,
        columns=(ColumnMeta(name="total", sql_type=SqlType.INT, nullable=False),),
    )
    with pytest.raises(ValidationError):
        table.row_model.model_validate({"total": "1"})
    row = table.row_model.model_validate({"total": 1})
    with pytest.raises(ValidationError):
        row.total = 2  # type: ignore[attr-defined]


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
    assert isinstance(row.loaded_at, datetime)  # type: ignore[attr-defined]
    assert row.loaded_at.tzinfo == UTC  # type: ignore[attr-defined]


def test_active_list_row_defaults() -> None:
    table = TableMeta(name="al_region", table_type=TableType.ACTIVE_LIST)
    row = table.row_model.model_validate({"region": "north"})
    assert row.is_active  # type: ignore[attr-defined]


def test_structured_report_and_legacy_validation_result() -> None:
    table = TableMeta(
        name="stg_measurements",
        table_type=TableType.STAGING,
        columns=(ColumnMeta(name="amount", sql_type=SqlType.DECIMAL, nullable=False),),
    )
    records: list[dict[str, Any]] = [{"amount": "12.50"}, {"amount": "not-a-number"}, {"extra": 1}]
    report = table.validate_rows(records)
    assert isinstance(report, ValidationReport)
    assert report.valid_count == 1
    assert report.invalid_count == 2
    assert [error.row_index for error in report.invalid_rows] == [1, 2]
    assert report.invalid_rows[0].errors[0].field == ("amount",)
    assert report.invalid_rows[0].errors[0].error_type == "value_error"

    valid_rows, invalid_rows = table.validate_rows_legacy(records)
    assert len(valid_rows) == 1
    assert [index for index, _ in invalid_rows] == [1, 2]
