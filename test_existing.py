"""
通达信数据接口测试模块

测试 pytdx 库的标准行情和扩展行情接口
"""

from pytdx.hq import TdxHq_API
from pytdx.exhq import TdxExHq_API

# 服务器配置
HQ_SERVER_HOST = "121.37.207.165"
HQ_SERVER_PORT = 7709
EXHQ_SERVER_HOST = "121.37.232.167"
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
        # 获取市场列表
        markets = api.get_markets()
        print("\n市场列表:")
        print(api.to_df(markets))
        
        # 获取合约数量
        count = api.get_instrument_count()
        print(f"\n合约总数: {count}")
        
        # 获取合约信息
        print("\n合约信息 (前100条):")
        print(api.get_instrument_info(0, 100))
        
        # 获取分时数据
        print("\n分时数据 (IFL0):")
        print(api.get_minute_time_data(47, "IFL0"))
        
        # 获取K线数据
        print("\n期货K线数据 (AO2601):")
        data = api.get_instrument_bars(
            category=0,      # K线类型
            market=1,        # 市场
            code="AO2601",   # 合约代码
            start=0,         # 起始位置
            count=100        # 获取数量
        )
        print(data)
    except Exception as e:
        print(f"扩展行情接口测试失败: {e}")
    finally:
        api.disconnect()


if __name__ == "__main__":
    test_standard_hq()
    test_extended_hq()