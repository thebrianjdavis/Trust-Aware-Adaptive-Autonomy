"""Define repeatable development and continuous-integration sessions."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import nox

PROJECT_ROOT = Path(__file__).resolve().parent
PYTHON_VERSION = (PROJECT_ROOT / ".python-version").read_text(encoding="utf-8").strip()
RUNTIME_REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
DEVELOPMENT_REQUIREMENTS = PROJECT_ROOT / "requirements-dev.txt"
DOCUMENTATION_REQUIREMENTS = PROJECT_ROOT / "requirements-docs.txt"
REPORT_DIRECTORY = PROJECT_ROOT / "build" / "reports"
SITE_DIRECTORY = PROJECT_ROOT / "site"
SITE_REPORT_DIRECTORY = SITE_DIRECTORY / "development" / "reports"

nox.options.sessions = ["tests"]
nox.options.error_on_missing_interpreters = True


def _install_requirements(
    session: nox.Session,
    *requirements_files: Path,
) -> None:
    """Install one or more requirement files into a Nox session.

    Args:
        session: Active Nox session receiving the dependencies.
        *requirements_files: Requirement files to install in order.
    """
    for requirements_file in requirements_files:
        session.install("-r", str(requirements_file))


def _run_tests(
    session: nox.Session,
    report_directory: Path | None = None,
) -> None:
    """Run pytest, optionally producing browsable HTML reports.

    Args:
        session: Active Nox session used to invoke pytest.
        report_directory: Destination for test and coverage HTML, if requested.
    """
    pytest_arguments = list(session.posargs)

    if report_directory is not None:
        if report_directory.exists():
            shutil.rmtree(report_directory)
        report_directory.mkdir(parents=True)
        pytest_arguments = [
            "--html",
            str(report_directory / "test-results.html"),
            "--self-contained-html",
            "--cov-report",
            f"html:{report_directory / 'coverage'}",
            "--metadata",
            "Commit",
            os.environ.get("GITHUB_SHA", "local working tree"),
            "--metadata",
            "Branch",
            os.environ.get("GITHUB_REF_NAME", "local working tree"),
            *pytest_arguments,
        ]

    session.run("python", "-m", "pytest", *pytest_arguments)


def _build_documentation(
    session: nox.Session,
    arguments: list[str] | None = None,
) -> None:
    """Build or serve the documentation site through MkDocs.

    Args:
        session: Active Nox session used to invoke MkDocs.
        arguments: Optional MkDocs arguments. A strict build is the default.
    """
    mkdocs_arguments = arguments or ["build", "--strict"]
    session.run("mkdocs", *mkdocs_arguments)


def _copy_reports_into_site() -> None:
    """Copy locally generated reports into the generated documentation site."""
    if SITE_REPORT_DIRECTORY.exists():
        shutil.rmtree(SITE_REPORT_DIRECTORY)
    SITE_REPORT_DIRECTORY.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(REPORT_DIRECTORY, SITE_REPORT_DIRECTORY)


@nox.session(python=PYTHON_VERSION)
def tests(session: nox.Session) -> None:
    """Run the unit-test suite and enforce the configured coverage threshold."""
    _install_requirements(session, DEVELOPMENT_REQUIREMENTS)
    _run_tests(session)


@nox.session(python=PYTHON_VERSION)
def reports(session: nox.Session) -> None:
    """Run the unit tests and write test and coverage HTML reports."""
    _install_requirements(session, DEVELOPMENT_REQUIREMENTS)
    _run_tests(session, REPORT_DIRECTORY)


@nox.session(python=PYTHON_VERSION)
def docs(session: nox.Session) -> None:
    """Build the documentation strictly or run a requested MkDocs command."""
    _install_requirements(
        session,
        RUNTIME_REQUIREMENTS,
        DOCUMENTATION_REQUIREMENTS,
    )
    requested_arguments = list(session.posargs) or None
    _build_documentation(session, requested_arguments)


@nox.session(python=PYTHON_VERSION)
def ci(session: nox.Session) -> None:
    """Run tests once, build reports and docs, and assemble the local site."""
    _install_requirements(
        session,
        DEVELOPMENT_REQUIREMENTS,
        DOCUMENTATION_REQUIREMENTS,
    )
    _run_tests(session, REPORT_DIRECTORY)
    _build_documentation(session)
    _copy_reports_into_site()
