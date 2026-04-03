"""PE Timeline chart with dual axes and green entry zones."""

import pandas as pd
from bokeh.models import (
    BoxAnnotation, ColumnDataSource, HoverTool, Label,
    LinearAxis, NumeralTickFormatter, Range1d, Span,
)
from bokeh.plotting import figure

from app.config import COLORS


def _find_contiguous_periods(dates, mask):
    """Find start/end dates of contiguous True periods in a boolean mask."""
    periods = []
    in_period = False
    start = None
    for i, (date, val) in enumerate(zip(dates, mask)):
        if val and not in_period:
            start = date
            in_period = True
        elif not val and in_period:
            periods.append((start, dates[i - 1]))
            in_period = False
    if in_period:
        periods.append((start, dates[-1]))
    return periods


def create_pe_timeline_chart(
    df: pd.DataFrame,
    threshold: float = 20,
    signal_type: str = "PE Ratio",
) -> figure:
    """
    Dual-axis chart: Nifty Close (left) + PE/PB Ratio (right)
    with green-shaded entry zones where valuation < threshold.
    """
    val_col = "PB" if signal_type == "PB Ratio" else "PE"
    val_label = "PB Ratio" if signal_type == "PB Ratio" else "PE Ratio"

    source = ColumnDataSource(
        data={"date": df["Date"], "close": df["Close"], "val": df[val_col]}
    )

    p = figure(
        x_axis_type="datetime", height=480,
        sizing_mode="stretch_width",
        tools="pan,wheel_zoom,box_zoom,reset,save",
        toolbar_location="above",
    )

    # --- Styling ---
    p.yaxis.axis_label = "Nifty Close"
    p.yaxis.formatter = NumeralTickFormatter(format="0,0")


    # --- Secondary Y axis for PE/PB ---
    pe_min = max(float(df[val_col].min()) - 2, 0)
    pe_max = float(df[val_col].max()) + 2
    p.extra_y_ranges = {"val_range": Range1d(start=pe_min, end=pe_max)}
    pe_axis = LinearAxis(
        y_range_name="val_range", axis_label=val_label,
    )
    p.add_layout(pe_axis, "right")

    # --- Green zones where valuation < threshold ---
    below_mask = (df[val_col] < threshold).values
    dates = df["Date"].values
    for start, end in _find_contiguous_periods(dates, below_mask):
        p.add_layout(BoxAnnotation(
            left=pd.Timestamp(start), right=pd.Timestamp(end),
            fill_alpha=0.12, fill_color=COLORS["green_zone"], line_color=None,
        ))

    # --- Threshold dashed line ---
    p.add_layout(Span(
        location=threshold, dimension="width",
        line_color=COLORS["danger"], line_dash="dashed",
        line_width=1, line_alpha=0.5, y_range_name="val_range",
    ))

    # --- Price line ---
    p.line("date", "close", source=source, color=COLORS["price_line"],
           line_width=1.5, alpha=0.9, legend_label="Nifty Close")

    # --- PE/PB line ---
    p.line("date", "val", source=source, color=COLORS["pe_line"],
           line_width=1.5, alpha=0.8, y_range_name="val_range",
           legend_label=val_label)

    # --- Legend ---
    p.legend.location = "top_left"
    p.legend.click_policy = "hide"

    # --- Hover ---
    p.add_tools(HoverTool(
        tooltips=[("Date", "@date{%F}"), ("Nifty Close", "@close{0,0.00}"),
                  (val_label, "@val{0.0}")],
        formatters={"@date": "datetime"}, mode="vline",
    ))

    # --- Subtitle ---
    p.add_layout(Label(
        x=10, y=10, x_units="screen", y_units="screen",
        text=f"Green zones = {val_label} below {threshold:.0f} (entry opportunities)",
        text_font_size="11px",
    ))

    return p
