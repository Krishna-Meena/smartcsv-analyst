# 📊 SmartCSV Analyst

> **Interactive CSV Analysis & Data Exploration** — Upload a CSV. Understand it instantly.

---

## What Is This?

SmartCSV Analyst is a **fully self-contained, production-grade web application** built with Python and Streamlit. It lets you upload any CSV file and immediately get:

- Automatic data profiling and statistics
- Missing-value detection and smart imputation
- Data cleaning, filtering, and type conversion
- Interactive Plotly charts (histogram, scatter, heatmap, etc.)
- Automated insights (correlations, outliers, trends, skewness)
- One-click export of the cleaned dataset, audit log, and profile report

No database required. No API keys needed. No configuration. Just upload and explore.

---

## Who Is This For?

- **Data analysts** who want fast EDA without writing code
- **Data scientists** who want to validate a new dataset before modelling
- **Developers / students** learning data engineering patterns
- **Interviewers / portfolio viewers** — this demonstrates real production Python skills

---

## Project Structure

```
smartscv/
├── src/
│   └── smartcsv/                  # Main Python package
│       ├── app.py                 # Streamlit app router & sidebar
│       ├── config.py              # Frozen AppConfig dataclass
│       ├── core/                  # Business logic (pure Python, no Streamlit)
│       │   ├── ingestion.py       # CSV parsing, encoding detection, hashing
│       │   ├── cleaning.py        # Missing values, dedup, filter, derived cols
│       │   ├── profiling.py       # Statistical profiles, correlation matrix
│       │   ├── insights.py        # Automated insight generation
│       │   ├── visualization.py   # Plotly chart builders
│       │   └── export.py          # CSV, Parquet, JSON export helpers
│       ├── models/                # Data contracts (dataclasses)
│       │   ├── metadata.py        # DatasetMetadata, ColumnMetadata
│       │   ├── profile.py         # DatasetProfile, ColumnProfile, NumericProfile
│       │   └── chart_config.py    # ChartConfig, CHART_TYPES
│       ├── views/                 # Streamlit page renderers
│       │   ├── upload.py          # File upload + URL + sample data
│       │   ├── overview.py        # Dashboard: KPIs, column details, quality
│       │   ├── clean.py           # Missing, duplicates, types, filter, derived
│       │   ├── visualize.py       # Interactive chart builder
│       │   ├── insights.py        # Automated insight cards
│       │   └── export.py          # Download buttons for all outputs
│       └── utils/
│           ├── helpers.py         # Number formatting, column categorization
│           ├── logging.py         # Structured logging setup
│           └── validation.py      # File-size, URL, column-name validation
├── tests/
│   └── unit/                      # 140 unit tests
├── sample_data/
│   └── sample_finance.csv         # 303-row demo dataset
├── docker/
│   └── Dockerfile                 # Multi-stage Docker build
├── .github/workflows/ci.yml       # GitHub Actions CI/CD
├── .streamlit/config.toml         # Theme + upload size config
├── streamlit_app.py               # Streamlit Cloud entrypoint
├── requirements.txt               # Runtime deps for Streamlit Cloud
└── pyproject.toml                 # uv / hatchling build config
```

---

## Architecture

```
[ User Browser ]
      |
[ Streamlit Server ]
      |  app.py (router + sidebar)
[ views/*.py ]           <- UI only, zero business logic
      |  function calls
[ core/*.py ]            <- Pure Python, fully testable
      |  dataclasses
[ models/*.py ]          <- Typed contracts between layers
```

The key principle: **the UI layer never contains business logic**. All data transformations live in `core/`, making them independently testable without running Streamlit.

---

## Architecture Decisions

| Decision | Rationale |
|---|---|
| Layered architecture | views -> core -> models keeps UI and logic decoupled |
| Frozen dataclasses for config | Prevents accidental mutation of global settings |
| asteval for derived columns | Safe expression evaluation; zero use of eval() or exec() |
| views/ folder name (not pages/) | Streamlit auto-routes files named pages/ — renamed to prevent conflicts |
| Session state caching | Expensive profiling only runs when the DataFrame shape changes |
| Data sampling for viz | Datasets > 50,000 rows are sampled before chart rendering |
| src-layout | Package under src/smartcsv/ — isolates installed vs. editable code |

---

## Quality Metrics

| Check | Result |
|---|---|
| Unit tests | 140 / 140 passing |
| Ruff linting | 0 errors |
| MyPy type checking | 0 errors (25 source files) |
| eval() / exec() usage | None — asteval used exclusively |
| Test coverage (core) | 80-98% |

---

## How to Run Locally

```bash
# Prerequisites: Python 3.12+, uv
pip install uv

# Clone and install
git clone https://github.com/YOUR_USERNAME/smartcsv-analyst.git
cd smartcsv-analyst
uv sync --all-groups

# Run
uv run streamlit run streamlit_app.py
```

## How to Run with Docker

```bash
docker build -f docker/Dockerfile -t smartcsv-analyst .
docker run -p 8501:8501 smartcsv-analyst
```

---

## License

MIT 2025 SmartCSV Analyst Contributors
