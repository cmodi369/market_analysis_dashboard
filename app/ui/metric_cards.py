"""Metric card components for the dashboard sidebar."""

import panel as pn

from app.config import COLORS

# Inline SVG icons
ICONS = {
    "pe": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="22" height="22"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "signals": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="22" height="22"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
    "return": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="22" height="22"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
    "winrate": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="22" height="22"><rect x="3" y="12" width="4" height="9" rx="1"/><rect x="10" y="7" width="4" height="14" rx="1"/><rect x="17" y="3" width="4" height="18" rx="1"/></svg>',
}


def create_metric_card(
    icon_key: str, title: str, value: str, subtitle: str, accent_color: str,
) -> pn.pane.HTML:
    """Create a styled metric card with icon, value, and subtitle."""
    icon_svg = ICONS.get(icon_key, "")
    html = f"""
    <div class="metric-card" style="
        background: var(--panel-surface-color, #ffffff);
        border: 1px solid var(--panel-border-color, rgba(0,0,0,0.08));
        border-radius: 14px; padding: 18px 20px;
        display: flex; align-items: center; gap: 16px; min-width: 220px;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: default;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    " onmouseenter="this.style.boxShadow='0 8px 30px rgba(0,0,0,0.08)';this.style.transform='translateY(-2px)';"
       onmouseleave="this.style.boxShadow='0 1px 2px rgba(0,0,0,0.05)';this.style.transform='none';">
        <div style="
            background: {accent_color}1a; color: {accent_color};
            border-radius: 12px; width: 48px; height: 48px;
            display: flex; align-items: center; justify-content: center; flex-shrink: 0;
            border: 1px solid {accent_color}2b;
        ">{icon_svg}</div>
        <div style="flex: 1; min-width: 0;">
            <div style="font-size:11px; font-weight:600; text-transform:uppercase;
                letter-spacing:0.05em; color: var(--panel-on-surface-color, #64748b);
                opacity: 0.9; margin-bottom:4px;">{title}</div>
            <div style="font-size:26px; font-weight:700;
                color: var(--panel-primary-color, #1e293b);
                line-height:1.1; letter-spacing: -0.02em;">{value}</div>
            <div style="font-size:12px; color: var(--panel-on-surface-color, #94a3b8);
                opacity: 0.8; margin-top:4px;">{subtitle}</div>
        </div>
    </div>
    """
    return pn.pane.HTML(html, sizing_mode="stretch_width")


def create_metrics_row(
    current_pe: float, nifty_level: float, current_pb: float,
    entry_signals: int, threshold: float, signal_type: str,
    median_return: float, holding_period: str, win_rate: float,
) -> pn.Row:
    """Create the metrics bar with all four metric cards."""
    if signal_type == "PB Ratio":
        val_title, val_value = "CURRENT PB", f"{current_pb:.1f}"
        thr_label = f"PB < {threshold:.1f}"
    else:
        val_title, val_value = "CURRENT PE", f"{current_pe:.1f}"
        thr_label = f"PE < {threshold:.0f}"

    ret_prefix = "+" if median_return > 0 else ""
    return pn.Row(
        create_metric_card("pe", val_title, val_value,
                           f"Nifty at {nifty_level:,.0f}", COLORS["primary"]),
        create_metric_card("signals", "ENTRY SIGNALS", str(entry_signals),
                           f"{thr_label} months found", COLORS["info"]),
        create_metric_card("return", f"MEDIAN {holding_period.upper()} RETURN",
                           f"{ret_prefix}{median_return:.1f}%",
                           "Annualized CAGR", COLORS["success"]),
        create_metric_card("winrate", "WIN RATE", f"{win_rate:.0f}%",
                           "Positive return frequency", COLORS["warning"]),
        sizing_mode="stretch_width",
    )
