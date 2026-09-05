"""Tests for CSV ingestion module."""

import pytest

from smartcsv.core.ingestion import (
    IngestionError,
    compute_file_hash,
    detect_delimiter,
    detect_encoding,
    handle_duplicate_columns,
    ingest_csv,
)


class TestDetectEncoding:
    def test_utf8(self, valid_csv_bytes: bytes) -> None:
        encoding = detect_encoding(valid_csv_bytes)
        assert encoding.lower().replace("-", "") in ("utf8", "ascii", "utf8sig")

    def test_bom(self, csv_with_bom: bytes) -> None:
        encoding = detect_encoding(csv_with_bom)
        assert "utf" in encoding.lower() or "sig" in encoding.lower()

    def test_latin1(self) -> None:
        content = "name,city\nJosé,München\nRené,Zürich\n".encode("latin-1")
        encoding = detect_encoding(content)
        assert encoding is not None


class TestDetectDelimiter:
    def test_comma(self) -> None:
        assert detect_delimiter("a,b,c\n1,2,3\n") == ","

    def test_semicolon(self) -> None:
        assert detect_delimiter("a;b;c\n1;2;3\n") == ";"

    def test_tab(self) -> None:
        assert detect_delimiter("a\tb\tc\n1\t2\t3\n") == "\t"

    def test_fallback_to_comma(self) -> None:
        # Single value per line - sniffer might fail
        result = detect_delimiter("hello\n")
        assert result == ","  # Default fallback


class TestHandleDuplicateColumns:
    def test_no_duplicates(self) -> None:
        assert handle_duplicate_columns(["a", "b", "c"]) == ["a", "b", "c"]

    def test_with_duplicates(self) -> None:
        result = handle_duplicate_columns(["name", "name", "value"])
        assert result == ["name", "name_1", "value"]

    def test_multiple_duplicates(self) -> None:
        result = handle_duplicate_columns(["x", "x", "x"])
        assert result == ["x", "x_1", "x_2"]


class TestIngestCSV:
    def test_valid_csv(self, valid_csv_bytes: bytes) -> None:
        df, metadata = ingest_csv(valid_csv_bytes, "test.csv")
        assert len(df) == 3
        assert len(df.columns) == 3
        assert metadata.row_count == 3
        assert metadata.column_count == 3
        assert metadata.filename == "test.csv"

    def test_csv_with_bom(self, csv_with_bom: bytes) -> None:
        df, _metadata = ingest_csv(csv_with_bom, "bom.csv")
        assert len(df) == 2
        assert "id" in df.columns

    def test_empty_file(self, empty_csv_bytes: bytes) -> None:
        with pytest.raises(IngestionError, match="empty"):
            ingest_csv(empty_csv_bytes, "empty.csv")

    def test_semicolon_delimiter(self, semicolon_csv_bytes: bytes) -> None:
        df, metadata = ingest_csv(semicolon_csv_bytes, "semi.csv")
        assert len(df) == 3
        assert metadata.delimiter == ";"

    def test_tab_delimiter(self, tab_csv_bytes: bytes) -> None:
        df, metadata = ingest_csv(tab_csv_bytes, "tab.csv")
        assert len(df) == 2
        assert metadata.delimiter == "\t"

    def test_single_column(self, single_column_csv: bytes) -> None:
        df, metadata = ingest_csv(single_column_csv, "single.csv")
        assert len(df.columns) == 1
        assert metadata.column_count == 1

    def test_duplicate_columns(self, duplicate_column_csv: bytes) -> None:
        df, _metadata = ingest_csv(duplicate_column_csv, "dup.csv")
        assert len(df.columns) == 3
        # Should have renamed duplicates
        assert len(set(df.columns)) == 3

    def test_metadata_fields(self, valid_csv_bytes: bytes) -> None:
        _df, metadata = ingest_csv(valid_csv_bytes, "test.csv")
        assert metadata.file_size_bytes > 0
        assert metadata.memory_usage_bytes > 0
        assert metadata.encoding is not None
        assert metadata.delimiter is not None
        assert len(metadata.columns) == 3

    def test_headers_only(self) -> None:
        content = b"a,b,c\n"
        with pytest.raises(IngestionError, match="no data rows"):
            ingest_csv(content, "headers_only.csv")

    def test_malformed_csv(self, malformed_csv_bytes: bytes) -> None:
        # Should handle gracefully (warn mode)
        df, _metadata = ingest_csv(malformed_csv_bytes, "bad.csv")
        assert df is not None

    def test_file_size_display(self, valid_csv_bytes: bytes) -> None:
        _, metadata = ingest_csv(valid_csv_bytes, "test.csv")
        display = metadata.file_size_display
        assert any(unit in display for unit in ["B", "KB", "MB"])

    def test_filename_sanitized(self) -> None:
        content = b"a,b\n1,2\n"
        _, metadata = ingest_csv(content, "../../../etc/passwd")
        assert "/" not in metadata.filename
        assert "\\" not in metadata.filename


class TestComputeFileHash:
    def test_deterministic(self) -> None:
        data = b"hello world"
        assert compute_file_hash(data) == compute_file_hash(data)

    def test_different_content(self) -> None:
        assert compute_file_hash(b"abc") != compute_file_hash(b"xyz")
