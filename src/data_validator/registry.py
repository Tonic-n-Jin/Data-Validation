"""A small keyed registry used for extensible column and table types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from collections.abc import Mapping

V = TypeVar("V")


class UnknownTypeError(LookupError):
    """Raised when a column or table type key has not been registered."""


class Registry(Generic[V]):
    """Map string keys to specs; registering an existing key requires `replace=True`."""

    def __init__(self, kind: str) -> None:
        self._kind = kind
        self._items: dict[str, V] = {}

    def register(self, key: str, value: V, *, replace: bool = False) -> V:
        if key in self._items and not replace:
            raise ValueError(f"{self._kind} '{key}' is already registered; pass replace=True")
        self._items[str(key)] = value
        return value

    def unregister(self, key: str) -> V:
        self._require(key)
        return self._items.pop(key)

    def get(self, key: str) -> V:
        self._require(key)
        return self._items[key]

    def keys(self) -> tuple[str, ...]:
        return tuple(self._items)

    def snapshot(self) -> Mapping[str, V]:
        return dict(self._items)

    def restore(self, snapshot: Mapping[str, V]) -> None:
        self._items = dict(snapshot)

    def __contains__(self, key: object) -> bool:
        return key in self._items

    def _require(self, key: str) -> None:
        if key not in self._items:
            registered = ", ".join(sorted(self._items))
            raise UnknownTypeError(f"unknown {self._kind} '{key}'; registered: {registered}")
