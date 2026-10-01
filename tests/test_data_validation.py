import unittest
from decimal import Decimal

from pydantic import TypeAdapter, ValidationError

from data_validation import ColumnMeta, SqlType, TableMeta, TableType


class SqlTypeTests(unittest.TestCase):
    def test_python_types_and_numeric_classification(self):
        self.assertIs(SqlType.BIT.python_type, bool)
        self.assertIs(SqlType.DECIMAL.python_type, Decimal)
        self.assertTrue(SqlType.BIGINT.is_numeric)
        self.assertFalse(SqlType.NVARCHAR.is_numeric)


class ColumnMetaTests(unittest.TestCase):
    def test_primary_key_must_be_non_nullable(self):
        with self.assertRaises(ValidationError):
            ColumnMeta(name="id", sql_type=SqlType.INT, primary_key=True)

    def test_string_length_is_applied_to_row_annotation(self):
        column = ColumnMeta(
            name="label", sql_type=SqlType.NVARCHAR, max_length=3
        )
        with self.assertRaises(ValidationError):
            TableMeta(
                name="stg_input",
                table_type=TableType.STAGING,
                columns=(column,),
            ).row_model.model_validate({"label": "long"})


class TableMetaTests(unittest.TestCase):
    def test_table_catalog_can_be_validated_from_json(self):
        tables = TypeAdapter(list[TableMeta]).validate_json(
            b'[{"name":"al_region","table_type":"active_list"}]'
        )
        self.assertEqual(tables[0].table_type, TableType.ACTIVE_LIST)

    def test_invalid_active_list_name_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            TableMeta.model_validate(
                {"name": None, "table_type": "active_list"}
            )

    def test_active_list_is_scaffolded_and_defaulted(self):
        table = TableMeta.model_validate(
            {"name": "al_region", "table_type": "active_list"}
        )
        self.assertEqual([column.name for column in table.columns], ["region", "is_active"])
        self.assertEqual(table.columns[0].sql_type, SqlType.NVARCHAR)
        row = table.row_model.model_validate({"region": "north"})
        self.assertTrue(row.is_active)

    def test_type_rules_enforce_prefix_pk_and_duplicates(self):
        with self.assertRaises(ValidationError):
            TableMeta.model_validate(
                {
                    "name": "lu_status",
                    "table_type": "lookup",
                    "columns": [
                        {
                            "name": "id",
                            "sql_type": "int",
                            "primary_key": True,
                            "nullable": False,
                        }
                    ],
                }
            )

        with self.assertRaises(ValidationError):
            TableMeta.model_validate(
                {
                    "name": "wrong_name",
                    "table_type": "staging",
                }
            )

        with self.assertRaises(ValidationError):
            TableMeta.model_validate(
                {
                    "name": "stg_duplicate",
                    "table_type": "staging",
                    "columns": [
                        {"name": "value", "sql_type": "int"},
                        {"name": "value", "sql_type": "int"},
                    ],
                }
            )

    def test_fact_requires_fk_and_non_key_numeric_measure(self):
        TableMeta.model_validate(
            {
                "name": "fact_sales",
                "table_type": "fact",
                "columns": [
                    {
                        "name": "customer_id",
                        "sql_type": "int",
                        "nullable": False,
                        "references": "dim_customer.id",
                    },
                    {"name": "amount", "sql_type": "decimal"},
                ],
            }
        )
        with self.assertRaises(ValidationError):
            TableMeta.model_validate(
                {
                    "name": "fact_sales",
                    "table_type": "fact",
                    "columns": [
                        {
                            "name": "customer_id",
                            "sql_type": "int",
                            "nullable": False,
                            "references": "dim_customer.id",
                        }
                    ],
                }
            )

    def test_junction_requires_composite_foreign_key_primary_key(self):
        table = TableMeta.model_validate(
            {
                "name": "jct_customer_region",
                "table_type": "junction",
                "columns": [
                    {
                        "name": "customer_id",
                        "sql_type": "int",
                        "nullable": False,
                        "primary_key": True,
                        "references": "dim_customer.id",
                    },
                    {
                        "name": "region_id",
                        "sql_type": "int",
                        "nullable": False,
                        "primary_key": True,
                        "references": "al_region.region",
                    },
                ],
            }
        )
        self.assertEqual(len(table.pk), 2)

    def test_row_validation_reports_good_and_bad_record_indices(self):
        table = TableMeta.model_validate(
            {
                "name": "stg_measurements",
                "table_type": "staging",
                "columns": [
                    {
                        "name": "amount",
                        "sql_type": "decimal",
                        "nullable": False,
                    }
                ],
            }
        )
        good, bad = table.validate_rows(
            [{"amount": "12.50"}, {"amount": "not-a-number"}, {"extra": 1}]
        )
        self.assertEqual(len(good), 1)
        self.assertEqual(good[0].amount, Decimal("12.50"))
        self.assertEqual([index for index, _ in bad], [1, 2])


if __name__ == "__main__":
    unittest.main()
