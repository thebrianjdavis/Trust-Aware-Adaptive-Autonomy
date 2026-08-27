"""Tests that enforce the one-to-one source and test module layout."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_every_source_module_has_a_matching_test_module() -> None:
    missing_test_modules = []

    for source_path in sorted((PROJECT_ROOT / "src").rglob("*.py")):
        relative_source_path = source_path.relative_to(PROJECT_ROOT / "src")
        expected_test_path = (
            PROJECT_ROOT
            / "tests"
            / relative_source_path.parent
            / f"test_{relative_source_path.name}"
        )

        if not expected_test_path.is_file():
            missing_test_modules.append(
                str(expected_test_path.relative_to(PROJECT_ROOT))
            )

    assert not missing_test_modules, (
        "Every source module must have a matching test module. Missing: "
        + ", ".join(missing_test_modules)
    )
