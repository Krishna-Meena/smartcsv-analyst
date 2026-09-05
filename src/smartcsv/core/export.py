"""Data export module."""

from __future__ import annotations

import io
import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from smartcsv.utils.logging import get_logger

if TYPE_CHECKING:
    import pandas as pd

    from smartcsv.core.insights import Insight
    from smartcsv.models.profile import DatasetProfile

logger = get_logger(__name__)


def export_csv(df: pd.DataFrame) -> bytes:
    """Export DataFrame to CSV bytes."""
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False, encoding="utf-8")
    return buffer.getvalue()


def export_audit_log(audit_entries: list[dict[str, Any]]) -> str:
    """Export audit log to JSON string."""
    return json.dumps(audit_entries, indent=2, default=str)


def export_profile_report(profile: DatasetProfile, metadata: Any = None) -> str:
    """Export dataset profile as a formatted text report."""
    lines = []
    lines.append("=" * 60)
    lines.append("SMARTCSV ANALYST - DATASET PROFILE REPORT")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")

    # Dataset summary
    lines.append("DATASET SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Rows:                {profile.row_count:,}")
    lines.append(f"Columns:             {profile.column_count}")
    lines.append(f"Numeric Columns:     {profile.numeric_column_count}")
    lines.append(f"Categorical Columns: {profile.categorical_column_count}")
    lines.append(f"Datetime Columns:    {profile.datetime_column_count}")
    lines.append(
        f"Missing Cells:       {profile.total_missing_cells:,} ({profile.total_missing_percentage:.1f}%)"
    )
    lines.append(
        f"Duplicate Rows:      {profile.duplicate_row_count:,} ({profile.duplicate_row_percentage:.1f}%)"
    )
    lines.append("")

    # Column details
    lines.append("COLUMN DETAILS")
    lines.append("-" * 40)
    for col in profile.columns:
        lines.append(f"\n  {col.name} ({col.dtype})")
        lines.append(f"    Category:    {col.category}")
        lines.append(f"    Non-null:    {col.non_null_count:,}")
        lines.append(f"    Missing:     {col.missing_count:,} ({col.missing_percentage:.1f}%)")
        lines.append(f"    Unique:      {col.unique_count:,}")

        if col.numeric:
            n = col.numeric
            lines.append(f"    Mean:        {n.mean:,.4f}")
            lines.append(f"    Median:      {n.median:,.4f}")
            lines.append(f"    Std:         {n.std:,.4f}")
            lines.append(f"    Min:         {n.min_val:,.4f}")
            lines.append(f"    Max:         {n.max_val:,.4f}")
            lines.append(f"    Q1:          {n.q1:,.4f}")
            lines.append(f"    Q3:          {n.q3:,.4f}")
            lines.append(f"    IQR:         {n.iqr:,.4f}")
            lines.append(f"    Outliers:    {n.outlier_count}")

        if col.categorical:
            c = col.categorical
            lines.append(
                f"    Most Freq:   {c.most_frequent} ({c.most_frequent_count:,}, {c.most_frequent_percentage:.1f}%)"
            )

        if col.datetime:
            d = col.datetime
            lines.append(f"    Min Date:    {d.min_date}")
            lines.append(f"    Max Date:    {d.max_date}")
            lines.append(f"    Range:       {d.date_range_days} days")

    # Problem columns
    if profile.constant_columns:
        lines.append(f"\nCONSTANT COLUMNS: {', '.join(profile.constant_columns)}")
    if profile.high_missing_columns:
        lines.append(f"HIGH MISSING COLUMNS: {', '.join(profile.high_missing_columns)}")
    if profile.high_cardinality_columns:
        lines.append(f"HIGH CARDINALITY COLUMNS: {', '.join(profile.high_cardinality_columns)}")

    lines.append("")
    lines.append("=" * 60)
    lines.append("END OF REPORT")
    lines.append("=" * 60)

    return "\n".join(lines)


def export_insights_report(insights: list[Insight]) -> str:
    """Export insights as a formatted text report."""
    lines = []
    lines.append("=" * 60)
    lines.append("SMARTCSV ANALYST - INSIGHTS REPORT")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append(f"\nTotal Insights: {len(insights)}")
    lines.append("")

    for i, insight in enumerate(insights, 1):
        severity_icon = {"critical": "[!!!]", "warning": "[!!]", "info": "[i]"}
        icon = severity_icon.get(insight.severity, "[?]")

        lines.append(f"{i}. {icon} {insight.title}")
        lines.append(f"   Category: {insight.category}")
        lines.append(f"   {insight.explanation}")
        if insight.metric:
            lines.append(f"   Metric: {insight.metric} = {insight.metric_value}")
        if insight.suggestion:
            lines.append(f"   Suggestion: {insight.suggestion}")
        lines.append("")

    lines.append("=" * 60)
    lines.append("END OF REPORT")
    lines.append("=" * 60)

    return "\n".join(lines)
