# import requests
# from akshare.futures.futures_hist_em import futures_hist_em

# print("Testing futures_hist_em (original function)...")
# try:
#     # Use a standard symbol
#     df = futures_hist_em(symbol="热卷主连", period="daily", start_date="20240101", end_date="20240105")
#     print("Success!")
#     print(df.head())
# except Exception as e:
#     print(f"Failed: {e}")

# from pytdx.hq import TdxHq_API
# api = TdxHq_API()
# with api.connect('121.37.207.165', 7709):
#     # print(api.get_markets())
#     data = api.get_security_bars(9, 0, '000001', 0, 10)
#     print(data)
    #121.37.232.167:7727
from pytdx.exhq import TdxExHq_API
api = TdxExHq_API()
with api.connect('116.205.135.205', 7727):
    api.to_df(api.get_markets())
    print(api.get_markets())
    print(api.get_instrument_count())
    print(api.get_instrument_info(0, 100))
    print(api.get_minute_time_data(47, "IFL0"))
    data=api.get_instrument_bars(0, 1, "AO2601", 0, 100)
    print(data)