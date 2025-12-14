"""
技术指标分析 API 路由

基于 MyTT 库提供期货 k 线数据的技术指标计算功能
支持常用指标：MACD, KDJ, RSI, BOLL, ATR, CCI, MA, EMA 等
"""

from typing import Optional, List, Dict, Any
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np

# 导入 MyTT 技术指标库
import sys
from pathlib import Path
mytt_path = Path(__file__).parent.parent / "analysis"
sys.path.insert(0, str(mytt_path))
from mytt import *

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# Pydantic 数据模型
# ============================================================

class KLineData(BaseModel):
    """K线数据模型"""
    date: str = Field(..., description="日期，格式：YYYY-MM-DD")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: Optional[float] = Field(None, description="成交量")


class MACDParams(BaseModel):
    """MACD 指标参数"""
    short: int = Field(12, description="短期周期")
    long: int = Field(26, description="长期周期")
    m: int = Field(9, description="信号线周期")


class KDJParams(BaseModel):
    """KDJ 指标参数"""
    n: int = Field(9, description="RSV周期")
    m1: int = Field(3, description="K值周期")
    m2: int = Field(3, description="D值周期")


class RSIParams(BaseModel):
    """RSI 指标参数"""
    n: int = Field(24, description="周期")


class BOLLParams(BaseModel):
    """BOLL 指标参数"""
    n: int = Field(20, description="周期")
    p: int = Field(2, description="标准差倍数")


class ATRParams(BaseModel):
    """ATR 指标参数"""
    n: int = Field(20, description="周期")


class CCIParams(BaseModel):
    """CCI 指标参数"""
    n: int = Field(14, description="周期")


class MAParams(BaseModel):
    """MA 指标参数"""
    periods: List[int] = Field([5, 10, 20, 30, 60], description="周期列表")


class EMAParams(BaseModel):
    """EMA 指标参数"""
    periods: List[int] = Field([5, 10, 20, 30, 60], description="周期列表")


class IndicatorRequest(BaseModel):
    """通用指标请求模型"""
    data: List[KLineData] = Field(..., description="K线数据列表")
    params: Optional[Dict[str, Any]] = Field(None, description="指标参数")


class BatchIndicatorRequest(BaseModel):
    """批量指标请求模型"""
    data: List[KLineData] = Field(..., description="K线数据列表")
    indicators: List[str] = Field(..., description="要计算的指标列表，如: ['MACD', 'KDJ', 'RSI']")
    params: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="各指标参数，格式：{'MACD': {'short': 12}, 'RSI': {'n': 24}}")


# ============================================================
# 辅助函数
# ============================================================

def prepare_kline_data(data: List[KLineData]) -> pd.DataFrame:
    """
    将 K 线数据转换为 pandas DataFrame
    
    Args:
        data: K线数据列表
        
    Returns:
        pd.DataFrame: 包含 OPEN, HIGH, LOW, CLOSE, VOLUME 列的 DataFrame
        
    Raises:
        HTTPException: 数据不足或格式错误时抛出
    """
    if len(data) < 2:
        raise HTTPException(
            status_code=400,
            detail="数据不足，至少需要 2 条 K 线数据"
        )
    
    try:
        df = pd.DataFrame([item.dict() for item in data])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        # 准备 MyTT 所需的列名（大写）
        OPEN = df['open'].values
        HIGH = df['high'].values
        LOW = df['low'].values
        CLOSE = df['close'].values
        VOLUME = df['volume'].values if 'volume' in df.columns else np.zeros(len(df))
        
        return {
            'df': df,
            'OPEN': OPEN,
            'HIGH': HIGH,
            'LOW': LOW,
            'CLOSE': CLOSE,
            'VOLUME': VOLUME
        }
    except Exception as e:
        logger.error(f"数据准备失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"数据格式错误: {str(e)}"
        )


def build_response(df: pd.DataFrame, indicator_name: str, indicator_data: Dict[str, np.ndarray]) -> Dict[str, Any]:
    """
    构建指标响应数据
    
    Args:
        df: 原始数据 DataFrame
        indicator_name: 指标名称
        indicator_data: 指标计算结果字典
        
    Returns:
        Dict: 响应数据
    """
    result = []
    for i in range(len(df)):
        item = {
            'date': df.iloc[i]['date'].strftime('%Y-%m-%d')
        }
        for key, values in indicator_data.items():
            # 处理 NaN 值
            value = values[i] if i < len(values) else None
            if isinstance(value, (np.floating, float)) and np.isnan(value):
                value = None
            elif isinstance(value, np.floating):
                value = float(value)
            item[key] = value
        result.append(item)
    
    return {
        'success': True,
        'indicator': indicator_name,
        'data': result
    }


# ============================================================
# 技术指标 API 端点
# ============================================================

@router.post("/macd")
async def calculate_macd(request: IndicatorRequest):
    """
    计算 MACD 指标（移动平均收敛散度）
    
    返回字段：
    - dif: 差离值（短期EMA - 长期EMA）
    - dea: 信号线（DIF的EMA）
    - macd: MACD柱状图（(DIF - DEA) * 2）
    """
    try:
        kdata = prepare_kline_data(request.data)
        
        # 获取参数
        params = MACDParams(**(request.params or {}))
        
        # 计算 MACD
        DIF, DEA, MACD_BAR = MACD(kdata['CLOSE'], params.short, params.long, params.m)
        
        return build_response(
            kdata['df'],
            'MACD',
            {'dif': DIF, 'dea': DEA, 'macd': MACD_BAR}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MACD 计算失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"MACD 计算失败: {str(e)}")


@router.post("/kdj")
async def calculate_kdj(request: IndicatorRequest):
    """
    计算 KDJ 指标（随机指标）
    
    返回字段：
    - k: K 值
    - d: D 值
    - j: J 值
    """
    try:
        kdata = prepare_kline_data(request.data)
        
        # 获取参数
        params = KDJParams(**(request.params or {}))
        
        # 计算 KDJ
        K, D, J = KDJ(kdata['CLOSE'], kdata['HIGH'], kdata['LOW'], params.n, params.m1, params.m2)
        
        return build_response(
            kdata['df'],
            'KDJ',
            {'k': K, 'd': D, 'j': J}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"KDJ 计算失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"KDJ 计算失败: {str(e)}")


@router.post("/rsi")
async def calculate_rsi(request: IndicatorRequest):
    """
    计算 RSI 指标（相对强弱指数）
    
    返回字段：
    - rsi: RSI 值
    """
    try:
        kdata = prepare_kline_data(request.data)
        
        # 获取参数
        params = RSIParams(**(request.params or {}))
        
        # 计算 RSI
        rsi_values = RSI(kdata['CLOSE'], params.n)
        
        return build_response(
            kdata['df'],
            'RSI',
            {'rsi': rsi_values}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RSI 计算失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"RSI 计算失败: {str(e)}")


@router.post("/boll")
async def calculate_boll(request: IndicatorRequest):
    """
    计算 BOLL 指标（布林带）
    
    返回字段：
    - upper: 上轨
    - mid: 中轨
    - lower: 下轨
    """
    try:
        kdata = prepare_kline_data(request.data)
        
        # 获取参数
        params = BOLLParams(**(request.params or {}))
        
        # 计算 BOLL
        UPPER, MID, LOWER = BOLL(kdata['CLOSE'], params.n, params.p)
        
        return build_response(
            kdata['df'],
            'BOLL',
            {'upper': UPPER, 'mid': MID, 'lower': LOWER}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"BOLL 计算失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"BOLL 计算失败: {str(e)}")


@router.post("/atr")
async def calculate_atr(request: IndicatorRequest):
    """
    计算 ATR 指标（真实波动幅度）
    
    返回字段：
    - atr: ATR 值
    """
    try:
        kdata = prepare_kline_data(request.data)
        
        # 获取参数
        params = ATRParams(**(request.params or {}))
        
        # 计算 ATR
        atr_values = ATR(kdata['CLOSE'], kdata['HIGH'], kdata['LOW'], params.n)
        
        return build_response(
            kdata['df'],
            'ATR',
            {'atr': atr_values}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ATR 计算失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"ATR 计算失败: {str(e)}")


@router.post("/cci")
async def calculate_cci(request: IndicatorRequest):
    """
    计算 CCI 指标（顺势指标）
    
    返回字段：
    - cci: CCI 值
    """
    try:
        kdata = prepare_kline_data(request.data)
        
        # 获取参数
        params = CCIParams(**(request.params or {}))
        
        # 计算 CCI
        cci_values = CCI(kdata['CLOSE'], kdata['HIGH'], kdata['LOW'], params.n)
        
        return build_response(
            kdata['df'],
            'CCI',
            {'cci': cci_values}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CCI 计算失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"CCI 计算失败: {str(e)}")


@router.post("/ma")
async def calculate_ma(request: IndicatorRequest):
    """
    计算 MA 指标（移动平均线）
    
    返回字段：
    - ma5, ma10, ma20 等（根据参数中的 periods）
    """
    try:
        kdata = prepare_kline_data(request.data)
        
        # 获取参数
        params = MAParams(**(request.params or {}))
        
        # 计算多个周期的 MA
        ma_data = {}
        for period in params.periods:
            ma_values = MA(kdata['CLOSE'], period)
            ma_data[f'ma{period}'] = ma_values
        
        return build_response(
            kdata['df'],
            'MA',
            ma_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MA 计算失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"MA 计算失败: {str(e)}")


@router.post("/ema")
async def calculate_ema(request: IndicatorRequest):
    """
    计算 EMA 指标（指数移动平均线）
    
    返回字段：
    - ema5, ema10, ema20 等（根据参数中的 periods）
    """
    try:
        kdata = prepare_kline_data(request.data)
        
        # 获取参数
        params = EMAParams(**(request.params or {}))
        
        # 计算多个周期的 EMA
        ema_data = {}
        for period in params.periods:
            ema_values = EMA(kdata['CLOSE'], period)
            ema_data[f'ema{period}'] = ema_values
        
        return build_response(
            kdata['df'],
            'EMA',
            ema_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"EMA 计算失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"EMA 计算失败: {str(e)}")


@router.post("/batch")
async def calculate_batch(request: BatchIndicatorRequest):
    """
    批量计算多个技术指标
    
    支持的指标：MACD, KDJ, RSI, BOLL, ATR, CCI, MA, EMA
    
    返回所有指标的综合结果
    """
    try:
        kdata = prepare_kline_data(request.data)
        
        all_indicator_data = {}
        
        for indicator in request.indicators:
            indicator = indicator.upper()
            
            # 获取该指标的参数
            params = (request.params or {}).get(indicator, {})
            
            try:
                if indicator == 'MACD':
                    p = MACDParams(**params)
                    DIF, DEA, MACD_BAR = MACD(kdata['CLOSE'], p.short, p.long, p.m)
                    all_indicator_data.update({'dif': DIF, 'dea': DEA, 'macd': MACD_BAR})
                    
                elif indicator == 'KDJ':
                    p = KDJParams(**params)
                    K, D, J = KDJ(kdata['CLOSE'], kdata['HIGH'], kdata['LOW'], p.n, p.m1, p.m2)
                    all_indicator_data.update({'k': K, 'd': D, 'j': J})
                    
                elif indicator == 'RSI':
                    p = RSIParams(**params)
                    rsi_values = RSI(kdata['CLOSE'], p.n)
                    all_indicator_data['rsi'] = rsi_values
                    
                elif indicator == 'BOLL':
                    p = BOLLParams(**params)
                    UPPER, MID, LOWER = BOLL(kdata['CLOSE'], p.n, p.p)
                    all_indicator_data.update({'upper': UPPER, 'mid': MID, 'lower': LOWER})
                    
                elif indicator == 'ATR':
                    p = ATRParams(**params)
                    atr_values = ATR(kdata['CLOSE'], kdata['HIGH'], kdata['LOW'], p.n)
                    all_indicator_data['atr'] = atr_values
                    
                elif indicator == 'CCI':
                    p = CCIParams(**params)
                    cci_values = CCI(kdata['CLOSE'], kdata['HIGH'], kdata['LOW'], p.n)
                    all_indicator_data['cci'] = cci_values
                    
                elif indicator == 'MA':
                    p = MAParams(**params)
                    for period in p.periods:
                        ma_values = MA(kdata['CLOSE'], period)
                        all_indicator_data[f'ma{period}'] = ma_values
                        
                elif indicator == 'EMA':
                    p = EMAParams(**params)
                    for period in p.periods:
                        ema_values = EMA(kdata['CLOSE'], period)
                        all_indicator_data[f'ema{period}'] = ema_values
                        
                else:
                    logger.warning(f"未知的指标: {indicator}")
                    
            except Exception as e:
                logger.error(f"计算 {indicator} 失败: {e}", exc_info=True)
                # 继续计算其他指标
                continue
        
        return build_response(
            kdata['df'],
            'BATCH',
            all_indicator_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量计算失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"批量计算失败: {str(e)}")


@router.get("/")
async def get_indicators_info():
    """
    获取可用的技术指标列表
    """
    return {
        "description": "MyTT 技术指标分析 API",
        "available_indicators": [
            {
                "name": "MACD",
                "description": "移动平均收敛散度",
                "endpoint": "/indicators/macd",
                "params": {"short": 12, "long": 26, "m": 9}
            },
            {
                "name": "KDJ",
                "description": "随机指标",
                "endpoint": "/indicators/kdj",
                "params": {"n": 9, "m1": 3, "m2": 3}
            },
            {
                "name": "RSI",
                "description": "相对强弱指数",
                "endpoint": "/indicators/rsi",
                "params": {"n": 24}
            },
            {
                "name": "BOLL",
                "description": "布林带",
                "endpoint": "/indicators/boll",
                "params": {"n": 20, "p": 2}
            },
            {
                "name": "ATR",
                "description": "真实波动幅度",
                "endpoint": "/indicators/atr",
                "params": {"n": 20}
            },
            {
                "name": "CCI",
                "description": "顺势指标",
                "endpoint": "/indicators/cci",
                "params": {"n": 14}
            },
            {
                "name": "MA",
                "description": "移动平均线",
                "endpoint": "/indicators/ma",
                "params": {"periods": [5, 10, 20, 30, 60]}
            },
            {
                "name": "EMA",
                "description": "指数移动平均线",
                "endpoint": "/indicators/ema",
                "params": {"periods": [5, 10, 20, 30, 60]}
            }
        ],
        "batch_endpoint": "/indicators/batch",
        "documentation": "/docs"
    }
