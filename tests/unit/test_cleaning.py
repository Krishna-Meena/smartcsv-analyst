"""Tests for data cleaning module."""

import pandas as pd
import pytest

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


class TestFillMissingNumeric:
    def test_fill_mean(self, sample_df_with_missing: pd.DataFrame) -> None:
        result, count = fill_missing_numeric(sample_df_with_missing, "value", "mean")
        assert count > 0
        assert result["value"].isna().sum() == 0

    def test_fill_median(self, sample_df_with_missing: pd.DataFrame) -> None:
        result, count = fill_missing_numeric(sample_df_with_missing, "value", "median")
        assert count > 0
        assert result["value"].isna().sum() == 0

    def test_fill_zero(self, sample_df_with_missing: pd.DataFrame) -> None:
        result, count = fill_missing_numeric(sample_df_with_missing, "value", "zero")
        assert count > 0
        assert result["value"].isna().sum() == 0

    def test_invalid_method(self, sample_df_with_missing: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="Invalid fill method"):
            fill_missing_numeric(sample_df_with_missing, "value", "invalid")

    def test_non_numeric_column(self, sample_df: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="not numeric"):
            fill_missing_numeric(sample_df, "category", "mean")

    def test_nonexistent_column(self, sample_df: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="not found"):
            fill_missing_numeric(sample_df, "nonexistent", "mean")

    def test_no_missing_values(self, sample_df: pd.DataFrame) -> None:
        _result, count = fill_missing_numeric(sample_df, "value", "mean")
        assert count == 0

    def test_does_not_modify_original(self, sample_df_with_missing: pd.DataFrame) -> None:
        original_missing = sample_df_with_missing["value"].isna().sum()
        fill_missing_numeric(sample_df_with_missing, "value", "mean")
        assert sample_df_with_missing["value"].isna().sum() == original_missing


class TestFillMissingCategorical:
    def test_fill_mode(self, sample_df_with_missing: pd.DataFrame) -> None:
        result, count = fill_missing_categorical(sample_df_with_missing, "category", "mode")
        assert count > 0
        assert result["category"].isna().sum() == 0

    def test_fill_custom(self, sample_df_with_missing: pd.DataFrame) -> None:
        result, count = fill_missing_categorical(
            sample_df_with_missing, "category", "custom", "Unknown"
        )
        assert count > 0
        assert "Unknown" in result["category"].values

    def test_custom_without_value(self, sample_df_with_missing: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="Custom value must be provided"):
            fill_missing_categorical(sample_df_with_missing, "category", "custom")

    def test_invalid_method(self, sample_df_with_missing: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="Invalid fill method"):
            fill_missing_categorical(sample_df_with_missing, "category", "invalid")


class TestDropMissing:
    def test_drop_all_missing(self, sample_df_with_missing: pd.DataFrame) -> None:
        result, count = drop_missing_rows(sample_df_with_missing)
        assert count > 0
        assert result.isna().sum().sum() == 0

    def test_drop_specific_columns(self, sample_df_with_missing: pd.DataFrame) -> None:
        result, count = drop_missing_rows(sample_df_with_missing, columns=["value"])
        assert count > 0
        assert result["value"].isna().sum() == 0

    def test_drop_columns_by_threshold(self, sample_df_with_missing: pd.DataFrame) -> None:
        _result, dropped = drop_columns_by_missing(sample_df_with_missing, threshold=10)
        assert isinstance(dropped, list)


class TestRemoveDuplicates:
    def test_remove_duplicates(self, sample_df_with_duplicates: pd.DataFrame) -> None:
        result, count = remove_duplicates(sample_df_with_duplicates)
        assert count > 0
        assert len(result) < len(sample_df_with_duplicates)

    def test_no_duplicates(self, sample_df: pd.DataFrame) -> None:
        result, count = remove_duplicates(sample_df)
        assert count == 0
        assert len(result) == len(sample_df)


class TestConvertColumnType:
    def test_to_numeric(self) -> None:
        df = pd.DataFrame({"x": ["1", "2", "3", "4", "5"]})
        result, count = convert_column_type(df, "x", "numeric")
        assert pd.api.types.is_numeric_dtype(result["x"])
        assert count == 5

    def test_to_string(self, sample_df: pd.DataFrame) -> None:
        _result, count = convert_column_type(sample_df, "value", "string")
        assert count > 0

    def test_to_datetime(self) -> None:
        df = pd.DataFrame({"d": ["2023-01-01", "2023-02-01", "2023-03-01"]})
        result, _count = convert_column_type(df, "d", "datetime")
        assert pd.api.types.is_datetime64_any_dtype(result["d"])

    def test_to_categorical(self, sample_df: pd.DataFrame) -> None:
        result, _count = convert_column_type(sample_df, "category", "categorical")
        assert result["category"].dtype.name == "category"

    def test_invalid_numeric_conversion(self) -> None:
        df = pd.DataFrame({"x": ["hello", "world", "foo", "bar"]})
        with pytest.raises(ValueError, match="Unable to convert"):
            convert_column_type(df, "x", "numeric")

    def test_invalid_type(self, sample_df: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="Unsupported target type"):
            convert_column_type(sample_df, "value", "boolean")

    def test_nonexistent_column(self, sample_df: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="not found"):
            convert_column_type(sample_df, "nonexistent", "numeric")


class TestFilterDataframe:
    def test_equals(self, sample_df: pd.DataFrame) -> None:
        result, removed = filter_dataframe(sample_df, "category", "equals", "A")
        assert all(result["category"] == "A")
        assert removed > 0

    def test_not_equals(self, sample_df: pd.DataFrame) -> None:
        result, _removed = filter_dataframe(sample_df, "category", "not_equals", "A")
        assert all(result["category"] != "A")

    def test_greater_than(self, sample_df: pd.DataFrame) -> None:
        result, _removed = filter_dataframe(sample_df, "value", "greater_than", 100)
        assert all(result["value"] > 100)

    def test_less_than(self, sample_df: pd.DataFrame) -> None:
        result, _removed = filter_dataframe(sample_df, "value", "less_than", 100)
        assert all(result["value"] < 100)

    def test_between(self, sample_df: pd.DataFrame) -> None:
        result, _removed = filter_dataframe(sample_df, "value", "between", 80, 120)
        assert all((result["value"] >= 80) & (result["value"] <= 120))

    def test_contains(self, sample_df: pd.DataFrame) -> None:
        result, _removed = filter_dataframe(sample_df, "name", "contains", "Item_1")
        assert len(result) > 0

    def test_is_null(self, sample_df_with_missing: pd.DataFrame) -> None:
        result, _removed = filter_dataframe(sample_df_with_missing, "value", "is_null", None)
        assert all(result["value"].isna())

    def test_not_null(self, sample_df_with_missing: pd.DataFrame) -> None:
        result, _removed = filter_dataframe(sample_df_with_missing, "value", "not_null", None)
        assert all(result["value"].notna())

    def test_invalid_operation(self, sample_df: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="Unsupported filter"):
            filter_dataframe(sample_df, "value", "invalid_op", 100)

    def test_nonexistent_column(self, sample_df: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="not found"):
            filter_dataframe(sample_df, "nonexistent", "equals", "x")


class TestDerivedColumn:
    def test_simple_expression(self, sample_df: pd.DataFrame) -> None:
        result, _desc = create_derived_column(sample_df, "total", "value + quantity")
        assert "total" in result.columns

    def test_multiplication(self, sample_df: pd.DataFrame) -> None:
        result, _desc = create_derived_column(sample_df, "revenue", "quantity * price")
        assert "revenue" in result.columns
        assert len(result) == len(sample_df)

    def test_empty_name(self, sample_df: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="empty"):
            create_derived_column(sample_df, "", "value + 1")

    def test_empty_expression(self, sample_df: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="empty"):
            create_derived_column(sample_df, "new_col", "")

    def test_import_blocked(self, sample_df: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="restricted"):
            create_derived_column(sample_df, "hack", "import os")

    def test_eval_blocked(self, sample_df: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="restricted"):
            create_derived_column(sample_df, "hack", 'eval("1+1")')

    def test_exec_blocked(self, sample_df: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="restricted"):
            create_derived_column(sample_df, "hack", 'exec("x=1")')

    def test_os_blocked(self, sample_df: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="restricted"):
            create_derived_column(sample_df, "hack", 'os.system("whoami")')

    def test_subprocess_blocked(self, sample_df: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="restricted"):
            create_derived_column(sample_df, "hack", 'subprocess.call("ls")')

    def test_dunder_blocked(self, sample_df: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="restricted"):
            create_derived_column(sample_df, "hack", '__import__("os")')

    def test_does_not_modify_original(self, sample_df: pd.DataFrame) -> None:
        original_cols = list(sample_df.columns)
        create_derived_column(sample_df, "new_col", "value * 2")
        assert list(sample_df.columns) == original_cols


class TestAuditTrail:
    def test_add_entry(self) -> None:
        trail = AuditTrail()
        entry = AuditEntry(action="test", column="col", method="method", rows_affected=5)
        trail.add(entry)
        assert len(trail.entries) == 1

    def test_to_list(self) -> None:
        trail = AuditTrail()
        trail.add(AuditEntry(action="test1", rows_affected=1))
        trail.add(AuditEntry(action="test2", rows_affected=2))
        result = trail.to_list()
        assert len(result) == 2
        assert result[0]["action"] == "test1"

    def test_clear(self) -> None:
        trail = AuditTrail()
        trail.add(AuditEntry(action="test", rows_affected=0))
        trail.clear()
        assert len(trail.entries) == 0

    def test_entries_are_copies(self) -> None:
        trail = AuditTrail()
        trail.add(AuditEntry(action="test", rows_affected=0))
        entries = trail.entries
        entries.clear()
        assert len(trail.entries) == 1
