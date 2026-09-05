"""Validation utilities for SmartCSV Analyst."""

import re
import urllib.parse

import pandas as pd


def validate_file_size(size_bytes: int, max_mb: int = 200) -> tuple[bool, str]:
    """Validate that the file size is within the allowed limit."""
    max_bytes = max_mb * 1024 * 1024
    if size_bytes > max_bytes:
        return False, f"File exceeds maximum size of {max_mb} MB."
    return True, ""


def validate_url(url: str) -> tuple[bool, str]:
    """Validate that a URL is well-formed and uses http/https."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, "URL must use HTTP or HTTPS protocol."
        if not parsed.netloc:
            return False, "URL must contain a valid domain."
        return True, ""
    except Exception:
        return False, "Invalid URL format."


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to remove path separators and invalid characters."""
    # Remove path separators
    filename = filename.replace("/", "_").replace("\\", "_")
    # Remove null bytes
    filename = filename.replace("\0", "")
    # Restrict to safe characters (alphanumeric, dot, underscore, hyphen)
    filename = re.sub(r"[^a-zA-Z0-9.\-_]", "_", filename)
    return filename


def validate_dataframe(df: pd.DataFrame) -> tuple[bool, str]:
    """Validate that a DataFrame is suitable for analysis."""
    if df is None:
        return False, "DataFrame is None."
    if df.empty:
        if len(df.columns) == 0:
            return False, "The dataset has no data and no columns."
        return False, "The dataset contains no data rows."
    return True, ""


def validate_column_name(name: str, df: pd.DataFrame) -> tuple[bool, str]:
    """Validate that a column exists in the DataFrame."""
    if name not in df.columns:
        return False, f"Column '{name}' not found in the dataset."
    return True, ""
