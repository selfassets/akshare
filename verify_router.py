import sys
import os
try:
    from akshare.api.routers.futures import get_futures_market_info_em
    print("Router function import successful")
except Exception as e:
    print(f"Router import failed: {e}")
    sys.exit(1)
