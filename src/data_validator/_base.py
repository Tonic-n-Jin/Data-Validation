"""Shared model configuration and identifier types."""

from __future__ import annotations

from typing import Annotated

from pydantic import ConfigDict, StringConstraints

MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=False)
ROW_CONFIG = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=False, strict=True)
Ident = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z_][A-Za-z0-9_]*$", max_length=128),
]
Reference = Annotated[
    str,
    StringConstraints(
        pattern=r"^[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*$",
        max_length=257,
    ),
]
ACTIVE_FLAG = "is_active"
