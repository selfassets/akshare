"""
通达信数据接口测试模块

测试 pytdx 库的标准行情和扩展行情接口
"""

from pytdx.hq import TdxHq_API
from pytdx.exhq import TdxExHq_API

# 标准行情服务器配置
HQ_SERVER_HOST = "121.37.207.165"
HQ_SERVER_PORT = 7709

# 扩展行情服务器列表 (经测试可用的服务器)
EXHQ_SERVERS = [
    {"ip": "112.74.214.43", "port": 7727, "name": "扩展市场深圳双线1"},
    {"ip": "121.37.232.167", "port": 7727, "name": "原测试服务器"},
]


def test_standard_hq():
    """测试标准行情接口"""
    print("=" * 60)
    print("测试标准行情接口 (TdxHq_API)")
    print("=" * 60)
    
    api = TdxHq_API()
    try:
        api.connect(HQ_SERVER_HOST, HQ_SERVER_PORT)
        
        # 1. 获取股票行情
        print("\n[1] 获取股票行情 (get_security_quotes):")
        quotes = api.get_security_quotes([(0, "000001"), (1, "600000")])
        print(api.to_df(quotes) if quotes else "无数据")
        
        # 2. 获取K线数据
        print("\n[2] 获取K线数据 (get_security_bars):")
        bars = api.get_security_bars(
            category=9,      # K线类型: 0=5分钟, 1=15分钟, 2=30分钟, 3=1小时, 4=日线, 9=日线
            market=0,        # 市场: 0=深圳, 1=上海
            code="000001",   # 股票代码
            start=0,         # 起始位置
            count=10         # 获取数量
        )
        print(api.to_df(bars) if bars else "无数据")
        
        # 3. 获取市场股票数量
        print("\n[3] 获取市场股票数量 (get_security_count):")
        count_sz = api.get_security_count(0)  # 深圳
        count_sh = api.get_security_count(1)  # 上海
        print(f"深圳市场股票数量: {count_sz}")
        print(f"上海市场股票数量: {count_sh}")
        
        # 4. 获取股票列表
        print("\n[4] 获取股票列表 (get_security_list):")
        stock_list = api.get_security_list(0, 0)  # 深圳市场从0开始
        print(api.to_df(stock_list[:10]) if stock_list else "无数据")
        
        # 5. 获取指数K线
        print("\n[5] 获取指数K线 (get_index_bars):")
        index_bars = api.get_index_bars(
            category=9,      # 日线
            market=1,        # 上海
            code="000001",   # 上证指数
            start=0,
            count=10
        )
        print(api.to_df(index_bars) if index_bars else "无数据")
        
        # 6. 查询分时行情
        print("\n[6] 查询分时行情 (get_minute_time_data):")
        minute_data = api.get_minute_time_data(0, "000001")
        print(api.to_df(minute_data[:10]) if minute_data else "无数据")
        
        # 7. 查询历史分时行情
        print("\n[7] 查询历史分时行情 (get_history_minute_time_data):")
        history_minute = api.get_history_minute_time_data(0, "000001", 20241201)
        print(api.to_df(history_minute[:10]) if history_minute else "无数据")
        
        # 8. 查询分笔成交
        print("\n[8] 查询分笔成交 (get_transaction_data):")
        trans = api.get_transaction_data(0, "000001", 0, 10)
        print(api.to_df(trans) if trans else "无数据")
        
        # 9. 查询历史分笔成交
        print("\n[9] 查询历史分笔成交 (get_history_transaction_data):")
        history_trans = api.get_history_transaction_data(0, "000001", 20241201, 0, 10)
        print(api.to_df(history_trans) if history_trans else "无数据")
        
        # 10. 读取除权除息信息
        print("\n[10] 读取除权除息信息 (get_xdxr_info):")
        xdxr = api.get_xdxr_info(0, "000001")
        print(api.to_df(xdxr[:5]) if xdxr else "无数据")
        
        # 11. 读取财务信息
        print("\n[11] 读取财务信息 (get_finance_info):")
        finance = api.get_finance_info(0, "000001")
        print(finance if finance else "无数据")
        
        # 12. 查询公司信息目录
        print("\n[12] 查询公司信息目录 (get_company_info_category):")
        company_category = api.get_company_info_category(0, "000001")
        print(company_category[:3] if company_category else "无数据")
        
        return True
        
    except Exception as e:
        print(f"❌ 标准行情接口测试失败: {e}")
        return False
    finally:
        api.disconnect()


def test_extended_hq(host: str, port: int, name: str = ""):
    """测试扩展行情接口 (期货/外汇等)
    
    Args:
        host: 服务器IP地址
        port: 服务器端口
        name: 服务器名称
    """
    print("\n" + "=" * 60)
    print(f"测试扩展行情接口: {name} ({host}:{port})")
    print("=" * 60)
    
    api = TdxExHq_API()
    try:
        api.connect(host, port)
        
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
        
        return True
        
    except Exception as e:
        print(f"❌ 连接或测试失败: {e}")
        return False
    finally:
        api.disconnect()


if __name__ == "__main__":
    # test_standard_hq()
    
    # 循环测试所有扩展行情服务器
    print("开始循环测试所有扩展行情服务器...")
    print(f"共 {len(EXHQ_SERVERS)} 个服务器\n")
    
    results = []
    for i, server in enumerate(EXHQ_SERVERS, 1):
        print(f"\n{'#' * 60}")
        print(f"# 服务器 {i}/{len(EXHQ_SERVERS)}")
        print(f"{'#' * 60}")
        
        success = test_extended_hq(
            host=server["ip"],
            port=server["port"],
            name=server.get("name", "未命名")
        )
        results.append({
            "name": server.get("name", "未命名"),
            "ip": server["ip"],
            "port": server["port"],
            "success": success
        })
    
    # 打印测试结果汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    for r in results:
        status = "✅ 成功" if r["success"] else "❌ 失败"
        print(f"{status} | {r['name']} ({r['ip']}:{r['port']})")