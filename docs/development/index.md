# Development Guide

## Repository layout

```text
.
├── .github/
│   ├── actions/           # Shared GitHub Actions setup steps
│   └── workflows/         # Thin CI orchestration
├── .python-version        # Canonical Python version
├── analysis/              # Result parsing, tables, and plots
├── configs/               # Scenario overrides
├── data/                  # Raw and calibrated FEMA data
├── docs/                  # Markdown documentation portal
├── results/               # Generated experiment outputs
├── src/
│   ├── autonomy/          # Confidence and adaptive intervention
│   ├── environment/       # Models and episode generation
│   ├── planners/          # Baseline and AI heuristics
│   ├── simulation/        # Outcome and experiment orchestration
│   ├── supervisor/        # Supervisor behavior policies
│   └── trust/             # Bayesian trust model
├── tests/                  # Mirrors the src package structure
│   ├── autonomy/
│   ├── environment/
│   ├── planners/
│   ├── simulation/
│   ├── supervisor/
│   └── trust/
├── config.py              # Canonical simulation configuration
├── main.py                # Command-line entry point
├── mkdocs.yml             # Documentation configuration
├── noxfile.py             # Local and CI automation sessions
├── requirements-dev.txt   # Test and coverage dependencies
├── requirements-docs.txt  # Documentation build dependencies
├── requirements-nox.txt   # Automation runner dependency
└── requirements.txt       # Runtime dependencies
```

## Run the tests

Install Nox and run the test session from the repository root:

```bash
python -m pip install -r requirements-nox.txt
nox -s tests
```

Nox creates an isolated environment and installs the session dependencies. The
test session reports statement and branch coverage across `src/` and fails if
total coverage falls below 95%. Pass pytest arguments after `--`, for example
`nox -s tests -- tests/planners/test_ai_planner.py`.

Every branch push and every pull request targeting `main` runs the report
session through `.github/workflows/ci.yml`. That session executes the same tests
once while also generating the HTML artifacts used by the documentation site.

## Protect merges into main

The workflow exposes a uniquely named `Unit tests` status check for pull
requests targeting `main`. To make a failing test block the merge button, the
repository's ruleset or branch protection for `main` must require this status
check. In the GitHub repository settings:

1. Create or edit the branch ruleset/protection rule targeting `main`.
2. Enable **Require status checks to pass before merging**.
3. Add **Unit tests** as a required status check.
4. Enable **Do not allow bypassing** if the requirement should also apply to
   repository administrators.

GitHub only offers a check for selection after it has run in the repository, so
push this workflow once before selecting `Unit tests` in the protection rule.

The documentation workflow also publishes human-readable
[test results and coverage reports](test-reports.md) from the exact commit used
to build the site. These reports refresh after a successful push to `main`.

Test modules follow a one-to-one naming convention. Source code at
`src/<package>/<module>.py` belongs in `tests/<package>/test_<module>.py`.
`tests/test_source_layout.py` enforces this mapping, so CI identifies a missing
test module as soon as a new source module is introduced.

## Document Python code and tests

Every tracked Python module, class, method, function, fixture, helper, and test
must have a Python docstring. Test docstrings should state the behavior being
verified, while implementation docstrings should describe the object's purpose
and contract. Use a string literal immediately inside the object rather than a
regular comment so Python, `help()`, IDEs, and mkdocstrings can discover it.
Use the Google-style `Args`, `Returns`, `Raises`, and `Attributes` sections
configured in `mkdocs.yml`; do not use Doxygen directives such as `@brief`,
`@param`, or `@return` in Python files.

`tests/test_documentation.py` scans every tracked Python file with the standard
library AST. The normal `nox -s tests` command—and therefore the `Unit tests` CI
check—fails with the file, line, object type, and name when documentation is
missing. The same test module also reports the exact location of any Doxygen
directive, keeping the documentation convention consistent as the repository
grows.

## Build the documentation

```bash
nox -s docs -- serve
```

Open `http://127.0.0.1:8000/` for a live-reloading preview.

Validate the same strict build used in CI:

```bash
nox -s docs
```

Generated files are written to `site/` and should not be committed.

## Update API documentation

API pages contain mkdocstrings directives such as:

```markdown
::: src.autonomy.adaptive_autonomy
```

Keep public Python docstrings current; signatures and member listings update
automatically. New public modules should be added to the relevant API page and
to `nav` in `mkdocs.yml` when a new page is needed.

## Documentation features

Use fenced `mermaid` blocks for diagrams, `\( ... \)` or `\[ ... \]` for
mathematics, and language-tagged fenced blocks for code. Material provides
search, mobile navigation, copy buttons, light/dark palettes, and section tabs.

## Deployment

The `CI` workflow separates reusable commands from GitHub-specific
orchestration:

- `.python-version` is the single source for the Python version used locally,
  by Nox, and by GitHub Actions.
- `noxfile.py` defines independently runnable `tests`, `reports`, `docs`, and
  `ci` sessions.
- `.github/actions/setup-python-environment/action.yml` centralizes Python,
  pip-cache, and Nox setup for every job.
- `.github/workflows/ci.yml` defines event rules, job dependencies, artifact
  transfer, and deployment permissions.

Use `nox -s ci` to reproduce the complete pipeline locally. It runs the tests
once, generates the HTML reports, performs a strict documentation build, and
places the reports in the generated site.

Every push runs the `Unit tests` job. Pull requests targeting `main` also build
the documentation but do not deploy it. A successful push to `main`:

1. runs the tests and coverage gate;
2. uploads the generated reports as a workflow artifact;
3. builds the documentation and adds that exact artifact to the site;
4. deploys the assembled site through GitHub Pages.

The test report artifact is retained for 14 days. Jobs have explicit timeouts,
concurrent superseded runs are cancelled away from `main`, and write
permissions are limited to the deployment job.

When adding automation, prefer a Nox session for locally reproducible behavior,
extend the composite action only for setup shared by multiple jobs, and keep
event conditions and job relationships in the workflow. A separate rules file
is unnecessary while GitHub Actions can express those conditions directly.
