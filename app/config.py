"""Configuration constants for the Market Signals Dashboard."""

# Data settings
NIFTY_TICKER = "^NSEI"
CACHE_DIR = "data/cache"
CACHE_EXPIRY_HOURS = 24

# Default parameter values
DEFAULT_PE_THRESHOLD = 20
DEFAULT_PB_THRESHOLD = 3.5
DEFAULT_HOLDING_PERIOD = 3  # years
DEFAULT_SIGNAL_TYPE = "PE Ratio"

# Historical PE calibration
MEAN_PE = 22.0
MEAN_PB = 3.5

# PE Bucket definitions (bins of 2)
PE_BUCKET_EDGES = [0, 12, 14, 16, 18, 20, 22, 24, 100]
PE_BUCKET_LABELS = ["<12", "12-14", "14-16", "16-18", "18-20", "20-22", "22-24", ">24"]

PB_BUCKET_EDGES = [0, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 100]
PB_BUCKET_LABELS = [
    "<2.0", "2.0-2.5", "2.5-3.0", "3.0-3.5",
    "3.5-4.0", "4.0-4.5", "4.5-5.0", ">5.0",
]

# Holding period options
HOLDING_PERIODS = {
    "1 Year": 1,
    "3 Years": 3,
    "5 Years": 5,
    "7 Years": 7,
    "10 Years": 10,
}

# Color palette (refined SaaS-style slate/indigo)
COLORS = {
    "primary": "#6366f1",     # Indigo 500
    "success": "#10b981",     # Emerald 500
    "warning": "#f59e0b",     # Amber 500
    "danger": "#ef4444",      # Rose 500
    "info": "#06b6d4",        # Cyan 500
    "bg_dark": "#0f172a",     # Slate 900
    "card_dark": "#1e293b",   # Slate 800
    "text_primary": "#f8fafc", # Slate 50
    "text_secondary": "#94a3b8", # Slate 400
    "border": "rgba(226, 232, 240, 0.1)", # Subtle slate 200
    "green_zone": "#10b981",
    "price_line": "#6366f1",
    "pe_line": "#f97316",
    "grid": "rgba(148, 163, 184, 0.1)",
    "tick": "#94a3b8",
}
