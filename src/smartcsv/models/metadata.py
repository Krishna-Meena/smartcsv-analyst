"""Data models for dataset metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ColumnMetadata:
    """Metadata for a single column."""

    name: str
    dtype: str
    non_null_count: int
    missing_count: int
    missing_percentage: float
    unique_count: int
    cardinality: float  # unique_count / non_null_count
    sample_values: list[Any] = field(default_factory=list)


@dataclass
class DatasetMetadata:
    """Metadata for an entire dataset."""

    filename: str
    file_size_bytes: int
    row_count: int
    column_count: int
    encoding: str
    delimiter: str
    memory_usage_bytes: int
    detected_dtypes: dict[str, str] = field(default_factory=dict)
    missing_value_count: int = 0
    duplicate_row_count: int = 0
    columns: list[ColumnMetadata] = field(default_factory=list)
    upload_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def file_size_display(self) -> str:
        """Human-readable file size."""
        size = float(self.file_size_bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def memory_usage_display(self) -> str:
        """Human-readable memory usage."""
        size = float(self.memory_usage_bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
