"""Class-based table declaration support."""

from __future__ import annotations

from typing import Any

# Private Pydantic API: subclassing the model metaclass is the only way to
# collect ClassVar column declarations before Pydantic builds the model.
from pydantic._internal._model_construction import ModelMetaclass

from data_validator.columns.model import ColumnMeta


class TableDeclarationMeta(ModelMetaclass):
    """Collect `ColumnMeta` class attributes into an annotated table declaration."""

    def __new__(
        mcls,
        name: str,
        bases: tuple[type[Any], ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type[Any]:
        declared = tuple(value for value in namespace.values() if isinstance(value, ColumnMeta))
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        inherited = tuple(
            column for base in bases for column in getattr(base, "__declared_columns__", ())
        )
        # TableMeta declares this ClassVar; mypy only sees the metaclass's `type` result.
        cls.__declared_columns__ = inherited + declared  # type: ignore[attr-defined]
        return cls
