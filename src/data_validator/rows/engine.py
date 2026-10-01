"""Validate records against a row model and shape the results."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from pydantic import BaseModel, ValidationError

from data_validator.rows.report import FieldError, RowValidationError, ValidationReport

LegacyResult = tuple[list[BaseModel], list[tuple[int, ValidationError]]]


def validate_records(row_model: type[BaseModel], records: Iterable[dict[str, Any]]) -> LegacyResult:
    valid_rows: list[BaseModel] = []
    invalid_rows: list[tuple[int, ValidationError]] = []
    for row_index, record in enumerate(records):
        try:
            valid_rows.append(row_model.model_validate(record))
        except ValidationError as error:
            invalid_rows.append((row_index, error))
    return valid_rows, invalid_rows


def build_report(
    valid_rows: Sequence[BaseModel], invalid_rows: Sequence[tuple[int, ValidationError]]
) -> ValidationReport:
    return ValidationReport(
        valid_rows=tuple(valid_rows),
        invalid_rows=tuple(
            RowValidationError(
                row_index=index,
                errors=tuple(
                    FieldError(
                        field=tuple(error["loc"]),
                        message=error["msg"],
                        error_type=error["type"],
                    )
                    for error in validation_error.errors()
                ),
            )
            for index, validation_error in invalid_rows
        ),
    )
