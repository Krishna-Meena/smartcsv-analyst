"""Data export page."""

from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from smartcsv.utils.logging import get_logger

logger = get_logger(__name__)


def render() -> None:
    """Render the export page."""
    if "df" not in st.session_state or st.session_state.df is None:
        st.warning("No dataset loaded. Please upload a CSV file first.")
        return

    st.header("Export Data & Reports")

    df = st.session_state.df
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    st.subheader("1. Export Cleaned Dataset")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Cleaned CSV",
        data=csv,
        file_name=f"cleaned_dataset_{timestamp}.csv",
        mime="text/csv",
    )

    st.subheader("2. Export Audit Log")
    audit_trail = st.session_state.get("audit_trail")
    if audit_trail:
        history = audit_trail.entries
        audit_data = [
            {
                "timestamp": e.timestamp,
                "action": e.action,
                "column": e.column,
                "method": e.method,
                "rows_affected": e.rows_affected,
                "details": e.details,
            }
            for e in history
        ]
        audit_json = json.dumps(audit_data, indent=2).encode("utf-8")
        st.download_button(
            label="Download Audit Log (JSON)",
            data=audit_json,
            file_name=f"audit_log_{timestamp}.json",
            mime="application/json",
        )
    else:
        st.write("No cleaning operations have been tracked.")

    st.subheader("3. Export Dataset Profile")
    profile = st.session_state.get("profile")
    if profile:
        profile_text = "Dataset Profile\n==============\n"
        profile_text += f"Rows: {profile.row_count}\nColumns: {profile.column_count}\n"
        profile_text += f"Total Missing %: {profile.total_missing_percentage:.2f}%\n"
        profile_text += f"Duplicates: {profile.duplicate_row_count}\n\nColumn Details:\n"
        for col in profile.columns:
            profile_text += (
                f"- {col.name} ({col.category}): Missing {col.missing_percentage:.2f}%\n"
            )

        st.download_button(
            label="Download Profile Report",
            data=profile_text.encode("utf-8"),
            file_name=f"dataset_profile_{timestamp}.txt",
            mime="text/plain",
        )
    else:
        st.write("Dataset profile not generated yet. Visit the Overview page to generate it.")

    st.subheader("4. Export Insights Summary")
    insights = st.session_state.get("insights")
    if insights:
        insights_text = "Automated Insights\n==================\n\n"
        for i in insights:
            insights_text += f"[{i.severity.upper()}] {i.title}: {i.explanation}\n"
            if i.suggestion:
                insights_text += f"  Suggestion: {i.suggestion}\n"
            insights_text += "\n"

        st.download_button(
            label="Download Insights Summary",
            data=insights_text.encode("utf-8"),
            file_name=f"insights_summary_{timestamp}.txt",
            mime="text/plain",
        )
    else:
        st.write("Insights not generated yet. Visit the Insights page to generate them.")
