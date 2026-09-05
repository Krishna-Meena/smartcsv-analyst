# SmartCSV Analyst — Product Requirements Document

## Problem Statement

Data professionals frequently receive CSV datasets that require immediate understanding before deeper analysis. The current workflow involves switching between multiple tools (text editors for encoding issues, spreadsheets for quick stats, Python scripts for cleaning) before meaningful analysis can begin.

This friction delays insights, introduces errors, and creates a poor experience especially for:
- Analysts receiving data from external sources
- Data engineers validating pipeline outputs
- Students learning data analysis workflows

## Target Users

| User | Need |
|------|------|
| **Data Analysts** | Quick dataset understanding and cleaning before reporting |
| **Data Engineers** | Data quality assessment and validation |
| **Data Scientists** | Rapid EDA before modeling |
| **Students** | Learning data analysis workflows |
| **Business Users** | Self-service data exploration without coding |

## Goals

1. Provide a complete CSV analysis workflow in a single application
2. Automate encoding detection, profiling, and quality assessment
3. Enable interactive, auditable data cleaning
4. Generate meaningful visualizations with minimal configuration
5. Produce deterministic, explainable insights without AI/LLM dependencies
6. Demonstrate professional software engineering practices

## Non-Goals

1. **No LLM/AI integration** — Insights are rule-based and deterministic
2. **No multi-file analysis** — Focus on single CSV at a time
3. **No real-time data** — Batch/upload model only
4. **No authentication** — Single-user application
5. **No database connectivity** — CSV files only
6. **No predictive modeling** — Descriptive analysis only

## Functional Requirements

### FR-1: Data Ingestion
- FR-1.1: Accept CSV file upload via drag-and-drop
- FR-1.2: Detect file encoding automatically
- FR-1.3: Detect delimiter automatically
- FR-1.4: Handle BOM-encoded files
- FR-1.5: Handle malformed CSV gracefully
- FR-1.6: Detect and rename duplicate columns
- FR-1.7: Accept CSV from URL (with validation)
- FR-1.8: Enforce configurable file size limits
- FR-1.9: Display metadata after successful upload

### FR-2: Data Profiling
- FR-2.1: Compute dataset-level statistics (rows, columns, memory, types)
- FR-2.2: Compute per-column statistics appropriate to data type
- FR-2.3: Detect and count missing values
- FR-2.4: Detect and count duplicate rows
- FR-2.5: Identify constant columns
- FR-2.6: Identify high-cardinality columns
- FR-2.7: Detect outliers using IQR method
- FR-2.8: Profile datetime columns (range, distribution)

### FR-3: Data Cleaning
- FR-3.1: Fill numeric missing values (mean, median, zero)
- FR-3.2: Fill categorical missing values (mode, custom)
- FR-3.3: Drop rows/columns by missing threshold
- FR-3.4: Remove duplicate rows
- FR-3.5: Convert column types safely
- FR-3.6: Filter rows by conditions
- FR-3.7: Create derived columns with safe expressions
- FR-3.8: Record all actions in an audit trail

### FR-4: Visualization
- FR-4.1: Support 11+ chart types
- FR-4.2: Recommend charts based on data types
- FR-4.3: Allow configuration of axes, colors, facets
- FR-4.4: Sample large datasets for performance
- FR-4.5: Export charts as HTML and PNG

### FR-5: Insights
- FR-5.1: Generate rule-based insights
- FR-5.2: Detect missing data patterns
- FR-5.3: Identify correlations
- FR-5.4: Detect outliers
- FR-5.5: Identify basic trends
- FR-5.6: Classify insights by severity

### FR-6: Export
- FR-6.1: Export cleaned CSV
- FR-6.2: Export audit log (JSON)
- FR-6.3: Export profile report (text)
- FR-6.4: Export insights report (text)
- FR-6.5: Export charts (HTML/PNG)

## Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| **Performance** | Profiling under 3s for <10 MB files |
| **File Size** | Up to 200 MB (configurable) |
| **Security** | No eval/exec, restricted expressions |
| **Reliability** | Graceful error handling, no crashes |
| **Accessibility** | Color-blind safe palettes, sufficient contrast |
| **Maintainability** | >80% test coverage, clean architecture |
| **Reproducibility** | Full audit trail, locked dependencies |

## Architecture

Layered architecture with clear separation:

1. **UI Layer** (Streamlit pages) — Presentation only
2. **Core Layer** (Python modules) — Business logic, independently testable
3. **Model Layer** (dataclasses) — Data structures
4. **Utility Layer** — Logging, validation, helpers

## Success Metrics

| Metric | Target |
|--------|--------|
| Test coverage (core) | >80% |
| Lint errors (Ruff) | 0 |
| Type errors (MyPy) | 0 |
| Pages functional | 6/6 |
| Chart types supported | 11+ |
| Insight categories | 7+ |
| Docker build | Passes |
| CI pipeline | Green |

## Future Roadmap

### v1.1
- Excel and Parquet support
- Custom insight rules via YAML
- PDF report generation

### v1.2
- Polars backend option
- Saved analysis sessions
- Data validation rules

### v2.0
- Multi-dataset joins
- Collaborative features
- Plugin architecture
