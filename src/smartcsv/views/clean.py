"""Data cleaning and transformation page."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from smartcsv.core.cleaning import (
    AuditEntry,
    AuditTrail,
    convert_column_type,
    create_derived_column,
    drop_columns_by_missing,
    drop_missing_rows,
    fill_missing_categorical,
    fill_missing_numeric,
    filter_dataframe,
    remove_duplicates,
)
from smartcsv.utils.logging import get_logger

logger = get_logger(__name__)


def render() -> None:
    """Render the data cleaning page."""
    if "df" not in st.session_state or st.session_state.df is None:
        st.warning("No dataset loaded. Please upload a CSV file first.")
        return

    st.header("Data Cleaning & Transformation")

    df = st.session_state.df
    audit_trail = st.session_state.get("audit_trail")
    if audit_trail is None:
        audit_trail = AuditTrail()
        st.session_state.audit_trail = audit_trail

    tab_missing, tab_dupes, tab_type, tab_filter, tab_derived = st.tabs(
        ["Missing Values", "Duplicates", "Type Conversion", "Filter", "Derived Columns"]
    )

    with tab_missing:
        _render_missing_values_tab(df, audit_trail)

    with tab_dupes:
        _render_duplicates_tab(df, audit_trail)

    with tab_type:
        _render_type_conversion_tab(df, audit_trail)

    with tab_filter:
        _render_filter_tab(df, audit_trail)

    with tab_derived:
        _render_derived_columns_tab(df, audit_trail)

    st.divider()
    _render_audit_trail(audit_trail)

    with st.expander("Data Preview (After Cleaning)", expanded=True):
        st.dataframe(st.session_state.df.head(100), use_container_width=True)


def _render_missing_values_tab(df: pd.DataFrame, audit_trail: AuditTrail) -> None:
    st.subheader("Handle Missing Values")

    missing_summary = df.isnull().sum()
    missing_summary = missing_summary[missing_summary > 0]

    if missing_summary.empty:
        st.success("No missing values found in the dataset!")
        return

    st.write("Columns with missing values:")
    st.dataframe(
        pd.DataFrame(
            {
                "Missing Count": missing_summary,
                "Percentage": (missing_summary / len(df) * 100).round(2),
            }
        )
    )

    action = st.radio("Select action:", ["Drop Rows", "Drop Columns", "Fill Values"])

    if action == "Drop Rows":
        cols = st.multiselect(
            "Select columns to check for missing values (leave empty for all):", df.columns.tolist()
        )
        if st.button("Drop Rows"):
            columns_to_check = cols if cols else None
            new_df, count = drop_missing_rows(df, columns_to_check)
            st.session_state.df = new_df
            audit_trail.add(
                AuditEntry(
                    action="Drop Missing Rows",
                    rows_affected=count,
                    details=f"Dropped rows with missing values in {columns_to_check or 'all columns'}",
                )
            )
            _reset_cache()
            st.success(f"Dropped rows with missing values. New shape: {new_df.shape}")

    elif action == "Drop Columns":
        threshold = st.slider(
            "Drop columns with missing percentage >=", min_value=0.0, max_value=100.0, value=50.0
        )
        if st.button("Drop Columns"):
            new_df, removed_cols = drop_columns_by_missing(
                df, threshold / 100.0
            )  # Core function expects ratio (0-1)
            st.session_state.df = new_df
            audit_trail.add(
                AuditEntry(
                    action="Drop Missing Columns",
                    details=f"Dropped columns: {', '.join(removed_cols)} (threshold >= {threshold}%)",
                )
            )
            _reset_cache()
            st.success(
                f"Dropped columns with >= {threshold}% missing values. New shape: {new_df.shape}"
            )

    elif action == "Fill Values":
        col = st.selectbox("Select column:", missing_summary.index.tolist())

        dtype = df[col].dtype
        if pd.api.types.is_numeric_dtype(dtype):
            method = st.selectbox("Fill method:", ["mean", "median", "zero", "custom"])
        else:
            method = st.selectbox("Fill method:", ["mode", "custom"])

        fill_value: Any = None
        if method == "custom":
            fill_value = st.text_input("Enter custom value:")
            if pd.api.types.is_numeric_dtype(dtype) and fill_value:
                try:
                    fill_value = float(fill_value)
                except ValueError:
                    st.error("Custom value must be numeric for this column.")
                    fill_value = None

        if st.button("Fill Values"):
            if method == "custom" and fill_value is None:
                st.error("Please provide a valid custom value.")
            else:
                is_numeric = pd.api.types.is_numeric_dtype(df[col].dtype)
                if is_numeric:
                    new_df, count = fill_missing_numeric(
                        df, col, method
                    )  # numeric doesn't use custom_value
                else:
                    new_df, count = fill_missing_categorical(df, col, method, fill_value)
                st.session_state.df = new_df
                audit_trail.add(
                    AuditEntry(
                        action="Fill Missing",
                        column=col,
                        method=method,
                        rows_affected=count,
                        details=f"Filled using {method}"
                        + (f" ({fill_value})" if method == "custom" else ""),
                    )
                )
                _reset_cache()
                st.success(f"Filled missing values in '{col}' using {method}.")


def _render_duplicates_tab(df: pd.DataFrame, audit_trail: AuditTrail) -> None:
    st.subheader("Handle Duplicates")

    dup_count = df.duplicated().sum()
    st.write(f"Found **{dup_count:,}** duplicate rows.")

    subset = st.multiselect(
        "Consider only specific columns (leave empty for all):", df.columns.tolist()
    )
    keep = st.selectbox("Keep:", ["first", "last", "False (drop all)"])
    keep_val = False if keep == "False (drop all)" else keep

    if st.button("Remove Duplicates", disabled=dup_count == 0 and not subset):
        new_df, count = remove_duplicates(
            df, subset if subset else None, str(keep_val) if keep_val else "first"
        )  # core function takes string keep param
        st.session_state.df = new_df
        audit_trail.add(
            AuditEntry(
                action="Remove Duplicates",
                rows_affected=count,
                details=f"Kept {keep}, subset {subset or 'all'}",
            )
        )
        _reset_cache()
        st.success(f"Removed duplicates. New row count: {len(new_df):,}")


def _render_type_conversion_tab(df: pd.DataFrame, audit_trail: AuditTrail) -> None:
    st.subheader("Convert Data Types")

    col = st.selectbox("Select column:", df.columns.tolist(), key="type_conv_col")
    current_type = str(df[col].dtype)
    st.write(f"Current type: **{current_type}**")

    target_type = st.selectbox(
        "Target type:", ["int64", "float64", "string", "datetime64", "bool", "category"]
    )

    if st.button("Convert Type"):
        try:
            new_df, count = convert_column_type(df, col, target_type)
            st.session_state.df = new_df
            audit_trail.add(
                AuditEntry(
                    action="Convert Type",
                    column=col,
                    method=target_type,
                    rows_affected=count,
                    details=f"Converted {col} to {target_type}",
                )
            )
            _reset_cache()
            st.success(f"Converted '{col}' to {target_type}.")
        except Exception as e:
            st.error(f"Conversion failed: {e}")


def _render_filter_tab(df: pd.DataFrame, audit_trail: AuditTrail) -> None:
    st.subheader("Filter Data")

    col = st.selectbox("Select column to filter by:", df.columns.tolist(), key="filter_col")
    dtype = df[col].dtype

    if pd.api.types.is_numeric_dtype(dtype) or pd.api.types.is_datetime64_any_dtype(dtype):
        op = st.selectbox("Operation:", ["==", "!=", ">", "<", ">=", "<=", "between"])
    else:
        op = st.selectbox("Operation:", ["==", "!=", "contains", "in"])

    value: Any = None
    if op == "between":
        col1, col2 = st.columns(2)
        val1 = col1.text_input("Min value:")
        val2 = col2.text_input("Max value:")
        if val1 and val2:
            if pd.api.types.is_numeric_dtype(dtype):
                try:
                    value = (float(val1), float(val2))
                except ValueError:
                    st.error("Please enter numeric values.")
            else:
                value = (val1, val2)
    elif op == "in":
        val_str = st.text_input("Comma-separated values:")
        if val_str:
            value = [v.strip() for v in val_str.split(",")]
    else:
        val_str = st.text_input("Value:")
        if val_str:
            if pd.api.types.is_numeric_dtype(dtype):
                try:
                    value = float(val_str)
                except ValueError:
                    st.error("Please enter a numeric value.")
            else:
                value = val_str

    if st.button("Apply Filter"):
        if value is None and op not in ["between", "in"]:
            st.error("Please provide a value.")
        elif op == "between" and (not isinstance(value, tuple) or len(value) != 2):
            st.error("Please provide min and max values.")
        elif op == "in" and not isinstance(value, list):
            st.error("Please provide comma-separated values.")
        else:
            try:
                if op == "between":
                    new_df, removed = filter_dataframe(df, col, op, value[0], value[1])
                else:
                    new_df, removed = filter_dataframe(df, col, op, value)
                st.session_state.df = new_df
                audit_trail.add(
                    AuditEntry(
                        action="Filter Data",
                        column=col,
                        method=op,
                        rows_affected=len(removed)
                        if isinstance(removed, pd.DataFrame)
                        else removed,
                        details=f"Filtered {col} {op} {value}",
                    )
                )
                _reset_cache()
                st.success(f"Filter applied. New row count: {len(new_df):,}")
            except Exception as e:
                st.error(f"Filter failed: {e}")


def _render_derived_columns_tab(df: pd.DataFrame, audit_trail: AuditTrail) -> None:
    st.subheader("Create Derived Column")
    st.info(
        "Security Warning: This feature executes pandas eval. Only use with trusted inputs. Do not use restricted operations."
    )

    new_col_name = st.text_input("New column name:")
    expression = st.text_area(
        "Expression (e.g., `A + B` or `Salary * 1.1`):", help="Use column names as variables."
    )

    if st.button("Create Column"):
        if not new_col_name or not expression:
            st.error("Please provide both column name and expression.")
        else:
            try:
                new_df, details = create_derived_column(df, new_col_name, expression)
                st.session_state.df = new_df
                audit_trail.add(
                    AuditEntry(action="Create Derived Column", column=new_col_name, details=details)
                )
                _reset_cache()
                st.success(f"Created derived column '{new_col_name}'.")
            except Exception as e:
                st.error(f"Evaluation failed: {e}")


def _render_audit_trail(audit_trail: AuditTrail) -> None:
    st.subheader("Audit Trail")
    entries = audit_trail.entries
    if not entries:
        st.write("No cleaning operations performed yet.")
        return

    audit_df = pd.DataFrame(
        [
            {
                "Timestamp": e.timestamp,
                "Action": e.action,
                "Column": e.column,
                "Method": e.method,
                "Rows Affected": e.rows_affected,
                "Details": e.details,
            }
            for e in entries
        ]
    )

    st.dataframe(audit_df, use_container_width=True, hide_index=True)


def _reset_cache() -> None:
    """Clear cached derived states after data change."""
    st.session_state.pop("profile", None)
    st.session_state.pop("insights", None)
    st.session_state.pop("_profile_shape", None)
