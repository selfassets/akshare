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
        
        # 6. 根据 level 过滤返回数据
        if level == "basic":
            # basic 级别：仅返回分型和笔
            result["segments"] = []
            result["pivots"] = []
            result["trade_points"] = []
        elif level == "advanced":
            # advanced 级别：返回分型、笔、线段、中枢，不返回买卖点
            result["trade_points"] = []
        # full 级别：返回所有数据，不过滤
        
        # 7. 添加统计信息
        result["stats"] = {
            "symbol": symbol,
            "total_bars_raw": len(analyzer.bars_raw),
            "total_bars_merged": len(analyzer.bars_merged),
            "total_fractals": len(analyzer.fractals),
            "total_strokes": len(analyzer.strokes),
            "total_segments": len(analyzer.segments) if level != "basic" else 0,
            "total_pivots": len(analyzer.pivots) if level != "basic" else 0,
            "total_trade_points": len(analyzer.trade_points) if level == "full" else 0,
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


def _validate_date_format(date_str: str, field_name: str) -> None:
    """
    验证日期格式是否为 YYYYMMDD
    
    Args:
        date_str: 日期字符串
        field_name: 字段名称（用于错误提示）
    
    Raises:
        HTTPException: 如果日期格式无效
    """
    if not date_str:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} 不能为空"
        )
    
    if len(date_str) != 8 or not date_str.isdigit():
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} 格式错误，应为 YYYYMMDD 格式，当前值: {date_str}"
        )
    
    try:
        datetime.strptime(date_str, '%Y%m%d')
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} 日期无效，请检查年月日是否正确，当前值: {date_str}"
        )


@router.get("/results", response_model=Dict[str, Any])
async def get_results(
    symbol: str = Query("eg2601", description="期货代码，如 eg2601、热卷主连"),
    start_date: str = Query("20250101", description="开始日期 YYYYMMDD 格式"),
    end_date: str = Query("20261231", description="结束日期 YYYYMMDD 格式"),
    level: Literal["basic", "advanced", "full"] = Query(
        "full",
        description="分析级别: basic=分型+笔, advanced=+线段+中枢, full=+买卖点"
    ),
    include_bars: bool = Query(
        False,
        description="是否包含 K 线数据（raw 和 merged），设置为 true 会增加响应大小"
    ),
):
    """
    返回缠论分析的核心结果
    
    此端点用于前端绑定，默认不返回 K 线数据以减少数据传输量。
    如需获取 K 线数据，请设置 `include_bars=true`。
    
    **分析级别说明**:
    - `basic`: 仅包含分型和笔
    - `advanced`: 包含分型、笔、线段、中枢
    - `full`: 包含所有分析结果（分型、笔、线段、中枢、买卖点）
    
    **返回数据结构**:
    - `fractals`: 分型列表 (顶分型/底分型)
    - `strokes`: 笔列表 (向上笔/向下笔)
    - `segments`: 线段列表 (仅 advanced/full 级别)
    - `pivots`: 中枢列表 (仅 advanced/full 级别)
    - `trade_points`: 买卖点列表 (仅 full 级别)
    - `stats`: 统计信息
    - `bars_raw`: 原始 K 线 (仅当 include_bars=true)
    - `bars_merged`: 合并后 K 线 (仅当 include_bars=true)
    
    **示例**:
    ```
    GET /chanlun/results?symbol=eg2601&start_date=20250101&end_date=20261231
    GET /chanlun/results?symbol=eg2601&start_date=20250101&end_date=20261231&level=advanced
    GET /chanlun/results?symbol=eg2601&start_date=20250101&end_date=20261231&include_bars=true
    ```
    """
    # 验证日期格式
    _validate_date_format(start_date, "start_date")
    _validate_date_format(end_date, "end_date")
    
    # 验证日期范围
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail=f"开始日期 ({start_date}) 不能晚于结束日期 ({end_date})"
        )
    
    # 执行分析
    result = await analyze_chanlun(symbol, start_date, end_date, level)
    
    # 构建响应
    response = {
        "fractals": result["fractals"],
        "strokes": result["strokes"],
        "segments": result["segments"],
        "pivots": result["pivots"],
        "trade_points": result["trade_points"],
        "stats": result["stats"],
    }
    
    # 可选包含 K 线数据
    if include_bars:
        response["bars_raw"] = result.get("bars_raw", [])
        response["bars_merged"] = result.get("bars_merged", [])
    
    return response



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
