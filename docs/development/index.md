# Development Guide

## Repository layout

```text
.
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
├── requirements-dev.txt   # Test and coverage dependencies
├── requirements-docs.txt  # Documentation build dependencies
└── requirements.txt       # Runtime dependencies
```

## Run the tests

Install the test environment and run the suite from the repository root:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

The default command reports statement and branch coverage across `src/` and
fails if total coverage falls below 95%. Every branch push and every pull
request targeting `main` runs the same command through
`.github/workflows/tests.yml`.

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

`tests/test_documentation.py` scans every tracked Python file with the standard
library AST. The normal `python -m pytest` command—and therefore the `Unit tests`
CI check—fails with the file, line, object type, and name when documentation is
missing.

## Build the documentation

```bash
python -m pip install -r requirements.txt -r requirements-docs.txt
mkdocs serve
```

Open `http://127.0.0.1:8000/` for a live-reloading preview.

Validate the same strict build used in CI:

```bash
mkdocs build --strict
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

Pushes to `main` and manual workflow dispatches run the Pages workflow. It:

1. installs Python and documentation dependencies;
2. builds with `mkdocs build --strict`;
3. uploads the generated `site/` directory;
4. deploys it through GitHub Pages.

Pull requests build the portal without deploying it, catching broken links,
imports, and configuration errors before merge.
