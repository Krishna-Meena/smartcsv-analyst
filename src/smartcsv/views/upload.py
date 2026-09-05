"""Upload page for CSV file ingestion."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import streamlit as st

from smartcsv.config import config
from smartcsv.core.cleaning import AuditTrail
from smartcsv.core.ingestion import (
    IngestionError,
    compute_file_hash,
    ingest_csv,
    ingest_csv_from_url,
)
from smartcsv.utils.logging import get_logger

if TYPE_CHECKING:
    from smartcsv.models.metadata import DatasetMetadata

logger = get_logger(__name__)


def render() -> None:
    """Render the upload page."""
    st.header("Upload Dataset")
    st.markdown("Upload a CSV file to begin analysis. Supports drag-and-drop.")

    # Two tabs: file upload and URL
    tab_file, tab_url, tab_sample = st.tabs(["Upload File", "Load from URL", "Sample Data"])

    with tab_file:
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=["csv", "tsv", "txt"],
            help=f"Maximum file size: {config.MAX_UPLOAD_SIZE_MB} MB",
        )

        if uploaded_file is not None:
            _process_upload(uploaded_file.getvalue(), uploaded_file.name)

    with tab_url:
        url = st.text_input(
            "CSV URL",
            placeholder="https://example.com/data.csv",
            help="Enter a direct link to a CSV file",
        )
        if st.button("Load from URL", disabled=not url):
            with st.spinner("Downloading and processing..."):
                try:
                    df, metadata = ingest_csv_from_url(url)
                    _store_dataset(df, metadata, compute_file_hash(url.encode()))
                    st.success(
                        f"Successfully loaded {metadata.row_count:,} rows and {metadata.column_count} columns."
                    )
                except IngestionError as e:
                    st.error(str(e))
                except Exception as e:
                    logger.error(f"URL load failed: {e}")
                    st.error("An unexpected error occurred while loading from URL.")

    with tab_sample:
        st.markdown("Load the included sample finance dataset for demonstration.")
        if st.button("Load Sample Data"):
            _load_sample_data()

    # Show current dataset info if loaded
    if "df" in st.session_state and st.session_state.df is not None:
        st.divider()
        _display_metadata()


def _process_upload(file_bytes: bytes, filename: str) -> None:
    """Process an uploaded file."""
    # Check if this is the same file (avoid reprocessing)
    file_hash = compute_file_hash(file_bytes)
    if st.session_state.get("file_hash") == file_hash:
        return

    with st.spinner("Processing file..."):
        try:
            df, metadata = ingest_csv(file_bytes, filename)
            _store_dataset(df, metadata, file_hash)
            st.success(
                f"Successfully loaded **{metadata.filename}** — {metadata.row_count:,} rows, {metadata.column_count} columns."
            )
        except IngestionError as e:
            st.error(str(e))
        except Exception as e:
            logger.error(f"Upload processing failed: {e}")
            st.error("An unexpected error occurred while processing the file.")


def _load_sample_data() -> None:
    """Load the sample finance dataset."""
    import os

    sample_path = os.path.join(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        ),
        "sample_data",
        "sample_finance.csv",
    )

    try:
        with open(sample_path, "rb") as f:
            file_bytes = f.read()
        df, metadata = ingest_csv(file_bytes, "sample_finance.csv")
        _store_dataset(df, metadata, compute_file_hash(file_bytes))
        st.success(
            f"Sample data loaded — {metadata.row_count:,} rows, {metadata.column_count} columns."
        )
    except FileNotFoundError:
        st.error("Sample data file not found. Please ensure sample_data/sample_finance.csv exists.")
    except IngestionError as e:
        st.error(str(e))
    except Exception as e:
        logger.error(f"Sample data load failed: {e}")
        st.error("Failed to load sample data.")


def _store_dataset(df: pd.DataFrame, metadata: DatasetMetadata, file_hash: str) -> None:
    """Store dataset in session state."""
    st.session_state.df = df
    st.session_state.original_df = df.copy()
    st.session_state.metadata = metadata
    st.session_state.file_hash = file_hash
    st.session_state.audit_trail = AuditTrail()
    # Clear cached profile when new data is loaded
    st.session_state.pop("profile", None)
    st.session_state.pop("insights", None)


def _display_metadata() -> None:
    """Display dataset metadata."""
    meta = st.session_state.metadata

    st.subheader("Dataset Information")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows", f"{meta.row_count:,}")
    col2.metric("Columns", str(meta.column_count))
    col3.metric("File Size", meta.file_size_display)
    col4.metric("Memory", meta.memory_usage_display)

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Encoding", meta.encoding)
    col6.metric("Delimiter", repr(meta.delimiter))
    col7.metric("Missing Values", f"{meta.missing_value_count:,}")
    col8.metric("Duplicate Rows", f"{meta.duplicate_row_count:,}")

    # Data types
    with st.expander("Column Types", expanded=False):
        type_data = [
            {"Column": name, "Type": dtype} for name, dtype in meta.detected_dtypes.items()
        ]
        st.dataframe(pd.DataFrame(type_data), use_container_width=True, hide_index=True)

    # Preview
    with st.expander("Data Preview", expanded=True):
        st.dataframe(st.session_state.df.head(20), use_container_width=True, hide_index=True)
