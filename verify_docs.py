import inspect
from akshare.api.routers.futures import get_futures_comm_info

# Inspect the function signature to check parameter description
sig = inspect.signature(get_futures_comm_info)
param = sig.parameters['symbol']

print(f"Parameter: {param.name}")
print(f"Default value info: {param.default}")

# We expect the description to be in Chinese now
description = param.default.description
print(f"Description: {description}")

if "交易所范围" in description:
    print("Verification SUCCESS: Description contains Chinese")
else:
    print("Verification FAILED: Description does not match expected Chinese text")
