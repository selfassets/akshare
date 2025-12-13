"""
快速测试缠论API的脚本

直接导入模块测试，不需要启动HTTP服务
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
import pandas as pd

# 测试导入
print("测试导入模块...")
try:
    from akshare.api.analysis.chanlun_core import ChanlunAnalyzer, create_bars_from_dataframe, Bar
    print("✓ 成功导入 chanlun_core")
except Exception as e:
    print(f"✗ 导入失败: {e}")
    exit(1)

# 创建测试数据（模拟真实的期货数据）
print("\n创建测试数据...")
test_data = pd.DataFrame({
    '日期': pd.date_range('2024-01-01', periods=50),
    '开盘价': [3000 + i * 10 for i in range(50)],
    '收盘价': [3005 + i * 10 for i in range(50)],
    '最高价': [3010 + i * 10 for i in range(50)],
    '最低价': [2995 + i * 10 for i in range(50)],
    '成交量': [1000 + i * 100 for i in range(50)],
})

print(f"✓ 创建了 {len(test_data)} 条测试数据")

# 转换为Bar
print("\n转换为Bar对象...")
try:
    bars = create_bars_from_dataframe(test_data, symbol="TEST")
    print(f"✓ 转换了 {len(bars)} 根K线")
except Exception as e:
    print(f"✗ 转换失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 执行分析
print("\n执行缠论分析...")
try:
    analyzer = ChanlunAnalyzer(bars)
    print(f"✓ 分析完成")
    print(f"  - 原始K线: {len(analyzer.bars_raw)} 根")
    print(f"  - 合并后K线: {len(analyzer.bars_merged)} 根")
    print(f"  - 识别分型: {len(analyzer.fractals)} 个")
    print(f"  - 识别笔: {len(analyzer.strokes)} 笔")
except Exception as e:
    print(f"✗ 分析失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 转换为字典
print("\n转换为字典格式...")
try:
    result = analyzer.to_dict()
    print(f"✓ 转换成功")
    print(f"  - 包含 {len(result.keys())} 个字段")
except Exception as e:
    print(f"✗ 转换失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*60)
print("✅ 所有测试通过！缠论分析引擎运行正常。")
print("="*60)
