import sys
import pandas as pd
from akshare.futures.futures_hist_em import futures_hist_em_v1

print("Testing futures_hist_em_v1 with sec_id...")
try:
    # Use valid sec_id for testing (e.g. 113.cu2512)
    # Note: symbol argument was removed by user
    df = futures_hist_em_v1(sec_id="113.cu2512", period="daily")
    print(f"Result type: {type(df)}")
    if isinstance(df, pd.DataFrame):
        print(f"DataFrame shape: {df.shape}")
        if not df.empty:
            print(f"First row:\n{df.iloc[0]}")
        else:
            print("DataFrame is empty.")
    else:
        print("Result is not a DataFrame.")
except Exception as e:
    print(f"futures_hist_em_v1 failed: {e}")
    sys.exit(1)

print("\nVerification passed.")
