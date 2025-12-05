import sys
import os
import pandas as pd
from akshare.futures.futures_hist_em import fetch_futures_market_info_em, __fetch_exchange_symbol_raw_em

print("Testing fetch_futures_market_info_em...")
try:
    market_info = fetch_futures_market_info_em()
    print(f"Market info result type: {type(market_info)}")
    if isinstance(market_info, list) and len(market_info) > 0:
        print(f"Market info count: {len(market_info)}")
        print(f"First market: {market_info[0]}")
    else:
        print("Market info returned unexpected result.")
except Exception as e:
    print(f"fetch_futures_market_info_em failed: {e}")
    sys.exit(1)

print("\nTesting __fetch_exchange_symbol_raw_em (should still work)...")
try:
    exchange_symbols = __fetch_exchange_symbol_raw_em()
    print(f"Exchange symbols result type: {type(exchange_symbols)}")
    if isinstance(exchange_symbols, list) and len(exchange_symbols) > 0:
        print(f"Exchange symbols count: {len(exchange_symbols)}")
        print(f"First symbol: {exchange_symbols[0]}")
    else:
         print("Exchange symbols returned unexpected result.")
except Exception as e:
    print(f"__fetch_exchange_symbol_raw_em failed: {e}")
    sys.exit(1)

print("\nVerification passed.")
