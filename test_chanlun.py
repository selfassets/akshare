"""
缠论分析测试脚本

测试自实现的缠论分析引擎的各项功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import pandas as pd
from akshare.futures_derivative.futures_index_sina import futures_main_sina
from akshare.api.analysis.chanlun_core import ChanlunAnalyzer, create_bars_from_dataframe


def create_mock_data():
    """创建模拟K线数据用于测试"""
    import numpy as np
    
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # 生成模拟价格数据
    price = 3000.0
    data = []
    
    for dt in dates:
        # 随机涨跌
        change = np.random.randn() * 20
        price += change
        
        # 生成OHLC
        open_price = price
        close_price = price + np.random.randn() * 10
        high_price = max(open_price, close_price) + abs(np.random.randn() * 5)
        low_price = min(open_price, close_price) - abs(np.random.randn() * 5)
        volume = np.random.randint(1000, 10000)
        
        data.append({
            '日期': dt,
            '开盘价': open_price,
            '收盘价': close_price,
            '最高价': high_price,
            '最低价': low_price,
            '成交量': volume,
        })
    
    return pd.DataFrame(data)


def test_basic_analysis():
    """测试基础分析功能"""
    print("=" * 80)
    print("测试缠论分析引擎")
    print("=" * 80)
    
    # 1. 尝试获取测试数据
    print("\n1. 获取K线数据...")
    symbol = "热卷主连"
    start_date = "20240101"
    end_date = "20240331"
    
    df = None
    try:
        df = futures_main_sina(symbol=symbol, start_date=start_date, end_date=end_date)
        print(f"   ✓ 获取到 {len(df)} 条真实数据")
        print(f"   列名: {df.columns.tolist()}")
    except Exception as e:
        print(f"   ✗ 获取真实数据失败: {e}")
        print(f"   → 使用模拟数据进行测试")
        df = create_mock_data()
        print(f"   ✓ 创建了 {len(df)} 条模拟数据")

    
    # 2. 转换为 Bar 列表
    print("\n2. 转换 K 线数据...")
    try:
        bars = create_bars_from_dataframe(df, symbol=symbol)
        print(f"   ✓ 转换了 {len(bars)} 根 K 线")
        if len(bars) > 0:
            print(f"   第一根: {bars[0]}")
            print(f"   最后一根: {bars[-1]}")
    except Exception as e:
        print(f"   ✗ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. 执行缠论分析
    print("\n3. 执行缠论分析...")
    try:
        analyzer = ChanlunAnalyzer(bars)
        print(f"   ✓ 分析完成")
        print(f"   原始 K 线: {len(analyzer.bars_raw)} 根")
        print(f"   合并后 K 线: {len(analyzer.bars_merged)} 根")
        print(f"   识别分型: {len(analyzer.fractals)} 个")
        print(f"   识别笔: {len(analyzer.strokes)} 笔")
    except Exception as e:
        print(f"   ✗ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. 显示分型详情
    print("\n4. 分型详情（前10个）:")
    for i, fractal in enumerate(analyzer.fractals[:10]):
        print(f"   [{i}] {fractal.fractal_type.value:6s} - "
              f"{fractal.dt.strftime('%Y-%m-%d')} - "
              f"价格: {fractal.price:.2f} (高: {fractal.high:.2f}, 低: {fractal.low:.2f})")
    
    # 5. 显示笔详情
    print("\n5. 笔详情（前10笔）:")
    for i, stroke in enumerate(analyzer.strokes[:10]):
        print(f"   [{i}] {stroke.direction.value:4s} - "
              f"{stroke.start_dt.strftime('%Y-%m-%d')} -> {stroke.end_dt.strftime('%Y-%m-%d')} - "
              f"{stroke.start_price:.2f} -> {stroke.end_price:.2f} "
              f"(力度: {stroke.power:.2f})")
    
    # 6. 转换为字典
    print("\n6. 转换为 JSON 格式...")
    try:
        result = analyzer.to_dict()
        print(f"   ✓ 转换成功")
        print(f"   bars_raw: {len(result['bars_raw'])} 条")
        print(f"   bars_merged: {len(result['bars_merged'])} 条")
        print(f"   fractals: {len(result['fractals'])} 个")
        print(f"   strokes: {len(result['strokes'])} 笔")
    except Exception as e:
        print(f"   ✗ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)


def test_inclusion_handling():
    """测试包含关系处理"""
    print("\n" + "=" * 80)
    print("测试包含关系处理")
    print("=" * 80)
    
    from akshare.api.analysis.chanlun_core import Bar, Direction
    
    # 创建测试数据：模拟包含关系
    bars = [
        Bar(dt=datetime(2024, 1, 1), open=100, close=110, high=115, low=95, symbol="TEST", index=0),
        Bar(dt=datetime(2024, 1, 2), open=110, close=105, high=112, low=100, symbol="TEST", index=1),  # 被包含
        Bar(dt=datetime(2024, 1, 3), open=105, close=115, high=120, low=103, symbol="TEST", index=2),
    ]
    
    analyzer = ChanlunAnalyzer(bars)
    
    print(f"\n原始 K 线: {len(analyzer.bars_raw)} 根")
    for bar in analyzer.bars_raw:
        print(f"  {bar.dt.strftime('%Y-%m-%d')}: 高={bar.high:.2f}, 低={bar.low:.2f}")
    
    print(f"\n合并后 K 线: {len(analyzer.bars_merged)} 根")
    for bar in analyzer.bars_merged:
        print(f"  {bar.dt.strftime('%Y-%m-%d')}: 高={bar.high:.2f}, 低={bar.low:.2f}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_basic_analysis()
    test_inclusion_handling()
