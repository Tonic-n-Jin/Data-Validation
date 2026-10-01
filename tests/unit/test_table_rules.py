from __future__ import annotations

import pytest
from pydantic import ValidationError

from data_validator import (
    ACTIVE_FLAG,
    ColumnMeta,
    ColumnType,
    SqlType,
    TableMeta,
    TableType,
    get_table_type_spec,
)

PK = ColumnMeta(name="customer_id", sql_type=SqlType.INT, column_type=ColumnType.PRIMARY_KEY)
LABEL = ColumnMeta(name="label", sql_type=SqlType.NVARCHAR)
FK = ColumnMeta(
    name="customer_id",
    sql_type=SqlType.INT,
    column_type=ColumnType.FOREIGN_KEY,
    references="dim_customer.customer_id",
)
MEASURE = ColumnMeta(name="amount", sql_type=SqlType.DECIMAL)


def composite_fk(name: str, references: str | None = None) -> ColumnMeta:
    if references is None:
        return ColumnMeta(name=name, sql_type=SqlType.INT, column_type=ColumnType.COMPOSITE_KEY)
    return ColumnMeta(
        name=name,
        sql_type=SqlType.INT,
        column_type=ColumnType.COMPOSITE_KEY,
        references=references,
    )


def test_dimension_fact_and_junction_rules() -> None:
    dimension = TableMeta(
        name="dim_customer", table_type=TableType.DIMENSION, columns=(PK, LABEL)
    )
    fact = TableMeta(name="fact_sales", table_type=TableType.FACT, columns=(FK, MEASURE))
    junction = TableMeta(
        name="jct_customer_region",
        table_type=TableType.JUNCTION,
        columns=(
            composite_fk("customer_id", "dim_customer.customer_id"),
            composite_fk("region_id", "al_region.region"),
        ),
    )
    assert len(dimension.pk) == 1
    assert fact.table_type == TableType.FACT
    assert len(junction.pk) == 2


def test_active_list_is_scaffolded() -> None:
    table = TableMeta(name="al_region", table_type=TableType.ACTIVE_LIST)
    assert [column.name for column in table.columns] == ["region", "is_active"]
    assert table.columns[0].column_type == ColumnType.PRIMARY_KEY


@pytest.mark.parametrize(
    ("name", "table_type", "columns", "message"),
    [
        ("customer", TableType.DIMENSION, (PK, LABEL), "name must start with 'dim_'"),
        ("dim_customer", TableType.DIMENSION, (PK, PK), "duplicate column names"),
        ("dim_customer", TableType.DIMENSION, (LABEL,), "needs exactly 1 PK, has 0"),
        ("lu_status", TableType.LOOKUP, (PK,), "needs a non-key column"),
        ("fact_sales", TableType.FACT, (MEASURE,), "needs an FK column"),
        ("fact_sales", TableType.FACT, (FK, LABEL), "needs a numeric measure"),
        ("jct_pair", TableType.JUNCTION, (composite_fk("a", "dim_a.a"),), r"PK must be 2\+ FK"),
        (
            "jct_pair",
            TableType.JUNCTION,
            (composite_fk("a", "dim_a.a"), composite_fk("b")),
            r"PK must be 2\+ FK",
        ),
        ("al_region", TableType.ACTIVE_LIST, (PK, LABEL), "must be exactly"),
        (
            "al_region",
            TableType.ACTIVE_LIST,
            (
                ColumnMeta(
                    name="region", sql_type=SqlType.NVARCHAR, column_type=ColumnType.PRIMARY_KEY
                ),
                ColumnMeta(name=ACTIVE_FLAG, sql_type=SqlType.BIT, nullable=False),
            ),
            "is_active must be BIT NOT NULL DEFAULT True",
        ),
    ],
)
def test_table_rule_violations(
    name: str, table_type: TableType, columns: tuple[ColumnMeta, ...], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        TableMeta(name=name, table_type=table_type, columns=columns)


def test_staging_tables_have_no_structural_rules() -> None:
    assert TableMeta(name="stg_raw", table_type=TableType.STAGING, columns=(LABEL,))


def test_built_in_keys_resolve_to_enum_members() -> None:
    table = TableMeta(name="fact_sales", table_type="fact", columns=(FK, MEASURE))
    assert table.table_type is TableType.FACT


def test_unknown_table_type_is_rejected() -> None:
    with pytest.raises(ValidationError, match="unknown table type 'snapshot'"):
        TableMeta(name="snap_x", table_type="snapshot", columns=(LABEL,))


def test_every_built_in_table_type_is_registered_with_its_prefix() -> None:
    for table_type in TableType:
        assert get_table_type_spec(table_type).prefix == table_type.prefix
