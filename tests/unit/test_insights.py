"""Tests for insights engine."""

import numpy as np
import pandas as pd

from smartcsv.core.insights import generate_insights
from smartcsv.core.profiling import profile_dataset


class TestMissingDataInsights:
    def test_detects_missing(self, sample_df_with_missing: pd.DataFrame) -> None:
        profile = profile_dataset(sample_df_with_missing)
        insights = generate_insights(sample_df_with_missing, profile)
        missing_insights = [i for i in insights if i.category == "missing_data"]
        assert len(missing_insights) > 0

    def test_no_missing_no_insight(self, sample_df: pd.DataFrame) -> None:
        profile = profile_dataset(sample_df)
        insights = generate_insights(sample_df, profile)
        missing_insights = [i for i in insights if i.category == "missing_data"]
        assert len(missing_insights) == 0


class TestOutlierInsights:
    def test_detects_outliers(self, outlier_df: pd.DataFrame) -> None:
        profile = profile_dataset(outlier_df)
        insights = generate_insights(outlier_df, profile)
        outlier_insights = [i for i in insights if i.category == "outlier"]
        assert len(outlier_insights) > 0


class TestCorrelationInsights:
    def test_detects_correlation(self) -> None:
        np.random.seed(42)
        x = np.random.normal(0, 1, 100)
        df = pd.DataFrame(
            {"x": x, "y": x * 2 + np.random.normal(0, 0.1, 100), "z": np.random.normal(0, 1, 100)}
        )
        profile = profile_dataset(df)
        insights = generate_insights(df, profile)
        corr_insights = [i for i in insights if i.category == "correlation"]
        assert len(corr_insights) > 0


class TestQualityInsights:
    def test_duplicate_insight(self, sample_df_with_duplicates: pd.DataFrame) -> None:
        profile = profile_dataset(sample_df_with_duplicates)
        insights = generate_insights(sample_df_with_duplicates, profile)
        quality_insights = [i for i in insights if i.category == "quality"]
        assert any("Duplicate" in i.title for i in quality_insights)

    def test_constant_column_insight(self, constant_column_df: pd.DataFrame) -> None:
        profile = profile_dataset(constant_column_df)
        insights = generate_insights(constant_column_df, profile)
        constant_insights = [i for i in insights if "Constant" in i.title]
        assert len(constant_insights) > 0


class TestTrendInsights:
    def test_detects_trend(self, datetime_df: pd.DataFrame) -> None:
        profile = profile_dataset(datetime_df)
        insights = generate_insights(datetime_df, profile)
        trend_insights = [i for i in insights if i.category == "trend"]
        # Should detect the increasing trend column
        assert len(trend_insights) > 0


class TestInsightSeverity:
    def test_sorted_by_severity(self, sample_df_with_missing: pd.DataFrame) -> None:
        profile = profile_dataset(sample_df_with_missing)
        insights = generate_insights(sample_df_with_missing, profile)
        if len(insights) > 1:
            severity_order = {"critical": 0, "warning": 1, "info": 2}
            for i in range(len(insights) - 1):
                assert severity_order.get(insights[i].severity, 3) <= severity_order.get(
                    insights[i + 1].severity, 3
                )

    def test_insight_structure(self, sample_df_with_missing: pd.DataFrame) -> None:
        profile = profile_dataset(sample_df_with_missing)
        insights = generate_insights(sample_df_with_missing, profile)
        for insight in insights:
            assert insight.severity in ("critical", "warning", "info")
            assert insight.title
            assert insight.explanation
            assert insight.category
