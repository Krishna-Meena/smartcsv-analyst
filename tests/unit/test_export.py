"""Tests for export module."""

import json

import pandas as pd

from smartcsv.core.export import (
    export_audit_log,
    export_csv,
    export_insights_report,
    export_profile_report,
)
from smartcsv.core.insights import generate_insights
from smartcsv.core.profiling import profile_dataset


class TestExportCSV:
    def test_export_basic(self, sample_df: pd.DataFrame) -> None:
        result = export_csv(sample_df)
        assert isinstance(result, bytes)
        assert len(result) > 0
        # Should be valid CSV
        lines = result.decode("utf-8").strip().split("\n")
        assert len(lines) == len(sample_df) + 1  # header + data


class TestExportAuditLog:
    def test_export_empty(self) -> None:
        result = export_audit_log([])
        assert json.loads(result) == []

    def test_export_entries(self) -> None:
        entries = [
            {"action": "test", "column": "col", "rows_affected": 5},
            {"action": "test2", "column": "col2", "rows_affected": 10},
        ]
        result = export_audit_log(entries)
        parsed = json.loads(result)
        assert len(parsed) == 2


class TestExportProfile:
    def test_export_report(self, sample_df: pd.DataFrame) -> None:
        profile = profile_dataset(sample_df)
        report = export_profile_report(profile)
        assert "DATASET PROFILE REPORT" in report
        assert "Rows:" in report
        assert "Columns:" in report


class TestExportInsights:
    def test_export_report(self, sample_df_with_missing: pd.DataFrame) -> None:
        profile = profile_dataset(sample_df_with_missing)
        insights = generate_insights(sample_df_with_missing, profile)
        report = export_insights_report(insights)
        assert "INSIGHTS REPORT" in report

    def test_empty_insights(self) -> None:
        report = export_insights_report([])
        assert "Total Insights: 0" in report
