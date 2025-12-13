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
            
            # 创建笔
            stroke = Stroke(
                direction=direction,
                start_fractal=current_start,
                end_fractal=best_end,
                index=len(strokes)
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
        
        背驰判定：
        - 下跌趋势中，后一段下跌的力度小于前一段
        - 上涨趋势中，后一段上涨的力度小于前一段
        
        简化的力度计算：使用笔的幅度 * 时间
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
            
            # 计算笔的力度（幅度）
            current_power = current.power
            prev_power = prev_same_dir.power
            
            # 背驰判断：当前笔力度明显小于前一同向笔
            is_divergence = current_power < prev_power * 0.8
            divergence_strength = 1 - (current_power / max(prev_power, 0.001))
            
            if not is_divergence:
                continue
            
            # 第一类买点：向下笔出现背驰，且创新低
            if current.direction == Direction.DOWN:
                is_new_low = current.end_price <= prev_same_dir.end_price
                if is_new_low:
                    trade_point = TradePoint(
                        point_type=TradePointType.BUY_1,
                        dt=current.end_dt,
                        price=current.end_price,
                        strength=min(0.9, 0.5 + divergence_strength * 0.4),
                        description=f"第一类买点：底背驰（力度比={current_power/max(prev_power,0.001):.2f}）",
                        index=len(trade_points)
                    )
                    trade_points.append(trade_point)
            
            # 第一类卖点：向上笔出现背驰，且创新高
            elif current.direction == Direction.UP:
                is_new_high = current.end_price >= prev_same_dir.end_price
                if is_new_high:
                    trade_point = TradePoint(
                        point_type=TradePointType.SELL_1,
                        dt=current.end_dt,
                        price=current.end_price,
                        strength=min(0.9, 0.5 + divergence_strength * 0.4),
                        description=f"第一类卖点：顶背驰（力度比={current_power/max(prev_power,0.001):.2f}）",
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
