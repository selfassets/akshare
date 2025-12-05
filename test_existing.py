import requests
from akshare.futures.futures_hist_em import futures_hist_em

print("Testing futures_hist_em (original function)...")
try:
    # Use a standard symbol
    df = futures_hist_em(symbol="热卷主连", period="daily", start_date="20240101", end_date="20240105")
    print("Success!")
    print(df.head())
except Exception as e:
    print(f"Failed: {e}")
