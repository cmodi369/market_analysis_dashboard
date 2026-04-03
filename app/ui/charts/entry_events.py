"""Entry Events table using Panel widgets."""

import panel as pn
import pandas as pd


def create_entry_events_table(returns_df: pd.DataFrame) -> pn.widgets.Tabulator:
    """Tabulator table of all entry signal events with forward returns."""
    if returns_df.empty:
        return pn.pane.HTML(
            "<div style='padding:40px; text-align:center; color:#94a3b8;'>"
            "No entry signals found for the selected criteria.</div>",
            sizing_mode="stretch_width",
        )

    display_df = returns_df.copy()
    display_df["Entry Date"] = pd.to_datetime(display_df["Entry Date"]).dt.strftime("%Y-%m-%d")
    display_df["Exit Date"] = pd.to_datetime(display_df["Exit Date"]).dt.strftime("%Y-%m-%d")

    # Sort by entry date descending (most recent first)
    display_df = display_df.sort_values("Entry Date", ascending=False).reset_index(drop=True)

    tabulator = pn.widgets.Tabulator(
        display_df,
        sizing_mode="stretch_width",
        height=460,
        show_index=False,
        page_size=50,
        pagination="remote",
        header_filters=True,
        frozen_columns=["Entry Date"],
        text_align={"CAGR (%)": "right", "Entry Price": "right", "Exit Price": "right"},
    )
    return tabulator
