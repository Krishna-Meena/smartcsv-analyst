"""Data models for chart configuration."""

from __future__ import annotations

from dataclasses import dataclass

CHART_TYPES = [
    "histogram",
    "box_plot",
    "bar_chart",
    "scatter",
    "line",
    "grouped_bar",
    "scatter_color",
    "scatter_size",
    "faceted_scatter",
    "correlation_heatmap",
    "box_plot_grouped",
]


@dataclass
class ChartConfig:
    """Configuration for a chart."""

    chart_type: str
    x_column: str | None = None
    y_column: str | None = None
    color_column: str | None = None
    size_column: str | None = None
    facet_column: str | None = None
    title: str = ""
    aggregation: str | None = None  # 'mean', 'sum', 'count', 'median'
    sort_by: str | None = None
    nbins: int | None = None

    def validate(self) -> list[str]:
        """Validate chart configuration. Returns list of errors."""
        errors = []
        if self.chart_type not in CHART_TYPES:
            errors.append(f"Unsupported chart type: {self.chart_type}")
        if self.chart_type in (
            "scatter",
            "line",
            "scatter_color",
            "scatter_size",
            "faceted_scatter",
        ) and (not self.x_column or not self.y_column):
            errors.append(f"{self.chart_type} requires both x and y columns")
        if self.chart_type in ("histogram", "box_plot", "bar_chart") and not self.x_column:
            errors.append(f"{self.chart_type} requires an x column")
        if self.chart_type == "scatter_color" and not self.color_column:
            errors.append("scatter_color requires a color column")
        if self.chart_type == "scatter_size" and not self.size_column:
            errors.append("scatter_size requires a size column")
        return errors
