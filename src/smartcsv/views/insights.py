"""Data insights page."""

from __future__ import annotations

import streamlit as st

from smartcsv.core.insights import generate_insights
from smartcsv.core.profiling import profile_dataset
from smartcsv.utils.logging import get_logger

logger = get_logger(__name__)


def render() -> None:
    """Render the insights page."""
    if "df" not in st.session_state or st.session_state.df is None:
        st.warning("No dataset loaded. Please upload a CSV file first.")
        return

    st.header("Automated Insights")

    df = st.session_state.df
    profile = st.session_state.get("profile")

    if "insights" not in st.session_state:
        with st.spinner("Generating insights..."):
            if profile is None:
                profile = profile_dataset(df)
                st.session_state.profile = profile
            insights = generate_insights(df, profile)
            st.session_state.insights = insights
    else:
        insights = st.session_state.insights

    if not insights:
        st.info("No significant insights discovered.")
        return

    # Categories filter
    categories = list(set([i.category for i in insights]))
    selected_categories = st.multiselect("Filter by Category", categories, default=categories)

    filtered_insights = [i for i in insights if i.category in selected_categories]

    st.subheader("Key Findings")
    for insight in filtered_insights:
        if insight.severity == "critical":
            st.error(f"🚨 **{insight.title}**: {insight.explanation} (Metric: {insight.metric})")
        elif insight.severity == "warning":
            st.warning(f"⚠️ **{insight.title}**: {insight.explanation} (Metric: {insight.metric})")
        else:
            st.info(f"💡 **{insight.title}**: {insight.explanation} (Metric: {insight.metric})")

        if insight.suggestion:
            st.markdown(f"**Suggestion:** {insight.suggestion}")

    st.divider()
    # Export insights
    insights_text = "\n".join(
        [f"[{i.severity.upper()}] {i.title}: {i.explanation}" for i in insights]
    )
    st.download_button(
        "Export Insights Summary",
        data=insights_text.encode("utf-8"),
        file_name="insights_summary.txt",
        mime="text/plain",
    )
