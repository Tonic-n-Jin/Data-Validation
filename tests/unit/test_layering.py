"""Enforce the one-way import graph between package layers."""

from __future__ import annotations

import ast
from pathlib import Path

import data_validator

PACKAGE_ROOT = Path(data_validator.__file__).parent

# Lower ranks may never import higher ranks at runtime. Imports guarded by
# `if TYPE_CHECKING:` are exempt because they only exist for type hints.
LAYERS: dict[str, float] = {
    "data_validator._base": 0,
    "data_validator.registry": 0,
    "data_validator.types.sql": 0,
    "data_validator.types.column_type": 0,
    "data_validator.types.table_type": 0,
    "data_validator.types": 0.9,
    "data_validator.columns.constraints": 1.0,
    "data_validator.columns.specs": 1.1,
    "data_validator.columns.annotations": 1.2,
    "data_validator.columns.model": 1.3,
    "data_validator.columns": 1.9,
    "data_validator.rows.report": 2.0,
    "data_validator.rows.factory": 2.1,
    "data_validator.rows.engine": 2.2,
    "data_validator.rows": 2.9,
    "data_validator.tables.specs": 3.0,
    "data_validator.tables.builtins": 3.1,
    "data_validator.tables.declaration": 3.2,
    "data_validator.tables.model": 3.3,
    "data_validator.tables": 3.9,
    "data_validator": 4,
}


def module_name(path: Path) -> str:
    parts = path.relative_to(PACKAGE_ROOT.parent).with_suffix("").parts
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def runtime_imports(tree: ast.Module) -> list[str]:
    found: list[str] = []

    def visit(nodes: list[ast.stmt]) -> None:
        for node in nodes:
            if isinstance(node, ast.If) and ast.unparse(node.test) == "TYPE_CHECKING":
                visit(node.orelse)
                continue
            if isinstance(node, ast.Import):
                found.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    submodule = f"{node.module}.{alias.name}"
                    found.append(submodule if submodule in LAYERS else node.module)
            for field in ("body", "orelse", "finalbody", "handlers"):
                children = getattr(node, field, None)
                if isinstance(children, list):
                    visit([child for child in children if isinstance(child, ast.stmt)])

    visit(tree.body)
    return [name for name in found if name.startswith("data_validator")]


MODULES = {module_name(path): path for path in PACKAGE_ROOT.rglob("*.py")}


def test_every_module_has_a_layer() -> None:
    assert sorted(MODULES) == sorted(LAYERS)


def test_imports_only_point_down_the_layer_graph() -> None:
    violations = [
        f"{name} (layer {LAYERS[name]}) imports {imported} (layer {LAYERS[imported]})"
        for name, path in MODULES.items()
        for imported in runtime_imports(ast.parse(path.read_text()))
        if imported != name and LAYERS[imported] >= LAYERS[name]
    ]
    assert violations == []
