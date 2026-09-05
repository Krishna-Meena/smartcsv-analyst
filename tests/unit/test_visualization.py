"""Tests for visualization module."""

import pandas as pd
import plotly.graph_objects as go

from smartcsv.core.visualization import (
    create_chart,
    export_chart_html,
    recommend_charts,
    sample_for_viz,
    should_sample,
)
from smartcsv.models.chart_config import ChartConfig


class TestCreateChart:
    def test_histogram(self, sample_df: pd.DataFrame) -> None:
        cfg = ChartConfig(chart_type="histogram", x_column="value", title="Test")
        fig = create_chart(sample_df, cfg)
        assert fig is not None
        assert isinstance(fig, go.Figure)

    def test_box_plot(self, sample_df: pd.DataFrame) -> None:
        cfg = ChartConfig(chart_type="box_plot", x_column="value", title="Test")
        fig = create_chart(sample_df, cfg)
        assert fig is not None

    def test_bar_chart(self, sample_df: pd.DataFrame) -> None:
        cfg = ChartConfig(chart_type="bar_chart", x_column="category", title="Test")
        fig = create_chart(sample_df, cfg)
        assert fig is not None

    def test_scatter(self, sample_df: pd.DataFrame) -> None:
        cfg = ChartConfig(chart_type="scatter", x_column="value", y_column="price", title="Test")
        fig = create_chart(sample_df, cfg)
        assert fig is not None

    def test_line(self, sample_df: pd.DataFrame) -> None:
        cfg = ChartConfig(chart_type="line", x_column="date", y_column="value", title="Test")
        fig = create_chart(sample_df, cfg)
        assert fig is not None

    def test_correlation_heatmap(self, sample_df: pd.DataFrame) -> None:
        cfg = ChartConfig(chart_type="correlation_heatmap", x_column="value", title="Test")
        fig = create_chart(sample_df, cfg)
        assert fig is not None

    def test_invalid_chart_type(self, sample_df: pd.DataFrame) -> None:
        cfg = ChartConfig(chart_type="invalid_type", x_column="value")
        fig = create_chart(sample_df, cfg)
        assert fig is None

    def test_missing_required_column(self, sample_df: pd.DataFrame) -> None:
        cfg = ChartConfig(chart_type="scatter", x_column="value")  # missing y
        fig = create_chart(sample_df, cfg)
        assert fig is None

    def test_scatter_color(self, sample_df: pd.DataFrame) -> None:
        cfg = ChartConfig(
            chart_type="scatter_color",
            x_column="value",
            y_column="price",
            color_column="category",
            title="Test",
        )
        fig = create_chart(sample_df, cfg)
        assert fig is not None


class TestSampling:
    def test_small_dataset_no_sample(self, sample_df: pd.DataFrame) -> None:
        assert not should_sample(sample_df, "scatter")

    def test_sample_preserves_size(self) -> None:
        df = pd.DataFrame({"x": range(100)})
        result, sampled = sample_for_viz(df, max_points=50)
        assert len(result) == 50
        assert sampled is True

    def test_small_data_not_sampled(self) -> None:
        df = pd.DataFrame({"x": range(10)})
        result, sampled = sample_for_viz(df, max_points=50)
        assert len(result) == 10
        assert sampled is False


class TestRecommendCharts:
    def test_recommendations(self, sample_df: pd.DataFrame) -> None:
        recs = recommend_charts(sample_df)
        assert len(recs) > 0
        assert all(isinstance(r, ChartConfig) for r in recs)

    def test_numeric_only_recommendations(self, numeric_only_df: pd.DataFrame) -> None:
        recs = recommend_charts(numeric_only_df)
        assert len(recs) > 0


class TestExport:
    def test_export_html(self, sample_df: pd.DataFrame) -> None:
        cfg = ChartConfig(chart_type="histogram", x_column="value", title="Test")
        fig = create_chart(sample_df, cfg)
        assert fig is not None
        html = export_chart_html(fig)
        assert "<html>" in html.lower() or "plotly" in html.lower()
