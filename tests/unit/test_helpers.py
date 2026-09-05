"""Tests for helper utilities."""

import pandas as pd

from smartcsv.utils.helpers import (
    format_bytes,
    format_number,
    format_percentage,
    get_column_categories,
    hash_dataframe,
    safe_divide,
    truncate_string,
)
from smartcsv.utils.validation import (
    sanitize_filename,
    validate_dataframe,
    validate_file_size,
    validate_url,
)


class TestFormatNumber:
    def test_basic(self) -> None:
        assert format_number(1234567) == "1,234,567"

    def test_small(self) -> None:
        assert format_number(42) == "42"


class TestFormatPercentage:
    def test_basic(self) -> None:
        assert format_percentage(0.5) == "50.0%"

    def test_precision(self) -> None:
        assert format_percentage(0.12345, 2) == "12.35%"


class TestFormatBytes:
    def test_bytes(self) -> None:
        result = format_bytes(512)
        assert "B" in result

    def test_megabytes(self) -> None:
        result = format_bytes(5 * 1024 * 1024)
        assert "MB" in result


class TestTruncateString:
    def test_short_string(self) -> None:
        assert truncate_string("hello", 50) == "hello"

    def test_long_string(self) -> None:
        result = truncate_string("a" * 100, 10)
        assert len(result) <= 13  # 10 + '...'


class TestSafeDivide:
    def test_normal(self) -> None:
        assert safe_divide(10, 2) == 5.0

    def test_zero_divisor(self) -> None:
        assert safe_divide(10, 0) == 0.0

    def test_custom_default(self) -> None:
        assert safe_divide(10, 0, -1.0) == -1.0


class TestGetColumnCategories:
    def test_mixed_df(self, sample_df: pd.DataFrame) -> None:
        cats = get_column_categories(sample_df)
        assert "numeric" in cats
        assert "categorical" in cats
        assert "datetime" in cats
        assert len(cats["numeric"]) > 0


class TestHashDataframe:
    def test_deterministic(self, sample_df: pd.DataFrame) -> None:
        h1 = hash_dataframe(sample_df)
        h2 = hash_dataframe(sample_df)
        assert h1 == h2

    def test_different_data(self, sample_df: pd.DataFrame) -> None:
        h1 = hash_dataframe(sample_df)
        h2 = hash_dataframe(sample_df.head(5))
        assert h1 != h2


class TestValidation:
    def test_valid_file_size(self) -> None:
        valid, _msg = validate_file_size(1024, 200)
        assert valid

    def test_invalid_file_size(self) -> None:
        valid, _msg = validate_file_size(300 * 1024 * 1024, 200)
        assert not valid

    def test_valid_url(self) -> None:
        valid, _msg = validate_url("https://example.com/data.csv")
        assert valid

    def test_invalid_url_scheme(self) -> None:
        valid, _msg = validate_url("ftp://example.com/data.csv")
        assert not valid

    def test_invalid_url_no_host(self) -> None:
        valid, _msg = validate_url("not-a-url")
        assert not valid

    def test_sanitize_filename(self) -> None:
        result = sanitize_filename("../../../etc/passwd")
        assert "/" not in result
        assert "\\" not in result

    def test_sanitize_null_bytes(self) -> None:
        result = sanitize_filename("file\x00.csv")
        assert "\x00" not in result

    def test_valid_dataframe(self, sample_df: pd.DataFrame) -> None:
        valid, _msg = validate_dataframe(sample_df)
        assert valid

    def test_empty_dataframe(self) -> None:
        valid, _msg = validate_dataframe(pd.DataFrame())
        assert not valid
