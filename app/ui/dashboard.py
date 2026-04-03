"""Main dashboard layout with reactive callbacks."""

import panel as pn

from app.config import COLORS, HOLDING_PERIODS
from app.data.price_fetcher import load_market_data
from app.metrics.calculator import (
    calculate_forward_returns, compute_metrics, get_entry_signals, get_pe_buckets,
)
from app.ui.controls import (
    create_holding_period_select, create_pe_threshold_slider, create_signal_type_toggle,
)
from app.ui.metric_cards import create_metrics_row
from app.ui.charts.pe_timeline import create_pe_timeline_chart
from app.ui.charts.pe_vs_returns import create_pe_vs_returns_chart
from app.ui.charts.pe_buckets import create_pe_buckets_chart
from app.ui.charts.entry_events import create_entry_events_table


# ---------------------------------------------------------------------------
# Global data load (cached)
# ---------------------------------------------------------------------------
_DATA = None


def _get_data():
    global _DATA
    if _DATA is None:
        _DATA = load_market_data()
    return _DATA


# ---------------------------------------------------------------------------
# Reactive computation functions
# ---------------------------------------------------------------------------

def _compute_all(signal_type, holding_period_label, threshold):
    """Run the full analysis pipeline and return all outputs."""
    df = _get_data()
    holding_years = HOLDING_PERIODS[holding_period_label]

    # Determine PB threshold from PE threshold with rough scaling
    pb_threshold = round(threshold * 3.5 / 20, 1)

    signals = get_entry_signals(df, signal_type, threshold, pb_threshold)
    returns_df = calculate_forward_returns(df, signals["Date"], holding_years)
    metrics = compute_metrics(returns_df)
    buckets = get_pe_buckets(returns_df, signal_type)

    current_pe = float(df["PE"].iloc[-1])
    current_pb = float(df["PB"].iloc[-1])
    nifty_level = float(df["Close"].iloc[-1])

    return {
        "df": df, "signals": signals, "returns_df": returns_df,
        "metrics": metrics, "buckets": buckets,
        "current_pe": current_pe, "current_pb": current_pb,
        "nifty_level": nifty_level,
        "signal_type": signal_type, "holding_period": holding_period_label,
        "threshold": threshold,
    }


def _build_metrics_row(result):
    return create_metrics_row(
        current_pe=result["current_pe"],
        nifty_level=result["nifty_level"],
        current_pb=result["current_pb"],
        entry_signals=result["metrics"]["entry_signals"],
        threshold=result["threshold"],
        signal_type=result["signal_type"],
        median_return=result["metrics"]["median_return"],
        holding_period=result["holding_period"],
        win_rate=result["metrics"]["win_rate"],
    )


def _build_tabs(result):
    timeline = create_pe_timeline_chart(
        result["df"], result["threshold"], result["signal_type"],
    )
    scatter = create_pe_vs_returns_chart(result["returns_df"], result["signal_type"])
    buckets = create_pe_buckets_chart(result["buckets"], result["signal_type"])
    events = create_entry_events_table(result["returns_df"])

    tabs = pn.Tabs(
        ("PE Timeline", pn.pane.Bokeh(timeline, sizing_mode="stretch_width")),
        ("PE vs Returns", pn.pane.Bokeh(scatter, sizing_mode="stretch_width")),
        ("PE Buckets", pn.pane.Bokeh(buckets, sizing_mode="stretch_width")),
        ("Entry Events", events),
        sizing_mode="stretch_width",
        tabs_location="above",
        dynamic=True,
    )
    return pn.Card(
        tabs,
        sizing_mode="stretch_width",
        hide_header=True,
        margin=(10, 0),
        styles={"box-shadow": "none", "border": f"1px solid {COLORS['border']}"}
    )


# ---------------------------------------------------------------------------
# Dashboard builder
# ---------------------------------------------------------------------------


def create_dashboard():
    """Build and return the full Panel dashboard application."""
    pn.extension("tabulator", sizing_mode="stretch_width")

    # --- Widgets ---
    signal_toggle = create_signal_type_toggle()
    holding_col = create_holding_period_select()
    threshold_col = create_pe_threshold_slider()

    # Extract widgets from columns for reactive watching
    holding_select = holding_col[0]
    threshold_slider = threshold_col[1]

    # --- Reactive containers ---
    metrics_area = pn.Column(sizing_mode="stretch_width")
    charts_area = pn.Column(sizing_mode="stretch_width")

    def _update(event=None):
        result = _compute_all(
            signal_toggle.value, holding_select.value, threshold_slider.value,
        )
        metrics_area.clear()
        metrics_area.append(_build_metrics_row(result))

        charts_area.clear()
        charts_area.append(_build_tabs(result))

    # Wire up callbacks
    signal_toggle.param.watch(_update, "value")
    holding_select.param.watch(_update, "value")
    threshold_slider.param.watch(_update, "value")

    # Initial render
    _update()

    # --- Data range header info ---
    df = _get_data()
    start_date = df["Date"].iloc[0].strftime("%b %Y")
    end_date = df["Date"].iloc[-1].strftime("%b %Y")

    header_html = pn.pane.HTML(f"""
    <div style="display:flex; align-items:center; gap:20px;
         color: var(--panel-on-surface-color, {COLORS['text_secondary']}); font-size:13px;">
        <div style="display:flex; align-items:center; gap:6px;">
            <span style="font-size:16px;">📊</span>
            <span>Data: {start_date} – {end_date}</span>
        </div>
    </div>
    """, sizing_mode="stretch_width", align="end")

    # --- Controls bar ---
    controls_bar = pn.Row(
        pn.Column(pn.pane.HTML("<b style='font-size:12px; color:#94a3b8;'>Signal Type</b>"),
                  signal_toggle, width=280),
        pn.Column(pn.pane.HTML("<b style='font-size:12px; color:#94a3b8;'>Holding Period</b>"),
                  holding_col, width=180),
        threshold_col,
        pn.layout.HSpacer(),
        header_html,
        sizing_mode="stretch_width",
    )
    controls_card = pn.Card(
        controls_bar,
        hide_header=True,
        sizing_mode="stretch_width",
        collapsible=False,
        margin=(10, 0),
        styles={"box-shadow": "none", "border": f"1px solid {COLORS['border']}"}
    )

    # --- Main content ---
    main_content = pn.Column(
        controls_card,
        pn.layout.Divider(margin=(0, 0, 0, 0)),
        metrics_area,
        charts_area,
        sizing_mode="stretch_width",
    )

    # --- Template ---
    template = pn.template.FastListTemplate(
        title="Market Analysis Dashboard",
        header_background="#0a1128",
        main=[main_content],
        theme_toggle=True,
        theme="default",
        accent_base_color=COLORS["primary"],
        main_layout=None,
        meta_description="Real-time Nifty 50 PE/PB analysis dashboard with entry signals",
    )

    return template
