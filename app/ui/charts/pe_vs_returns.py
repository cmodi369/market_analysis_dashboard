"""PE vs Forward Returns scatter chart."""

import pandas as pd
from bokeh.models import ColumnDataSource, HoverTool, Span
from bokeh.plotting import figure

from app.config import COLORS


def create_pe_vs_returns_chart(
    returns_df: pd.DataFrame,
    signal_type: str = "PE Ratio",
) -> figure:
    """Scatter chart: PE/PB at entry (X) vs forward annualized CAGR (Y)."""
    x_col = "PB at Entry" if signal_type == "PB Ratio" else "PE at Entry"
    x_label = "PB at Entry" if signal_type == "PB Ratio" else "PE at Entry"

    p = figure(
        title=f"{x_label} vs Forward Returns",
        x_axis_label=x_label, y_axis_label="Annualized CAGR (%)",
        height=480, sizing_mode="stretch_width",
        tools="pan,wheel_zoom,box_zoom,reset,save",
        toolbar_location="above",
    )

    # Style axes
    p.title.text_font_size = "14px"
    p.outline_line_color = None

    if returns_df.empty:
        return p

    df = returns_df.copy()
    df["color"] = df["CAGR (%)"].apply(
        lambda x: COLORS["success"] if x > 0 else COLORS["danger"]
    )
    source = ColumnDataSource(df)

    # Zero line
    p.add_layout(Span(
        location=0, dimension="width",
        line_color=COLORS["tick"], line_dash="dashed", line_width=1,
    ))

    # Scatter
    p.scatter(
        x_col, "CAGR (%)", source=source,
        size=7, color="color", alpha=0.7, line_color=None,
    )

    # Hover
    p.add_tools(HoverTool(tooltips=[
        ("Entry Date", "@{Entry Date}{%F}"),
        (x_label, f"@{{{x_col}}}{{0.0}}"),
        ("CAGR", "@{CAGR (%)}{0.0}%"),
    ], formatters={"@{Entry Date}": "datetime"}))

    return p
