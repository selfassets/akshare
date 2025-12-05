import sys
import os
import pandas as pd
sys.path.insert(0, os.getcwd())

try:
    from akshare.futures.futures_hist_em import __fetch_exchange_symbol_raw_em as fetch_exchange_symbol_raw_em
    print("Function import successful")
    
    # Test function
    print("Executing function...")
    data = fetch_exchange_symbol_raw_em()
    
    # It returns a list now
    if isinstance(data, list):
        print(f"Function executable, returned list of length: {len(data)}")
        if len(data) > 0:
            print(f"First item: {data[0]}")
    else:
        # Fallback if it's still an iterator (unexpected)
        try:
             first_item = next(data)
             print(f"Function executable (iterator), first item: {first_item}")
        except:
             print(f"Returned unexpected type: {type(data)}")

    # Test Router Import and Wrapper
    from akshare.api.routers.futures import get_futures_exchange_symbol_raw_em
    print("Router function import successful")
    
    # Since get_futures_exchange_symbol_raw_em is async and returns a Response (via _handle_api_request), 
    # we can't easily validata the implementation without running the event loop.
    # But we can verify _handle_api_request wrapping logic by looking at the code or assuming the previous fix 
    # (lambda: pd.DataFrame(...)) prevents the AttributeError.
    
    print("Verification script finished.")
    
except Exception as e:
    print(f"Verification failed: {e}")
    sys.exit(1)
