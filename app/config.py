from pathlib import Path

# Moving average lookbacks — standard commodity market periods
MA_FAST = 20   # one trading month
MA_MEDIUM = 50   # one trading quarter
MA_SLOW = 200  # one trading year

# MACD parameters — universal defaults across all trading platforms
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# RSI parameters — Wilder's original period, daily standard
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# Pipeline settings
COMMODITIES = ["copper", "zinc", "crude_oil"]
YEARS = [2020, 2021]
ROOT = Path(__file__).parent.parent
DB_PATH  = ROOT / "data" / "oildesk.db"
CSV_PATH = ROOT / "data" / "MarketData.csv"

# Strategy parameters
SIGNAL_THRESHOLD = 0.5