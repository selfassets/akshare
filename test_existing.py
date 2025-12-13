"""
通达信数据接口测试模块

测试 pytdx 库的标准行情和扩展行情接口
"""

from pytdx.hq import TdxHq_API
from pytdx.exhq import TdxExHq_API

# 服务器配置
HQ_SERVER_HOST = "121.37.207.165"
HQ_SERVER_PORT = 7709
EXHQ_SERVER_HOST = "119.23.127.172"
EXHQ_SERVER_PORT = 7727


def test_standard_hq():
    """测试标准行情接口"""
    print("=" * 50)
    print("测试标准行情接口 (TdxHq_API)")
    print("=" * 50)
    
    api = TdxHq_API()
    try:
        api.connect(HQ_SERVER_HOST, HQ_SERVER_PORT)
        # 获取股票K线数据 (上证指数)
        data = api.get_security_bars(
            category=9,      # K线类型: 9=日线
            market=0,        # 市场: 0=深圳, 1=上海
            code="000001",   # 股票代码
            start=0,         # 起始位置
            count=10         # 获取数量
        )
        print("获取 000001 日线数据:")
        print(data)
    except Exception as e:
        print(f"标准行情接口测试失败: {e}")
    finally:
        api.disconnect()


def test_extended_hq():
    """测试扩展行情接口 (期货/外汇等)"""
    print("\n" + "=" * 50)
    print("测试扩展行情接口 (TdxExHq_API)")
    print("=" * 50)
    
    api = TdxExHq_API()
    try:
        api.connect(EXHQ_SERVER_HOST, EXHQ_SERVER_PORT)
        
        # 1. 获取市场列表
        print("\n[1] 获取市场列表 (get_markets):")
        markets = api.get_markets()
        print(api.to_df(markets) if markets else "无数据")
        
        # 2. 获取合约数量
        print("\n[2] 获取合约数量 (get_instrument_count):")
        count = api.get_instrument_count()
        print(f"合约总数: {count}")
        
        # 3. 获取合约信息
        print("\n[3] 获取合约信息 (get_instrument_info):")
        instruments = api.get_instrument_info(0, 100)
        print(api.to_df(instruments) if instruments else "无数据")
        
        # 4. 查询五档行情
        print("\n[4] 查询五档行情 (get_instrument_quote):")
        quote = api.get_instrument_quote(47, "IFL0")
        print(api.to_df(quote) if quote else "无数据")
        
        # 5. 查询分时行情
        print("\n[5] 查询分时行情 (get_minute_time_data):")
        minute_data = api.get_minute_time_data(47, "IFL0")
        print(api.to_df(minute_data) if minute_data else "无数据")
        
        # 6. 查询历史分时行情
        print("\n[6] 查询历史分时行情 (get_history_minute_time_data):")
        history_minute = api.get_history_minute_time_data(47, "IFL0", 20241201)
        print(api.to_df(history_minute) if history_minute else "无数据")
        
        # 7. 查询K线数据
        print("\n[7] 查询K线数据 (get_instrument_bars):")
        bars = api.get_instrument_bars(
            category=0,      # K线类型: 0=5分钟, 1=15分钟, 2=30分钟, 3=1小时, 4=日线
            market=47,       # 市场ID
            code="IFL0",     # 合约代码
            start=0,         # 起始位置
            count=10         # 获取数量
        )
        print(api.to_df(bars) if bars else "无数据")
        
        # 8. 查询分笔成交数据
        print("\n[8] 查询分笔成交数据 (get_transaction_data):")
        trans = api.get_transaction_data(47, "IFL0", 0, 10)
        print(api.to_df(trans) if trans else "无数据")
        
        # 9. 查询历史分笔成交数据
        print("\n[9] 查询历史分笔成交数据 (get_history_transaction_data):")
        history_trans = api.get_history_transaction_data(47, "IFL0", 20241201, 0, 10)
        print(api.to_df(history_trans) if history_trans else "无数据")
        
    except Exception as e:
        print(f"扩展行情接口测试失败: {e}")
    finally:
        api.disconnect()


if __name__ == "__main__":
    # test_standard_hq()
    test_extended_hq()