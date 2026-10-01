# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Requires Python >= 3.11 and `pydantic>=2.13`. Tests use the standard-library `unittest` (no pytest config).

```bash
python3 -m unittest discover -s tests -v                                   # full suite
python3 -m unittest tests.test_data.TableMetaTests -v                      # one class
python3 -m unittest tests.test_data.TableMetaTests.test_dimension_fact_and_junction_rules -v  # one test
```

No linter or formatter is configured. `data.py` carries a file-level `# pyright: reportIncompatibleVariableOverride=false` for the `Literal` overrides on the typed column subclasses.

## Architecture

The entire library is the single module `data.py` (the only public module; the old `data_validation` re-export was removed). It is a declarative data-warehouse schema framework built on Pydantic v2, layered as:

1. **`SqlType`** — SQL type enum mapped to Python types via `_PYTHON_TYPES`, with family predicates (`is_numeric`, `is_string`, `is_temporal`, `supports_precision_scale`) that the other layers use to decide which metadata is legal.
2. **`ColumnType`** — owns key semantics in two places: `defaults()` is applied in `ColumnMeta`'s *before* validator (e.g. PK/composite key → `primary_key`, `nullable=False`, `indexed`; system date → `auto_utc`), and `violation()` is checked in the *after* validator. Add new column-kind behavior here, not in `ColumnMeta`.
3. **`ColumnMeta`** — schema metadata plus cross-field checks in `_validate_metadata`. It also compiles itself into runtime validation: `annotation()` builds an `Annotated[...]` type (string constraints, decimal parsing + precision/scale, bounds, allowed values; `| None` if nullable) and `field_info()` picks the default (`auto_utc` factory, explicit default, `None`, or required). `PrimaryKeyColumn`, `ForeignKeyColumn`, etc. are thin subclasses pinning `column_type` to a `Literal`.
4. **`TableType`** — owns per-family naming prefixes (`al_`, `lu_`, `dim_`, `fact_`, `jct_`, `stg_`) and `scaffold()`, which auto-generates Active List columns (`<name-without-prefix>` NVARCHAR PK + `is_active BIT NOT NULL DEFAULT True`) when none are given.
5. **`TableMeta`** — uses the custom metaclass `TableDeclarationMeta` (subclass of Pydantic's `ModelMetaclass`) to collect `ClassVar[ColumnMeta]` attributes into `__declared_columns__`, including inherited ones. Its *before* validator fills `columns` from declared columns, else from `TableType.scaffold()`. Its *after* validator enforces prefix, unique column names, and table-family structure rules in `_type_rule_errors()`. Direct construction and class declaration must go through identical rules.
6. **Row validation** — `TableMeta.row_model` (a `cached_property`) builds a Pydantic model via `create_model` from each column's `annotation()`/`field_info()`, using `ROW_CONFIG` (`strict=True`, `extra="forbid"`, frozen). `validate_rows()` returns a frozen `ValidationReport` of valid rows and per-row `RowValidationError`/`FieldError`; `validate_rows_legacy()` returns the old `(valid_rows, [(index, ValidationError)])` tuple shape. Both share `_validate_rows()`.

Conventions that span the module:
- All framework models use `MODEL_CONFIG` (frozen, `extra="forbid"`); collections are tuples/frozensets, not lists.
- Because rows are validated with `strict=True`, values are not coerced (e.g. `"1"` is rejected for INT). DECIMAL/NUMERIC is the exception: `_parse_decimal` runs as a `BeforeValidator` so strings are accepted.
- New public names must be added to `__all__`.

## Repository notes

- `.github/agents/review-and-commit.agent.md` defines the review/commit-message convention: report findings first (severity, file:line, failing scenario, impact), skip pure style nits, don't modify files or commit unless asked, and write a short imperative commit subject (≤ ~50 chars) that reflects the actual diff. Conventional-commit prefixes are not used in this repo's history.
- Development happens on `develop`; PRs target `main`.
