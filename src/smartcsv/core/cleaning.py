"""Data cleaning and transformation module."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from asteval import Interpreter

from smartcsv.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AuditEntry:
    """Record of a single cleaning/transformation action."""

    action: str
    column: str | None = None
    method: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    rows_affected: int = 0
    details: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AuditTrail:
    """Maintains a log of all cleaning/transformation actions."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def add(self, entry: AuditEntry) -> None:
        self._entries.append(entry)
        logger.info(
            f"Audit: {entry.action} on {entry.column or 'dataset'} - {entry.rows_affected} rows affected"
        )

    @property
    def entries(self) -> list[AuditEntry]:
        return list(self._entries)

    def to_list(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._entries]

    def clear(self) -> None:
        self._entries.clear()


def fill_missing_numeric(df: pd.DataFrame, column: str, method: str) -> tuple[pd.DataFrame, int]:
    """Fill missing values in a numeric column.

    Args:
        df: Input DataFrame.
        column: Column name.
        method: One of 'mean', 'median', 'zero'.

    Returns:
        Tuple of (modified DataFrame, count of filled values).

    Raises:
        ValueError: If method is invalid or column is not numeric.
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in dataset.")

    if not pd.api.types.is_numeric_dtype(df[column]):
        raise ValueError(f"Column '{column}' is not numeric. Cannot use {method} fill.")

    missing_count = int(df[column].isna().sum())
    if missing_count == 0:
        return df, 0

    result = df.copy()
    if method == "mean":
        fill_value = result[column].mean()
    elif method == "median":
        fill_value = result[column].median()
    elif method == "zero":
        fill_value = 0
    else:
        raise ValueError(f"Invalid fill method: '{method}'. Use 'mean', 'median', or 'zero'.")

    result[column] = result[column].fillna(fill_value)
    return result, missing_count


def fill_missing_categorical(
    df: pd.DataFrame, column: str, method: str, custom_value: str | None = None
) -> tuple[pd.DataFrame, int]:
    """Fill missing values in a categorical column.

    Args:
        df: Input DataFrame.
        column: Column name.
        method: One of 'mode', 'custom'.
        custom_value: Value to use when method is 'custom'.

    Returns:
        Tuple of (modified DataFrame, count of filled values).
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in dataset.")

    missing_count = int(df[column].isna().sum())
    if missing_count == 0:
        return df, 0

    result = df.copy()
    if method == "mode":
        mode_val = result[column].mode()
        if len(mode_val) == 0:
            raise ValueError(f"Cannot compute mode for column '{column}' - all values are missing.")
        fill_value = mode_val.iloc[0]
    elif method == "custom":
        if custom_value is None:
            raise ValueError("Custom value must be provided when using 'custom' fill method.")
        fill_value = custom_value
    else:
        raise ValueError(f"Invalid fill method: '{method}'. Use 'mode' or 'custom'.")

    result[column] = result[column].fillna(fill_value)
    return result, missing_count


def drop_missing_rows(
    df: pd.DataFrame, columns: list[str] | None = None
) -> tuple[pd.DataFrame, int]:
    """Drop rows with missing values.

    Args:
        df: Input DataFrame.
        columns: Optional list of columns to check. If None, checks all columns.

    Returns:
        Tuple of (modified DataFrame, count of dropped rows).
    """
    original_len = len(df)
    result = df.dropna(subset=columns) if columns else df.dropna()
    dropped = original_len - len(result)
    return result.reset_index(drop=True), dropped


def drop_columns_by_missing(df: pd.DataFrame, threshold: float) -> tuple[pd.DataFrame, list[str]]:
    """Drop columns where missing percentage exceeds threshold.

    Args:
        df: Input DataFrame.
        threshold: Missing percentage threshold (0-100).

    Returns:
        Tuple of (modified DataFrame, list of dropped column names).
    """
    missing_pct = df.isna().mean() * 100
    cols_to_drop = missing_pct[missing_pct > threshold].index.tolist()
    result = df.drop(columns=cols_to_drop)
    return result, cols_to_drop


def remove_duplicates(
    df: pd.DataFrame, subset: list[str] | None = None, keep: str | bool = "first"
) -> tuple[pd.DataFrame, int]:
    """Remove duplicate rows.

    Returns:
        Tuple of (modified DataFrame, count of removed rows).
    """
    original_len = len(df)
    from typing import cast

    result = df.drop_duplicates(subset=subset, keep=cast("Any", keep)).reset_index(drop=True)
    removed = original_len - len(result)
    return result, removed


def convert_column_type(
    df: pd.DataFrame, column: str, target_type: str
) -> tuple[pd.DataFrame, int]:
    """Safely convert a column to a different type.

    Args:
        df: Input DataFrame.
        column: Column name.
        target_type: One of 'numeric', 'string', 'datetime', 'categorical'.

    Returns:
        Tuple of (modified DataFrame, count of successful conversions).

    Raises:
        ValueError: If conversion fails for too many values.
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in dataset.")

    result = df.copy()
    non_null = result[column].notna().sum()

    if target_type == "numeric":
        converted = pd.to_numeric(result[column], errors="coerce")
        success_count = int(converted.notna().sum())
        if success_count == 0 and non_null > 0:
            raise ValueError(
                f"Unable to convert column '{column}' to numeric. No values could be parsed as numbers."
            )
        if success_count < non_null * 0.5:
            raise ValueError(
                f"Unable to convert column '{column}' to numeric because {non_null - success_count} "
                f"out of {non_null} values could not be parsed."
            )
        result[column] = converted
        return result, success_count

    elif target_type == "string":
        result[column] = result[column].astype(str).replace("nan", pd.NA).replace("None", pd.NA)
        return result, int(non_null)

    elif target_type == "datetime":
        converted = pd.to_datetime(result[column], errors="coerce", format="mixed")
        success_count = int(converted.notna().sum())
        if success_count == 0 and non_null > 0:
            raise ValueError(
                f"Unable to convert column '{column}' to datetime. No values could be parsed as dates."
            )
        if success_count < non_null * 0.5:
            raise ValueError(
                f"Unable to convert column '{column}' to datetime because {non_null - success_count} "
                f"out of {non_null} values could not be parsed."
            )
        result[column] = converted
        return result, success_count

    elif target_type == "categorical":
        result[column] = result[column].astype("category")
        return result, int(non_null)

    else:
        raise ValueError(
            f"Unsupported target type: '{target_type}'. Use 'numeric', 'string', 'datetime', or 'categorical'."
        )


def filter_dataframe(
    df: pd.DataFrame,
    column: str,
    operation: str,
    value: Any,
    value2: Any = None,
) -> tuple[pd.DataFrame, int]:
    """Filter rows based on a condition.

    Args:
        df: Input DataFrame.
        column: Column to filter on.
        operation: One of 'equals', 'not_equals', 'greater_than', 'less_than',
                   'greater_equal', 'less_equal', 'between', 'contains', 'not_contains',
                   'is_null', 'not_null', 'in_list'.
        value: Primary filter value.
        value2: Secondary value for 'between' operation.

    Returns:
        Tuple of (filtered DataFrame, count of removed rows).
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found.")

    original_len = len(df)

    if operation == "equals":
        mask = df[column] == value
    elif operation == "not_equals":
        mask = df[column] != value
    elif operation == "greater_than":
        mask = df[column] > value
    elif operation == "less_than":
        mask = df[column] < value
    elif operation == "greater_equal":
        mask = df[column] >= value
    elif operation == "less_equal":
        mask = df[column] <= value
    elif operation == "between":
        if value2 is None:
            raise ValueError("'between' filter requires both value and value2.")
        mask = df[column].between(value, value2)
    elif operation == "contains":
        mask = df[column].astype(str).str.contains(str(value), case=False, na=False)
    elif operation == "not_contains":
        mask = ~df[column].astype(str).str.contains(str(value), case=False, na=False)
    elif operation == "is_null":
        mask = df[column].isna()
    elif operation == "not_null":
        mask = df[column].notna()
    elif operation == "in_list":
        if isinstance(value, str):
            value = [v.strip() for v in value.split(",")]
        mask = df[column].isin(value)
    else:
        raise ValueError(f"Unsupported filter operation: '{operation}'")

    result = df[mask].reset_index(drop=True)
    removed = original_len - len(result)
    return result, removed


# Safe expression evaluator for derived columns
SAFE_MATH_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "len": len,
    "int": int,
    "float": float,
    "str": str,
}


def create_derived_column(
    df: pd.DataFrame, new_column_name: str, expression: str
) -> tuple[pd.DataFrame, str]:
    """Create a derived column using a safe expression evaluator.

    Uses asteval with restricted namespace. NEVER uses eval() or exec().

    Args:
        df: Input DataFrame.
        new_column_name: Name for the new column.
        expression: Expression using column names as variables.
                    Example: 'revenue - cost' or 'quantity * unit_price'

    Returns:
        Tuple of (modified DataFrame, description of what was created).

    Raises:
        ValueError: If expression is invalid or unsafe.
    """
    if not new_column_name or not new_column_name.strip():
        raise ValueError("Column name cannot be empty.")

    if not expression or not expression.strip():
        raise ValueError("Expression cannot be empty.")

    # Security checks
    dangerous_patterns = [
        "import",
        "__",
        "exec",
        "eval",
        "compile",
        "open",
        "file",
        "os.",
        "sys.",
        "subprocess",
        "pathlib",
        "shutil",
        "glob",
        "socket",
        "http",
        "urllib",
        "requests",
        "pickle",
        "getattr",
        "setattr",
        "delattr",
        "globals",
        "locals",
        "breakpoint",
        "exit",
        "quit",
    ]
    expr_lower = expression.lower()
    for pattern in dangerous_patterns:
        if pattern in expr_lower:
            raise ValueError(
                f"Expression contains restricted operation: '{pattern}'. "
                "Only mathematical operations on columns are allowed."
            )

    # Create a safe interpreter
    aeval = Interpreter()

    # Clear any default symbols that could be dangerous
    # Add only safe math operations
    aeval.symtable.clear()
    for name, func in SAFE_MATH_FUNCTIONS.items():
        aeval.symtable[name] = func

    # Add numpy functions
    aeval.symtable["np"] = np
    aeval.symtable["log"] = np.log
    aeval.symtable["log10"] = np.log10
    aeval.symtable["sqrt"] = np.sqrt
    aeval.symtable["exp"] = np.exp
    aeval.symtable["sin"] = np.sin
    aeval.symtable["cos"] = np.cos
    aeval.symtable["pi"] = np.pi

    # Add column data as variables
    for col in df.columns:
        safe_col_name = col.replace(" ", "_").replace("-", "_")
        aeval.symtable[safe_col_name] = df[col].values

    # Evaluate expression
    try:
        result_values = aeval(expression)
    except Exception as e:
        raise ValueError(f"Could not evaluate expression: {e}") from e

    if aeval.error:
        errors = "; ".join(str(err.get_error()) for err in aeval.error)
        raise ValueError(f"Expression error: {errors}")

    if result_values is None:
        raise ValueError("Expression produced no result.")

    result = df.copy()
    result[new_column_name] = result_values

    return result, f"Created column '{new_column_name}' = {expression}"
