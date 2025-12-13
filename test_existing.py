"""
通达信数据接口测试模块

测试 pytdx 库的标准行情和扩展行情接口
"""

from pytdx.hq import TdxHq_API
from pytdx.exhq import TdxExHq_API

# coding: utf-8
# see https://github.com/rainx/pytdx/issues/38 IP寻优的简单办法
# by yutianst

import datetime

from pytdx.exhq import TdxExHq_API
from pytdx.hq import TdxHq_API

stock_ip = [
    # 旧有的数据源
    # {"ip": "106.120.74.86", "port": 7711, "name": "北京行情主站1"},
    # {"ip": "113.105.73.88", "port": 7709, "name": "深圳行情主站"},
    # {"ip": "113.105.73.88", "port": 7711, "name": "深圳行情主站"},
    # {"ip": "114.80.80.222", "port": 7711, "name": "上海行情主站"},
    # {"ip": "117.184.140.156", "port": 7711, "name": "移动行情主站"},
    # {"ip": "119.147.171.206", "port": 443, "name": "广州行情主站"},
    # {"ip": "119.147.171.206", "port": 80, "name": "广州行情主站"},
    # {"ip": "218.108.50.178", "port": 7711, "name": "杭州行情主站"},
    # {"ip": "221.194.181.176", "port": 7711, "name": "北京行情主站2"},
    # {"ip": "106.120.74.86", "port": 7709},
    # {"ip": "112.95.140.74", "port": 7709},
    # {"ip": "112.95.140.92", "port": 7709},
    # {"ip": "112.95.140.93", "port": 7709},
    # {"ip": "113.05.73.88", "port": 7709},
    # {"ip": "114.67.61.70", "port": 7709},
    # {"ip": "114.80.149.19", "port": 7709},
    # {"ip": "114.80.149.22", "port": 7709},
    # {"ip": "114.80.149.84", "port": 7709},
    # {"ip": "114.80.80.222", "port": 7709},
    # {"ip": "115.238.56.198", "port": 7709},
    # {"ip": "115.238.90.165", "port": 7709},
    # {"ip": "117.184.140.156", "port": 7709},
    # {"ip": "119.147.164.60", "port": 7709},
    # {"ip": "119.147.171.206", "port": 7709},
    # {"ip": "119.29.51.30", "port": 7709},
    # {"ip": "121.14.104.70", "port": 7709},
    # {"ip": "121.14.104.72", "port": 7709},
    # {"ip": "121.14.110.194", "port": 7709},
    # {"ip": "121.14.2.7", "port": 7709},
    # {"ip": "123.125.108.23", "port": 7709},
    # {"ip": "123.125.108.24", "port": 7709},
    # {"ip": "124.160.88.183", "port": 7709},
    # {"ip": "180.153.18.17", "port": 7709},
    {"ip": "180.153.18.170", "port": 7709},
    # {"ip": "180.153.18.171", "port": 7709},
    # {"ip": "180.153.39.51", "port": 7709},
    # {"ip": "218.108.47.69", "port": 7709},
    # {"ip": "218.108.50.178", "port": 7709},
    # {"ip": "218.108.98.244", "port": 7709},
    {"ip": "218.75.126.9", "port": 7709},
    # {"ip": "218.9.148.108", "port": 7709},
    # {"ip": "221.194.181.176", "port": 7709},
    # {"ip": "59.173.18.69", "port": 7709},
    {"ip": "60.12.136.250", "port": 7709},
    {"ip": "60.191.117.167", "port": 7709},
    # {"ip": "60.28.29.69", "port": 7709},
    # {"ip": "61.135.142.73", "port": 7709},
    # {"ip": "61.135.142.88", "port": 7709},
    # {"ip": "61.152.107.168", "port": 7721},
    # {"ip": "61.152.249.56", "port": 7709},
    # {"ip": "61.153.144.179", "port": 7709},
    # {"ip": "61.153.209.138", "port": 7709},
    # {"ip": "61.153.209.139", "port": 7709},
    # {"ip": "hq.cjis.cn", "port": 7709},
    # {"ip": "hq1.daton.com.cn", "port": 7709},
    # {"ip": "jstdx.gtjas.com", "port": 7709},
    {"ip": "shtdx.gtjas.com", "port": 7709},
    {"ip": "sztdx.gtjas.com", "port": 7709},
    # {"ip": "113.105.142.162", "port": 7721},
    # {"ip": "23.129.245.199", "port": 7721},
    # 新的数据源
    {"ip": "110.41.147.114", "port": 7709, "name": "通达信深圳双线主站1"},
    {"ip": "110.41.2.72", "port": 7709, "name": "通达信深圳双线主站2"},
    {"ip": "110.41.4.4", "port": 7709, "name": "通达信深圳双线主站3"},
    {"ip": "175.178.112.197", "port": 7709, "name": "通达信深圳双线主站4"},
    {"ip": "175.178.128.227", "port": 7709, "name": "通达信深圳双线主站5"},
    {"ip": "110.41.154.219", "port": 7709, "name": "通达信深圳双线主站6"},
    {"ip": "124.70.176.52", "port": 7709, "name": "通达信上海双线主站1"},
    {"ip": "122.51.120.217", "port": 7709, "name": "通达信上海双线主站2"},
    {"ip": "123.60.186.45", "port": 7709, "name": "通达信上海双线主站3"},
    {"ip": "123.60.164.122", "port": 7709, "name": "通达信上海双线主站4"},
    {"ip": "111.229.247.189", "port": 7709, "name": "通达信上海双线主站5"},
    {"ip": "124.70.199.56", "port": 7709, "name": "通达信上海双线主站6"},
    {"ip": "121.36.54.217", "port": 7709, "name": "通达信北京双线主站1"},
    {"ip": "121.36.81.195", "port": 7709, "name": "通达信北京双线主站2"},
    {"ip": "123.249.15.60", "port": 7709, "name": "通达信北京双线主站3"},
    {"ip": "124.71.85.110", "port": 7709, "name": "通达信广州双线主站1"},
    {"ip": "139.9.51.18", "port": 7709, "name": "通达信广州双线主站2"},
    {"ip": "139.159.239.163", "port": 7709, "name": "通达信广州双线主站3"},
    {"ip": "122.51.232.182", "port": 7709, "name": "通达信上海双线主站7"},
    {"ip": "118.25.98.114", "port": 7709, "name": "通达信上海双线主站8"},
    {"ip": "121.36.225.169", "port": 7709, "name": "通达信上海双线主站9"},
    {"ip": "123.60.70.228", "port": 7709, "name": "通达信上海双线主站10"},
    {"ip": "123.60.73.44", "port": 7709, "name": "通达信上海双线主站11"},
    {"ip": "124.70.133.119", "port": 7709, "name": "通达信上海双线主站12"},
    {"ip": "124.71.187.72", "port": 7709, "name": "通达信上海双线主站13"},
    {"ip": "124.71.187.122", "port": 7709, "name": "通达信上海双线主站14"},
    # {"ip": "119.97.185.59", "port": 7709, "name": "通达信武汉电信主站1"},
    {"ip": "129.204.230.128", "port": 7709, "name": "通达信深圳双线主站7"},
    {"ip": "124.70.75.113", "port": 7709, "name": "通达信北京双线主站4"},
    {"ip": "124.71.9.153", "port": 7709, "name": "通达信广州双线主站4"},
    {"ip": "123.60.84.66", "port": 7709, "name": "通达信上海双线主站15"},
    {"ip": "111.230.186.52", "port": 7709, "name": "通达信深圳双线主站8"},
    {"ip": "120.46.186.223", "port": 7709, "name": "通达信北京双线主站5"},
    {"ip": "124.70.22.210", "port": 7709, "name": "通达信北京双线主站6"},
    {"ip": "139.9.133.247", "port": 7709, "name": "通达信北京双线主站7"},
    {"ip": "116.205.163.254", "port": 7709, "name": "通达信广州双线主站5"},
    {"ip": "116.205.171.132", "port": 7709, "name": "通达信广州双线主站6"},
    {"ip": "116.205.183.150", "port": 7709, "name": "通达信广州双线主站7"},
]

future_ip = [
    # 旧有的数据源
    # {"ip": "106.14.95.149", "port": 7727, "name": "扩展市场上海双线"},
    {"ip": "112.74.214.43", "port": 7727, "name": "扩展市场深圳双线1"},
    # {"ip": "119.147.86.171", "port": 7727, "name": "扩展市场深圳主站"},
    # {"ip": "119.97.185.5", "port": 7727, "name": "扩展市场武汉主站1"},
    # {"ip": "120.24.0.77", "port": 7727, "name": "扩展市场深圳双线2"},
    # {"ip": "124.74.236.94", "port": 7721},
    # {"ip": "202.103.36.71", "port": 443, "name": "扩展市场武汉主站2"},
    # {"ip": "47.92.127.181", "port": 7727, "name": "扩展市场北京主站"},
    # {"ip": "59.175.238.38", "port": 7727, "name": "扩展市场武汉主站3"},
    # {"ip": "61.152.107.141", "port": 7727, "name": "扩展市场上海主站1"},
    # {"ip": "61.152.107.171", "port": 7727, "name": "扩展市场上海主站2"},
    # {"ip": "47.107.75.159", "port": 7727, "name": "扩展市场深圳双线3"},
    # 新的数据源 (经测试，以下服务器连接成功但无数据返回)
    # {"ip": "120.25.218.6", "port": 7727, "name": "扩展市场深圳双线2"},
    # {"ip": "43.139.173.246", "port": 7727, "name": "扩展市场深圳双线3"},
    # {"ip": "159.75.90.107", "port": 7727, "name": "扩展市场深圳双线4"},
    # {"ip": "106.52.170.195", "port": 7727, "name": "扩展市场深圳双线5"},
    # {"ip": "139.9.191.175", "port": 7727, "name": "扩展市场广州双线3"},
    # {"ip": "175.24.47.69", "port": 7727, "name": "扩展市场上海双线7"},
    # {"ip": "150.158.9.199", "port": 7727, "name": "扩展市场上海双线1"},
    # {"ip": "150.158.20.127", "port": 7727, "name": "扩展市场上海双线2"},
    # {"ip": "49.235.119.116", "port": 7727, "name": "扩展市场上海双线3"},
    # {"ip": "49.234.13.160", "port": 7727, "name": "扩展市场上海双线4"},
    # 经测试有完整数据返回的服务器
    {"ip": "116.205.143.214", "port": 7727, "name": "扩展市场广州双线1"},
    # {"ip": "124.71.223.19", "port": 7727, "name": "扩展市场广州双线2"},
    # {"ip": "113.45.175.47", "port": 7727, "name": "扩展市场广州双线4"},
    # {"ip": "123.60.173.210", "port": 7727, "name": "扩展市场上海双线5"},
    # {"ip": "118.89.69.202", "port": 7727, "name": "扩展市场上海双线6"},
]


def ping(ip, port=7709, type_="stock"):
    api = TdxHq_API()
    apix = TdxExHq_API()
    __time1 = datetime.datetime.now()
    try:
        if type_ in ["stock"]:
            with api.connect(ip, port, time_out=0.7):
                res = api.get_security_list(0, 1)
                if res is not None:
                    if len(res) > 800:
                        print("GOOD RESPONSE {}".format(ip))
                        return datetime.datetime.now() - __time1
                    else:
                        print("BAD RESPONSE {}".format(ip))
                        return datetime.timedelta(9, 9, 0)

                else:
                    print("BAD RESPONSE {}".format(ip))
                    return datetime.timedelta(9, 9, 0)
        elif type_ in ["future"]:
            with apix.connect(ip, port, time_out=0.7):
                res = apix.get_instrument_count()
                if res is not None:
                    if res > 20000:
                        print("GOOD RESPONSE {}".format(ip))
                        return datetime.datetime.now() - __time1
                    else:
                        print("️Bad FUTUREIP REPSONSE {}".format(ip))
                        return datetime.timedelta(9, 9, 0)
                else:
                    print("️Bad FUTUREIP REPSONSE {}".format(ip))
                    return datetime.timedelta(9, 9, 0)
    except Exception as e:
        if isinstance(e, TypeError):
            pass
        else:
            print("BAD RESPONSE {}".format(ip))
        return datetime.timedelta(9, 9, 0)


def select_best_ip(_type="stock"):
    """目前这里给的是单线程的选优, 如果需要多进程的选优/ 最优ip缓存 可以参考
    https://github.com/QUANTAXIS/QUANTAXIS/blob/master/QUANTAXIS/QAFetch/QATdx.py#L106


    Keyword Arguments:
        _type {str} -- [description] (default: {'stock'})

    Returns:
        [type] -- [description]
    """

    ip_list = stock_ip if _type == "stock" else future_ip

    data = [ping(x["ip"], x["port"], _type) for x in ip_list]
    results = []
    for i in range(len(data)):
        # 删除ping不通的数据
        if data[i] < datetime.timedelta(0, 9, 0):
            results.append((data[i], ip_list[i]))

    # 按照ping值从小大大排序
    results = [x[1] for x in sorted(results, key=lambda x: x[0])]

    return results[0]



# 标准行情服务器配置
HQ_SERVER_HOST = "121.37.207.165"
HQ_SERVER_PORT = 7709

# 扩展行情服务器列表 (经测试可用的服务器)
EXHQ_SERVERS = [
    {"ip": "61.152.107.141", "port": 7727, "name": "扩展市场深圳双线1"},
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
    # print(len(stock_ip))
    # ip = select_best_ip("stock")
    # print(ip)

    # print(len(future_ip))
    # ip = select_best_ip("future")
    # print(ip)
    
    # test_standard_hq()
    
    # 循环测试所有扩展行情服务器 (使用 future_ip 列表)
    print("开始循环测试所有扩展行情服务器...")
    print(f"共 {len(future_ip)} 个服务器\n")
    
    results = []
    for i, server in enumerate(future_ip, 1):
        print(f"\n{'#' * 60}")
        print(f"# 服务器 {i}/{len(future_ip)}")
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