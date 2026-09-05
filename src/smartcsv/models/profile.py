"""Data models for dataset profiling results."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class NumericProfile:
    """Statistical profile for a numeric column."""

    mean: float
    median: float
    std: float
    min_val: float
    max_val: float
    q1: float
    q3: float
    iqr: float
    outlier_count: int
    skewness: float | None = None
    kurtosis: float | None = None


@dataclass
class CategoricalProfile:
    """Profile for a categorical column."""

    most_frequent: str
    most_frequent_count: int
    most_frequent_percentage: float
    unique_count: int
    top_values: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class DatetimeProfile:
    """Profile for a datetime column."""

    min_date: str
    max_date: str
    date_range_days: int
    most_common_day: str | None = None


@dataclass
class ColumnProfile:
    """Complete profile for a single column."""

    name: str
    dtype: str
    category: str  # 'numeric', 'categorical', 'datetime', 'other'
    non_null_count: int
    missing_count: int
    missing_percentage: float
    unique_count: int
    cardinality: float
    numeric: NumericProfile | None = None
    categorical: CategoricalProfile | None = None
    datetime: DatetimeProfile | None = None


@dataclass
class DatasetProfile:
    """Complete profile for a dataset."""

    row_count: int
    column_count: int
    memory_usage_bytes: int
    numeric_column_count: int
    categorical_column_count: int
    datetime_column_count: int
    other_column_count: int
    total_missing_cells: int
    total_missing_percentage: float
    duplicate_row_count: int
    duplicate_row_percentage: float
    columns: list[ColumnProfile] = field(default_factory=list)
    constant_columns: list[str] = field(default_factory=list)
    high_missing_columns: list[str] = field(default_factory=list)
    high_cardinality_columns: list[str] = field(default_factory=list)
