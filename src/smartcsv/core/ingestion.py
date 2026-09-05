"""CSV ingestion and parsing module."""

from __future__ import annotations

import csv
import hashlib
import io

import pandas as pd
from charset_normalizer import from_bytes

from smartcsv.models.metadata import ColumnMetadata, DatasetMetadata
from smartcsv.utils.logging import get_logger
from smartcsv.utils.validation import sanitize_filename, validate_file_size

# We assume there is a config module, providing a fallback config if not present
try:
    from smartcsv.config import config
except ImportError:

    class DummyConfig:
        MAX_UPLOAD_SIZE_MB = 200

    config = DummyConfig()  # type: ignore

logger = get_logger(__name__)


class IngestionError(Exception):
    """Raised when CSV ingestion fails."""

    pass


def detect_encoding(raw_bytes: bytes) -> str:
    """Detect file encoding using charset-normalizer."""
    # Handle BOM
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if raw_bytes.startswith(b"\xff\xfe"):
        return "utf-16-le"
    if raw_bytes.startswith(b"\xfe\xff"):
        return "utf-16-be"

    result = from_bytes(raw_bytes)
    best = result.best()
    if best is None:
        raise IngestionError(
            "Unable to determine the file encoding. Please ensure the file is a valid text file."
        )
    encoding = best.encoding
    logger.info(f"Detected encoding: {encoding}")
    return encoding


def detect_delimiter(text: str) -> str:
    """Detect CSV delimiter using csv.Sniffer."""
    try:
        sample = text[:8192]
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|:")
        delimiter = dialect.delimiter
        logger.info(f"Detected delimiter: {delimiter!r}")
        return delimiter
    except csv.Error:
        logger.warning("Could not detect delimiter, defaulting to comma")
        return ","


def handle_duplicate_columns(columns: list[str]) -> list[str]:
    """Rename duplicate column names by appending suffixes."""
    seen: dict[str, int] = {}
    result: list[str] = []
    for col in columns:
        if col in seen:
            seen[col] += 1
            result.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            result.append(col)
    return result


def ingest_csv(file_bytes: bytes, filename: str) -> tuple[pd.DataFrame, DatasetMetadata]:
    """Ingest a CSV file from raw bytes.

    Args:
        file_bytes: Raw bytes of the CSV file.
        filename: Original filename.

    Returns:
        Tuple of (DataFrame, DatasetMetadata).

    Raises:
        IngestionError: If the file cannot be parsed.
    """
    safe_name = sanitize_filename(filename)
    file_size = len(file_bytes)

    # Validate file size
    is_valid, msg = validate_file_size(file_size, config.MAX_UPLOAD_SIZE_MB)
    if not is_valid:
        raise IngestionError(msg)

    # Check empty file
    if file_size == 0:
        raise IngestionError("The uploaded file is empty. Please upload a CSV file with data.")

    # Detect encoding
    try:
        encoding = detect_encoding(file_bytes)
    except IngestionError:
        raise
    except Exception as e:
        logger.error(f"Encoding detection failed: {e}")
        raise IngestionError("Unable to determine the file encoding.") from e

    # Decode bytes
    try:
        text = file_bytes.decode(encoding)
    except (UnicodeDecodeError, LookupError) as e:
        logger.error(f"Decoding failed with {encoding}: {e}")
        # Try fallback encodings
        for fallback in ["utf-8", "latin-1", "cp1252"]:
            try:
                text = file_bytes.decode(fallback)
                encoding = fallback
                break
            except (UnicodeDecodeError, LookupError):
                continue
        else:
            raise IngestionError(
                "Unable to decode the file. Please check the file encoding."
            ) from e

    # Strip BOM if present
    text = text.lstrip("\ufeff")

    # Check if file has content
    stripped = text.strip()
    if not stripped:
        raise IngestionError("The file appears to be empty after decoding.")

    # Detect delimiter
    delimiter = detect_delimiter(text)

    # Parse CSV
    try:
        df = pd.read_csv(
            io.StringIO(text),
            delimiter=delimiter,
            on_bad_lines="warn",
            engine="python",
            dtype_backend="numpy_nullable",
        )
    except pd.errors.EmptyDataError:
        raise IngestionError(
            "The file contains no parseable data. Please check the file format."
        ) from None
    except pd.errors.ParserError as e:
        logger.error(f"CSV parsing failed: {e}")
        raise IngestionError(
            "Couldn't parse this CSV. Please check the delimiter, quoting, and file format."
        ) from e
    except Exception as e:
        logger.error(f"Unexpected parsing error: {e}")
        raise IngestionError(
            "An unexpected error occurred while parsing the file. Please ensure it is a valid CSV."
        ) from e

    # Handle empty DataFrame
    if df.empty and df.columns.empty:
        raise IngestionError("The file contains no data columns.")

    if len(df) == 0:
        raise IngestionError("The file contains headers but no data rows.")

    # Handle duplicate columns
    if df.columns.duplicated().any():
        df.columns = pd.Index(handle_duplicate_columns(list(df.columns.astype(str))))
        logger.info("Renamed duplicate columns")

    # Ensure column names are strings
    df.columns = pd.Index([str(c) for c in df.columns])

    # Try to infer better dtypes
    df = _optimize_dtypes(df)

    # Build metadata
    metadata = _build_metadata(df, safe_name, file_size, encoding, delimiter)

    logger.info(
        f"Successfully ingested {safe_name}: {metadata.row_count} rows, {metadata.column_count} columns"
    )
    return df, metadata


def ingest_csv_from_url(url: str) -> tuple[pd.DataFrame, DatasetMetadata]:
    """Ingest a CSV file from a URL.

    Args:
        url: HTTP(S) URL pointing to a CSV file.

    Returns:
        Tuple of (DataFrame, DatasetMetadata).

    Raises:
        IngestionError: If the URL is invalid or file cannot be downloaded/parsed.
    """
    import urllib.error
    import urllib.request

    from smartcsv.utils.validation import validate_url

    is_valid, msg = validate_url(url)
    if not is_valid:
        raise IngestionError(msg)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SmartCSV-Analyst/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status != 200:
                raise IngestionError(f"Failed to download file: HTTP {response.status}")

            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > config.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                raise IngestionError(
                    f"File exceeds maximum size of {config.MAX_UPLOAD_SIZE_MB} MB."
                )

            file_bytes = response.read()
    except urllib.error.URLError as e:
        logger.error(f"URL fetch failed: {e}")
        raise IngestionError(f"Could not download from URL: {e.reason}") from e
    except urllib.error.HTTPError as e:
        raise IngestionError(f"HTTP error {e.code}: {e.reason}") from e
    except Exception as e:
        if isinstance(e, IngestionError):
            raise
        logger.error(f"URL fetch error: {e}")
        raise IngestionError("Failed to download the CSV file from the provided URL.") from e

    # Extract filename from URL
    from urllib.parse import urlparse

    parsed = urlparse(url)
    filename = parsed.path.split("/")[-1] or "downloaded.csv"

    return ingest_csv(file_bytes, filename)


def _optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Attempt to infer better dtypes for columns."""
    for col in df.columns:
        # Try numeric conversion
        if df[col].dtype == object:
            try:
                converted = pd.to_numeric(df[col], errors="coerce")
                # Only convert if most values are numeric (>80%)
                if converted.notna().sum() > 0.8 * df[col].notna().sum():
                    df[col] = converted
                    continue
            except (ValueError, TypeError):
                pass

            # Try datetime conversion
            try:
                converted = pd.to_datetime(df[col], errors="coerce", format="mixed")
                if converted.notna().sum() > 0.8 * df[col].notna().sum():
                    df[col] = converted
                    continue
            except (ValueError, TypeError):
                pass
    return df


def _build_metadata(
    df: pd.DataFrame,
    filename: str,
    file_size: int,
    encoding: str,
    delimiter: str,
) -> DatasetMetadata:
    """Build DatasetMetadata from a parsed DataFrame."""
    columns = []
    for col in df.columns:
        non_null = int(df[col].notna().sum())
        missing = int(df[col].isna().sum())
        total = len(df)
        unique = int(df[col].nunique())

        columns.append(
            ColumnMetadata(
                name=str(col),
                dtype=str(df[col].dtype),
                non_null_count=non_null,
                missing_count=missing,
                missing_percentage=round(missing / total * 100, 2) if total > 0 else 0.0,
                unique_count=unique,
                cardinality=round(unique / non_null, 4) if non_null > 0 else 0.0,
                sample_values=df[col].dropna().head(5).tolist(),
            )
        )

    return DatasetMetadata(
        filename=filename,
        file_size_bytes=file_size,
        row_count=len(df),
        column_count=len(df.columns),
        encoding=encoding,
        delimiter=delimiter,
        memory_usage_bytes=int(df.memory_usage(deep=True).sum()),
        detected_dtypes={str(col): str(df[col].dtype) for col in df.columns},
        missing_value_count=int(df.isna().sum().sum()),
        duplicate_row_count=int(df.duplicated().sum()),
        columns=columns,
    )


def compute_file_hash(file_bytes: bytes) -> str:
    """Compute SHA-256 hash of file content for caching."""
    return hashlib.sha256(file_bytes).hexdigest()
