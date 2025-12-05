import requests

def test_url(name, url, proxies=None, headers=None):
    print(f"\nTesting {name} ({url})")
    print(f"Proxies: {proxies}")
    print(f"Headers: {headers}")
    try:
        r = requests.get(url, params={}, proxies=proxies, headers=headers, timeout=5)
        print(f"Result: {r.status_code} OK")
    except Exception as e:
        print(f"Result: FAIL - {e}")

# Base settings
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"}

# 1. Test General Connectivity (Baidu)
test_url("Baidu", "https://www.baidu.com", proxies=None, headers=headers)

# 2. Test EastMoney with System Proxy (default)
test_url("EastMoney (Default)", "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=113.cu2512")

# 3. Test EastMoney Direct (No Proxy)
test_url("EastMoney (Direct)", "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=113.cu2512", proxies={"http": None, "https": None})

# 4. Test EastMoney with Headers + Direct
test_url("EastMoney (Direct + Headers)", "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=113.cu2512", proxies={"http": None, "https": None}, headers=headers)

# 5. Test EastMoney HTTP (if supported)
test_url("EastMoney (HTTP)", "http://push2his.eastmoney.com/api/qt/stock/kline/get?secid=113.cu2512", proxies={"http": None, "https": None}, headers=headers)
