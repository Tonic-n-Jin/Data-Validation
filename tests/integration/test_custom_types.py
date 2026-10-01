from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import pytest
from pydantic import ValidationError

from data_validator import (
    ColumnMeta,
    ColumnTypeSpec,
    SqlType,
    TableMeta,
    TableType,
    TableTypeSpec,
    get_table_type_spec,
    register_column_type,
    register_table_type,
    unregister_table_type,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


def snapshot_rules(table: TableMeta) -> Sequence[str]:
    if not any(column.name == "as_of" for column in table.columns):
        return ["needs an as_of column"]
    return ()


def audit_user_check(column: ColumnMeta) -> str | None:
    return None if column.sql_type.is_string else "requires a string type"


@pytest.fixture
def custom_types() -> None:
    register_table_type(TableTypeSpec("snapshot", "snap_", snapshot_rules))
    register_column_type(ColumnTypeSpec("audit_user", {"nullable": False}, audit_user_check))


@pytest.mark.usefixtures("custom_types")
def test_custom_table_and_column_types_validate_end_to_end() -> None:
    table = TableMeta(
        name="snap_balances",
        table_type="snapshot",
        columns=(
            ColumnMeta(name="as_of", sql_type=SqlType.DATE, nullable=False),
            ColumnMeta(name="loaded_by", sql_type=SqlType.NVARCHAR, column_type="audit_user"),
        ),
    )
    assert table.table_type == "snapshot"
    assert not table.columns[1].nullable
    report = table.validate_rows([{"as_of": None, "loaded_by": "etl"}, {"as_of": None}])
    assert report.invalid_count == 2

    with pytest.raises(ValidationError, match="needs an as_of column"):
        TableMeta(name="snap_x", table_type="snapshot", columns=table.columns[1:])
    with pytest.raises(ValidationError, match="name must start with 'snap_'"):
        TableMeta(name="balances", table_type="snapshot", columns=table.columns)
    with pytest.raises(ValidationError, match="audit_user column 'who' requires a string"):
        ColumnMeta(name="who", sql_type=SqlType.INT, column_type="audit_user")


@pytest.mark.usefixtures("custom_types")
def test_custom_types_work_in_class_declarations() -> None:
    class Balances(TableMeta):
        name: str = "snap_balances"
        table_type: str = "snapshot"
        as_of: ClassVar[ColumnMeta] = ColumnMeta(name="as_of", sql_type=SqlType.DATE)

    assert Balances().table_type == "snapshot"


def test_custom_scaffold_fills_empty_tables() -> None:
    register_table_type(
        TableTypeSpec(
            "event",
            "evt_",
            scaffold=lambda name: (ColumnMeta(name="event_at", sql_type=SqlType.DATETIME2),),
        )
    )
    table = TableMeta(name="evt_clicks", table_type="event")
    assert [column.name for column in table.columns] == ["event_at"]


def test_replacing_a_built_in_spec_changes_its_rules() -> None:
    columns = (ColumnMeta(name="label", sql_type=SqlType.NVARCHAR),)
    TableMeta(name="stg_raw", table_type=TableType.STAGING, columns=columns)
    register_table_type(
        TableTypeSpec(TableType.STAGING, "stg_", lambda table: ["staging is frozen"]),
        replace=True,
    )
    with pytest.raises(ValidationError, match="staging is frozen"):
        TableMeta(name="stg_raw", table_type=TableType.STAGING, columns=columns)


def test_unregistered_types_are_rejected() -> None:
    unregister_table_type(TableType.STAGING)
    with pytest.raises(ValidationError, match="unknown table type 'staging'"):
        TableMeta(name="stg_raw", table_type=TableType.STAGING)


def test_registry_is_restored_between_tests() -> None:
    assert get_table_type_spec(TableType.STAGING).rules is not None
    with pytest.raises(ValidationError, match="unknown table type 'snapshot'"):
        TableMeta(name="snap_x", table_type="snapshot")
