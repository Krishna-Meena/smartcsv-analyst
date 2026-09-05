# TECH_STACK.md — Technologies Used in SmartCSV Analyst

A complete reference of every tool, library, and service used — what it is, why we chose it, and how it is used in the project.

---

## Core Application

### Python 3.12
- **What:** The programming language
- **Why:** Latest stable release with full type-hint support, `match` statements, and `tomllib` built-in
- **Used for:** Everything

### Streamlit 1.45+
- **What:** An open-source framework for building data web apps in pure Python — no HTML/CSS/JS required
- **Why:** Ideal for data-focused apps; handles UI state, file uploads, and interactive widgets out of the box
- **Used for:** All 6 pages, sidebar navigation, file uploader, download buttons, charts, metrics, expanders

---

## Data Processing

### Pandas 2.2+
- **What:** The standard Python library for tabular data
- **Why:** Industry-standard DataFrame manipulation; first-class integration with Streamlit and Plotly
- **Used for:** CSV parsing, column profiling, missing-value imputation, duplicate removal, filtering, type conversion

### NumPy 2.0+
- **What:** Numerical computing library
- **Why:** Required by Pandas and SciPy; used directly for array operations and outlier calculations
- **Used for:** IQR outlier detection, linear regression arrays in trend analysis, data sampling

### SciPy 1.14+
- **What:** Scientific computing library built on NumPy
- **Why:** Provides `scipy.stats.linregress` for trend detection without pulling in a full ML library
- **Used for:** Linear regression for time-series trend analysis in the Insights module

---

## Visualization

### Plotly 6.0+
- **What:** Interactive charting library with both Python and JavaScript rendering
- **Why:** Charts are interactive (zoom, hover, pan) in the browser; exports cleanly to HTML and PNG
- **Used for:** Histograms, scatter plots, box plots, bar charts, line charts, heatmaps, pie charts

### Kaleido 0.2+
- **What:** Plotly's static image export engine
- **Why:** Required to export Plotly charts as PNG without a browser
- **Used for:** "Export as PNG" button in the Visualize page

---

## Security & Expressions

### asteval 1.0+
- **What:** Safe mathematical expression evaluator for Python
- **Why:** Users need to create derived columns (e.g., `Price * 1.1`). Using Python's built-in `eval()` would be a critical security hole. asteval provides a restricted environment with no access to builtins, imports, or file system.
- **Used for:** "Derived Columns" feature in the Clean page

---

## Encoding Detection

### charset-normalizer 3.3+
- **What:** Detects the character encoding of text files
- **Why:** CSV files can be encoded in UTF-8, Latin-1, CP1252, etc. Without detection, non-ASCII characters break on load.
- **Used for:** Auto-detecting file encoding in `core/ingestion.py` before passing to `pd.read_csv()`

---

## Configuration & Serialization

### PyYAML 6.0+
- **What:** YAML parser and emitter for Python
- **Why:** Required by several dependencies; used for config file parsing
- **Used for:** Indirect dependency; included for completeness

---

## Package Management & Build

### uv
- **What:** An extremely fast Python package manager (written in Rust)
- **Why:** 10-100x faster than pip; handles virtual environments, dependency locking, and project builds
- **Used for:** `uv sync` to install dependencies, `uv run` to run scripts, `uv export` to generate requirements.txt

### Hatchling
- **What:** A PEP 517/518 compliant build backend
- **Why:** Modern, fast, zero-config build backend that works with `pyproject.toml`
- **Used for:** `pyproject.toml` build system; packages `src/smartcsv/` into a wheel

### pyproject.toml
- **What:** The modern Python project configuration standard (PEP 517/518/621)
- **Why:** Single file for project metadata, dependencies, tool config (ruff, mypy, pytest)
- **Used for:** Project definition, dependency declaration, tool configuration

---

## Code Quality

### Ruff
- **What:** An extremely fast Python linter and formatter (written in Rust)
- **Why:** Replaces flake8 + isort + pyupgrade + dozens of other tools; runs in milliseconds
- **Used for:** Linting (`ruff check`), formatting (`ruff format`), import sorting; enforces E/F/W/I/N/UP/B/A/SIM/TCH/RUF rule sets

### MyPy
- **What:** Static type checker for Python
- **Why:** Catches type mismatches at development time; enforces contracts between `core/` and `views/`
- **Used for:** `uv run mypy src/smartcsv/` — checks all 25 source files

### pandas-stubs / types-PyYAML
- **What:** Type stub packages for third-party libraries
- **Why:** MyPy needs type information for libraries that don't ship their own `.pyi` files
- **Used for:** Enabling MyPy to type-check Pandas and PyYAML code

---

## Testing

### pytest 8.0+
- **What:** The standard Python testing framework
- **Why:** Clean test discovery, parametrize support, excellent fixture system
- **Used for:** 140 unit tests across ingestion, cleaning, profiling, insights, visualization

### pytest-cov
- **What:** Code coverage plugin for pytest
- **Why:** Measures which lines of code are actually executed during tests
- **Used for:** `--cov=src/smartcsv` flag; generates HTML and XML coverage reports

---

## CI/CD & Deployment

### GitHub Actions
- **What:** GitHub's built-in CI/CD automation
- **Why:** Free for public repositories; runs on every push and pull request
- **Used for:** Runs ruff, mypy, pytest, and Docker build verification on every commit
- **Config:** `.github/workflows/ci.yml`

### Docker (Multi-stage)
- **What:** Container platform
- **Why:** Reproducible builds; the app runs identically on any machine or cloud service with Docker
- **Build:** Two stages — `builder` (installs deps with uv) → `runtime` (minimal image, non-root user)
- **Config:** `docker/Dockerfile`

### Streamlit Community Cloud (Free Deployment)
- **What:** Streamlit's free hosting platform for Streamlit apps
- **Why:** One-click GitHub integration; free tier; perfect for demo/portfolio apps
- **Config:** `streamlit_app.py` (root entrypoint), `requirements.txt`, `.streamlit/config.toml`

---

## Deployment Files Summary

| File | Purpose |
|---|---|
| `streamlit_app.py` | Entrypoint for Streamlit Cloud (adds src/ to sys.path) |
| `requirements.txt` | Runtime dependencies for Streamlit Cloud pip install |
| `.streamlit/config.toml` | App theme, upload size limit, usage stats opt-out |
| `docker/Dockerfile` | Multi-stage production Docker image |
| `.github/workflows/ci.yml` | GitHub Actions CI pipeline |
| `pyproject.toml` | Full project config (deps, tools, build) |
| `uv.lock` | Deterministic dependency lock file |

---

## Summary Table

| Category | Tool | Version |
|---|---|---|
| Language | Python | 3.12+ |
| Web Framework | Streamlit | 1.45+ |
| Data | Pandas | 2.2+ |
| Numerics | NumPy | 2.0+ |
| Statistics | SciPy | 1.14+ |
| Charts | Plotly | 6.0+ |
| PNG Export | Kaleido | 0.2+ |
| Safe Eval | asteval | 1.0+ |
| Encoding | charset-normalizer | 3.3+ |
| Pkg Manager | uv | latest |
| Build Backend | Hatchling | latest |
| Linter | Ruff | 0.8+ |
| Type Checker | MyPy | 1.13+ |
| Test Runner | pytest | 8.0+ |
| Coverage | pytest-cov | 6.0+ |
| CI/CD | GitHub Actions | — |
| Container | Docker | any |
| Hosting | Streamlit Cloud | free |
