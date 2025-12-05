import requests
import os

url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
params = {"secid": "113.cu2512"}

print("Environment Proxies:")
print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY')}")
print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY')}")
print(f"ALL_PROXY: {os.environ.get('ALL_PROXY')}")

print("\nMethod 1: proxies={}")
try:
    requests.get(url, params=params, proxies={}, timeout=5)
    print("Method 1 SUCCESS")
except Exception as e:
    print(f"Method 1 FAIL: {e}")

print("\nMethod 2: proxies={'http': None, 'https': None}")
try:
    requests.get(url, params=params, proxies={"http": None, "https": None}, timeout=5)
    print("Method 2 SUCCESS")
except Exception as e:
    print(f"Method 2 FAIL: {e}")
