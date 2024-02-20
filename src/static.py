"""Script to download repos from GitHub"""

import os
import fire
from tqdm import tqdm
import json
import logging
import ast
from common import wrap_repo
from navigate import ModuleNavigator
from funcy import group_by, lmap, lfilter
from pathlib import Path
from funcy_chain import Chain
import csv
from functools import reduce


def collect_py_files(root: str) -> list[str]:
    py_files: list[str] = []
    for parent, _, files in os.walk(root):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(parent, file))
    return py_files


def collect_funcs(
    nav: ModuleNavigator,
) -> dict[bool, list[ast.FunctionDef]]:
    """collect testing functions from the target file"""

    def is_test_cls(node: ast.AST):
        """is a test class if
        1.1 class name starts with Test
        1.2 inherit from unittest.TestCase
        2. a static class without a init function
        """
        if not isinstance(node, ast.ClassDef):
            return False
        # if not node.name.startswith('Test'): return False
        test_prefix = node.name.startswith("Test")
        inherit_unittest_attr = any(
            isinstance(base, ast.Attribute) and base.attr == "TestCase"
            for base in node.bases
        )
        inherit_unittest_name = any(
            isinstance(base, ast.Name) and base.id == "TestCase" for base in node.bases
        )
        if not any([test_prefix, inherit_unittest_name, inherit_unittest_attr]):
            return False
        cls_funcs = nav.find_all(ast.FunctionDef, root=node)
        return not any(func.name == "__init__" for func in cls_funcs)

    def has_assert(func: ast.AST):
        # builtin assertion
        if len(nav.find_all(ast.Assert, root=func)) > 0:
            return True
        # Testcase in unittest, eg. self.assertEqual
        for call in nav.find_all(ast.Call, root=func):
            if isinstance(call.func, ast.Attribute) and call.func.attr.startswith(
                "assert"
            ):
                return True
        return False

    def is_test_outside_cls(func: ast.FunctionDef):
        """decide if the function is a testing function outside a class
        return true if its name starts with "test"
        """
        return func.name.startswith("test")

    def is_test_inside_cls(func: ast.FunctionDef, path: list[ast.AST]):
        """decide if the function is a testing function inside a class
        return true if its class is prefixed by "Test" and either
        + it is prefixed by "test"
        + it is decorated with @staticmethod and @classmethods
        """
        # keep only the node in path whose name is prefixed by "Test"
        cls_path = [n for n in path if is_test_cls(n)]
        if len(cls_path) == 0:
            return False
        if func.name.startswith("test"):
            return True
        decorators = getattr(func, "decorator_list", [])
        return any(
            isinstance(d, ast.Name) and d.id in ("staticmethod", "classmethods")
            for d in decorators
        )

    def _is_test_fn(func: ast.FunctionDef):
        path = nav.get_path_to(func)
        is_cls = [isinstance(n, ast.ClassDef) for n in path]
        is_test = False
        is_test |= any(is_cls) and is_test_inside_cls(func, path)
        is_test |= not any(is_cls) and is_test_outside_cls(func)
        is_test &= has_assert(func)
        return is_test

    funcs: list[ast.FunctionDef] = nav.find_all(ast.FunctionDef)
    d: dict[bool, list[ast.FunctionDef]] = group_by(_is_test_fn, funcs)
    return d


def merge_dict(
    d1: dict[bool, list[ast.AST]], d2: dict[bool, list[ast.AST]]
) -> dict[bool, list[ast.AST]]:
    return {True: d1[True] + d2[True], False: d1[False] + d2[False]}


def is_properity_based(func: ast.FunctionDef) -> bool:
    for decorator in func.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id in (
            "given",
            "hypothesis.given",
        ):
            return True
    return False


def main(
    input_repo_list_path: str = "data/meta/oss_fuzz_python_filtered.jsonl",
    root: str = "data/repos/",
    output_csv_file: str = "output.csv",
):
    with open(input_repo_list_path, "r") as fp:
        repo_id_list = (
            Chain(fp.read().splitlines())
            .map(json.loads)
            .map(lambda x: x["repo_id"])
            .value
        )

    root = os.path.abspath(root)
    rows = []
    for repo_id in tqdm(repo_id_list[:1]):
        repo_root = os.path.join(root, wrap_repo(repo_id))
        all_files = collect_py_files(repo_root)
        navs = lmap(ModuleNavigator, all_files)
        func_ds = lmap(collect_funcs, navs)
        func_dict = reduce(merge_dict, func_ds)

        n_tests = len(func_dict[True])
        n_property_based = len(lfilter(is_properity_based, func_dict[True]))
        csv_row = {
            "repo_id": repo_id,
            "#files": len(all_files),
            "#lines": sum(m.total_lines for m in navs),
            "#funcs": len(func_dict[False]),
            "#unit": n_tests - n_property_based,
            "#proptery_based": n_property_based,
        }
        rows.append(csv_row)

    with open(output_csv_file, "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fire.Fire(main)