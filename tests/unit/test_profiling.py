"""Tests for dataset profiling module."""

import numpy as np
import pandas as pd

from smartcsv.core.profiling import (
    compute_correlation_matrix,
    get_top_correlations,
    profile_dataset,
)


class TestProfileDataset:
    def test_basic_profile(self, sample_df: pd.DataFrame) -> None:
        profile = profile_dataset(sample_df)
        assert profile.row_count == len(sample_df)
        assert profile.column_count == len(sample_df.columns)
        assert profile.numeric_column_count > 0
        assert profile.categorical_column_count > 0
        assert len(profile.columns) == len(sample_df.columns)

    def test_missing_data_profile(self, sample_df_with_missing: pd.DataFrame) -> None:
        profile = profile_dataset(sample_df_with_missing)
        assert profile.total_missing_cells > 0
        assert profile.total_missing_percentage > 0

        # Check column-level missing
        value_col = next(c for c in profile.columns if c.name == "value")
        assert value_col.missing_count > 0
        assert value_col.missing_percentage > 0

    def test_duplicate_detection(self, sample_df_with_duplicates: pd.DataFrame) -> None:
        profile = profile_dataset(sample_df_with_duplicates)
        assert profile.duplicate_row_count > 0
        assert profile.duplicate_row_percentage > 0

    def test_numeric_profile(self, sample_df: pd.DataFrame) -> None:
        profile = profile_dataset(sample_df)
        numeric_cols = [c for c in profile.columns if c.numeric is not None]
        assert len(numeric_cols) > 0

        for col in numeric_cols:
            assert col.numeric is not None
            assert col.numeric.mean is not None
            assert col.numeric.median is not None
            assert col.numeric.std is not None
            assert col.numeric.q1 <= col.numeric.median <= col.numeric.q3

    def test_categorical_profile(self, sample_df: pd.DataFrame) -> None:
        profile = profile_dataset(sample_df)
        cat_cols = [c for c in profile.columns if c.categorical is not None]
        assert len(cat_cols) > 0

        for col in cat_cols:
            assert col.categorical is not None
            assert col.categorical.most_frequent != ""
            assert col.categorical.most_frequent_count > 0
            assert len(col.categorical.top_values) > 0

    def test_datetime_profile(self, datetime_df: pd.DataFrame) -> None:
        profile = profile_dataset(datetime_df)
        dt_cols = [c for c in profile.columns if c.datetime is not None]
        assert len(dt_cols) > 0

        dt_col = dt_cols[0]
        assert dt_col.datetime is not None
        assert dt_col.datetime.min_date != "N/A"
        assert dt_col.datetime.date_range_days > 0

    def test_constant_column(self, constant_column_df: pd.DataFrame) -> None:
        profile = profile_dataset(constant_column_df)
        assert "constant" in profile.constant_columns

    def test_high_cardinality(self, high_cardinality_df: pd.DataFrame) -> None:
        profile = profile_dataset(high_cardinality_df)
        assert "unique_col" in profile.high_cardinality_columns

    def test_outlier_detection(self, outlier_df: pd.DataFrame) -> None:
        profile = profile_dataset(outlier_df)
        value_col = next(c for c in profile.columns if c.name == "value")
        assert value_col.numeric is not None
        assert value_col.numeric.outlier_count > 0

    def test_empty_numeric_column(self) -> None:
        df = pd.DataFrame({"x": [np.nan, np.nan, np.nan], "y": [1, 2, 3]})
        profile = profile_dataset(df)
        assert len(profile.columns) == 2


class TestCorrelation:
    def test_correlation_matrix(self, numeric_only_df: pd.DataFrame) -> None:
        corr = compute_correlation_matrix(numeric_only_df)
        assert corr is not None
        assert corr.shape[0] == corr.shape[1]
        # Diagonal should be 1.0
        for i in range(len(corr)):
            assert abs(corr.iloc[i, i] - 1.0) < 0.001

    def test_correlation_insufficient_columns(self) -> None:
        df = pd.DataFrame({"x": [1, 2, 3]})
        assert compute_correlation_matrix(df) is None

    def test_constant_columns_excluded(self, constant_column_df: pd.DataFrame) -> None:
        corr = compute_correlation_matrix(constant_column_df)
        if corr is not None:
            assert "constant" not in corr.columns

    def test_top_correlations(self, numeric_only_df: pd.DataFrame) -> None:
        corr = compute_correlation_matrix(numeric_only_df)
        assert corr is not None
        top = get_top_correlations(corr, n=5)
        assert len(top) > 0
        # Should be sorted by absolute value
        for i in range(len(top) - 1):
            assert abs(top[i][2]) >= abs(top[i + 1][2])
