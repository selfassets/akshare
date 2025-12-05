import sys
from akshare.futures.futures_hist_em import fetch_futures_market_details_em

print("Testing fetch_futures_market_details_em...")
try:
    # Test with CFFEX (market_id 114)
    market_id = "114" 
    details = fetch_futures_market_details_em(market_id=market_id)
    print(f"Market details type: {type(details)}")
    if isinstance(details, list) and len(details) > 0:
        print(f"Details count for {market_id}: {len(details)}")
        print(f"First item: {details[0]}")
    else:
        print("Market details returned unexpected result.")
except Exception as e:
    print(f"fetch_futures_market_details_em failed: {e}")
    sys.exit(1)

print("Verification passed.")
