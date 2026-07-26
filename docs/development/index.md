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
├── config.py              # Canonical simulation configuration
├── main.py                # Command-line entry point
├── mkdocs.yml             # Documentation configuration
├── requirements-docs.txt  # Documentation build dependencies
└── requirements.txt       # Runtime dependencies
```

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
