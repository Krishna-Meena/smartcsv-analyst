"""Helper utilities for SmartCSV Analyst."""

import hashlib

import numpy as np
import pandas as pd


def format_number(n: int | float) -> str:
    """Format a number with commas."""
    if isinstance(n, float):
        return f"{n:,.2f}"
    return f"{n:,}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a float ratio (0-1) as a percentage string."""
    return f"{value * 100:.{decimals}f}%"


def format_bytes(size_bytes: int) -> str:
    """Format bytes into a human-readable string."""
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def truncate_string(s: str, max_len: int = 50) -> str:
    """Truncate a string if it exceeds max_len."""
    if not isinstance(s, str):
        s = str(s)
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """Divide two numbers safely, returning default if division by zero."""
    try:
        if b == 0:
            return default
        return float(a) / float(b)
    except (ZeroDivisionError, TypeError, ValueError):
        return default


def get_column_categories(df: pd.DataFrame) -> dict[str, list[str]]:
    """Group column names by their general data type category."""
    categories: dict[str, list[str]] = {
        "numeric": [],
        "categorical": [],
        "datetime": [],
        "other": [],
    }

    for col in df.columns:
        dtype = df[col].dtype
        if pd.api.types.is_numeric_dtype(dtype):
            categories["numeric"].append(col)
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            categories["datetime"].append(col)
        elif (
            pd.api.types.is_object_dtype(dtype)
            or isinstance(dtype, pd.CategoricalDtype)
            or pd.api.types.is_string_dtype(dtype)
        ):
            categories["categorical"].append(col)
        else:
            categories["other"].append(col)

    return categories


def hash_dataframe(df: pd.DataFrame) -> str:
    """Create a hash of a DataFrame for caching purposes."""
    hasher = hashlib.md5()
    hasher.update(str(df.shape).encode())
    hasher.update(str(list(df.columns)).encode())
    if not df.empty:
        sample = pd.concat([df.head(5), df.tail(5)])
        hasher.update(np.array(pd.util.hash_pandas_object(sample, index=True)).tobytes())
    return hasher.hexdigest()
