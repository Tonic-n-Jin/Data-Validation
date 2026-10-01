# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Requires Python >= 3.11 and `pydantic>=2.7` (the suite is verified on 2.7.4 and 2.13.x). System pip is externally managed, so work in the project venv:

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest                                              # full suite
.venv/bin/pytest tests/unit   # or -m unit / -m integration (markers are applied by directory in conftest.py)
.venv/bin/pytest tests/unit/test_table_rules.py::test_table_rule_violations   # one test
.venv/bin/ruff check . && .venv/bin/ruff format --check .
.venv/bin/mypy                                                # strict, with the pydantic plugin, over src and tests
```

`ruff format` also formats the Python blocks in `README.md`.

## Architecture

`src/data_validator/` is a declarative data-warehouse schema framework built on Pydantic v2. Its layers import strictly downward, and `tests/unit/test_layering.py` enforces this with an explicit `LAYERS` map. Every new module must be added to that map. Imports under `if TYPE_CHECKING:` are exempt, which is how specs type-hint `ColumnMeta`/`TableMeta` without cycles.

1. **Layer 0 — keys and plumbing.**
   - `_base.py` holds `MODEL_CONFIG`, `ROW_CONFIG`, `Ident`, `Reference` and `ACTIVE_FLAG`.
   - `registry.py` holds the generic `Registry` and `UnknownTypeError`.
   - `types/` holds the `SqlType`, `ColumnType` and `TableType` StrEnums. `ColumnType`/`TableType` are only keys plus prefix data; they carry no behavior.
2. **Layer 1 — `columns/`.**
   - `specs.py` holds `ColumnTypeSpec` (`defaults` applied with `setdefault`, plus a `check` that returns a violation message) and the `COLUMN_TYPES` registry. The built-in specs are registered at import time.
   - `model.py` holds `ColumnMeta`. Its *before* validator applies the spec's defaults and its *after* validator runs the cross-field checks, then `spec.check`.
   - `annotations.py` compiles a column into an `Annotated[...]` type and a `FieldInfo`, using the validator factories in `constraints.py`.
3. **Layer 2 — `rows/`.**
   - `factory.build_row_model` wraps `create_model` with `ROW_CONFIG` (strict, frozen, `extra="forbid"`).
   - `engine.validate_records` returns the legacy `(valid, [(index, ValidationError)])` shape, and `build_report` turns it into the frozen `ValidationReport`.
4. **Layer 3 — `tables/`.**
   - `specs.py` holds `TableTypeSpec` (prefix, `rules`, optional `scaffold`) and the `TABLE_TYPES` registry.
   - `builtins.py` holds the built-in family rules and Active List scaffolding, and registers them on import. `tables/model.py` imports it for that side effect.
   - `declaration.py` holds `TableDeclarationMeta`, which subclasses Pydantic's private `ModelMetaclass` and collects `ClassVar[ColumnMeta]` attributes, including inherited ones.
   - `model.py` holds `TableMeta`, whose validators and row methods delegate to the spec and to `rows/`.
5. **`__init__.py`** contains re-exports only. New public names go into its `__all__`.

**Cross-cutting behavior:**
- **Type keys.** `table_type`/`column_type` are `TableTypeKey`/`ColumnTypeKey`, which are `str` fields validated against the registries. Built-in keys are normalized back to their enum members, so keep `is TableType.X` working. Both model validators also look up the spec directly, because class declarations may re-annotate `table_type` as plain `TableType` or `str`.
- **Registries are global.** The autouse fixture in `tests/conftest.py` snapshots and restores them around every test.
- **Strict rows.** Values are not coerced (`"1"` is rejected for INT). DECIMAL/NUMERIC is the exception: `parse_decimal` runs as a `BeforeValidator`.
- **Ruff and Pydantic.** Ruff's `TC` rules are configured with `runtime-evaluated-base-classes` so that imports used by Pydantic field annotations stay at runtime. Don't move those imports under `TYPE_CHECKING` by hand.

## Repository notes

- `.github/agents/review-and-commit.agent.md` defines the review and commit-message convention:
  - report findings first, giving severity, file:line, the failing scenario and the impact;
  - skip pure style nits;
  - don't modify files or commit unless asked;
  - write a short imperative commit subject (about 50 characters or fewer) that reflects the actual diff.
  
  Conventional-commit prefixes are not used in this repo's history.
- Development happens on `develop`, and PRs target `main`.
