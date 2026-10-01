"""Structured row validation results."""

from __future__ import annotations

from pydantic import BaseModel, Field

from data_validator._base import MODEL_CONFIG


class FieldError(BaseModel):
    model_config = MODEL_CONFIG

    field: tuple[str | int, ...]
    message: str
    error_type: str


class RowValidationError(BaseModel):
    model_config = MODEL_CONFIG

    row_index: int = Field(ge=0)
    errors: tuple[FieldError, ...]


class ValidationReport(BaseModel):
    model_config = MODEL_CONFIG

    valid_rows: tuple[BaseModel, ...]
    invalid_rows: tuple[RowValidationError, ...]

    @property
    def valid_count(self) -> int:
        return len(self.valid_rows)

    @property
    def invalid_count(self) -> int:
        return len(self.invalid_rows)
