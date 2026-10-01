"""Runtime validator factories compiled into generated row models."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


def parse_decimal(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return Decimal(value)
        except InvalidOperation as error:
            raise ValueError("must be a valid decimal value") from error
    return value


def decimal_precision_validator(precision: int, scale: int) -> Callable[[Decimal], Decimal]:
    def validate(value: Decimal) -> Decimal:
        if not value.is_finite():
            raise ValueError("must be a finite decimal value")
        digits = value.as_tuple().digits
        exponent = value.as_tuple().exponent
        if not isinstance(exponent, int):
            raise ValueError("must be a finite decimal value")
        decimals = max(-exponent, 0)
        integer_digits = len(digits) - decimals
        if decimals > scale or integer_digits + decimals > precision:
            raise ValueError(f"must fit DECIMAL({precision}, {scale}); received {value}")
        return value

    return validate


def allowed_values_validator(allowed_values: frozenset[Any]) -> Callable[[Any], Any]:
    def validate(value: Any) -> Any:
        if value not in allowed_values:
            raise ValueError(f"must be one of {sorted(map(str, allowed_values))}")
        return value

    return validate


def utc_now() -> datetime:
    return datetime.now(UTC)
