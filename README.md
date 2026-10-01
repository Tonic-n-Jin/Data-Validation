# Data Validator

An immutable, Pydantic v2 data warehouse schema framework. Declare tables and
columns once, have their structure checked against warehouse conventions, and
validate incoming records against a strict row model generated from the schema.

```bash
pip install -e ".[dev]"   # Python >= 3.11, pydantic >= 2.7
```

## Core API

Everything below is importable from `data_validator`.

- `SqlType` maps SQL types to Python types and exposes numeric, string, temporal,
  and boolean family predicates.
- `ColumnMeta` describes physical columns, including PII metadata, references,
  precision/scale, string patterns, allowed values, and numeric or temporal
  ranges.
- `ColumnType` names the built-in column types: key, identity, foreign-key,
  composite-key, and system-date behavior.
- `TableType` names the built-in table families and their name prefixes.
- `TableMeta` applies table-family naming and structure rules, builds a strict
  runtime Pydantic row model, and validates datasets.
- `ColumnTypeSpec`, `TableTypeSpec` and the `register_*` functions add custom
  column and table types (see [Extending column and table types](#extending-column-and-table-types)).

All framework models are frozen and reject unknown schema fields. Generated row
models are strict: they reject unknown record fields and do not coerce values
(`"1"` is not an `INT`), except that `DECIMAL`/`NUMERIC` columns accept numeric
strings.

## Direct schemas

```python
from decimal import Decimal

from data_validator import ColumnMeta, ColumnType, SqlType, TableMeta, TableType

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
from data_validator import TableMeta, TableType

active_regions = TableMeta(name="al_region", table_type=TableType.ACTIVE_LIST)
assert [column.name for column in active_regions.columns] == ["region", "is_active"]
```

Facts require a foreign key and a non-key numeric measure. Junctions require a
composite primary key made of foreign-key columns. Lookups and dimensions require
one primary key and at least one non-key attribute. Staging tables have no
structural rules.

## Class declarations

Use `ClassVar[ColumnMeta]` declarations to define reusable table schema classes.
They are collected by the table metaclass, inherited by subclasses, and use
exactly the same validation rules as direct schemas.

```python
from typing import ClassVar

from data_validator import ColumnMeta, ColumnType, SqlType, TableMeta, TableType


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

## Extending column and table types

`table_type` and `column_type` accept any registered key. The built-in keys
still resolve to their `TableType`/`ColumnType` members, so
`table.table_type is TableType.FACT` holds. Custom keys stay plain strings.
An unregistered key raises a `ValidationError` that lists the registered keys.

- A `TableTypeSpec` has a `key`, a name `prefix`, an optional `rules` callable
  that returns error messages for a built table, and an optional `scaffold`
  callable that generates columns when a table is declared without any.
- A `ColumnTypeSpec` has a `key`, `defaults` that are applied with `setdefault`
  before validation, and a `check` callable that returns a violation message or
  `None`.

```python
from data_validator import (
    ColumnMeta,
    ColumnTypeSpec,
    SqlType,
    TableMeta,
    TableTypeSpec,
    register_column_type,
    register_table_type,
)


def snapshot_rules(table: TableMeta) -> list[str]:
    if not any(column.name == "as_of" for column in table.columns):
        return ["needs an as_of column"]
    return []


register_table_type(TableTypeSpec(key="snapshot", prefix="snap_", rules=snapshot_rules))
register_column_type(
    ColumnTypeSpec(
        key="audit_user",
        defaults={"nullable": False},
        check=lambda column: None if column.sql_type.is_string else "requires a string type",
    )
)

balances = TableMeta(
    name="snap_balances",
    table_type="snapshot",
    columns=(
        ColumnMeta(name="as_of", sql_type=SqlType.DATE, nullable=False),
        ColumnMeta(name="loaded_by", sql_type=SqlType.NVARCHAR, column_type="audit_user"),
    ),
)
assert balances.columns[1].nullable is False
```

Registering an existing key raises unless you pass `replace=True`, which is also
how to change the rules of a built-in type. Use `get_table_type_spec()` and
`get_column_type_spec()` to inspect a spec, and `unregister_table_type()` and
`unregister_column_type()` to remove one. The registries are process-wide.

## Migrating from `data.py`

Version 0.2.0 replaces the single `data.py` module with the `data_validator`
package. If you are upgrading:

- Change `from data import ...` to `from data_validator import ...`.
- `TableType.scaffold()` is now `get_table_type_spec(key).scaffold`.
- `ColumnType.defaults()` and `ColumnType.violation()` are now
  `get_column_type_spec(key).apply_defaults()` and `.check()`.
- `table_type` and `column_type` are typed as registered string keys. Custom
  types are plain `str`, not enum members.

## Development

```bash
pytest                      # whole suite
pytest tests/unit           # or: pytest -m unit
pytest -m integration
ruff check . && ruff format --check .
mypy
```

`tests/unit/test_layering.py` enforces the package's one-way import graph, and
`tests/integration/test_readme_examples.py` runs every Python example in this
README.
