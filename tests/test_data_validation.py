from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import ClassVar
import unittest

from pydantic import TypeAdapter, ValidationError

from data import (
    ColumnMeta,
    ColumnType,
    PrimaryKeyColumn,
    SqlType,
    TableMeta,
    TableType,
    ValidationReport,
)
from data_validation import ColumnMeta as CompatibilityColumnMeta


class SqlTypeTests(unittest.TestCase):
    def test_python_mappings_and_type_families(self) -> None:
        self.assertIs(SqlType.BIT.python_type, bool)
        self.assertIs(SqlType.DECIMAL.python_type, Decimal)
        self.assertTrue(SqlType.NUMERIC.is_numeric)
        self.assertTrue(SqlType.NVARCHAR.is_string)
        self.assertTrue(SqlType.DATETIME2.is_temporal)
        self.assertTrue(SqlType.BIT.is_boolean)
        self.assertTrue(SqlType.DECIMAL.supports_precision_scale)
        self.assertFalse(SqlType.INT.supports_precision_scale)


class ColumnMetaTests(unittest.TestCase):
    def test_column_type_defaults_and_invariants(self) -> None:
        primary_key = ColumnMeta(
            name="id", sql_type=SqlType.INT, column_type=ColumnType.PRIMARY_KEY
        )
        self.assertTrue(primary_key.primary_key)
        self.assertTrue(primary_key.indexed)
        self.assertFalse(primary_key.nullable)

        with self.assertRaises(ValidationError):
            ColumnMeta(
                name="missing_reference",
                sql_type=SqlType.INT,
                column_type=ColumnType.FOREIGN_KEY,
            )
        with self.assertRaises(ValidationError):
            ColumnMeta(
                name="bad_identity",
                sql_type=SqlType.NVARCHAR,
                column_type=ColumnType.IDENTITY,
            )
        with self.assertRaises(ValidationError):
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
        self.assertEqual(identity.default, 1)
        self.assertTrue(
            PrimaryKeyColumn(name="alternate_id", sql_type=SqlType.INT).primary_key
        )

    def test_metadata_constraints_compile_into_row_model(self) -> None:
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
        self.assertEqual(row.amount, Decimal("12.50"))
        for invalid in (
            {"code": "TOOLONG", "amount": "12.50", "observed_on": date(2024, 6, 1)},
            {"code": "XYZ", "amount": "12.50", "observed_on": date(2024, 6, 1)},
            {"code": "ABC", "amount": "100.00", "observed_on": date(2024, 6, 1)},
            {"code": "ABC", "amount": "12.345", "observed_on": date(2024, 6, 1)},
            {"code": "ABC", "amount": "12.50", "observed_on": date(2025, 1, 1)},
        ):
            with self.assertRaises(ValidationError):
                table.row_model.model_validate(invalid)

    def test_system_date_uses_utc_datetime_factory(self) -> None:
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
        self.assertIsInstance(row.loaded_at, datetime)
        self.assertEqual(row.loaded_at.tzinfo, timezone.utc)


class TableMetaTests(unittest.TestCase):
    def test_compatibility_import_and_json_catalog(self) -> None:
        self.assertIs(CompatibilityColumnMeta, ColumnMeta)
        tables = TypeAdapter(list[TableMeta]).validate_json(
            b'[{"name":"al_region","table_type":"active_list"}]'
        )
        self.assertEqual(tables[0].table_type, TableType.ACTIVE_LIST)

    def test_active_list_is_scaffolded_and_defaulted(self) -> None:
        table = TableMeta(name="al_region", table_type=TableType.ACTIVE_LIST)
        self.assertEqual([column.name for column in table.columns], ["region", "is_active"])
        self.assertEqual(table.columns[0].column_type, ColumnType.PRIMARY_KEY)
        row = table.row_model.model_validate({"region": "north"})
        self.assertTrue(row.is_active)

    def test_dimension_fact_and_junction_rules(self) -> None:
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
        self.assertEqual(len(dimension.pk), 1)
        self.assertEqual(fact.table_type, TableType.FACT)
        self.assertEqual(len(junction.pk), 2)

    def test_annotated_class_declaration_uses_same_rules(self) -> None:
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
        self.assertEqual([column.name for column in schema.columns], ["customer_id", "label"])

    def test_structured_report_and_legacy_validation_result(self) -> None:
        table = TableMeta(
            name="stg_measurements",
            table_type=TableType.STAGING,
            columns=(
                ColumnMeta(name="amount", sql_type=SqlType.DECIMAL, nullable=False),
            ),
        )
        records = [{"amount": "12.50"}, {"amount": "not-a-number"}, {"extra": 1}]
        report = table.validate_rows(records)
        self.assertIsInstance(report, ValidationReport)
        self.assertEqual(report.valid_count, 1)
        self.assertEqual(report.invalid_count, 2)
        self.assertEqual([error.row_index for error in report.invalid_rows], [1, 2])
        self.assertEqual(report.invalid_rows[0].errors[0].field, ("amount",))

        valid_rows, invalid_rows = table.validate_rows_legacy(records)
        self.assertEqual(len(valid_rows), 1)
        self.assertEqual([index for index, _ in invalid_rows], [1, 2])


if __name__ == "__main__":
    unittest.main()
