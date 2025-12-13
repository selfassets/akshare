"""
缠论分析核心模块

实现完整的缠论分析算法，包括：
- K线数据处理和包含关系处理
- 分型识别（顶分型、底分型）
- 笔识别（基于分型的笔）
- 线段识别（基于笔的线段）
- 中枢识别（价格重叠区间）
- 买卖点识别（背驰判断）

不依赖 czsc 库，完全独立实现。
"""

from typing import List, Optional, Literal, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import pandas as pd
import numpy as np


class Direction(Enum):
    """方向枚举"""
    UP = "up"  # 向上
    DOWN = "down"  # 向下


class FractalType(Enum):
    """分型类型"""
    TOP = "top"  # 顶分型
    BOTTOM = "bottom"  # 底分型


class TradePointType(Enum):
    """买卖点类型"""
    BUY_1 = "buy_1"  # 第一类买点
    BUY_2 = "buy_2"  # 第二类买点
    BUY_3 = "buy_3"  # 第三类买点
    SELL_1 = "sell_1"  # 第一类卖点
    SELL_2 = "sell_2"  # 第二类卖点
    SELL_3 = "sell_3"  # 第三类卖点


class TrendType(Enum):
    """走势类型"""
    TREND_UP = "trend_up"  # 趋势上涨（两个以上同向中枢）
    TREND_DOWN = "trend_down"  # 趋势下跌
    CONSOLIDATION = "consolidation"  # 盘整（单中枢）
    UNKNOWN = "unknown"  # 未知（数据不足）


@dataclass
class Bar:
    """K线数据类"""
    dt: datetime  # 时间
    open: float  # 开盘价
    close: float  # 收盘价
    high: float  # 最高价
    low: float  # 最低价
    vol: float = 0.0  # 成交量
    symbol: str = ""  # 品种代码
    index: int = 0  # 序号
    
    def __post_init__(self):
        """验证数据有效性"""
        if self.high < self.low:
            raise ValueError(f"高点 {self.high} 不能低于低点 {self.low}")
        if self.high < max(self.open, self.close):
            raise ValueError(f"高点 {self.high} 不能低于开盘价/收盘价")
        if self.low > min(self.open, self.close):
            raise ValueError(f"低点 {self.low} 不能高于开盘价/收盘价")
    
    @property
    def direction(self) -> Direction:
        """K线方向"""
        return Direction.UP if self.close >= self.open else Direction.DOWN


@dataclass
class Fractal:
    """分型数据类"""
    fractal_type: FractalType  # 分型类型
    dt: datetime  # 分型时间（中间K线的时间）
    high: float  # 分型高点
    low: float  # 分型低点
    power: float = 0.0  # 分型强度（可选）
    bars: List[Bar] = field(default_factory=list)  # 构成分型的K线（通常是3根）
    index: int = 0  # 在分型列表中的序号
    
    @property
    def price(self) -> float:
        """分型的关键价格：顶分型取高点，底分型取低点"""
        return self.high if self.fractal_type == FractalType.TOP else self.low


@dataclass
class Stroke:
    """笔数据类"""
    direction: Direction  # 笔的方向
    start_fractal: Fractal  # 起始分型
    end_fractal: Fractal  # 结束分型
    index: int = 0  # 在笔列表中的序号
    macd_area: float = 0.0  # MACD 面积（用于背驰判断）
    bar_start_idx: int = -1  # 起始K线在 bars_merged 中的索引
    bar_end_idx: int = -1  # 结束K线在 bars_merged 中的索引
    
    @property
    def start_dt(self) -> datetime:
        """笔的起始时间"""
        return self.start_fractal.dt
    
    @property
    def end_dt(self) -> datetime:
        """笔的结束时间"""
        return self.end_fractal.dt
    
    @property
    def start_price(self) -> float:
        """笔的起始价格"""
        return self.start_fractal.price
    
    @property
    def end_price(self) -> float:
        """笔的结束价格"""
        return self.end_fractal.price
    
    @property
    def high(self) -> float:
        """笔的最高价"""
        return max(self.start_fractal.high, self.end_fractal.high)
    
    @property
    def low(self) -> float:
        """笔的最低价"""
        return min(self.start_fractal.low, self.end_fractal.low)
    
    @property
    def power(self) -> float:
        """笔的力度（价格变化幅度）"""
        return abs(self.end_price - self.start_price)


@dataclass
class Segment:
    """线段数据类"""
    direction: Direction  # 线段方向
    strokes: List[Stroke]  # 构成线段的笔
    start_dt: datetime  # 起始时间
    end_dt: datetime  # 结束时间
    high: float  # 线段最高价
    low: float  # 线段最低价
    index: int = 0  # 在线段列表中的序号
    
    @property
    def start_price(self) -> float:
        """线段的起始价格：向上线段从低点开始，向下线段从高点开始"""
        return self.low if self.direction == Direction.UP else self.high
    
    @property
    def end_price(self) -> float:
        """线段的结束价格：向上线段到高点结束，向下线段到低点结束"""
        return self.high if self.direction == Direction.UP else self.low


@dataclass
class Pivot:
    """中枢数据类"""
    level: int  # 中枢级别（1=1分钟级别，2=5分钟级别，以此类推）
    direction: Direction  # 中枢方向（中枢前一笔的方向）
    high: float  # 中枢上沿
    low: float  # 中枢下沿
    start_dt: datetime  # 中枢开始时间
    end_dt: datetime  # 中枢结束时间
    strokes: List[Stroke] = field(default_factory=list)  # 构成中枢的笔
    index: int = 0  # 在中枢列表中的序号
    trend_type: TrendType = TrendType.UNKNOWN  # 中枢所在走势类型
    
    @property
    def center(self) -> float:
        """中枢中心价格"""
        return (self.high + self.low) / 2
    
    @property
    def amplitude(self) -> float:
        """中枢振幅"""
        return self.high - self.low


@dataclass
class TradePoint:
    """买卖点数据类"""
    point_type: TradePointType  # 买卖点类型
    dt: datetime  # 时间
    price: float  # 价格
    strength: float = 0.0  # 强度（0-1，基于价格的背驰程度）
    macd_strength: float = 0.0  # MACD 背驰强度（0-1）
    description: str = ""  # 描述
    index: int = 0  # 序号


class ChanlunAnalyzer:
    """缠论分析器"""
    
    def __init__(self, bars: List[Bar]):
        """
        初始化缠论分析器
        
        Args:
            bars: 原始K线列表
        """
        self.bars_raw = bars  # 原始K线
        self.bars_merged: List[Bar] = []  # 处理包含关系后的K线
        self.fractals: List[Fractal] = []  # 分型列表
        self.strokes: List[Stroke] = []  # 笔列表
        self.segments: List[Segment] = []  # 线段列表
        self.pivots: List[Pivot] = []  # 中枢列表
        self.trade_points: List[TradePoint] = []  # 买卖点列表
        
        # 执行分析
        self._analyze()
    
    def _analyze(self):
        """执行完整的缠论分析"""
        # 1. 处理包含关系
        self._merge_bars()
        
        # 2. 计算 MACD 指标
        self._calculate_macd()
        
        # 3. 识别分型
        self._identify_fractals()
        
        # 4. 识别笔
        self._identify_strokes()
        
        # 5. 计算笔的 MACD 面积
        self._calculate_stroke_macd_area()
        
        # 6. 识别线段（使用特征序列方法）
        self._identify_segments()
        
        # 7. 识别中枢
        self._identify_pivots()
        
        # 8. 识别趋势/盘整类型
        self._identify_trend_type()
        
        # 9. 识别买卖点
        self._identify_trade_points()
    
    def _merge_bars(self):
        """
        处理K线包含关系
        
        包含关系定义：
        - 如果 K1 的高低点完全包含 K2，或 K2 完全包含 K1，则存在包含关系
        - 处理方式：根据前一根K线的方向，合并K线
          - 向上：高点取两者最高，低点取两者较高的低点
          - 向下：低点取两者最低，高点取两者较低的高点
        """
        if len(self.bars_raw) < 2:
            self.bars_merged = self.bars_raw.copy()
            return
        
        merged = [self.bars_raw[0]]
        
        for i in range(1, len(self.bars_raw)):
            current = self.bars_raw[i]
            last = merged[-1]
            
            # 判断是否存在包含关系
            if self._has_inclusion(last, current):
                # 确定方向：基于前面的K线方向
                if len(merged) >= 2:
                    direction = merged[-2].direction
                else:
                    direction = last.direction
                
                # 根据方向合并K线
                if direction == Direction.UP:
                    # 向上：高点取最高，低点取高者
                    new_high = max(last.high, current.high)
                    new_low = max(last.low, current.low)
                    # 确保 open/close 在 high/low 范围内
                    new_open = max(min(last.open, new_high), new_low)
                    new_close = max(min(current.close, new_high), new_low)
                    merged_bar = Bar(
                        dt=current.dt,
                        open=new_open,
                        close=new_close,
                        high=new_high,
                        low=new_low,
                        vol=last.vol + current.vol,
                        symbol=current.symbol,
                        index=current.index
                    )
                else:
                    # 向下：低点取最低，高点取低者
                    new_high = min(last.high, current.high)
                    new_low = min(last.low, current.low)
                    # 确保 open/close 在 high/low 范围内
                    new_open = max(min(last.open, new_high), new_low)
                    new_close = max(min(current.close, new_high), new_low)
                    merged_bar = Bar(
                        dt=current.dt,
                        open=new_open,
                        close=new_close,
                        high=new_high,
                        low=new_low,
                        vol=last.vol + current.vol,
                        symbol=current.symbol,
                        index=current.index
                    )
                merged[-1] = merged_bar
            else:
                merged.append(current)
        
        self.bars_merged = merged
    
    def _has_inclusion(self, bar1: Bar, bar2: Bar) -> bool:
        """
        判断两根K线是否存在包含关系
        
        Args:
            bar1: 第一根K线
            bar2: 第二根K线
        
        Returns:
            是否存在包含关系
        """
        # bar1 包含 bar2
        if bar1.high >= bar2.high and bar1.low <= bar2.low:
            return True
        # bar2 包含 bar1
        if bar2.high >= bar1.high and bar2.low <= bar1.low:
            return True
        return False
    
    def _calculate_macd(self, short: int = 12, long: int = 26, signal: int = 9):
        """
        计算 MACD 指标
        
        Args:
            short: 短期 EMA 周期（默认12）
            long: 长期 EMA 周期（默认26）
            signal: 信号线周期（默认9）
        """
        if len(self.bars_merged) < long:
            self.macd_dif = []
            self.macd_dea = []
            self.macd_hist = []
            return
        
        # 提取收盘价
        closes = np.array([bar.close for bar in self.bars_merged])
        
        # 计算 EMA
        def ema(data: np.ndarray, period: int) -> np.ndarray:
            alpha = 2 / (period + 1)
            result = np.zeros_like(data)
            result[0] = data[0]
            for i in range(1, len(data)):
                result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]
            return result
        
        ema_short = ema(closes, short)
        ema_long = ema(closes, long)
        
        # DIF = 短期EMA - 长期EMA
        dif = ema_short - ema_long
        
        # DEA = DIF 的 signal 周期 EMA
        dea = ema(dif, signal)
        
        # MACD 柱状图 = (DIF - DEA) * 2
        macd_hist = (dif - dea) * 2
        
        self.macd_dif = dif.tolist()
        self.macd_dea = dea.tolist()
        self.macd_hist = macd_hist.tolist()
    
    def _calculate_stroke_macd_area(self):
        """
        计算每一笔的 MACD 面积
        
        MACD 面积用于辅助背驰判断：
        - 比较两段同向走势的 MACD 柱状图面积
        - 如果后一段面积明显小于前一段，可能是背驰
        """
        if not hasattr(self, 'macd_hist') or not self.macd_hist:
            return
        
        for stroke in self.strokes:
            # 获取笔对应的 K 线索引范围
            start_idx = stroke.bar_start_idx
            end_idx = stroke.bar_end_idx
            
            if start_idx < 0 or end_idx < 0 or start_idx >= len(self.macd_hist):
                continue
            
            end_idx = min(end_idx, len(self.macd_hist) - 1)
            
            # 计算 MACD 面积（取绝对值之和）
            macd_area = sum(abs(self.macd_hist[i]) for i in range(start_idx, end_idx + 1))
            stroke.macd_area = macd_area
    
    def _identify_fractals(self):
        """
        识别分型
        
        分型定义（使用处理过包含关系的K线）：
        - 顶分型：第2根K线高点严格高于第1、3根K线的高点
        - 底分型：第2根K线低点严格低于第1、3根K线的低点
        
        注意：处理包含关系后的K线不存在包含关系，因此只需检查高点或低点
        """
        if len(self.bars_merged) < 3:
            return
        
        fractals = []
        i = 0
        
        while i <= len(self.bars_merged) - 3:
            bar1 = self.bars_merged[i]
            bar2 = self.bars_merged[i + 1]
            bar3 = self.bars_merged[i + 2]
            
            # 检查顶分型：中间K线高点严格最高
            if bar2.high > bar1.high and bar2.high > bar3.high:
                # 计算分型强度：高点突出程度
                power = min(bar2.high - bar1.high, bar2.high - bar3.high)
                fractal = Fractal(
                    fractal_type=FractalType.TOP,
                    dt=bar2.dt,
                    high=bar2.high,
                    low=bar2.low,
                    power=power,
                    bars=[bar1, bar2, bar3],
                    index=len(fractals)
                )
                fractals.append(fractal)
                i += 2  # 跳过已识别的分型
                continue
            
            # 检查底分型：中间K线低点严格最低
            if bar2.low < bar1.low and bar2.low < bar3.low:
                # 计算分型强度：低点突出程度
                power = min(bar1.low - bar2.low, bar3.low - bar2.low)
                fractal = Fractal(
                    fractal_type=FractalType.BOTTOM,
                    dt=bar2.dt,
                    high=bar2.high,
                    low=bar2.low,
                    power=power,
                    bars=[bar1, bar2, bar3],
                    index=len(fractals)
                )
                fractals.append(fractal)
                i += 2  # 跳过已识别的分型
                continue
            
            i += 1
        
        self.fractals = fractals
    
    def _identify_strokes(self):
        """
        识别笔
        
        笔的定义：
        - 由顶分型和底分型交替构成
        - 相邻两个分型之间至少有一根独立K线（处理包含关系后）
        - 向上笔：底分型 -> 顶分型，且顶分型高点 > 底分型高点
        - 向下笔：顶分型 -> 底分型，且底分型低点 < 顶分型低点
        
        使用更宽松的规则确保能识别出更多笔
        """
        if len(self.fractals) < 2:
            return
        
        strokes = []
        
        # 找到第一个有效的分型作为起点
        current_start = self._find_first_valid_start()
        if current_start is None:
            # 如果找不到有效起点，使用第一个分型
            current_start = self.fractals[0]
        
        # 记录当前分型索引
        current_start_idx = self.fractals.index(current_start)
        i = current_start_idx + 1
        
        while i < len(self.fractals):
            candidate_end = self.fractals[i]
            
            # 必须是不同类型的分型
            if candidate_end.fractal_type == current_start.fractal_type:
                # 同类型：更新起始分型为更极端的那个（但只有在还没形成任何笔时才更新）
                if current_start.fractal_type == FractalType.TOP:
                    if candidate_end.high > current_start.high:
                        current_start = candidate_end
                        current_start_idx = i
                else:
                    if candidate_end.low < current_start.low:
                        current_start = candidate_end
                        current_start_idx = i
                i += 1
                continue
            
            # 检查是否有足够的K线间隔（放宽到3根K线）
            if not self._has_enough_bars_between(current_start, candidate_end):
                i += 1
                continue
            
            # 验证价格关系
            valid_price = False
            if current_start.fractal_type == FractalType.BOTTOM:
                # 向上笔：终点高点必须高于起点高点
                if candidate_end.high > current_start.high:
                    valid_price = True
                    direction = Direction.UP
            else:
                # 向下笔：终点低点必须低于起点低点
                if candidate_end.low < current_start.low:
                    valid_price = True
                    direction = Direction.DOWN
            
            if not valid_price:
                i += 1
                continue
            
            # 向前看：是否有更好的结束分型？（在遇到不同类型分型之前）
            best_end = candidate_end
            best_end_idx = i
            for j in range(i + 1, min(i + 10, len(self.fractals))):  # 限制向前看的范围
                next_fractal = self.fractals[j]
                if next_fractal.fractal_type != candidate_end.fractal_type:
                    break  # 遇到不同类型，停止搜索
                # 检查是否更极端
                if direction == Direction.UP:
                    if next_fractal.high > best_end.high:
                        best_end = next_fractal
                        best_end_idx = j
                else:
                    if next_fractal.low < best_end.low:
                        best_end = next_fractal
                        best_end_idx = j
            
            # 创建笔（包含 K 线索引用于 MACD 计算）
            start_idx = self._get_bar_index(current_start.dt)
            end_idx = self._get_bar_index(best_end.dt)
            stroke = Stroke(
                direction=direction,
                start_fractal=current_start,
                end_fractal=best_end,
                index=len(strokes),
                bar_start_idx=start_idx,
                bar_end_idx=end_idx
            )
            strokes.append(stroke)
            
            # 以当前笔的结束分型作为下一笔的起始分型
            current_start = best_end
            current_start_idx = best_end_idx
            i = best_end_idx + 1
        
        self.strokes = strokes
    
    def _find_first_valid_start(self) -> Optional[Fractal]:
        """
        找到第一个有效的起始分型
        
        策略：找到第一个能与后续分型形成笔的分型
        """
        for i, fractal in enumerate(self.fractals):
            # 检查是否能与后续任意分型形成有效笔
            for j in range(i + 1, min(i + 15, len(self.fractals))):  # 限制搜索范围
                next_fractal = self.fractals[j]
                if next_fractal.fractal_type != fractal.fractal_type:
                    if self._has_enough_bars_between(fractal, next_fractal):
                        # 验证价格关系
                        if fractal.fractal_type == FractalType.BOTTOM:
                            if next_fractal.high > fractal.high:
                                return fractal
                        else:
                            if next_fractal.low < fractal.low:
                                return fractal
                    # 不满足条件继续找其他分型
                    continue
        return self.fractals[0] if self.fractals else None
    
    def _has_enough_bars_between(self, f1: Fractal, f2: Fractal) -> bool:
        """
        检查两个分型之间是否有足够的K线
        
        标准：两个分型之间至少有1根独立K线（不被两个分型共用）
        使用分型的索引来判断，放宽标准
        """
        # 使用分型的 index 属性来判断间隔
        # 分型索引差 >= 1 表示不是连续的分型（放宽标准）
        if abs(f2.index - f1.index) >= 1:
            return True
        
        # 如果分型有关联的 bars，使用 bars 的 index 来判断
        if f1.bars and f2.bars:
            # 取中间K线的索引（分型由3根K线组成，中间那根是分型位置）
            f1_bar_index = f1.bars[1].index if len(f1.bars) >= 2 else f1.bars[0].index
            f2_bar_index = f2.bars[1].index if len(f2.bars) >= 2 else f2.bars[0].index
            # K线索引差 >= 3 表示有足够间隔
            return abs(f2_bar_index - f1_bar_index) >= 3
        
        # 备用方案：通过日期查找
        f1_dt = f1.dt
        f2_dt = f2.dt
        
        f1_index = -1
        f2_index = -1
        
        for idx, bar in enumerate(self.bars_merged):
            if bar.dt == f1_dt:
                f1_index = idx
            if bar.dt == f2_dt:
                f2_index = idx
        
        if f1_index == -1 or f2_index == -1:
            # 如果找不到，默认返回True允许形成笔（放宽限制）
            return True
        
        # 放宽标准：索引差 >= 3 表示有足够的间隔
        return abs(f2_index - f1_index) >= 3
    
    def _get_bar_index(self, dt: datetime) -> int:
        """
        获取指定时间的 K 线在 bars_merged 中的索引
        
        Args:
            dt: K 线时间
        
        Returns:
            K 线索引，找不到返回 -1
        """
        for idx, bar in enumerate(self.bars_merged):
            if bar.dt == dt:
                return idx
        return -1
    
    def _identify_segments(self):
        """
        识别线段（使用特征序列方法）
        
        线段定义（标准缠论）：
        - 至少由3笔构成
        - 线段方向由第一笔确定
        - 线段的结束由特征序列分型确定
        
        特征序列方法：
        1. 将同向的笔抽象为特征序列元素（用笔的高低点代表）
        2. 在特征序列上处理包含关系
        3. 在特征序列上识别顶/底分型
        4. 分型出现则线段结束
        """
        if len(self.strokes) < 3:
            return
        
        segments = []
        i = 0
        
        while i < len(self.strokes):
            # 尝试从位置 i 开始识别一条线段
            segment_result = self._identify_one_segment(i)
            
            if segment_result is not None:
                segment, next_i = segment_result
                segments.append(segment)
                segment.index = len(segments) - 1
                i = next_i
            else:
                i += 1
        
        self.segments = segments
    
    def _identify_one_segment(self, start_idx: int) -> Optional[Tuple[Segment, int]]:
        """
        从指定位置开始识别一条线段
        
        Args:
            start_idx: 起始笔索引
        
        Returns:
            (线段, 下一个起始位置) 或 None
        """
        if start_idx >= len(self.strokes):
            return None
        
        # 线段方向由第一笔确定
        direction = self.strokes[start_idx].direction
        
        # 收集所有笔直到识别出线段结束
        strokes_collected = []
        j = start_idx
        
        while j < len(self.strokes):
            strokes_collected.append(self.strokes[j])
            
            # 至少需要3笔才能形成线段
            if len(strokes_collected) >= 3:
                # 构建特征序列并检查是否有分型
                feature_fractal = self._check_feature_sequence_fractal(strokes_collected, direction)
                
                if feature_fractal is not None:
                    # 找到特征序列分型，线段结束
                    # 线段结束点是分型对应的笔
                    end_stroke_idx = feature_fractal
                    strokes_in_segment = strokes_collected[:end_stroke_idx + 1]
                    
                    if len(strokes_in_segment) >= 3:
                        segment = Segment(
                            direction=direction,
                            strokes=strokes_in_segment,
                            start_dt=strokes_in_segment[0].start_dt,
                            end_dt=strokes_in_segment[-1].end_dt,
                            high=max(s.high for s in strokes_in_segment),
                            low=min(s.low for s in strokes_in_segment),
                            index=0
                        )
                        # 下一个线段从当前线段的最后一笔开始
                        return (segment, start_idx + len(strokes_in_segment) - 1)
            
            j += 1
            
            # 防止线段过长
            if len(strokes_collected) >= 25:
                break
        
        # 如果没有找到特征序列分型但有足够的笔，也创建线段
        if len(strokes_collected) >= 3:
            segment = Segment(
                direction=direction,
                strokes=strokes_collected,
                start_dt=strokes_collected[0].start_dt,
                end_dt=strokes_collected[-1].end_dt,
                high=max(s.high for s in strokes_collected),
                low=min(s.low for s in strokes_collected),
                index=0
            )
            return (segment, start_idx + len(strokes_collected))
        
        return None
    
    def _check_feature_sequence_fractal(self, strokes: List[Stroke], seg_direction: Direction) -> Optional[int]:
        """
        检查笔序列中的特征序列是否形成分型
        
        特征序列定义：
        - 向上线段：取所有向下笔作为特征序列元素
        - 向下线段：取所有向上笔作为特征序列元素
        
        Args:
            strokes: 笔列表
            seg_direction: 线段方向
        
        Returns:
            特征序列分型对应的笔索引，None 表示未找到
        """
        # 提取特征序列元素（与线段方向相反的笔）
        feature_elements = []
        for idx, stroke in enumerate(strokes):
            if stroke.direction != seg_direction:
                feature_elements.append({
                    'idx': idx,
                    'high': stroke.high,
                    'low': stroke.low,
                    'stroke': stroke
                })
        
        if len(feature_elements) < 3:
            return None
        
        # 处理特征序列的包含关系
        merged_features = self._merge_feature_sequence(feature_elements, seg_direction)
        
        if len(merged_features) < 3:
            return None
        
        # 在合并后的特征序列上识别分型
        for i in range(len(merged_features) - 2):
            f1, f2, f3 = merged_features[i], merged_features[i + 1], merged_features[i + 2]
            
            if seg_direction == Direction.UP:
                # 向上线段找底分型（特征序列的底分型表示线段结束）
                if f2['low'] < f1['low'] and f2['low'] < f3['low']:
                    # 返回底分型中间元素对应的原始笔索引
                    return f2['idx']
            else:
                # 向下线段找顶分型
                if f2['high'] > f1['high'] and f2['high'] > f3['high']:
                    return f2['idx']
        
        return None
    
    def _merge_feature_sequence(self, features: List[Dict], seg_direction: Direction) -> List[Dict]:
        """
        处理特征序列的包含关系
        
        Args:
            features: 特征序列元素列表
            seg_direction: 线段方向
        
        Returns:
            处理包含关系后的特征序列
        """
        if len(features) < 2:
            return features
        
        merged = [features[0].copy()]
        
        for i in range(1, len(features)):
            current = features[i]
            last = merged[-1]
            
            # 检查包含关系
            has_inclusion = (
                (last['high'] >= current['high'] and last['low'] <= current['low']) or
                (current['high'] >= last['high'] and current['low'] <= last['low'])
            )
            
            if has_inclusion:
                # 根据线段方向处理包含
                if seg_direction == Direction.UP:
                    # 向上线段：特征序列向下，取低点更低者
                    if current['low'] < last['low']:
                        merged[-1] = {
                            'idx': current['idx'],
                            'high': min(last['high'], current['high']),
                            'low': current['low'],
                            'stroke': current['stroke']
                        }
                else:
                    # 向下线段：特征序列向上，取高点更高者
                    if current['high'] > last['high']:
                        merged[-1] = {
                            'idx': current['idx'],
                            'high': current['high'],
                            'low': max(last['low'], current['low']),
                            'stroke': current['stroke']
                        }
            else:
                merged.append(current.copy())
        
        return merged
    
    def _identify_pivots(self):
        """
        识别中枢
        
        中枢定义：
        - 至少3笔重叠部分构成中枢
        - 中枢区间 = 重叠部分的高低点
        - 简化实现：基于连续的笔找出价格重叠区间
        """
        if len(self.strokes) < 3:
            return
        
        pivots = []
        i = 0
        
        while i <= len(self.strokes) - 3:
            # 取3笔检查是否有重叠
            stroke1 = self.strokes[i]
            stroke2 = self.strokes[i + 1]
            stroke3 = self.strokes[i + 2]
            
            # 计算重叠区间
            overlap_high = min(stroke1.high, stroke2.high, stroke3.high)
            overlap_low = max(stroke1.low, stroke2.low, stroke3.low)
            
            # 如果有重叠，形成中枢
            if overlap_high > overlap_low:
                # 扩展中枢：继续向后找更多重叠的笔
                j = i + 3
                strokes_in_pivot = [stroke1, stroke2, stroke3]
                
                while j < len(self.strokes):
                    next_stroke = self.strokes[j]
                    # 检查是否在中枢区间内
                    if next_stroke.low <= overlap_high and next_stroke.high >= overlap_low:
                        strokes_in_pivot.append(next_stroke)
                        # 更新中枢区间
                        overlap_high = min(overlap_high, next_stroke.high)
                        overlap_low = max(overlap_low, next_stroke.low)
                        j += 1
                    else:
                        break
                
                # 创建中枢
                pivot = Pivot(
                    level=1,  # 简化实现，统一为1级
                    direction=stroke1.direction,
                    high=overlap_high,
                    low=overlap_low,
                    start_dt=strokes_in_pivot[0].start_dt,
                    end_dt=strokes_in_pivot[-1].end_dt,
                    strokes=strokes_in_pivot,
                    index=len(pivots)
                )
                pivots.append(pivot)
                i = j
            else:
                i += 1
        
        self.pivots = pivots
    
    def _identify_trend_type(self):
        """
        识别走势类型（趋势/盘整）
        
        走势类型定义：
        - 趋势上涨：存在两个以上向上的中枢，且后一个中枢高于前一个
        - 趋势下跌：存在两个以上向下的中枢，且后一个中枢低于前一个
        - 盘整：单中枢或中枢之间有重叠
        """
        if len(self.pivots) < 1:
            return
        
        # 如果只有一个中枢，标记为盘整
        if len(self.pivots) == 1:
            self.pivots[0].trend_type = TrendType.CONSOLIDATION
            return
        
        # 分析相邻中枢的关系
        for i in range(len(self.pivots)):
            if i == 0:
                # 第一个中枢暂时标记为未知
                self.pivots[i].trend_type = TrendType.UNKNOWN
                continue
            
            prev_pivot = self.pivots[i - 1]
            curr_pivot = self.pivots[i]
            
            # 检查中枢是否有重叠
            has_overlap = (
                curr_pivot.low <= prev_pivot.high and 
                curr_pivot.high >= prev_pivot.low
            )
            
            if has_overlap:
                # 重叠则为盘整
                curr_pivot.trend_type = TrendType.CONSOLIDATION
                prev_pivot.trend_type = TrendType.CONSOLIDATION
            else:
                # 不重叠则为趋势
                if curr_pivot.center > prev_pivot.center:
                    # 中枢抬高，趋势上涨
                    curr_pivot.trend_type = TrendType.TREND_UP
                    if prev_pivot.trend_type == TrendType.UNKNOWN:
                        prev_pivot.trend_type = TrendType.TREND_UP
                else:
                    # 中枢降低，趋势下跌
                    curr_pivot.trend_type = TrendType.TREND_DOWN
                    if prev_pivot.trend_type == TrendType.UNKNOWN:
                        prev_pivot.trend_type = TrendType.TREND_DOWN
    
    def _identify_trade_points(self):
        """
        识别买卖点
        
        买卖点类型：
        - 第一类买点：下跌趋势中出现底背驰
        - 第二类买点：一买后的回调不创新低
        - 第三类买点：中枢突破向上后回踩不进中枢
        - 第一类卖点：上涨趋势中出现顶背驰
        - 第二类卖点：一卖后的反弹不创新高
        - 第三类卖点：中枢突破向下后反抽不进中枢
        """
        trade_points = []
        
        # 1. 基于笔识别一类买卖点（背驰判断）
        self._identify_first_class_points(trade_points)
        
        # 2. 基于一类买卖点识别二类买卖点
        self._identify_second_class_points(trade_points)
        
        # 3. 基于中枢识别三类买卖点
        self._identify_third_class_points(trade_points)
        
        # 按时间排序
        trade_points.sort(key=lambda p: p.dt)
        for i, tp in enumerate(trade_points):
            tp.index = i
        
        self.trade_points = trade_points
    
    def _identify_first_class_points(self, trade_points: List[TradePoint]):
        """
        识别第一类买卖点（基于背驰）
        
        背驰判定（增强版）：
        - 价格背驰：后一段走势创新高/新低，但力度减弱
        - MACD 背驰：后一段 MACD 面积明显小于前一段
        - 综合判断：价格和 MACD 双重确认提高可靠性
        """
        if len(self.strokes) < 5:
            return
        
        for i in range(4, len(self.strokes)):
            current = self.strokes[i]
            
            # 找前面同向的笔进行比较
            prev_same_dir = None
            for j in range(i - 2, -1, -2):  # 同向笔间隔2
                if j >= 0 and self.strokes[j].direction == current.direction:
                    prev_same_dir = self.strokes[j]
                    break
            
            if prev_same_dir is None:
                continue
            
            # 计算价格力度（幅度）
            current_power = current.power
            prev_power = prev_same_dir.power
            
            # 计算 MACD 面积比
            current_macd = current.macd_area if current.macd_area > 0 else 0.001
            prev_macd = prev_same_dir.macd_area if prev_same_dir.macd_area > 0 else 0.001
            
            # 价格背驰判断：当前笔力度明显小于前一同向笔
            price_ratio = current_power / max(prev_power, 0.001)
            is_price_divergence = price_ratio < 0.8
            price_strength = 1 - price_ratio if is_price_divergence else 0
            
            # MACD 背驰判断
            macd_ratio = current_macd / max(prev_macd, 0.001)
            is_macd_divergence = macd_ratio < 0.8
            macd_strength = 1 - macd_ratio if is_macd_divergence else 0
            
            # 综合判断：至少一个背驰，双重背驰可靠性更高
            if not (is_price_divergence or is_macd_divergence):
                continue
            
            # 判断是否创新高/新低
            if current.direction == Direction.DOWN:
                # 第一类买点：向下笔出现背驰，且创新低
                is_new_low = current.end_price <= prev_same_dir.end_price
                if is_new_low:
                    # 综合强度
                    combined_strength = 0.5
                    if is_price_divergence and is_macd_divergence:
                        combined_strength = 0.8 + min(price_strength, macd_strength) * 0.15
                    elif is_price_divergence:
                        combined_strength = 0.6 + price_strength * 0.2
                    elif is_macd_divergence:
                        combined_strength = 0.55 + macd_strength * 0.2
                    
                    divergence_desc = []
                    if is_price_divergence:
                        divergence_desc.append(f"价格力度比={price_ratio:.2f}")
                    if is_macd_divergence:
                        divergence_desc.append(f"MACD面积比={macd_ratio:.2f}")
                    
                    trade_point = TradePoint(
                        point_type=TradePointType.BUY_1,
                        dt=current.end_dt,
                        price=current.end_price,
                        strength=min(0.95, combined_strength),
                        macd_strength=macd_strength,
                        description=f"第一类买点：底背驰（{', '.join(divergence_desc)}）",
                        index=len(trade_points)
                    )
                    trade_points.append(trade_point)
            
            elif current.direction == Direction.UP:
                # 第一类卖点：向上笔出现背驰，且创新高
                is_new_high = current.end_price >= prev_same_dir.end_price
                if is_new_high:
                    # 综合强度
                    combined_strength = 0.5
                    if is_price_divergence and is_macd_divergence:
                        combined_strength = 0.8 + min(price_strength, macd_strength) * 0.15
                    elif is_price_divergence:
                        combined_strength = 0.6 + price_strength * 0.2
                    elif is_macd_divergence:
                        combined_strength = 0.55 + macd_strength * 0.2
                    
                    divergence_desc = []
                    if is_price_divergence:
                        divergence_desc.append(f"价格力度比={price_ratio:.2f}")
                    if is_macd_divergence:
                        divergence_desc.append(f"MACD面积比={macd_ratio:.2f}")
                    
                    trade_point = TradePoint(
                        point_type=TradePointType.SELL_1,
                        dt=current.end_dt,
                        price=current.end_price,
                        strength=min(0.95, combined_strength),
                        macd_strength=macd_strength,
                        description=f"第一类卖点：顶背驰（{', '.join(divergence_desc)}）",
                        index=len(trade_points)
                    )
                    trade_points.append(trade_point)
    
    def _identify_second_class_points(self, trade_points: List[TradePoint]):
        """
        识别第二类买卖点
        
        二买：一买之后，价格回调但不创新低
        二卖：一卖之后，价格反弹但不创新高
        """
        # 找出所有一类买卖点
        first_buys = [tp for tp in trade_points if tp.point_type == TradePointType.BUY_1]
        first_sells = [tp for tp in trade_points if tp.point_type == TradePointType.SELL_1]
        
        # 识别二买
        for buy1 in first_buys:
            # 找一买对应的笔索引
            buy1_stroke_idx = -1
            for idx, stroke in enumerate(self.strokes):
                if stroke.end_dt == buy1.dt:
                    buy1_stroke_idx = idx
                    break
            
            if buy1_stroke_idx < 0 or buy1_stroke_idx + 2 >= len(self.strokes):
                continue
            
            # 一买后的第二笔（回调笔，向下）
            pullback = self.strokes[buy1_stroke_idx + 2] if buy1_stroke_idx + 2 < len(self.strokes) else None
            
            if pullback and pullback.direction == Direction.DOWN:
                # 回调不创新低
                if pullback.end_price > buy1.price:
                    trade_point = TradePoint(
                        point_type=TradePointType.BUY_2,
                        dt=pullback.end_dt,
                        price=pullback.end_price,
                        strength=0.75,
                        description="第二类买点：一买后回调不创新低",
                        index=len(trade_points)
                    )
                    trade_points.append(trade_point)
        
        # 识别二卖
        for sell1 in first_sells:
            # 找一卖对应的笔索引
            sell1_stroke_idx = -1
            for idx, stroke in enumerate(self.strokes):
                if stroke.end_dt == sell1.dt:
                    sell1_stroke_idx = idx
                    break
            
            if sell1_stroke_idx < 0 or sell1_stroke_idx + 2 >= len(self.strokes):
                continue
            
            # 一卖后的第二笔（反弹笔，向上）
            bounce = self.strokes[sell1_stroke_idx + 2] if sell1_stroke_idx + 2 < len(self.strokes) else None
            
            if bounce and bounce.direction == Direction.UP:
                # 反弹不创新高
                if bounce.end_price < sell1.price:
                    trade_point = TradePoint(
                        point_type=TradePointType.SELL_2,
                        dt=bounce.end_dt,
                        price=bounce.end_price,
                        strength=0.75,
                        description="第二类卖点：一卖后反弹不创新高",
                        index=len(trade_points)
                    )
                    trade_points.append(trade_point)
    
    def _identify_third_class_points(self, trade_points: List[TradePoint]):
        """
        识别第三类买卖点
        
        三买：向上离开中枢后，回踩不进入中枢区间
        三卖：向下离开中枢后，反抽不进入中枢区间
        """
        for pivot in self.pivots:
            # 找中枢结束时对应的笔索引
            pivot_end_index = -1
            for j, stroke in enumerate(self.strokes):
                if stroke.end_dt == pivot.end_dt:
                    pivot_end_index = j
                    break
            
            if pivot_end_index < 0 or pivot_end_index + 2 >= len(self.strokes):
                continue
            
            # 离开中枢的笔
            leave_stroke = self.strokes[pivot_end_index + 1] if pivot_end_index + 1 < len(self.strokes) else None
            # 回踩/反抽的笔
            return_stroke = self.strokes[pivot_end_index + 2] if pivot_end_index + 2 < len(self.strokes) else None
            
            if leave_stroke is None or return_stroke is None:
                continue
            
            # 三买：向上离开中枢（离开笔的低点高于中枢上沿），回踩不进中枢
            if leave_stroke.direction == Direction.UP and leave_stroke.low > pivot.high:
                if return_stroke.direction == Direction.DOWN and return_stroke.low > pivot.high:
                    trade_point = TradePoint(
                        point_type=TradePointType.BUY_3,
                        dt=return_stroke.end_dt,
                        price=return_stroke.end_price,
                        strength=0.7,
                        description="第三类买点：向上突破中枢后回踩不进中枢",
                        index=len(trade_points)
                    )
                    trade_points.append(trade_point)
            
            # 三卖：向下离开中枢（离开笔的高点低于中枢下沿），反抽不进中枢
            if leave_stroke.direction == Direction.DOWN and leave_stroke.high < pivot.low:
                if return_stroke.direction == Direction.UP and return_stroke.high < pivot.low:
                    trade_point = TradePoint(
                        point_type=TradePointType.SELL_3,
                        dt=return_stroke.end_dt,
                        price=return_stroke.end_price,
                        strength=0.7,
                        description="第三类卖点：向下突破中枢后反抽不进中枢",
                        index=len(trade_points)
                    )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式，用于API返回
        
        Returns:
            包含所有分析结果的字典
        """
        return {
            "bars_raw": [
                {
                    "dt": bar.dt.isoformat(),
                    "open": bar.open,
                    "close": bar.close,
                    "high": bar.high,
                    "low": bar.low,
                    "vol": bar.vol,
                }
                for bar in self.bars_raw  # 返回全部数据
            ],
            "bars_merged": [
                {
                    "dt": bar.dt.isoformat(),
                    "open": bar.open,
                    "close": bar.close,
                    "high": bar.high,
                    "low": bar.low,
                    "vol": bar.vol,
                }
                for bar in self.bars_merged  # 返回全部数据
            ],
            "fractals": [
                {
                    "type": fractal.fractal_type.value,
                    "dt": fractal.dt.isoformat(),
                    "high": fractal.high,
                    "low": fractal.low,
                    "price": fractal.price,
                }
                for fractal in self.fractals
            ],
            "strokes": [
                {
                    "direction": stroke.direction.value,
                    "start_dt": stroke.start_dt.isoformat(),
                    "end_dt": stroke.end_dt.isoformat(),
                    "start_price": stroke.start_price,
                    "end_price": stroke.end_price,
                    "high": stroke.high,
                    "low": stroke.low,
                    "power": stroke.power,
                    "macd_area": stroke.macd_area,  # 新增
                }
                for stroke in self.strokes
            ],
            "segments": [
                {
                    "direction": segment.direction.value,
                    "start_dt": segment.start_dt.isoformat(),
                    "end_dt": segment.end_dt.isoformat(),
                    "start_price": segment.start_price,
                    "end_price": segment.end_price,
                    "high": segment.high,
                    "low": segment.low,
                    "stroke_count": len(segment.strokes),
                }
                for segment in self.segments
            ],
            "pivots": [
                {
                    "level": pivot.level,
                    "direction": pivot.direction.value,
                    "high": pivot.high,
                    "low": pivot.low,
                    "center": pivot.center,
                    "amplitude": pivot.amplitude,
                    "start_dt": pivot.start_dt.isoformat(),
                    "end_dt": pivot.end_dt.isoformat(),
                    "stroke_count": len(pivot.strokes),
                    "trend_type": pivot.trend_type.value,  # 新增
                }
                for pivot in self.pivots
            ],
            "trade_points": [
                {
                    "type": point.point_type.value,
                    "dt": point.dt.isoformat(),
                    "price": point.price,
                    "strength": point.strength,
                    "macd_strength": point.macd_strength,  # 新增
                    "description": point.description,
                }
                for point in self.trade_points
            ],
        }


def create_bars_from_dataframe(df: pd.DataFrame, symbol: str = "") -> List[Bar]:
    """
    从 DataFrame 创建 Bar 列表
    
    Args:
        df: K线数据 DataFrame，需要包含 dt/日期, open/开盘价, close/收盘价, high/最高价, low/最低价 等列
        symbol: 品种代码
    
    Returns:
        Bar 列表
    """
    bars = []
    
    # 识别列名
    date_col = None
    for col in ['dt', '日期', 'date', 'datetime', 'trading_date']:
        if col in df.columns:
            date_col = col
            break
    
    open_col = None
    for col in ['open', '开盘价', 'open_price']:
        if col in df.columns:
            open_col = col
            break
    
    close_col = None
    for col in ['close', '收盘价', 'close_price']:
        if col in df.columns:
            close_col = col
            break
    
    high_col = None
    for col in ['high', '最高价', 'high_price']:
        if col in df.columns:
            high_col = col
            break
    
    low_col = None
    for col in ['low', '最低价', 'low_price']:
        if col in df.columns:
            low_col = col
            break
    
    vol_col = None
    for col in ['vol', 'volume', '成交量']:
        if col in df.columns:
            vol_col = col
            break
    
    # 检查必需列
    if not all([date_col, open_col, close_col, high_col, low_col]):
        raise ValueError(f"DataFrame 缺少必需的列。现有列: {df.columns.tolist()}")
    
    # 转换数据
    for idx, row in df.iterrows():
        try:
            dt = row[date_col]
            if not isinstance(dt, datetime):
                dt = pd.to_datetime(dt)
            
            bar = Bar(
                dt=dt,
                open=float(row[open_col]),
                close=float(row[close_col]),
                high=float(row[high_col]),
                low=float(row[low_col]),
                vol=float(row[vol_col]) if vol_col and pd.notna(row[vol_col]) else 0.0,
                symbol=symbol,
                index=idx if isinstance(idx, int) else len(bars)
            )
            bars.append(bar)
        except Exception as e:
            # 跳过无效数据
            continue
    
    return bars


class MultiLevelAnalyzer:
    """
    多级别缠论分析器
    
    实现多级别递归分析，支持：
    - 将低级别的线段作为高级别的笔
    - 区间套买卖点识别
    """
    
    def __init__(self, bars: List[Bar], levels: int = 3):
        """
        初始化多级别分析器
        
        Args:
            bars: 最低级别 K 线
            levels: 分析级别数（向上递归，默认3级）
        """
        self.bars = bars
        self.levels = min(max(levels, 1), 5)  # 限制1-5级
        self.analyzers: Dict[int, ChanlunAnalyzer] = {}
        self.nested_trade_points: List[TradePoint] = []
        
        # 执行多级别分析
        self._analyze()
    
    def _analyze(self):
        """执行多级别递归分析"""
        # 第1级：原始K线分析
        self.analyzers[1] = ChanlunAnalyzer(self.bars)
        
        # 递归分析更高级别
        for level in range(2, self.levels + 1):
            prev_analyzer = self.analyzers[level - 1]
            
            # 使用上一级别的线段构建当前级别的 K 线
            higher_bars = self._segments_to_bars(prev_analyzer.segments, level)
            
            if len(higher_bars) < 3:
                # 数据不足，停止递归
                break
            
            self.analyzers[level] = ChanlunAnalyzer(higher_bars)
        
        # 寻找区间套买卖点
        self._find_nested_trade_points()
    
    def _segments_to_bars(self, segments: List[Segment], level: int) -> List[Bar]:
        """
        将线段转换为 K 线（用于高级别分析）
        
        Args:
            segments: 线段列表
            level: 当前级别
        
        Returns:
            K 线列表
        """
        bars = []
        for i, seg in enumerate(segments):
            # 用线段的起止时间和高低点构造 K 线
            if seg.direction == Direction.UP:
                bar = Bar(
                    dt=seg.end_dt,
                    open=seg.low,
                    close=seg.high,
                    high=seg.high,
                    low=seg.low,
                    vol=0.0,
                    symbol=f"L{level}",
                    index=i
                )
            else:
                bar = Bar(
                    dt=seg.end_dt,
                    open=seg.high,
                    close=seg.low,
                    high=seg.high,
                    low=seg.low,
                    vol=0.0,
                    symbol=f"L{level}",
                    index=i
                )
            bars.append(bar)
        return bars
    
    def _find_nested_trade_points(self):
        """
        寻找区间套买卖点
        
        区间套：当多个级别同时出现买卖点信号时，形成更可靠的买卖点
        """
        nested_points = []
        
        # 获取所有级别的买卖点
        all_trade_points: Dict[int, List[TradePoint]] = {}
        for level, analyzer in self.analyzers.items():
            all_trade_points[level] = analyzer.trade_points
        
        # 以最低级别为基准，检查是否有更高级别的确认
        base_points = all_trade_points.get(1, [])
        
        for base_tp in base_points:
            confirmation_count = 1  # 基础级别算1次确认
            confirming_levels = [1]
            
            # 检查更高级别是否有类似的买卖点
            for level in range(2, self.levels + 1):
                if level not in all_trade_points:
                    continue
                
                higher_points = all_trade_points[level]
                
                for higher_tp in higher_points:
                    # 检查是否是同类型的买卖点
                    if higher_tp.point_type != base_tp.point_type:
                        continue
                    
                    # 检查时间是否接近（高级别时间精度较低）
                    time_diff = abs((higher_tp.dt - base_tp.dt).days)
                    tolerance = level * 5  # 级别越高，容忍的时间差越大
                    
                    if time_diff <= tolerance:
                        confirmation_count += 1
                        confirming_levels.append(level)
                        break
            
            # 如果有多级别确认，创建区间套买卖点
            if confirmation_count >= 2:
                # 增强信号强度
                enhanced_strength = min(0.98, base_tp.strength + 0.1 * (confirmation_count - 1))
                
                nested_tp = TradePoint(
                    point_type=base_tp.point_type,
                    dt=base_tp.dt,
                    price=base_tp.price,
                    strength=enhanced_strength,
                    macd_strength=base_tp.macd_strength,
                    description=f"区间套{base_tp.description}（{confirmation_count}级别确认：L{confirming_levels}）",
                    index=len(nested_points)
                )
                nested_points.append(nested_tp)
        
        self.nested_trade_points = nested_points
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式，用于API返回
        
        Returns:
            包含所有级别分析结果的字典
        """
        result = {
            "levels": {},
            "nested_trade_points": [
                {
                    "type": tp.point_type.value,
                    "dt": tp.dt.isoformat(),
                    "price": tp.price,
                    "strength": tp.strength,
                    "macd_strength": tp.macd_strength,
                    "description": tp.description,
                }
                for tp in self.nested_trade_points
            ],
        }
        
        for level, analyzer in self.analyzers.items():
            result["levels"][f"level_{level}"] = {
                "fractals_count": len(analyzer.fractals),
                "strokes_count": len(analyzer.strokes),
                "segments_count": len(analyzer.segments),
                "pivots_count": len(analyzer.pivots),
                "trade_points_count": len(analyzer.trade_points),
                "trade_points": [
                    {
                        "type": tp.point_type.value,
                        "dt": tp.dt.isoformat(),
                        "price": tp.price,
                        "strength": tp.strength,
                        "description": tp.description,
                    }
                    for tp in analyzer.trade_points
                ],
            }
        
        return result
