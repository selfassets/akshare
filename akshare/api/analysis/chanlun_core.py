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

from typing import List, Optional, Literal, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import pandas as pd


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
    strength: float = 0.0  # 强度（0-1，背驰程度）
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
        
        # 2. 识别分型
        self._identify_fractals()
        
        # 3. 识别笔
        self._identify_strokes()
        
        # 4. 识别线段
        self._identify_segments()
        
        # 5. 识别中枢
        self._identify_pivots()
        
        # 6. 识别买卖点
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
    
    def _identify_fractals(self):
        """
        识别分型
        
        分型定义（使用处理过包含关系的K线）：
        - 顶分型：第2根K线高点是3根K线中最高的，且第2根K线低点 >= 第1、3根的低点
        - 底分型：第2根K线低点是3根K线中最低的，且第2根K线高点 <= 第1、3根的高点
        """
        if len(self.bars_merged) < 3:
            return
        
        fractals = []
        i = 0
        
        while i <= len(self.bars_merged) - 3:
            bar1 = self.bars_merged[i]
            bar2 = self.bars_merged[i + 1]
            bar3 = self.bars_merged[i + 2]
            
            # 检查顶分型
            if (bar2.high >= bar1.high and bar2.high >= bar3.high and
                bar2.low >= bar1.low and bar2.low >= bar3.low):
                fractal = Fractal(
                    fractal_type=FractalType.TOP,
                    dt=bar2.dt,
                    high=bar2.high,
                    low=bar2.low,
                    bars=[bar1, bar2, bar3],
                    index=len(fractals)
                )
                fractals.append(fractal)
                i += 2  # 跳过已识别的分型
                continue
            
            # 检查底分型
            if (bar2.low <= bar1.low and bar2.low <= bar3.low and
                bar2.high <= bar1.high and bar2.high <= bar3.high):
                fractal = Fractal(
                    fractal_type=FractalType.BOTTOM,
                    dt=bar2.dt,
                    high=bar2.high,
                    low=bar2.low,
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
        - 向上笔：底分型 -> 顶分型
        - 向下笔：顶分型 -> 底分型
        """
        if len(self.fractals) < 2:
            return
        
        strokes = []
        i = 0
        
        while i < len(self.fractals) - 1:
            start_fractal = self.fractals[i]
            end_fractal = self.fractals[i + 1]
            
            # 检查相邻分型是否可以形成笔
            if start_fractal.fractal_type != end_fractal.fractal_type:
                # 确定笔的方向
                if start_fractal.fractal_type == FractalType.BOTTOM:
                    direction = Direction.UP
                else:
                    direction = Direction.DOWN
                
                # 创建笔
                stroke = Stroke(
                    direction=direction,
                    start_fractal=start_fractal,
                    end_fractal=end_fractal,
                    index=len(strokes)
                )
                strokes.append(stroke)
            
            i += 1
        
        self.strokes = strokes
    
    def _identify_segments(self):
        """
        识别线段
        
        线段定义：
        - 至少由3笔构成
        - 线段方向由第一笔确定
        - 当出现反向的特征序列分型时，线段结束
        """
        if len(self.strokes) < 3:
            return
        
        segments = []
        i = 0
        
        while i < len(self.strokes):
            # 线段起始笔
            start_stroke = self.strokes[i]
            direction = start_stroke.direction
            
            # 收集同方向的笔
            strokes_in_segment = [start_stroke]
            j = i + 1
            
            while j < len(self.strokes):
                current_stroke = self.strokes[j]
                next_stroke = self.strokes[j + 1] if j + 1 < len(self.strokes) else None
                
                # 检查是否形成线段终止（特征序列分型破坏）
                if next_stroke and len(strokes_in_segment) >= 3:
                    # 简化判断：如果连续出现反向笔导致价格突破前高/前低，则线段结束
                    if direction == Direction.UP:
                        # 向上线段：如果价格跌破前低，线段结束
                        if current_stroke.end_price < strokes_in_segment[-2].end_price:
                            break
                    else:
                        # 向下线段：如果价格突破前高，线段结束
                        if current_stroke.end_price > strokes_in_segment[-2].end_price:
                            break
                
                strokes_in_segment.append(current_stroke)
                j += 1
                
                # 限制线段长度，避免过长
                if len(strokes_in_segment) >= 20:
                    break
            
            # 创建线段（至少3笔）
            if len(strokes_in_segment) >= 3:
                segment = Segment(
                    direction=direction,
                    strokes=strokes_in_segment,
                    start_dt=strokes_in_segment[0].start_dt,
                    end_dt=strokes_in_segment[-1].end_dt,
                    high=max(s.high for s in strokes_in_segment),
                    low=min(s.low for s in strokes_in_segment),
                    index=len(segments)
                )
                segments.append(segment)
            
            i = j if j > i else i + 1
        
        self.segments = segments
    
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
    
    def _identify_trade_points(self):
        """
        识别买卖点
        
        买卖点类型（简化实现）：
        - 第一类买点：下跌趋势的最低点（底背驰）
        - 第三类买点：中枢突破向上
        - 第一类卖点：上涨趋势的最高点（顶背驰）
        - 第三类卖点：中枢突破向下
        """
        trade_points = []
        
        # 基于笔识别买卖点
        for i, stroke in enumerate(self.strokes):
            if i == 0:
                continue
            
            prev_stroke = self.strokes[i - 1]
            
            # 第一类买点：向下笔后的向上笔，且创新低后反转
            if prev_stroke.direction == Direction.DOWN and stroke.direction == Direction.UP:
                # 检查是否是局部最低点
                is_low_point = True
                for j in range(max(0, i - 3), min(len(self.strokes), i + 3)):
                    if j != i - 1 and self.strokes[j].low < prev_stroke.low:
                        is_low_point = False
                        break
                
                if is_low_point:
                    trade_point = TradePoint(
                        point_type=TradePointType.BUY_1,
                        dt=stroke.start_dt,
                        price=stroke.start_price,
                        strength=0.8,
                        description="第一类买点：底部反转",
                        index=len(trade_points)
                    )
                    trade_points.append(trade_point)
            
            # 第一类卖点：向上笔后的向下笔，且创新高后反转
            if prev_stroke.direction == Direction.UP and stroke.direction == Direction.DOWN:
                # 检查是否是局部最高点
                is_high_point = True
                for j in range(max(0, i - 3), min(len(self.strokes), i + 3)):
                    if j != i - 1 and self.strokes[j].high > prev_stroke.high:
                        is_high_point = False
                        break
                
                if is_high_point:
                    trade_point = TradePoint(
                        point_type=TradePointType.SELL_1,
                        dt=stroke.start_dt,
                        price=stroke.start_price,
                        strength=0.8,
                        description="第一类卖点：顶部反转",
                        index=len(trade_points)
                    )
                    trade_points.append(trade_point)
        
        # 基于中枢识别三类买卖点
        for i, pivot in enumerate(self.pivots):
            # 找中枢后的第一笔
            pivot_end_index = -1
            for j, stroke in enumerate(self.strokes):
                if stroke.end_dt == pivot.end_dt:
                    pivot_end_index = j
                    break
            
            if pivot_end_index >= 0 and pivot_end_index < len(self.strokes) - 1:
                next_stroke = self.strokes[pivot_end_index + 1]
                
                # 第三类买点：向上突破中枢
                if next_stroke.direction == Direction.UP and next_stroke.low > pivot.high:
                    trade_point = TradePoint(
                        point_type=TradePointType.BUY_3,
                        dt=next_stroke.start_dt,
                        price=next_stroke.start_price,
                        strength=0.7,
                        description="第三类买点：向上突破中枢",
                        index=len(trade_points)
                    )
                    trade_points.append(trade_point)
                
                # 第三类卖点：向下突破中枢
                if next_stroke.direction == Direction.DOWN and next_stroke.high < pivot.low:
                    trade_point = TradePoint(
                        point_type=TradePointType.SELL_3,
                        dt=next_stroke.start_dt,
                        price=next_stroke.start_price,
                        strength=0.7,
                        description="第三类卖点：向下突破中枢",
                        index=len(trade_points)
                    )
                    trade_points.append(trade_point)
        
        self.trade_points = trade_points
    
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
                }
                for stroke in self.strokes
            ],
            "segments": [
                {
                    "direction": segment.direction.value,
                    "start_dt": segment.start_dt.isoformat(),
                    "end_dt": segment.end_dt.isoformat(),
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
                }
                for pivot in self.pivots
            ],
            "trade_points": [
                {
                    "type": point.point_type.value,
                    "dt": point.dt.isoformat(),
                    "price": point.price,
                    "strength": point.strength,
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
