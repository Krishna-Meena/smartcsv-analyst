"""Shared test fixtures."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """A basic sample DataFrame with mixed types."""
    np.random.seed(42)
    n = 100
    return pd.DataFrame(
        {
            "id": range(1, n + 1),
            "name": [f"Item_{i}" for i in range(1, n + 1)],
            "category": np.random.choice(["A", "B", "C", "D"], n),
            "value": np.random.normal(100, 25, n).round(2),
            "quantity": np.random.randint(1, 50, n),
            "price": np.random.uniform(10, 500, n).round(2),
            "date": pd.date_range("2023-01-01", periods=n, freq="D"),
            "region": np.random.choice(["North", "South", "East", "West"], n),
            "discount": np.random.uniform(0, 0.3, n).round(2),
        }
    )


@pytest.fixture
def sample_df_with_missing(sample_df: pd.DataFrame) -> pd.DataFrame:
    """Sample DataFrame with intentional missing values."""
    df = sample_df.copy()
    np.random.seed(42)
    # Add missing values
    mask = np.random.random(len(df)) < 0.1
    df.loc[mask, "value"] = np.nan
    mask2 = np.random.random(len(df)) < 0.15
    df.loc[mask2, "category"] = np.nan
    mask3 = np.random.random(len(df)) < 0.05
    df.loc[mask3, "price"] = np.nan
    return df


@pytest.fixture
def sample_df_with_duplicates(sample_df: pd.DataFrame) -> pd.DataFrame:
    """Sample DataFrame with duplicate rows."""
    duplicates = sample_df.head(5)
    return pd.concat([sample_df, duplicates], ignore_index=True)


@pytest.fixture
def numeric_only_df() -> pd.DataFrame:
    """DataFrame with only numeric columns."""
    np.random.seed(42)
    return pd.DataFrame(
        {
            "a": np.random.normal(0, 1, 50),
            "b": np.random.normal(5, 2, 50),
            "c": np.random.normal(0, 1, 50) * 2 + np.random.normal(5, 2, 50),  # correlated with b
        }
    )


@pytest.fixture
def constant_column_df() -> pd.DataFrame:
    """DataFrame with a constant column."""
    return pd.DataFrame(
        {
            "varying": [1, 2, 3, 4, 5],
            "constant": [42, 42, 42, 42, 42],
            "category": ["A", "A", "B", "B", "C"],
        }
    )


@pytest.fixture
def valid_csv_bytes() -> bytes:
    """Valid CSV file as bytes."""
    content = "id,name,value\n1,Alice,100\n2,Bob,200\n3,Charlie,300\n"
    return content.encode("utf-8")


@pytest.fixture
def csv_with_bom() -> bytes:
    """CSV file with UTF-8 BOM."""
    content = "id,name,value\n1,Alice,100\n2,Bob,200\n"
    return b"\xef\xbb\xbf" + content.encode("utf-8")


@pytest.fixture
def empty_csv_bytes() -> bytes:
    """Empty CSV file."""
    return b""


@pytest.fixture
def malformed_csv_bytes() -> bytes:
    """Malformed CSV with inconsistent columns."""
    return b"a,b,c\n1,2\n3,4,5,6\n7,8,9\n"


@pytest.fixture
def semicolon_csv_bytes() -> bytes:
    """CSV with semicolon delimiter."""
    return b"id;name;value\n1;Alice;100\n2;Bob;200\n3;Charlie;300\n"


@pytest.fixture
def tab_csv_bytes() -> bytes:
    """CSV with tab delimiter."""
    return b"id\tname\tvalue\n1\tAlice\t100\n2\tBob\t200\n"


@pytest.fixture
def single_column_csv() -> bytes:
    """Single column CSV."""
    return b"values\n1\n2\n3\n4\n5\n"


@pytest.fixture
def duplicate_column_csv() -> bytes:
    """CSV with duplicate column names."""
    return b"name,name,value\nAlice,Smith,100\nBob,Jones,200\n"


@pytest.fixture
def datetime_df() -> pd.DataFrame:
    """DataFrame with datetime column."""
    dates = pd.date_range("2023-01-01", periods=30, freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "sales": np.random.normal(1000, 200, 30).round(2),
            "increasing": np.arange(30) * 10 + np.random.normal(0, 5, 30),
        }
    )


@pytest.fixture
def high_cardinality_df() -> pd.DataFrame:
    """DataFrame with high cardinality categorical."""
    n = 200
    return pd.DataFrame(
        {
            "id": range(n),
            "unique_col": [f"val_{i}" for i in range(n)],
            "normal_cat": np.random.choice(["X", "Y", "Z"], n),
        }
    )


@pytest.fixture
def outlier_df() -> pd.DataFrame:
    """DataFrame with outliers."""
    np.random.seed(42)
    values = np.random.normal(100, 10, 100)
    # Add outliers
    values[0] = 500
    values[1] = -200
    values[2] = 1000
    return pd.DataFrame({"value": values, "category": np.random.choice(["A", "B"], 100)})
