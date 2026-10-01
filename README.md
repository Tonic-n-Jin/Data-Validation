# Data Validation

An immutable, Pydantic v2 data warehouse schema framework. `data.py` is the
canonical public module; `data_validation.py` remains a compatibility re-export.

## Core API

- `SqlType` maps SQL types to Python types and exposes numeric, string, temporal,
  and boolean family predicates.
- `ColumnMeta` describes physical columns, including PII metadata, references,
  precision/scale, string patterns, allowed values, and numeric or temporal
  ranges.
- `ColumnType` enforces key, identity, foreign-key, composite-key, and
  system-date behavior.
- `TableMeta` applies table-family naming and structure rules, builds a strict
  runtime Pydantic row model, and validates datasets.

All framework models are frozen and reject unknown schema fields. Generated row
models reject unknown record fields.

## Direct schemas

```python
from decimal import Decimal

from data import ColumnMeta, ColumnType, SqlType, TableMeta, TableType

sales = TableMeta(
    name="fact_sales",
    table_type=TableType.FACT,
    columns=(
        ColumnMeta(
            name="customer_id",
            sql_type=SqlType.INT,
            column_type=ColumnType.FOREIGN_KEY,
            references="dim_customer.customer_id",
        ),
        ColumnMeta(
            name="amount",
            sql_type=SqlType.DECIMAL,
            nullable=False,
            precision=12,
            scale=2,
            min_value=Decimal("0.00"),
        ),
    ),
)
report = sales.validate_rows(
    [{"customer_id": 1, "amount": "12.50"}, {"customer_id": 2, "amount": "-1"}]
)
assert report.valid_count == 1
assert report.invalid_rows[0].row_index == 1
```

`validate_rows()` returns a frozen `ValidationReport` with `valid_rows` and
field-level `invalid_rows`. Use `validate_rows_legacy()` only when the prior
`(valid_rows, [(row_index, ValidationError)])` result is required.

## Table rules and scaffolding

`TableType` enforces these prefixes: Active List (`al_`), Lookup (`lu_`),
Dimension (`dim_`), Fact (`fact_`), Junction (`jct_`), and Staging (`stg_`).
An Active List created without columns is scaffolded as its derived-name primary
key plus `is_active BIT NOT NULL DEFAULT True`.

```python
active_regions = TableMeta(name="al_region", table_type=TableType.ACTIVE_LIST)
assert [column.name for column in active_regions.columns] == ["region", "is_active"]
```

Facts require a foreign key and a non-key numeric measure. Junctions require a
composite primary key made of foreign-key columns. Lookups and dimensions require
one primary key and at least one non-key attribute.

## Class declarations

Use `ClassVar[ColumnMeta]` declarations to define reusable table schema classes.
They are collected by the table metaclass and use exactly the same validation
rules as direct schemas.

```python
from typing import ClassVar
from data import ColumnMeta, ColumnType, SqlType, TableMeta, TableType

class Customer(TableMeta):
    name: str = "dim_customer"
    table_type: TableType = TableType.DIMENSION
    customer_id: ClassVar[ColumnMeta] = ColumnMeta(
        name="customer_id",
        sql_type=SqlType.INT,
        column_type=ColumnType.PRIMARY_KEY,
    )
    name_text: ClassVar[ColumnMeta] = ColumnMeta(
        name="name_text", sql_type=SqlType.NVARCHAR, max_length=200
    )

customer_schema = Customer()
```

## Verification

Run the standard-library test suite with:

```bash
python3 -m unittest discover -s tests -v
```
