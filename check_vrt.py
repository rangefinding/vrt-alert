import yfinance as yf
import requests
import os
from datetime import datetime, timezone

TICKER = "VRT"
PULLBACK_THRESHOLD = 0.04  # 4%
LOOKBACK_DAYS = 20         # rolling high window

def get_vrt_data():
    stock = yf.Ticker(TICKER)
    hist = stock.history(period=f"{LOOKBACK_DAYS + 5}d")  # buffer for weekends/holidays

    if hist.empty or len(hist) < 2:
        raise ValueError("Not enough price history returned.")

    recent_high = hist["High"].tail(LOOKBACK_DAYS).max()
    current_price = hist["Close"].iloc[-1]
    return current_price, recent_high

def send_slack_alert(current_price, recent_high, pullback_pct):
    webhook_url = os.environ["SLACK_WEBHOOK_URL"]

    message = (
        f":rotating_light: *VRT Pullback Alert*\n"
        f"Vertiv Holdings has pulled back *{pullback_pct:.1f}%* from its {LOOKBACK_DAYS}-day high.\n\n"
        f"• *Current Price:* ${current_price:.2f}\n"
        f"• *{LOOKBACK_DAYS}-Day High:* ${recent_high:.2f}\n"
        f"• *Drop:* ${recent_high - current_price:.2f}\n"
        f"• *Threshold:* {PULLBACK_THRESHOLD * 100:.0f}%\n\n"
        f"_Checked at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_"
    )

    payload = {"text": message}
    response = requests.post(webhook_url, json=payload)
    response.raise_for_status()
    print(f"Alert sent: VRT at ${current_price:.2f}, {pullback_pct:.1f}% below {LOOKBACK_DAYS}-day high of ${recent_high:.2f}")

def main():
    current_price, recent_high = get_vrt_data()
    pullback_pct = (recent_high - current_price) / recent_high * 100

    print(f"VRT: ${current_price:.2f} | {LOOKBACK_DAYS}-day high: ${recent_high:.2f} | Pullback: {pullback_pct:.2f}%")

    if pullback_pct >= PULLBACK_THRESHOLD * 100:
        send_slack_alert(current_price, recent_high, pullback_pct)
    else:
        print(f"No alert — pullback ({pullback_pct:.2f}%) is below {PULLBACK_THRESHOLD * 100:.0f}% threshold.")

if __name__ == "__main__":
    main()
