"""Dashboard control widgets."""

import panel as pn

from app.config import DEFAULT_HOLDING_PERIOD, DEFAULT_PE_THRESHOLD, DEFAULT_SIGNAL_TYPE, HOLDING_PERIODS


def create_signal_type_toggle() -> pn.widgets.RadioButtonGroup:
    """Create signal type selector with custom segmented styling."""
    return pn.widgets.RadioButtonGroup(
        name="Signal Type",
        options=["PE Ratio", "PB Ratio", "PE + PB"],
        value=DEFAULT_SIGNAL_TYPE,
        stylesheets=["""
            .bk-btn.bk-active {
                font-weight: bold !important;
            }
        """]
    )


def create_holding_period_select() -> pn.Column:
    """Create styled holding period dropdown with subtitle."""
    select = pn.widgets.Select(
        name="",
        options=list(HOLDING_PERIODS.keys()),
        value="3 Years",
        width=150,
        stylesheets=["""
            .bk-input {
                border: 1px solid #86868b !important;
                border-radius: 6px !important;
            }
        """]
    )
    subtitle = pn.pane.HTML(
        "<div style='font-size:11px; color:#94a3b8; margin-top:-4px;'>Forward CAGR horizon</div>",
        width=150
    )
    return pn.Column(select, subtitle)


def create_pe_threshold_slider() -> pn.Column:
    """Create PE threshold slider with descriptive subtitle."""
    slider = pn.widgets.IntSlider(
        name="",
        start=10,
        end=35,
        step=1,
        value=DEFAULT_PE_THRESHOLD,
        bar_color="#86868b", # Matched to neutral secondary
        width=280,
    )

    # Reactive slider label (value-aware) with stylesheet
    threshold_label = pn.pane.HTML(
        pn.bind(lambda v: f"PE Threshold: {v}", slider),
        stylesheets=["""
            :host {
                font-size: 12px;
                color: #94a3b8;
                font-weight: bold;
                margin-bottom: 2px;
            }
        """]
    )
    subtitle = pn.pane.HTML(
        "<div style='font-size:11px; color:#94a3b8; margin-top:-4px;'>Invest when Nifty PE drops below this level</div>",
        width=280
    )
    return pn.Column(threshold_label, slider, subtitle, width=280)
