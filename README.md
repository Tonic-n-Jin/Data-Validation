# Data-Validation

Pydantic-based validation for SQL table metadata and row data. Requires Python
3.11+ and Pydantic 2.13+.

```python
from data_validation import TableMeta

table = TableMeta.model_validate(
    {"name": "al_region", "table_type": "active_list"}
)
good_rows, invalid_rows = table.validate_rows(
    [{"region": "north"}, {"region": 42}]
)
```

Table type prefixes and schema rules are defined by `TableType`. An active-list
table is scaffolded automatically; other tables provide their columns explicitly.
`invalid_rows` contains `(record_index, ValidationError)` pairs. For pandas input,
convert missing values to `None` before calling `validate_rows`:

```python
records = df.astype(object).where(df.notna(), None).to_dict("records")
good_rows, invalid_rows = table.validate_rows(records)
```
