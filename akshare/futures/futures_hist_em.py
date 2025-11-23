#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2024/2/20 17:00
Desc: 东方财富网-期货行情
https://qhweb.eastmoney.com/quote
"""

import logging
import re
from functools import lru_cache
from typing import Tuple, Dict

import pandas as pd
import requests

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def __futures_hist_separate_char_and_numbers_em(symbol: str = "焦煤2506") -> tuple:
    """
    东方财富网-期货行情-交易所品种对照表原始数据
    https://quote.eastmoney.com/qihuo/al2505.html
    :param symbol: 股票代码
    :type symbol: str
    :return: 交易所品种对照表原始数据
    :rtype: pandas.DataFrame
    """
    logger.debug(f"开始分离符号: {symbol}")
    char = re.findall(pattern="[\u4e00-\u9fa5a-zA-Z]+", string=symbol)
    numbers = re.findall(pattern=r"\d+", string=symbol)
    logger.debug(f"分离结果 - 字符部分: {char[0]}, 数字部分: {numbers[0]}")
    return char[0], numbers[0]


# @lru_cache()
def __fetch_exchange_symbol_raw_em() -> iter:
    """
    东方财富网-期货行情-交易所品种对照表原始数据
    https://quote.eastmoney.com/qihuo/al2505.html
    :return: 交易所品种对照表原始数据
    :rtype: iter
    """
    logger.info("开始获取交易所品种原始数据")
    url = "https://futsse-static.eastmoney.com/redis"
    params = {"msgid": "gnweb"}
    try:
        logger.debug(f"请求主品种数据, URL: {url}")
        r = requests.get(url, params=params)
        r.raise_for_status()
        data_json = r.json()
        logger.info(f"成功获取主品种数据, 共 {len(data_json)} 个市场")

        for idx, item in enumerate(data_json):
            market_id = item["mktid"]
            logger.debug(f"处理市场 {idx + 1}/{len(data_json)}, 市场ID: {market_id}")

            params = {"msgid": str(market_id)}
            r = requests.get(url, params=params)
            r.raise_for_status()
            inner_data_json = r.json()
            logger.debug(f"市场 {market_id} 获得 {len(inner_data_json)} 组数据")

            for num in range(1, len(inner_data_json) + 1):
                params = {"msgid": str(market_id) + f"_{num}"}
                r = requests.get(url, params=params)
                r.raise_for_status()
                inner_data_json = r.json()
                for inner_item in inner_data_json:
                    yield inner_item
                logger.debug(f"市场 {market_id} 第 {num} 组: 获得 {len(inner_data_json)} 条记录")

        logger.info("成功获取所有交易所品种数据")
    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"获取交易所品种原始数据出错: {e}", exc_info=True)
        raise


@lru_cache()
def __get_exchange_symbol_map() -> Tuple[Dict, Dict, Dict, Dict]:
    """
    东方财富网-期货行情-交易所品种映射
    https://quote.eastmoney.com/qihuo/al2505.html
    :return: 交易所品种映射
    :rtype: pandas.DataFrame
    """
    logger.info("开始构建交易所品种映射")
    try:
        all_exchange_symbol_list = __fetch_exchange_symbol_raw_em()
        c_contract_mkt = {}
        c_contract_to_e_contract = {}
        e_symbol_mkt = {}
        c_symbol_mkt = {}

        for idx, item in enumerate(all_exchange_symbol_list):
            c_contract_mkt[item["name"]] = item["mktid"]
            c_contract_to_e_contract[item["name"]] = item["code"]
            e_symbol_mkt[item["vcode"]] = item["mktid"]
            c_symbol_mkt[item["vname"]] = item["mktid"]

        logger.info(f"映射构建完成 - 中文合约: {len(c_contract_mkt)}, 合约代码: {len(c_contract_to_e_contract)}, "
                   f"英文符号: {len(e_symbol_mkt)}, 中文符号: {len(c_symbol_mkt)}")
        logger.debug(f"中文符号映射示例: {dict(list(c_symbol_mkt.items())[:5])}")

        return c_contract_mkt, c_contract_to_e_contract, e_symbol_mkt, c_symbol_mkt
    except Exception as e:
        logger.error(f"构建交易所品种映射出错: {e}", exc_info=True)
        raise

@lru_cache()
def futures_hist_table_em() -> pd.DataFrame:
    """
    东方财富网-期货行情-交易所品种对照表
    https://quote.eastmoney.com/qihuo/al2505.html
    :return: 交易所品种对照表
    :rtype: pandas.DataFrame
    """
    logger.info("开始获取期货历史表")
    try:
        all_exchange_symbol_list = __fetch_exchange_symbol_raw_em()
        logger.debug("准备转换数据为 DataFrame")

        temp_df = pd.DataFrame(all_exchange_symbol_list)
        temp_df = temp_df[["mktname", "name", "code"]]
        temp_df.columns = ["市场简称", "合约中文代码", "合约代码"]

        logger.info(f"期货历史表获取成功, 共 {len(temp_df)} 行 {len(temp_df.columns)} 列")
        logger.debug(f"表头: {list(temp_df.columns)}")

        return temp_df
    except Exception as e:
        logger.error(f"获取期货历史表出错: {e}", exc_info=True)
        raise


def futures_hist_em(
    symbol: str = "热卷主连",
    period: str = "daily",
    start_date: str = "19900101",
    end_date: str = "20500101",
) -> pd.DataFrame:
    """
    东方财富网-期货行情-行情数据
    https://qhweb.eastmoney.com/quote
    :param symbol: 期货代码
    :type symbol: str
    :param period: choice of {'daily', 'weekly', 'monthly'}
    :type period: str
    :param start_date: 开始日期
    :type start_date: str
    :param end_date: 结束日期
    :type end_date: str
    :return: 行情数据
    :rtype: pandas.DataFrame
    """
    logger.info(f"开始获取期货行情数据 - 品种: {symbol}, 周期: {period}, 日期范围: {start_date}~{end_date}")

    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    period_dict = {"daily": "101", "weekly": "102", "monthly": "103"}

    try:
        logger.debug("获取交易所品种映射")
        c_contract_mkt, c_contract_to_e_contract, e_symbol_mkt, c_symbol_mkt = (
            __get_exchange_symbol_map()
        )

        try:
            sec_id = f"{c_contract_mkt[symbol]}.{c_contract_to_e_contract[symbol]}"
            logger.debug(f"从映射表获取 sec_id: {sec_id}")
        except KeyError:
            logger.debug(f"未在映射表中找到 {symbol}, 尝试解析符号")
            symbol_char, numbers = __futures_hist_separate_char_and_numbers_em(symbol)
            if re.match(pattern="^[\u4e00-\u9fa5]+$", string=symbol_char):
                sec_id = str(c_symbol_mkt[symbol_char]) + "." + symbol
                logger.debug(f"使用中文符号映射获取 sec_id: {sec_id}")
            else:
                sec_id = str(e_symbol_mkt[symbol_char]) + "." + symbol
                logger.debug(f"使用英文符号映射获取 sec_id: {sec_id}")

        params = {
            "secid": sec_id,
            "klt": period_dict[period],
            "fqt": "1",
            "lmt": "10000",
            "end": "20500000",
            "iscca": "1",
            "fields1": "f1,f2,f3,f4,f5,f6,f7,f8",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64",
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "forcect": "1",
        }

        logger.debug(f"向服务器发送请求 URL: {url}")
        r = requests.get(url, timeout=15, params=params)
        r.raise_for_status()
        logger.debug("服务器请求成功")

        data_json = r.json()
        if not data_json.get("data") or not data_json["data"].get("klines"):
            logger.warning(f"未获取到 {symbol} 的行情数据")
            return pd.DataFrame()

        logger.info(f"成功获取 {len(data_json['data']['klines'])} 条原始行情数据")

        temp_df = pd.DataFrame([item.split(",") for item in data_json["data"]["klines"]])
        if temp_df.empty:
            logger.warning("数据转换后为空")
            return temp_df

        logger.debug(f"原始数据形状: {temp_df.shape}")

        temp_df.columns = [
            "时间",
            "开盘",
            "收盘",
            "最高",
            "最低",
            "成交量",
            "成交额",
            "-",
            "涨跌幅",
            "涨跌",
            "_",
            "_",
            "持仓量",
            "_",
        ]
        temp_df = temp_df[
            [
                "时间",
                "开盘",
                "最高",
                "最低",
                "收盘",
                "涨跌",
                "涨跌幅",
                "成交量",
                "成交额",
                "持仓量",
            ]
        ]
        logger.debug("列选择完成")

        temp_df.index = pd.to_datetime(temp_df["时间"])
        logger.debug(f"时间索引转换完成, 时间范围: {temp_df.index.min()} - {temp_df.index.max()}")

        logger.debug(f"按日期范围过滤: {start_date} 到 {end_date}")
        temp_df = temp_df[start_date:end_date]
        logger.info(f"过滤后数据行数: {len(temp_df)}")

        temp_df.reset_index(drop=True, inplace=True)

        logger.debug("开始数据类型转换")
        temp_df["开盘"] = pd.to_numeric(temp_df["开盘"], errors="coerce")
        temp_df["收盘"] = pd.to_numeric(temp_df["收盘"], errors="coerce")
        temp_df["最高"] = pd.to_numeric(temp_df["最高"], errors="coerce")
        temp_df["最低"] = pd.to_numeric(temp_df["最低"], errors="coerce")
        temp_df["成交量"] = pd.to_numeric(temp_df["成交量"], errors="coerce")
        temp_df["成交额"] = pd.to_numeric(temp_df["成交额"], errors="coerce")
        temp_df["涨跌"] = pd.to_numeric(temp_df["涨跌"], errors="coerce")
        temp_df["涨跌幅"] = pd.to_numeric(temp_df["涨跌幅"], errors="coerce")
        temp_df["持仓量"] = pd.to_numeric(temp_df["持仓量"], errors="coerce")
        temp_df["时间"] = pd.to_datetime(temp_df["时间"], errors="coerce").dt.date
        logger.debug("数据类型转换完成")

        logger.info(f"期货行情数据获取成功, 最终数据形状: {temp_df.shape}")
        logger.debug(f"数据摘要:\n{temp_df.head().to_string()}")

        return temp_df
    except requests.exceptions.Timeout:
        logger.error(f"请求超时 - 品种: {symbol}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP请求失败 - 品种: {symbol}, 错误: {e}", exc_info=True)
        raise
    except KeyError as e:
        logger.error(f"未找到符号映射 - 品种: {symbol}, 缺失键: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"获取期货行情数据出错 - 品种: {symbol}, 错误: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # futures_hist_table_em_df = futures_hist_table_em()
    # print(futures_hist_table_em_df)

    futures_hist_em_df = futures_hist_em(symbol="热卷主连", period="daily")
    print(futures_hist_em_df)
