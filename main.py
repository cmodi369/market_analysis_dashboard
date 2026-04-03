"""Entry point for the Nifty Market Signals Dashboard."""

from app.ui.dashboard import create_dashboard

dashboard = create_dashboard()
dashboard.servable()
