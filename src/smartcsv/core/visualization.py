"""Visualization engine using Plotly."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from smartcsv.config import config
from smartcsv.models.chart_config import ChartConfig
from smartcsv.utils.helpers import get_column_categories
from smartcsv.utils.logging import get_logger

if TYPE_CHECKING:
    import pandas as pd

logger = get_logger(__name__)

DEFAULT_TEMPLATE = "plotly_white"


def should_sample(df: pd.DataFrame, chart_type: str) -> bool:
    """Determine if the dataset should be sampled for visualization."""
    if chart_type in ("scatter", "scatter_color", "scatter_size", "faceted_scatter", "line"):
        return len(df) > config.MAX_SCATTER_POINTS
    return len(df) > config.LARGE_DATASET_THRESHOLD


def sample_for_viz(df: pd.DataFrame, max_points: int | None = None) -> tuple[pd.DataFrame, bool]:
    """Sample a DataFrame for visualization if needed.

    Returns:
        Tuple of (sampled DataFrame, whether sampling was applied).
    """
    threshold = max_points or config.SAMPLE_SIZE_FOR_VIZ
    if len(df) <= threshold:
        return df, False
    return df.sample(n=threshold, random_state=42), True


def create_chart(df: pd.DataFrame, chart_config: ChartConfig) -> go.Figure | None:
    """Create a Plotly chart based on configuration.

    Args:
        df: Source DataFrame.
        chart_config: Chart configuration.

    Returns:
        Plotly Figure or None if chart cannot be created.
    """
    errors = chart_config.validate()
    if errors:
        logger.warning(f"Chart validation errors: {errors}")
        return None

    # Sample if needed
    plot_df, was_sampled = (
        sample_for_viz(df) if should_sample(df, chart_config.chart_type) else (df, False)
    )

    title = chart_config.title
    if was_sampled:
        title = f"{title} (sampled: {len(plot_df):,} of {len(df):,} rows)"

    try:
        fig = _build_chart(plot_df, chart_config, title)
        if fig:
            fig.update_layout(
                template=DEFAULT_TEMPLATE,
                font=dict(family="Inter, sans-serif"),
                margin=dict(l=60, r=40, t=60, b=60),
                colorway=config.COLORBLIND_PALETTE,
            )
        return fig
    except Exception as e:
        logger.error(f"Chart creation failed: {e}")
        return None


def _build_chart(df: pd.DataFrame, cfg: ChartConfig, title: str) -> go.Figure | None:
    """Build the actual chart figure."""
    chart_builders = {
        "histogram": _build_histogram,
        "box_plot": _build_box_plot,
        "bar_chart": _build_bar_chart,
        "scatter": _build_scatter,
        "line": _build_line,
        "grouped_bar": _build_grouped_bar,
        "scatter_color": _build_scatter_color,
        "scatter_size": _build_scatter_size,
        "faceted_scatter": _build_faceted_scatter,
        "correlation_heatmap": _build_correlation_heatmap,
        "box_plot_grouped": _build_box_plot_grouped,
    }

    builder = chart_builders.get(cfg.chart_type)
    if builder is None:
        logger.error(f"Unknown chart type: {cfg.chart_type}")
        return None

    return builder(df, cfg, title)


def _build_histogram(df: pd.DataFrame, cfg: ChartConfig, title: str) -> go.Figure:
    return px.histogram(
        df,
        x=cfg.x_column,
        nbins=cfg.nbins or 30,
        title=title,
        color=cfg.color_column,
        labels={cfg.x_column: cfg.x_column},
    )


def _build_box_plot(df: pd.DataFrame, cfg: ChartConfig, title: str) -> go.Figure:
    return px.box(df, y=cfg.x_column, title=title)


def _build_bar_chart(df: pd.DataFrame, cfg: ChartConfig, title: str) -> go.Figure:
    if cfg.y_column and cfg.aggregation:
        agg_df = (
            df.groupby(cfg.x_column, observed=True)
            .agg({cfg.y_column: cfg.aggregation})
            .reset_index()
        )
        if cfg.sort_by == "value":
            agg_df = agg_df.sort_values(cfg.y_column, ascending=False)
        return px.bar(agg_df, x=cfg.x_column, y=cfg.y_column, title=title)
    else:
        counts = df[cfg.x_column].value_counts().reset_index()
        counts.columns = [cfg.x_column, "count"]
        if cfg.sort_by == "value":
            counts = counts.sort_values("count", ascending=False)
        return px.bar(counts, x=cfg.x_column, y="count", title=title)


def _build_scatter(df: pd.DataFrame, cfg: ChartConfig, title: str) -> go.Figure:
    return px.scatter(df, x=cfg.x_column, y=cfg.y_column, title=title)


def _build_line(df: pd.DataFrame, cfg: ChartConfig, title: str) -> go.Figure:
    plot_df = df.sort_values(cfg.x_column) if cfg.x_column else df
    return px.line(plot_df, x=cfg.x_column, y=cfg.y_column, title=title)


def _build_grouped_bar(df: pd.DataFrame, cfg: ChartConfig, title: str) -> go.Figure:
    if cfg.aggregation and cfg.y_column:
        agg_df = (
            df.groupby([cfg.x_column, cfg.color_column], observed=True)
            .agg({cfg.y_column: cfg.aggregation})
            .reset_index()
        )
        return px.bar(
            agg_df,
            x=cfg.x_column,
            y=cfg.y_column,
            color=cfg.color_column,
            barmode="group",
            title=title,
        )
    return px.bar(
        df, x=cfg.x_column, y=cfg.y_column, color=cfg.color_column, barmode="group", title=title
    )


def _build_scatter_color(df: pd.DataFrame, cfg: ChartConfig, title: str) -> go.Figure:
    return px.scatter(df, x=cfg.x_column, y=cfg.y_column, color=cfg.color_column, title=title)


def _build_scatter_size(df: pd.DataFrame, cfg: ChartConfig, title: str) -> go.Figure:
    return px.scatter(
        df,
        x=cfg.x_column,
        y=cfg.y_column,
        size=cfg.size_column,
        color=cfg.color_column,
        title=title,
        size_max=20,
    )


def _build_faceted_scatter(df: pd.DataFrame, cfg: ChartConfig, title: str) -> go.Figure:
    return px.scatter(
        df,
        x=cfg.x_column,
        y=cfg.y_column,
        color=cfg.color_column,
        facet_col=cfg.facet_column,
        facet_col_wrap=3,
        title=title,
    )


def _build_correlation_heatmap(df: pd.DataFrame, cfg: ChartConfig, title: str) -> go.Figure:
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) < 2:
        return go.Figure().add_annotation(
            text="Not enough numeric columns for correlation.", showarrow=False
        )

    corr = df[numeric_cols].corr()
    fig = go.Figure(
        data=go.Heatmap(
            z=corr.values,
            x=corr.columns.tolist(),
            y=corr.columns.tolist(),
            colorscale="RdBu_r",
            zmin=-1,
            zmax=1,
            text=corr.round(2).values,
            texttemplate="%{text}",
            textfont={"size": 10},
        )
    )
    fig.update_layout(title=title or "Correlation Heatmap", width=700, height=600)
    return fig


def _build_box_plot_grouped(df: pd.DataFrame, cfg: ChartConfig, title: str) -> go.Figure:
    return px.box(df, x=cfg.color_column, y=cfg.x_column, color=cfg.color_column, title=title)


def recommend_charts(df: pd.DataFrame) -> list[ChartConfig]:
    """Recommend chart types based on dataset column types."""
    categories = get_column_categories(df)
    recommendations = []

    numeric = categories["numeric"]
    categorical = categories["categorical"]
    datetime_cols = categories["datetime"]

    # Univariate numeric
    for col in numeric[:3]:
        recommendations.append(
            ChartConfig(chart_type="histogram", x_column=col, title=f"Distribution of {col}")
        )
        recommendations.append(
            ChartConfig(chart_type="box_plot", x_column=col, title=f"Box Plot of {col}")
        )

    # Univariate categorical
    for col in categorical[:3]:
        if df[col].nunique() <= 20:
            recommendations.append(
                ChartConfig(chart_type="bar_chart", x_column=col, title=f"Frequency of {col}")
            )

    # Bivariate
    if len(numeric) >= 2:
        recommendations.append(
            ChartConfig(
                chart_type="scatter",
                x_column=numeric[0],
                y_column=numeric[1],
                title=f"{numeric[0]} vs {numeric[1]}",
            )
        )

    if datetime_cols and numeric:
        recommendations.append(
            ChartConfig(
                chart_type="line",
                x_column=datetime_cols[0],
                y_column=numeric[0],
                title=f"{numeric[0]} over time",
            )
        )

    if numeric and categorical:
        cat_col = next((c for c in categorical if df[c].nunique() <= 10), None)
        if cat_col:
            recommendations.append(
                ChartConfig(
                    chart_type="box_plot_grouped",
                    x_column=numeric[0],
                    color_column=cat_col,
                    title=f"{numeric[0]} by {cat_col}",
                )
            )

    # Correlation heatmap
    if len(numeric) >= 2:
        recommendations.append(
            ChartConfig(
                chart_type="correlation_heatmap", x_column=numeric[0], title="Correlation Heatmap"
            )
        )

    return recommendations


def export_chart_html(fig: go.Figure) -> str:
    """Export a chart to HTML string."""
    from typing import cast

    return cast("str", fig.to_html(include_plotlyjs="cdn", full_html=True))


def export_chart_png(fig: go.Figure) -> bytes | None:
    """Export a chart to PNG bytes using Kaleido.

    Returns None if export fails.
    """
    try:
        from typing import cast

        return cast("bytes", fig.to_image(format="png", width=1200, height=800, scale=2))
    except Exception as e:
        logger.error(f"PNG export failed: {e}")
        return None
