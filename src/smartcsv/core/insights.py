"""Rule-based insights engine.

Generates deterministic, explainable insights from dataset profiles.
No LLM or generative AI - all insights are rule-based.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
from scipy import stats

from smartcsv.config import config
from smartcsv.utils.helpers import get_column_categories
from smartcsv.utils.logging import get_logger

if TYPE_CHECKING:
    from smartcsv.models.profile import DatasetProfile

logger = get_logger(__name__)


@dataclass
class Insight:
    """A single analytical insight."""

    severity: str  # 'info', 'warning', 'critical'
    category: str  # 'missing_data', 'quality', 'correlation', 'outlier', 'distribution', 'trend'
    title: str
    explanation: str
    metric: str = ""
    metric_value: Any = None
    column: str | None = None
    suggestion: str = ""


def generate_insights(df: pd.DataFrame, profile: DatasetProfile) -> list[Insight]:
    """Generate all insights for a dataset.

    Args:
        df: The DataFrame.
        profile: The dataset profile.

    Returns:
        List of Insight objects, sorted by severity.
    """
    insights: list[Insight] = []

    insights.extend(_missing_data_insights(profile))
    insights.extend(_quality_insights(df, profile))
    insights.extend(_outlier_insights(profile))
    insights.extend(_correlation_insights(df))
    insights.extend(_distribution_insights(df, profile))
    insights.extend(_trend_insights(df))
    insights.extend(_constant_column_insights(profile))
    insights.extend(_cardinality_insights(profile))

    # Sort by severity
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    insights.sort(key=lambda x: severity_order.get(x.severity, 3))

    return insights


def _missing_data_insights(profile: DatasetProfile) -> list[Insight]:
    """Generate insights about missing data."""
    insights = []

    if profile.total_missing_percentage > 0:
        severity = (
            "critical"
            if profile.total_missing_percentage > 20
            else ("warning" if profile.total_missing_percentage > 5 else "info")
        )
        insights.append(
            Insight(
                severity=severity,
                category="missing_data",
                title="Missing Data Detected",
                explanation=f"The dataset has {profile.total_missing_cells:,} missing values "
                f"({profile.total_missing_percentage:.1f}% of all cells).",
                metric="Total Missing %",
                metric_value=profile.total_missing_percentage,
                suggestion="Consider imputing or removing missing values before analysis.",
            )
        )

    for col in profile.columns:
        if col.missing_percentage > 50:
            insights.append(
                Insight(
                    severity="critical",
                    category="missing_data",
                    title=f"High Missing Rate: {col.name}",
                    explanation=f"Column '{col.name}' has {col.missing_percentage:.1f}% missing values. "
                    f"Consider removal if data cannot be recovered.",
                    metric="Missing %",
                    metric_value=col.missing_percentage,
                    column=col.name,
                    suggestion="Consider dropping this column or investigating data collection issues.",
                )
            )
        elif col.missing_percentage > 10:
            insights.append(
                Insight(
                    severity="warning",
                    category="missing_data",
                    title=f"Notable Missing Values: {col.name}",
                    explanation=f"Column '{col.name}' has {col.missing_percentage:.1f}% missing values.",
                    metric="Missing %",
                    metric_value=col.missing_percentage,
                    column=col.name,
                    suggestion="Consider imputation using mean, median, or mode.",
                )
            )

    return insights


def _quality_insights(df: pd.DataFrame, profile: DatasetProfile) -> list[Insight]:
    """Generate data quality insights."""
    insights = []

    if profile.duplicate_row_count > 0:
        pct = profile.duplicate_row_percentage
        severity = "warning" if pct > 5 else "info"
        insights.append(
            Insight(
                severity=severity,
                category="quality",
                title="Duplicate Rows Found",
                explanation=f"Found {profile.duplicate_row_count:,} duplicate rows "
                f"({pct:.1f}% of the dataset).",
                metric="Duplicate Rows",
                metric_value=profile.duplicate_row_count,
                suggestion="Consider removing duplicates if they are not intentional.",
            )
        )

    return insights


def _outlier_insights(profile: DatasetProfile) -> list[Insight]:
    """Generate outlier insights."""
    insights = []

    for col in profile.columns:
        if col.numeric and col.numeric.outlier_count > 0:
            total = col.non_null_count
            outlier_pct = round(col.numeric.outlier_count / total * 100, 1) if total > 0 else 0

            severity = "warning" if outlier_pct > 10 else "info"

            insights.append(
                Insight(
                    severity=severity,
                    category="outlier",
                    title=f"Outliers Detected: {col.name}",
                    explanation=f"Column '{col.name}' has {col.numeric.outlier_count:,} outliers "
                    f"({outlier_pct}% of values) using IQR method. "
                    f"Range: [{col.numeric.min_val:,.2f}, {col.numeric.max_val:,.2f}], "
                    f"IQR: {col.numeric.iqr:,.2f}.",
                    metric="Outlier Count",
                    metric_value=col.numeric.outlier_count,
                    column=col.name,
                    suggestion="Review outliers to determine if they represent data errors or genuine extreme values.",
                )
            )

    return insights


def _correlation_insights(df: pd.DataFrame) -> list[Insight]:
    """Generate correlation insights."""
    insights: list[Insight] = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # Need at least 2 numeric columns and enough data
    if len(numeric_cols) < 2 or len(df) < 10:
        return insights

    # Filter out constant columns
    valid_cols = [c for c in numeric_cols if df[c].nunique() > 1]
    if len(valid_cols) < 2:
        return insights

    corr = df[valid_cols].corr()

    for i in range(len(valid_cols)):
        for j in range(i + 1, len(valid_cols)):
            from typing import cast

            val = float(cast("Any", corr.iloc[i, j]))
            if pd.isna(val):
                continue

            if abs(val) >= config.CORRELATION_STRONG_THRESHOLD:
                direction = "positive" if val > 0 else "negative"
                insights.append(
                    Insight(
                        severity="info",
                        category="correlation",
                        title=f"Strong {direction.title()} Correlation",
                        explanation=f"'{valid_cols[i]}' and '{valid_cols[j]}' show strong {direction} "
                        f"correlation (r = {val:.3f}).",
                        metric="Pearson r",
                        metric_value=round(val, 4),
                        suggestion=f"These columns are strongly {direction}ly correlated. "
                        "Consider if one could be derived from the other.",
                    )
                )

    return insights


def _distribution_insights(df: pd.DataFrame, profile: DatasetProfile) -> list[Insight]:
    """Generate distribution insights."""
    insights = []

    for col in profile.columns:
        if col.numeric and col.numeric.skewness is not None and abs(col.numeric.skewness) > 2:
            direction = "right" if col.numeric.skewness > 0 else "left"
            insights.append(
                Insight(
                    severity="info",
                    category="distribution",
                    title=f"Highly Skewed: {col.name}",
                    explanation=f"Column '{col.name}' is highly {direction}-skewed "
                    f"(skewness = {col.numeric.skewness:.2f}). This may affect "
                    f"statistical analyses that assume normality.",
                    metric="Skewness",
                    metric_value=col.numeric.skewness,
                    column=col.name,
                    suggestion="Consider log transformation or other normalization techniques.",
                )
            )

    return insights


def _trend_insights(df: pd.DataFrame) -> list[Insight]:
    """Detect basic trends in time series data.

    This is descriptive trend analysis only, not forecasting.
    """
    insights: list[Insight] = []
    categories = get_column_categories(df)
    datetime_cols = categories["datetime"]
    numeric_cols = categories["numeric"]

    if not datetime_cols or not numeric_cols:
        return insights

    date_col = datetime_cols[0]

    for num_col in numeric_cols[:3]:  # Limit to first 3 numeric columns
        try:
            temp = df[[date_col, num_col]].dropna().sort_values(date_col)
            if len(temp) < config.TREND_MIN_POINTS:
                continue

            # Simple linear regression for trend direction
            x = np.arange(len(temp)).astype(float)
            y = temp[num_col].to_numpy(dtype=float)

            slope, _intercept, r_value, _p_value, _std_err = stats.linregress(x, y)
            r_squared = r_value**2

            # Coefficient of variation for volatility
            cv = np.std(y) / np.mean(y) if np.mean(y) != 0 else 0

            if r_squared < 0.1:
                trend = "no clear trend"
                if abs(cv) > 0.5:
                    trend = "high volatility with no clear trend"
            elif slope > 0:
                trend = "increasing"
            else:
                trend = "decreasing"

            if trend != "no clear trend":
                insights.append(
                    Insight(
                        severity="info",
                        category="trend",
                        title=f"Trend Detected: {num_col}",
                        explanation=f"'{num_col}' shows a {trend} pattern over time "
                        f"(R² = {r_squared:.3f}). "
                        f"Note: This is descriptive trend analysis, not a forecast.",
                        metric="R²",
                        metric_value=round(r_squared, 4),
                        column=num_col,
                    )
                )
        except Exception as e:
            logger.debug(f"Trend analysis failed for {num_col}: {e}")

    return insights


def _constant_column_insights(profile: DatasetProfile) -> list[Insight]:
    """Generate insights for constant columns."""
    insights = []
    for col_name in profile.constant_columns:
        insights.append(
            Insight(
                severity="warning",
                category="quality",
                title=f"Constant Column: {col_name}",
                explanation=f"Column '{col_name}' contains only one unique value and may provide "
                f"little analytical value.",
                metric="Unique Values",
                metric_value=1,
                column=col_name,
                suggestion="Consider removing this column as it provides no variance.",
            )
        )
    return insights


def _cardinality_insights(profile: DatasetProfile) -> list[Insight]:
    """Generate insights for high-cardinality columns."""
    insights = []
    for col_name in profile.high_cardinality_columns:
        col = next((c for c in profile.columns if c.name == col_name), None)
        if col:
            insights.append(
                Insight(
                    severity="info",
                    category="quality",
                    title=f"High Cardinality: {col_name}",
                    explanation=f"Column '{col_name}' contains {col.unique_count:,} unique values "
                    f"and may be unsuitable for categorical visualization or grouping.",
                    metric="Unique Values",
                    metric_value=col.unique_count,
                    column=col_name,
                    suggestion="Consider binning or grouping values for analysis.",
                )
            )
    return insights
