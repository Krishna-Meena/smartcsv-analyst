"""Data visualization page."""

from __future__ import annotations

import streamlit as st

from smartcsv.core.visualization import (
    create_chart,
    export_chart_html,
    export_chart_png,
    recommend_charts,
)
from smartcsv.models.chart_config import CHART_TYPES, ChartConfig
from smartcsv.utils.logging import get_logger

logger = get_logger(__name__)


def render() -> None:
    """Render the visualization page."""
    if "df" not in st.session_state or st.session_state.df is None:
        st.warning("No dataset loaded. Please upload a CSV file first.")
        return

    st.header("Data Visualization")

    df = st.session_state.df

    if len(df) > 50000:
        st.warning(
            "Performance Warning: The dataset is large. Visualizations may be slow or unresponsive. Consider sampling the data."
        )

    st.subheader("Recommended Charts")
    recs = recommend_charts(df)
    if recs:
        cols = st.columns(len(recs[:3]))
        for idx, rec in enumerate(recs[:3]):
            if cols[idx].button(
                f"{rec.chart_type.title()} for {rec.x_column} & {rec.y_column}", key=f"rec_{idx}"
            ):
                st.session_state.selected_chart_type = rec.chart_type
                st.session_state.selected_x = rec.x_column
                st.session_state.selected_y = rec.y_column
    else:
        st.write("No specific recommendations based on column types.")

    st.divider()

    st.sidebar.header("Chart Configuration")

    chart_types = CHART_TYPES
    chart_type_index = (
        chart_types.index(st.session_state.get("selected_chart_type", "scatter"))
        if st.session_state.get("selected_chart_type", "scatter") in chart_types
        else 0
    )
    chart_type = st.sidebar.selectbox("Chart Type", chart_types, index=chart_type_index)

    x_col_index = (
        df.columns.tolist().index(st.session_state.get("selected_x", df.columns[0]))
        if st.session_state.get("selected_x") in df.columns
        else 0
    )
    x_col = st.sidebar.selectbox("X Axis", df.columns.tolist(), index=x_col_index)

    y_col = None
    if chart_type in ["scatter", "line", "bar_chart", "box_plot"]:
        y_col_index = (
            df.columns.tolist().index(st.session_state.get("selected_y", df.columns[0]))
            if st.session_state.get("selected_y") in df.columns
            else 0
        )
        y_col = st.sidebar.selectbox("Y Axis", df.columns.tolist(), index=y_col_index)

    color_col = st.sidebar.selectbox("Color by (optional)", ["None", *df.columns.tolist()])
    color_val = color_col if color_col != "None" else None

    title = st.sidebar.text_input(
        "Chart Title", f"{chart_type.title()} of {x_col}" + (f" vs {y_col}" if y_col else "")
    )

    fig = None
    try:
        config_kwargs = {
            "chart_type": chart_type,
            "x_column": x_col,
            "y_column": y_col,
            "color_column": color_val,
            "title": title,
        }

        if chart_type == "histogram":
            bins = st.sidebar.slider("Number of bins", 5, 100, 30)
            config_kwargs["nbins"] = bins

        config = ChartConfig(**config_kwargs)

        if st.button("Generate Chart"):
            fig = create_chart(df, config)
            if fig is None:
                st.error("Could not generate chart.")
                return

            st.plotly_chart(fig, use_container_width=True)

            # Export buttons
            col1, col2 = st.columns(2)
            html_bytes = export_chart_html(fig).encode("utf-8")
            col1.download_button(
                "Export as HTML", data=html_bytes, file_name="chart.html", mime="text/html"
            )

            try:
                png_bytes = export_chart_png(fig)
                if png_bytes:
                    col2.download_button(
                        "Export as PNG", data=png_bytes, file_name="chart.png", mime="image/png"
                    )
            except Exception:
                col2.info("PNG export requires `kaleido` package.")

    except Exception as e:
        st.error(f"Error generating chart: {e}")
