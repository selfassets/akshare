"""
缠论分析 API 路由

提供基于自实现算法的缠论分析功能，不依赖 czsc 库。
"""

from typing import Dict, Any, Literal
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
import pandas as pd

from akshare.futures_derivative.futures_index_sina import futures_main_sina
from akshare.api.analysis.chanlun_core import ChanlunAnalyzer, create_bars_from_dataframe

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/analyze", response_model=Dict[str, Any])
async def analyze_chanlun(
    symbol: str = Query("eg2601", description="期货代码"),
    start_date: str = Query("20250101", description="开始日期 YYYYMMDD"),
    end_date: str = Query("20261231", description="结束日期 YYYYMMDD"),
    level: Literal["basic", "advanced", "full"] = Query(
        "basic",
        description="分析级别: basic=分型+笔, advanced=+线段+中枢, full=+买卖点"
    ),
):
    """
    对指定品种进行缠论分析（自实现，不依赖 czsc 库）
    
    返回数据包括:
    - bars_raw: 原始K线数据
    - bars_merged: 处理包含关系后的K线
    - fractals: 分型列表（顶分型、底分型）
    - strokes: 笔列表
    - segments: 线段列表（advanced 及以上级别）
    - pivots: 中枢列表（advanced 及以上级别）
    - trade_points: 买卖点列表（full 级别）
    
    示例:
    ```
    GET /chanlun/analyze?symbol=eg2601&start_date=20250101&end_date=20261231&level=basic
    ```
    """
    try:
        logger.info(
            f"开始缠论分析: symbol={symbol}, start={start_date}, end={end_date}, level={level}"
        )
        
        # 1. 获取 K 线数据
        try:
            df = futures_main_sina(symbol=symbol, start_date=start_date, end_date=end_date)
            logger.info(f"获取到 {len(df)} 条数据")
        except Exception as e:
            logger.error(f"获取 K 线数据失败: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail=f"获取 K 线数据失败: {str(e)}"
            )
        
        if df.empty:
            logger.warning(f"未找到 K 线数据: {symbol}")
            raise HTTPException(
                status_code=404,
                detail=f"未找到品种 {symbol} 的K线数据"
            )
        
        # 2. 按日期范围过滤
        date_col = None
        for col in ['日期', 'date', 'trading_date', 'datetime', 'dt']:
            if col in df.columns:
                date_col = col
                break
        
        if date_col is None:
            logger.error(f"未找到日期列，现有列: {df.columns.tolist()}")
            raise HTTPException(
                status_code=500,
                detail=f"数据格式错误：未找到日期列。现有列: {df.columns.tolist()}"
            )
        
        df[date_col] = pd.to_datetime(df[date_col])
        start_dt = pd.to_datetime(start_date, format='%Y%m%d')
        end_dt = pd.to_datetime(end_date, format='%Y%m%d')
        df = df[(df[date_col] >= start_dt) & (df[date_col] <= end_dt)]
        
        if df.empty:
            logger.warning(f"日期范围内没有数据: {start_date} - {end_date}")
            raise HTTPException(
                status_code=404,
                detail=f"日期范围 {start_date} - {end_date} 内没有数据"
            )
        
        # 3. 转换为 Bar 列表
        try:
            bars = create_bars_from_dataframe(df, symbol=symbol)
            logger.info(f"转换了 {len(bars)} 根 K 线")
        except Exception as e:
            logger.error(f"转换 K 线数据失败: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"转换 K 线数据失败: {str(e)}"
            )
        
        if len(bars) == 0:
            raise HTTPException(
                status_code=404,
                detail="没有可用的K线数据"
            )
        
        # 4. 执行缠论分析
        try:
            analyzer = ChanlunAnalyzer(bars)
            logger.info(
                f"缠论分析完成: {len(analyzer.fractals)} 个分型, "
                f"{len(analyzer.strokes)} 笔"
            )
        except Exception as e:
            logger.error(f"缠论分析失败: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"缠论分析失败: {str(e)}"
            )
        
        # 5. 转换为 JSON 格式
        result = analyzer.to_dict()
        
        # 6. 添加统计信息
        result["stats"] = {
            "symbol": symbol,
            "total_bars_raw": len(analyzer.bars_raw),
            "total_bars_merged": len(analyzer.bars_merged),
            "total_fractals": len(analyzer.fractals),
            "total_strokes": len(analyzer.strokes),
            "total_segments": len(analyzer.segments),
            "total_pivots": len(analyzer.pivots),
            "total_trade_points": len(analyzer.trade_points),
            "analysis_level": level,
            "analysis_time": datetime.now().isoformat(),
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"未预期的错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"分析过程发生错误: {str(e)}"
        )


@router.get("/fractals", response_model=Dict[str, Any])
async def get_fractals(
    symbol: str = Query("热卷主连", description="期货代码"),
    start_date: str = Query("20240101", description="开始日期 YYYYMMDD"),
    end_date: str = Query("20241231", description="结束日期 YYYYMMDD"),
):
    """
    仅返回分型数据
    
    示例:
    ```
    GET /chanlun/fractals?symbol=热卷主连&start_date=20240101&end_date=20241231
    ```
    """
    result = await analyze_chanlun(symbol, start_date, end_date, "basic")
    return {
        "fractals": result["fractals"],
        "stats": result["stats"],
    }


@router.get("/strokes", response_model=Dict[str, Any])
async def get_strokes(
    symbol: str = Query("热卷主连", description="期货代码"),
    start_date: str = Query("20240101", description="开始日期 YYYYMMDD"),
    end_date: str = Query("20241231", description="结束日期 YYYYMMDD"),
):
    """
    仅返回笔数据
    
    示例:
    ```
    GET /chanlun/strokes?symbol=热卷主连&start_date=20240101&end_date=20241231
    ```
    """
    result = await analyze_chanlun(symbol, start_date, end_date, "basic")
    return {
        "strokes": result["strokes"],
        "stats": result["stats"],
    }


@router.get("/results", response_model=Dict[str, Any])
async def get_results(
    symbol: str = Query("eg2601", description="期货代码"),
    start_date: str = Query("20250101", description="开始日期 YYYYMMDD"),
    end_date: str = Query("20261231", description="结束日期 YYYYMMDD"),
):
    """
    只返回缠论分析的核心结果（不包含K线数据）
    
    返回数据包括:
    - fractals: 分型列表
    - strokes: 笔列表
    - segments: 线段列表
    - pivots: 中枢列表
    - trade_points: 买卖点列表
    
    示例:
    ```
    GET /chanlun/results?symbol=eg2601&start_date=20250101&end_date=20261231
    ```
    """
    result = await analyze_chanlun(symbol, start_date, end_date, "full")
    return {
        "fractals": result["fractals"],
        "strokes": result["strokes"],
        "segments": result["segments"],
        "pivots": result["pivots"],
        "trade_points": result["trade_points"],
        "stats": result["stats"],
    }



@router.get("/health", response_model=Dict[str, str])
async def health_check():
    """
    健康检查端点
    """
    return {
        "status": "ok",
        "module": "chanlun_core",
        "description": "独立实现的缠论分析引擎"
    }
