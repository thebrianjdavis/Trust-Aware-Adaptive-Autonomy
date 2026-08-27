"""Tests that enforce consistent, complete Python documentation."""

import ast
import re
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTABLE_NODE_TYPES = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
DOXYGEN_COMMENT_PATTERN = re.compile(r"^\s*#{1,2}\s*@\w+")


def get_tracked_python_files() -> list[Path]:
    """Return every Python file tracked by the repository."""
    result = subprocess.run(
        ["git", "ls-files", "*.py"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    relative_paths = result.stdout.splitlines()
    tracked_paths = [PROJECT_ROOT / relative_path for relative_path in relative_paths]

    # Include this test before it is staged so local runs also validate it.
    return sorted(set(tracked_paths) | {Path(__file__)})


def find_missing_docstrings(python_path: Path) -> list[str]:
    """Return descriptions of undocumented objects in one Python file."""
    syntax_tree = ast.parse(
        python_path.read_text(encoding="utf-8"),
        filename=str(python_path),
    )
    relative_path = python_path.relative_to(PROJECT_ROOT)
    missing_docstrings = []

    if ast.get_docstring(syntax_tree) is None:
        missing_docstrings.append(f"{relative_path}: module")

    for node in ast.walk(syntax_tree):
        is_undocumented_object = (
            isinstance(node, DOCUMENTABLE_NODE_TYPES)
            and ast.get_docstring(node) is None
        )
        if is_undocumented_object:
            node_kind = "class" if isinstance(node, ast.ClassDef) else "function"
            missing_docstrings.append(
                f"{relative_path}:{node.lineno}: {node_kind} {node.name}"
            )

    return missing_docstrings


def find_doxygen_comments(python_path: Path) -> list[str]:
    """Return descriptions of Doxygen directives in one Python file."""
    relative_path = python_path.relative_to(PROJECT_ROOT)
    doxygen_comments = []

    for line_number, line in enumerate(
        python_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if DOXYGEN_COMMENT_PATTERN.match(line):
            doxygen_comments.append(f"{relative_path}:{line_number}: {line.strip()}")

    return doxygen_comments


def test_every_python_object_has_a_docstring() -> None:
    """Require docstrings on tracked modules, classes, methods, and functions."""
    missing_docstrings = []

    for python_path in get_tracked_python_files():
        missing_docstrings.extend(find_missing_docstrings(python_path))

    assert not missing_docstrings, (
        "Every Python module, class, method, and function must have a docstring:\n"
        + "\n".join(missing_docstrings)
    )


def test_python_files_do_not_use_doxygen_comments() -> None:
    """Require Python documentation to use docstrings instead of Doxygen tags."""
    doxygen_comments = []

    for python_path in get_tracked_python_files():
        doxygen_comments.extend(find_doxygen_comments(python_path))

    assert not doxygen_comments, (
        "Replace Doxygen directives with Google-style Python docstrings:\n"
        + "\n".join(doxygen_comments)
    )
