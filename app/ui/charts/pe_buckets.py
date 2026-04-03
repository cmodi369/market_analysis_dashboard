"""PE Buckets bar chart showing median returns by valuation range."""

import pandas as pd
from bokeh.models import ColumnDataSource, HoverTool, LabelSet
from bokeh.plotting import figure
from bokeh.transform import factor_cmap

from app.config import COLORS


def create_pe_buckets_chart(
    bucket_df: pd.DataFrame,
    signal_type: str = "PE Ratio",
) -> figure:
    """Bar chart: median CAGR grouped by PE/PB buckets (bins of 2)."""
    label = "PB" if signal_type == "PB Ratio" else "PE"

    p = figure(
        title=f"Median CAGR by {label} Bucket",
        x_axis_label=f"{label} Range at Entry",
        y_axis_label="Median Annualized CAGR (%)",
        height=480, sizing_mode="stretch_width",
        x_range=list(bucket_df["Bucket"].astype(str)),
        tools="save",
        toolbar_location="above",
    )

    # Style
    p.title.text_font_size = "14px"
    p.xgrid.grid_line_color = None
    p.outline_line_color = None
    p.xaxis.major_label_orientation = 0.6


    if bucket_df.empty:
        return p

    df = bucket_df.copy()
    df["Bucket"] = df["Bucket"].astype(str)
    df["color"] = df["Median CAGR (%)"].apply(
        lambda x: COLORS["success"] if x > 0 else COLORS["danger"]
    )
    source = ColumnDataSource(df)

    p.vbar(
        x="Bucket", top="Median CAGR (%)", source=source,
        width=0.7, color="color", alpha=0.85,
        line_color=None,
    )

    # Value labels on top of bars
    labels = LabelSet(
        x="Bucket", y="Median CAGR (%)", text="Median CAGR (%)",
        source=source, text_font_size="10px",
        text_align="center", y_offset=5,
    )
    p.add_layout(labels)

    # Hover
    p.add_tools(HoverTool(tooltips=[
        (f"{label} Bucket", "@Bucket"),
        ("Median CAGR", "@{Median CAGR (%)}{0.0}%"),
        ("Signals", "@Count"),
    ]))

    return p
