"""Dataset profiling module."""

from __future__ import annotations

import numpy as np
import pandas as pd

from smartcsv.config import config
from smartcsv.models.profile import (
    CategoricalProfile,
    ColumnProfile,
    DatasetProfile,
    DatetimeProfile,
    NumericProfile,
)
from smartcsv.utils.helpers import get_column_categories
from smartcsv.utils.logging import get_logger

logger = get_logger(__name__)


def profile_dataset(df: pd.DataFrame) -> DatasetProfile:
    """Generate a complete profile for a dataset.

    This operation is read-only and does not modify the DataFrame.

    Args:
        df: The DataFrame to profile.

    Returns:
        DatasetProfile with all column-level and dataset-level statistics.
    """
    categories = get_column_categories(df)
    column_profiles = []

    for col in df.columns:
        col_str = str(col)
        series = df[col]
        non_null = int(series.notna().sum())
        missing = int(series.isna().sum())
        total = len(df)
        unique = int(series.nunique())
        missing_pct = round(missing / total * 100, 2) if total > 0 else 0.0
        cardinality = round(unique / non_null, 4) if non_null > 0 else 0.0

        # Determine category
        if col_str in categories["numeric"]:
            category = "numeric"
            numeric_profile = _profile_numeric(series)
            cat_profile = None
            dt_profile = None
        elif col_str in categories["datetime"]:
            category = "datetime"
            numeric_profile = None
            cat_profile = None
            dt_profile = _profile_datetime(series)
        elif col_str in categories["categorical"]:
            category = "categorical"
            numeric_profile = None
            cat_profile = _profile_categorical(series)
            dt_profile = None
        else:
            category = "other"
            numeric_profile = None
            cat_profile = _profile_categorical(series) if non_null > 0 else None
            dt_profile = None

        column_profiles.append(
            ColumnProfile(
                name=col_str,
                dtype=str(series.dtype),
                category=category,
                non_null_count=non_null,
                missing_count=missing,
                missing_percentage=missing_pct,
                unique_count=unique,
                cardinality=cardinality,
                numeric=numeric_profile,
                categorical=cat_profile,
                datetime=dt_profile,
            )
        )

    # Dataset-level stats
    total_cells = len(df) * len(df.columns)
    total_missing = int(df.isna().sum().sum())
    dup_count = int(df.duplicated().sum())

    # Identify problem columns
    constant_cols = [
        cp.name
        for cp in column_profiles
        if cp.unique_count <= config.CONSTANT_COLUMN_NUNIQUE and cp.non_null_count > 0
    ]
    high_missing = [
        cp.name
        for cp in column_profiles
        if cp.missing_percentage >= config.HIGH_MISSING_THRESHOLD * 100
    ]
    high_card = [
        cp.name
        for cp in column_profiles
        if cp.category == "categorical" and cp.unique_count >= config.HIGH_CARDINALITY_THRESHOLD
    ]

    return DatasetProfile(
        row_count=len(df),
        column_count=len(df.columns),
        memory_usage_bytes=int(df.memory_usage(deep=True).sum()),
        numeric_column_count=len(categories["numeric"]),
        categorical_column_count=len(categories["categorical"]),
        datetime_column_count=len(categories["datetime"]),
        other_column_count=len(df.columns)
        - len(categories["numeric"])
        - len(categories["categorical"])
        - len(categories["datetime"]),
        total_missing_cells=total_missing,
        total_missing_percentage=round(total_missing / total_cells * 100, 2)
        if total_cells > 0
        else 0.0,
        duplicate_row_count=dup_count,
        duplicate_row_percentage=round(dup_count / len(df) * 100, 2) if len(df) > 0 else 0.0,
        columns=column_profiles,
        constant_columns=constant_cols,
        high_missing_columns=high_missing,
        high_cardinality_columns=high_card,
    )


def _profile_numeric(series: pd.Series) -> NumericProfile:
    """Profile a numeric column."""
    clean = series.dropna()
    if len(clean) == 0:
        return NumericProfile(
            mean=0.0,
            median=0.0,
            std=0.0,
            min_val=0.0,
            max_val=0.0,
            q1=0.0,
            q3=0.0,
            iqr=0.0,
            outlier_count=0,
        )

    q1 = float(clean.quantile(0.25))
    q3 = float(clean.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - config.OUTLIER_IQR_MULTIPLIER * iqr
    upper = q3 + config.OUTLIER_IQR_MULTIPLIER * iqr
    outliers = int(((clean < lower) | (clean > upper)).sum())

    try:
        from typing import Any, cast

        skew = float(cast("Any", clean.skew()))
        kurt = float(cast("Any", clean.kurtosis()))
    except Exception:
        skew = None
        kurt = None

    return NumericProfile(
        mean=round(float(clean.mean()), 4),
        median=round(float(clean.median()), 4),
        std=round(float(clean.std()), 4),
        min_val=float(clean.min()),
        max_val=float(clean.max()),
        q1=round(q1, 4),
        q3=round(q3, 4),
        iqr=round(iqr, 4),
        outlier_count=outliers,
        skewness=round(skew, 4) if skew is not None else None,
        kurtosis=round(kurt, 4) if kurt is not None else None,
    )


def _profile_categorical(series: pd.Series) -> CategoricalProfile:
    """Profile a categorical column."""
    clean = series.dropna().astype(str)
    if len(clean) == 0:
        return CategoricalProfile(
            most_frequent="",
            most_frequent_count=0,
            most_frequent_percentage=0.0,
            unique_count=0,
            top_values=[],
        )

    value_counts = clean.value_counts()
    most_freq = str(value_counts.index[0])
    most_freq_count = int(value_counts.iloc[0])

    return CategoricalProfile(
        most_frequent=most_freq,
        most_frequent_count=most_freq_count,
        most_frequent_percentage=round(most_freq_count / len(clean) * 100, 2),
        unique_count=int(value_counts.shape[0]),
        top_values=[(str(k), int(v)) for k, v in value_counts.head(10).items()],
    )


def _profile_datetime(series: pd.Series) -> DatetimeProfile:
    """Profile a datetime column."""
    clean = pd.to_datetime(series, errors="coerce").dropna()
    if len(clean) == 0:
        return DatetimeProfile(min_date="N/A", max_date="N/A", date_range_days=0)

    min_dt = clean.min()
    max_dt = clean.max()

    # Most common day of week
    try:
        most_common_day = clean.dt.day_name().mode().iloc[0]
    except Exception:
        most_common_day = None

    return DatetimeProfile(
        min_date=str(min_dt.date()),
        max_date=str(max_dt.date()),
        date_range_days=int((max_dt - min_dt).days),
        most_common_day=most_common_day,
    )


def compute_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame | None:
    """Compute Pearson correlation matrix for numeric columns.

    Returns None if fewer than 2 numeric columns exist.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) < 2:
        return None

    # Drop constant columns
    valid_cols = [c for c in numeric_cols if df[c].nunique() > 1]
    if len(valid_cols) < 2:
        return None

    return df[valid_cols].corr(method="pearson").round(4)


def get_top_correlations(corr_matrix: pd.DataFrame, n: int = 10) -> list[tuple[str, str, float]]:
    """Get top N strongest correlations (excluding self-correlations)."""
    pairs = []
    cols = corr_matrix.columns
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            val = corr_matrix.iloc[i, j]
            if pd.notna(val):
                from typing import Any, cast

                pairs.append((cols[i], cols[j], round(float(cast("Any", val)), 4)))

    pairs.sort(key=lambda x: abs(x[2]), reverse=True)
    return pairs[:n]
