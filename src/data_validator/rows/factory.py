"""Generate strict runtime row models from column metadata."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, create_model

from data_validator._base import ROW_CONFIG

if TYPE_CHECKING:
    from collections.abc import Iterable

    from data_validator.columns.model import ColumnMeta


def row_model_name(table_name: str) -> str:
    return f"{''.join(part.title() for part in table_name.split('_'))}Row"


def build_row_model(table_name: str, columns: Iterable[ColumnMeta]) -> type[BaseModel]:
    field_definitions: dict[str, Any] = {
        column.name: (column.annotation(), column.field_info()) for column in columns
    }
    return create_model(row_model_name(table_name), __config__=ROW_CONFIG, **field_definitions)
