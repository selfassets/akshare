#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Test script for verifying logging functionality
"""

import logging
import sys

# 配置日志输出到控制台
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# 导入模块
from akshare.futures.futures_hist_em import futures_hist_table_em, futures_hist_em

if __name__ == "__main__":
    print("=" * 60)
    print("测试日志功能 - 期货历史表")
    print("=" * 60)
    try:
        # futures_hist_table_em_df = futures_hist_table_em()
        # print(f"\n期货历史表:\n{futures_hist_table_em_df.head()}\n")
        pass
    except Exception as e:
        print(f"Error: {e}\n")

    print("\n" + "=" * 60)
    print("测试日志功能 - 期货行情数据")
    print("=" * 60)
    try:
        futures_hist_em_df = futures_hist_em(symbol="热卷主连", period="daily")
        print(f"\n期货行情数据:\n{futures_hist_em_df.head()}\n")
    except Exception as e:
        print(f"Error: {e}\n")

