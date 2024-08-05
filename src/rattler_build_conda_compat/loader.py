from __future__ import annotations

import itertools
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from ruamel.yaml import YAML

from rattler_build_conda_compat.conditional_list import visit_conditional_list

if TYPE_CHECKING:
    from collections.abc import Iterator
    from os import PathLike

SELECTOR_OPERATORS = ("and", "or", "not")


def _remove_empty_keys(some_dict: dict[str, Any]) -> dict[str, Any]:
    filtered_dict = {}
    for key, value in some_dict.items():
        if isinstance(value, list) and len(value) == 0:
            continue
        filtered_dict[key] = value

    return filtered_dict


def _flatten_lists(some_dict: dict[str, Any]) -> dict[str, Any]:
    result_dict: dict[str, Any] = {}
    for key, value in some_dict.items():
        if isinstance(value, dict):
            result_dict[key] = _flatten_lists(value)
        elif isinstance(value, list) and value and isinstance(value[0], list):
            result_dict[key] = list(itertools.chain(*value))
        else:
            result_dict[key] = value

    return result_dict


class RecipeLoader:
    _namespace: dict[str, Any] | None = None
    _allow_missing_selector: bool = False

    @classmethod
    @contextmanager
    def with_namespace(
        cls: type[RecipeLoader],
        namespace: dict[str, Any] | None,
        *,
        allow_missing_selector: bool = False,
    ) -> Iterator[None]:
        try:
            cls._namespace = namespace
            cls._allow_missing_selector = allow_missing_selector
            yield
        finally:
            del cls._namespace

    @classmethod
    def construct_sequence(  # noqa: C901, PLR0912
        cls,
        node: Any,
        deep: bool = False,  # noqa: FBT002, FBT001,
    ) -> list[Any]:
        """deep is True when creating an object/mapping recursively,
        in that case want the underlying elements available during construction
        """
        # find if then else selectors
        for sequence_idx, child_node in enumerate(node[:]):
            # if then is only present in MappingNode

            if isinstance(child_node, dict):
                # iterate to find if there is IF first

                the_evaluated_one = None
                for idx, (key, value) in enumerate(child_node.items()):
                    if key == "if":
                        # we catch the first one, let's try to find next pair of (then | else)
                        then_key, then_value = list(child_node.items())[idx + 1]

                        if then_key != "then":
                            msg = "cannot have if without then, please reformat your variant file"
                            raise ValueError(msg)

                        try:
                            _, else_value = list(child_node.items())[idx + 2]
                        except IndexError:
                            _, else_value = None, None

                        to_be_eval = f"{value}"

                        if cls._allow_missing_selector:
                            split_selectors = [
                                selector
                                for selector in to_be_eval.split()
                                if selector not in SELECTOR_OPERATORS
                            ]
                            for selector in split_selectors:
                                if cls._namespace and selector not in cls._namespace:
                                    cleaned_selector = selector.strip("(").rstrip(")")
                                    cls._namespace[cleaned_selector] = True

                        evaled = eval(to_be_eval, cls._namespace)  # noqa: S307
                        if evaled:
                            the_evaluated_one = then_value
                        elif else_value:
                            the_evaluated_one = else_value

                        if the_evaluated_one:
                            node.remove(child_node)
                            node.insert(sequence_idx, the_evaluated_one)
                        else:
                            # neither the evaluation or else node is present, so we remove this if
                            node.remove(child_node)

        if not isinstance(node, list):
            raise TypeError(
                None,
                None,
                f"expected a sequence node, but found {type(node)}",
                None,
            )

        return [cls.construct_object(child, deep=deep) for child in node]

    @classmethod
    def construct_object(cls, node: Any, deep: bool = False) -> Any:
        if isinstance(node, dict):
            return {key: cls.construct_object(value, deep) for key, value in node.items()}
        elif isinstance(node, list):
            return cls.construct_sequence(node, deep)
        else:
            return node


def load_yaml(content: str | bytes) -> Any:  # noqa: ANN401
    yaml = YAML(typ='safe')
    return yaml.load(content)


def parse_recipe_config_file(
    path: PathLike[str], namespace: dict[str, Any] | None, *, allow_missing_selector: bool = False
) -> dict[str, Any]:
    yaml = YAML(typ='safe')
    with open(path) as f, RecipeLoader.with_namespace(
        namespace, allow_missing_selector=allow_missing_selector
    ):
        content = yaml.load(f)
        content = RecipeLoader.construct_object(content)
    return _flatten_lists(_remove_empty_keys(content))


def load_all_requirements(content: dict[str, Any]) -> dict[str, Any]:
    requirements_section = dict(content.get("requirements", {}))
    if not requirements_section:
        return {}

    for section in requirements_section:
        section_reqs = requirements_section[section]
        if not section_reqs:
            continue

        requirements_section[section] = list(visit_conditional_list(section_reqs))

    return requirements_section


def load_all_tests(content: dict[str, Any]) -> list[dict]:
    tests_section = content.get("tests", [])
    if not tests_section:
        return []

    evaluated_tests = []

    for section in tests_section:
        evaluated_tests.extend(list(visit_conditional_list(section)))

    return evaluated_tests