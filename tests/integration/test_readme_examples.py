from __future__ import annotations

import re
from pathlib import Path

import pytest

README = Path(__file__).parents[2] / "README.md"
EXAMPLES = re.findall(r"```python\n(.*?)```", README.read_text(), flags=re.DOTALL)


def test_readme_has_examples() -> None:
    assert len(EXAMPLES) >= 4


@pytest.mark.parametrize("source", EXAMPLES, ids=[f"example_{i}" for i in range(len(EXAMPLES))])
def test_readme_example_runs(source: str) -> None:
    exec(compile(source, str(README), "exec"), {"__name__": "readme_example"})
