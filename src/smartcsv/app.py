"""SmartCSV Analyst - Interactive CSV Analysis & Data Exploration.

Main application entry point.
"""

from __future__ import annotations

import streamlit as st

from smartcsv.config import config
from smartcsv.utils.logging import get_logger

logger = get_logger(__name__)


def main() -> None:
    """Main application entry point."""
    _configure_page()
    _render_sidebar()
    _render_current_page()


def _configure_page() -> None:
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title=config.APP_NAME,
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS for professional look
    st.markdown(
        """
    <style>
    /* Clean, professional styling */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 16px;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.85rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 600;
        color: #0f172a;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
    }

    /* Headers */
    h1 {
        color: #0f172a;
        font-weight: 700;
    }

    h2, h3 {
        color: #1e293b;
        font-weight: 600;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #334155;
    }

    /* Download buttons */
    .stDownloadButton > button {
        background-color: #2563eb;
        color: white;
        border: none;
        border-radius: 6px;
    }

    .stDownloadButton > button:hover {
        background-color: #1d4ed8;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def _render_sidebar() -> None:
    """Render the navigation sidebar."""
    with st.sidebar:
        st.markdown(f"## 📊 {config.APP_NAME}")
        st.caption(config.APP_TAGLINE)
        st.divider()

        # Navigation
        pages = ["Upload", "Overview", "Clean", "Visualize", "Insights", "Export"]

        # Initialize current page
        if "current_page" not in st.session_state:
            st.session_state.current_page = "Upload"

        # Determine which pages are available
        has_data = "df" in st.session_state and st.session_state.df is not None

        for page in pages:
            disabled = not has_data and page != "Upload"
            if st.button(
                page,
                key=f"nav_{page}",
                use_container_width=True,
                disabled=disabled,
                type="primary" if st.session_state.current_page == page else "secondary",
            ):
                st.session_state.current_page = page
                st.rerun()

        st.divider()

        # Dataset status
        if has_data:
            meta = st.session_state.metadata
            st.markdown("**Current Dataset**")
            st.caption(f"{meta.filename}")
            st.caption(f"{meta.row_count:,} rows x {meta.column_count} cols")
            st.caption(f"Memory: {meta.memory_usage_display}")

            # Audit trail count
            if "audit_trail" in st.session_state:
                trail = st.session_state.audit_trail
                if trail.entries:
                    st.caption(f"Transformations: {len(trail.entries)}")
        else:
            st.info("Upload a CSV file to begin analysis.")

        # Footer
        st.divider()
        st.caption(f"v{config.VERSION}")


def _render_current_page() -> None:
    """Render the currently selected page."""
    page = st.session_state.get("current_page", "Upload")

    try:
        if page == "Upload":
            from smartcsv.views.upload import render

            render()
        elif page == "Overview":
            from smartcsv.views.overview import render

            render()
        elif page == "Clean":
            from smartcsv.views.clean import render

            render()
        elif page == "Visualize":
            from smartcsv.views.visualize import render

            render()
        elif page == "Insights":
            from smartcsv.views.insights import render

            render()
        elif page == "Export":
            from smartcsv.views.export import render

            render()
        else:
            st.error(f"Unknown page: {page}")
    except Exception as e:
        logger.error(f"Page rendering error: {e}", exc_info=True)
        st.error("An error occurred while rendering this page. Please try again.")


if __name__ == "__main__":
    main()
