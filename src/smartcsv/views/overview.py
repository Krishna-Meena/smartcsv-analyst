"""Overview dashboard page."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import plotly.express as px
import streamlit as st

from smartcsv.core.profiling import (
    compute_correlation_matrix,
    get_top_correlations,
    profile_dataset,
)
from smartcsv.utils.logging import get_logger

if TYPE_CHECKING:
    from smartcsv.models.profile import DatasetProfile

logger = get_logger(__name__)


def render() -> None:
    """Render the overview dashboard."""
    if "df" not in st.session_state or st.session_state.df is None:
        st.warning("No dataset loaded. Please upload a CSV file first.")
        return

    st.header("Dataset Overview")

    df = st.session_state.df

    # Compute or retrieve profile
    profile = _get_profile(df)
    st.session_state.profile = profile

    # KPI Cards
    _render_kpis(profile)

    st.divider()

    # Two column layout
    left, right = st.columns([3, 2])

    with left:
        _render_column_details(profile)

    with right:
        _render_quality_summary(profile)
        _render_type_distribution(profile)
        _render_correlation_preview(df)


def _get_profile(df: pd.DataFrame) -> DatasetProfile:
    """Get or compute dataset profile."""
    # Only recompute if df has changed
    current_shape = (len(df), len(df.columns))
    cached_shape = st.session_state.get("_profile_shape")

    if "profile" in st.session_state and cached_shape == current_shape:
        from typing import cast

        return cast("DatasetProfile", st.session_state.profile)

    with st.spinner("Profiling dataset..."):
        profile = profile_dataset(df)
        st.session_state._profile_shape = current_shape
    return profile


def _render_kpis(profile: DatasetProfile) -> None:
    """Render KPI metric cards."""
    cols = st.columns(6)
    cols[0].metric("Rows", f"{profile.row_count:,}")
    cols[1].metric("Columns", str(profile.column_count))
    cols[2].metric("Missing", f"{profile.total_missing_percentage:.1f}%")
    cols[3].metric("Duplicates", f"{profile.duplicate_row_count:,}")
    cols[4].metric("Numeric", str(profile.numeric_column_count))
    cols[5].metric("Categorical", str(profile.categorical_column_count))


def _render_column_details(profile: DatasetProfile) -> None:
    """Render detailed column profiles."""
    st.subheader("Column Details")

    for col in profile.columns:
        with st.expander(f"{col.name} ({col.category}, {col.dtype})", expanded=False):
            c1, c2, c3 = st.columns(3)
            c1.metric("Non-null", f"{col.non_null_count:,}")
            c2.metric("Missing", f"{col.missing_count:,} ({col.missing_percentage:.1f}%)")
            c3.metric("Unique", f"{col.unique_count:,}")

            if col.numeric:
                n = col.numeric
                st.markdown("**Numeric Statistics**")
                stats_df = pd.DataFrame(
                    {
                        "Statistic": [
                            "Mean",
                            "Median",
                            "Std Dev",
                            "Min",
                            "Max",
                            "Q1",
                            "Q3",
                            "IQR",
                            "Outliers",
                        ],
                        "Value": [
                            f"{n.mean:,.4f}",
                            f"{n.median:,.4f}",
                            f"{n.std:,.4f}",
                            f"{n.min_val:,.4f}",
                            f"{n.max_val:,.4f}",
                            f"{n.q1:,.4f}",
                            f"{n.q3:,.4f}",
                            f"{n.iqr:,.4f}",
                            f"{n.outlier_count:,}",
                        ],
                    }
                )
                st.dataframe(stats_df, use_container_width=True, hide_index=True)

                # Mini histogram
                if col.name in st.session_state.df.columns:
                    series = st.session_state.df[col.name].dropna()
                    if len(series) > 0:
                        fig = px.histogram(series, nbins=30, title=f"Distribution of {col.name}")
                        fig.update_layout(
                            height=250, margin=dict(l=20, r=20, t=40, b=20), showlegend=False
                        )
                        st.plotly_chart(fig, use_container_width=True)

            if col.categorical:
                c = col.categorical
                st.markdown(
                    f"**Most frequent:** {c.most_frequent} ({c.most_frequent_count:,}, {c.most_frequent_percentage:.1f}%)"
                )
                if c.top_values:
                    top_df = pd.DataFrame(c.top_values, columns=["Value", "Count"])
                    fig = px.bar(
                        top_df.head(10), x="Value", y="Count", title=f"Top Values: {col.name}"
                    )
                    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig, use_container_width=True)

            if col.datetime:
                d = col.datetime
                st.markdown(
                    f"**Date Range:** {d.min_date} to {d.max_date} ({d.date_range_days} days)"
                )
                if d.most_common_day:
                    st.markdown(f"**Most common day:** {d.most_common_day}")


def _render_quality_summary(profile: DatasetProfile) -> None:
    """Render data quality summary."""
    st.subheader("Data Quality")

    # Quality score (simple heuristic)
    issues = []
    if profile.total_missing_percentage > 5:
        issues.append("High missing values")
    if profile.duplicate_row_percentage > 1:
        issues.append("Duplicate rows")
    if profile.constant_columns:
        issues.append(f"{len(profile.constant_columns)} constant column(s)")
    if profile.high_cardinality_columns:
        issues.append(f"{len(profile.high_cardinality_columns)} high-cardinality column(s)")

    if not issues:
        st.success("No major data quality issues detected.")
    else:
        for issue in issues:
            st.warning(issue)

    # Missing values per column
    missing_cols = [c for c in profile.columns if c.missing_count > 0]
    if missing_cols:
        missing_df = pd.DataFrame(
            [
                {
                    "Column": c.name,
                    "Missing": c.missing_count,
                    "Missing %": f"{c.missing_percentage:.1f}%",
                }
                for c in missing_cols
            ]
        )
        st.dataframe(missing_df, use_container_width=True, hide_index=True)


def _render_type_distribution(profile: DatasetProfile) -> None:
    """Render column type distribution."""
    st.subheader("Column Types")
    type_data = pd.DataFrame(
        {
            "Type": ["Numeric", "Categorical", "Datetime", "Other"],
            "Count": [
                profile.numeric_column_count,
                profile.categorical_column_count,
                profile.datetime_column_count,
                profile.other_column_count,
            ],
        }
    )
    type_data = type_data[type_data["Count"] > 0]
    fig = px.pie(type_data, values="Count", names="Type", hole=0.4)
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)


def _render_correlation_preview(df: pd.DataFrame) -> None:
    """Render a correlation preview."""
    corr_matrix = compute_correlation_matrix(df)
    if corr_matrix is not None:
        st.subheader("Top Correlations")
        top = get_top_correlations(corr_matrix, n=5)
        if top:
            corr_df = pd.DataFrame(top, columns=["Column A", "Column B", "Correlation"])
            st.dataframe(corr_df, use_container_width=True, hide_index=True)
