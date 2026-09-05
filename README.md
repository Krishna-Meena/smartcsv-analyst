<div align="center">

# 📊 SmartCSV Analyst

**Interactive CSV Analysis & Data Exploration**

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.45+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Pandas](https://img.shields.io/badge/Pandas-2.2+-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![Plotly](https://img.shields.io/badge/Plotly-6.0+-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-140%20passing-brightgreen?style=for-the-badge)](tests/)

**[🚀 Live Demo](https://YOUR_APP.streamlit.app)** | **[📖 Project Docs](PROJECT.md)** | **[🔧 How It Works](WORKING.md)** | **[📦 Tech Stack](TECH_STACK.md)**

</div>

---

## What Is This?

SmartCSV Analyst is a **production-grade, fully tested web application** that turns any CSV file into instant insights — no code required.

Upload a CSV → get automatic profiling, data quality warnings, interactive charts, and smart cleaning tools in seconds.

> Built as a portfolio project to demonstrate: Python engineering, Pandas, statistical EDA, Streamlit, software architecture, testing, CI/CD, Docker, and security awareness.

---

## Features

| Feature | Description |
|---|---|
| 📥 **Smart Ingestion** | Auto-detects encoding (UTF-8, Latin-1, CP1252…), delimiter, and duplicate columns |
| 🔍 **Data Profiling** | Full statistical profile: mean, median, std, IQR, outliers, skewness for every column |
| 🧹 **Data Cleaning** | Fill/drop missing values, remove duplicates, convert types, filter rows, create derived columns |
| 📊 **Visualization** | 11 interactive Plotly chart types with export to HTML/PNG |
| 💡 **Automated Insights** | Detects correlations, outliers, trends, skewed distributions, constant columns |
| 📤 **Export** | Download cleaned CSV, audit log (JSON), profile report (TXT), insights summary (TXT) |
| 🔒 **Secure Eval** | Derived columns use `asteval` — zero `eval()` / `exec()` in the codebase |

---

## Quick Start

### Option 1: Run Locally with uv (Recommended)
```bash
# Install uv (fast Python package manager)
pip install uv

# Clone and run
git clone https://github.com/YOUR_USERNAME/smartcsv-analyst.git
cd smartcsv-analyst
uv sync
uv run streamlit run streamlit_app.py
```
Open http://localhost:8501

### Option 2: Run with Docker
```bash
git clone https://github.com/YOUR_USERNAME/smartcsv-analyst.git
cd smartcsv-analyst
docker build -f docker/Dockerfile -t smartcsv-analyst .
docker run -p 8501:8501 smartcsv-analyst
```

### Option 3: Install with pip
```bash
git clone https://github.com/YOUR_USERNAME/smartcsv-analyst.git
cd smartcsv-analyst
pip install -r requirements.txt
streamlit run streamlit_app.py
```

---

## Project Structure

```
smartcsv/
├── src/smartcsv/
│   ├── app.py              # Streamlit router + sidebar
│   ├── config.py           # Frozen config dataclass
│   ├── core/               # Pure Python business logic (fully testable)
│   │   ├── ingestion.py    # CSV parsing, encoding detection
│   │   ├── cleaning.py     # Missing values, dedup, filter, derived cols
│   │   ├── profiling.py    # Statistical profiling, correlation
│   │   ├── insights.py     # Automated insight generation
│   │   ├── visualization.py# Plotly chart builders
│   │   └── export.py       # Export helpers
│   ├── models/             # Typed data contracts (dataclasses)
│   └── views/              # Streamlit UI pages
├── tests/unit/             # 140 unit tests
├── sample_data/            # Built-in 303-row finance dataset
├── docker/Dockerfile       # Multi-stage production Docker build
├── .github/workflows/      # GitHub Actions CI/CD
├── streamlit_app.py        # Streamlit Cloud entrypoint
└── requirements.txt        # Runtime dependencies
```

---

## Architecture

```
views/*.py  (UI only)
    ↓
core/*.py   (pure Python, zero Streamlit imports)
    ↓
models/*.py (typed dataclasses — data contracts)
```

The UI layer **never** contains business logic. Every core function is independently unit-testable.

---

## Code Quality

```bash
uv run ruff check src/ tests/    # ✅ 0 errors
uv run mypy src/smartcsv/        # ✅ 0 errors (25 files)
uv run pytest                    # ✅ 140/140 passing
```

---

## Security

- ✅ Zero `eval()` or `exec()` — verified by grep
- ✅ `asteval` with restricted symbol table for derived column expressions
- ✅ Docker runs as non-root user
- ✅ File size validation (200 MB limit)
- ✅ Filename sanitization on upload

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Web Framework | Streamlit |
| Data | Pandas 2.x + NumPy 2.x |
| Statistics | SciPy |
| Charts | Plotly |
| Safe Eval | asteval |
| Encoding Detection | charset-normalizer |
| Linting | Ruff |
| Type Checking | MyPy |
| Testing | pytest + pytest-cov |
| Package Manager | uv |
| CI/CD | GitHub Actions |
| Container | Docker (multi-stage) |
| Hosting | Streamlit Community Cloud |

---

## License

MIT © 2026 SmartCSV Analyst Contributors
