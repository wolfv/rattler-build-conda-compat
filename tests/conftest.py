from __future__ import annotations

from os import mkdir
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture()
def python_recipe(tmpdir: Path) -> str:
    recipe_dir = tmpdir / "recipe"
    mkdir(recipe_dir)

    py_recipe = Path("tests/data/py_recipe.yaml").read_text()
    recipe_yaml: Path = recipe_dir / "recipe.yaml"
    recipe_yaml.write_text(py_recipe, encoding="utf8")

    variants = Path("tests/data/variants.yaml").read_text()
    variants_yaml: Path = recipe_dir / "variants.yaml"
    variants_yaml.write_text(variants, encoding="utf8")

    return recipe_dir


@pytest.fixture()
def env_recipe(tmpdir: Path) -> str:
    recipe_dir = tmpdir / "recipe"
    mkdir(recipe_dir)

    env_recipe = Path("tests/data/env_recipe.yaml").read_text()
    recipe_yaml: Path = recipe_dir / "recipe.yaml"
    recipe_yaml.write_text(env_recipe, encoding="utf8")

    return recipe_dir


@pytest.fixture()
def unix_namespace() -> dict[str, Any]:
    return {"linux-64": True, "unix": True}


@pytest.fixture()
def recipe_dir(tmpdir: Path) -> Path:
    py_recipe = Path("tests/data/py_recipe.yaml").read_text()
    recipe_dir = tmpdir / "recipe"
    mkdir(recipe_dir)

    (recipe_dir / "recipe.yaml").write_text(py_recipe, encoding="utf8")

    return recipe_dir


@pytest.fixture()
def old_recipe_dir(tmpdir: Path) -> Path:
    recipe_dir = tmpdir / "recipe"
    mkdir(recipe_dir)

    meta = Path(recipe_dir / "meta.yaml")
    meta.touch()

    return recipe_dir
