from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from data_validator.columns.specs import COLUMN_TYPES
from data_validator.tables.specs import TABLE_TYPES

if TYPE_CHECKING:
    from collections.abc import Iterator

TESTS_ROOT = Path(__file__).parent


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        suite = item.path.relative_to(TESTS_ROOT).parts[0]
        if suite in {"unit", "integration"}:
            item.add_marker(getattr(pytest.mark, suite))


@pytest.fixture(autouse=True)
def isolated_registries() -> Iterator[None]:
    """Undo any column or table type registration a test makes."""
    column_types, table_types = COLUMN_TYPES.snapshot(), TABLE_TYPES.snapshot()
    yield
    COLUMN_TYPES.restore(column_types)
    TABLE_TYPES.restore(table_types)
