"""Built-in column type keys."""

from __future__ import annotations

from enum import StrEnum


class ColumnType(StrEnum):
    PRIMARY_KEY = "primary_key"
    FOREIGN_KEY = "foreign_key"
    IDENTITY = "identity"
    COMPOSITE_KEY = "composite_key"
    SYSTEM_DATE = "system_date"
    MISCELLANEOUS = "miscellaneous"
