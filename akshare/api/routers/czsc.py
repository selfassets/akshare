"""
缠论分析 API 路由

提供基于 CZSC 库的缠论分析功能，包括分型、笔、中枢等元素的识别。
"""
from typing import List, Dict, Any, Literal
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Response
import pandas as pd

from akshare.futures_derivative.futures_index_sina import futures_main_sina

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()


def convert_czsc_data_to_json(czsc_obj) -> Dict[str, Any]:
    """
    将 CZSC 对象转换为 JSON 可序列化的字典
    
    :param czsc_obj: CZSC 分析对象
    :return: 包含缠论元素的字典
    """
    result = {
        "symbol": czsc_obj.symbol,
        "freq": str(czsc_obj.freq),
        "bars_raw": [],
        "bars_ubi": [],
        "bi_list": [],
        "fx_list": [],
    }
    
    # 转换原始 K 线
    for bar in czsc_obj.bars_raw[-200:]:  # 最近 200 根 K 线
        result["bars_raw"].append({
            "dt": bar.dt.isoformat() if isinstance(bar.dt, datetime) else str(bar.dt),
            "open": float(bar.open),
            "close": float(bar.close),
            "high": float(bar.high),
            "low": float(bar.low),
            "vol": float(bar.vol),
        })
    
    # 转换未完成笔的 K 线
    for bar in czsc_obj.bars_ubi:
        result["bars_ubi"].append({
            "dt": bar.dt.isoformat() if isinstance(bar.dt, datetime) else str(bar.dt),
            "open": float(bar.open),
            "close": float(bar.close),
            "high": float(bar.high),
            "low": float(bar.low),
        })
    
    # 转换笔
    for bi in czsc_obj.bi_list:
        result["bi_list"].append({
            "direction": str(bi.direction),
            "start_dt": bi.fx_a.dt.isoformat() if isinstance(bi.fx_a.dt, datetime) else str(bi.fx_a.dt),
            "end_dt": bi.fx_b.dt.isoformat() if isinstance(bi.fx_b.dt, datetime) else str(bi.fx_b.dt),
            "start_price": float(bi.fx_a.fx),
            "end_price": float(bi.fx_b.fx),
            "high": float(bi.high),
            "low": float(bi.low),
            "power": float(bi.power),
        })
    
    # 转换分型（包括 ubi 中的分型）
    for fx in czsc_obj.fx_list:
        result["fx_list"].append({
            "mark": str(fx.mark),
            "dt": fx.dt.isoformat() if isinstance(fx.dt, datetime) else str(fx.dt),
            "high": float(fx.high),
            "low": float(fx.low),
            "fx": float(fx.fx),
        })
    
    return result


@router.get("/analyze", response_model=Dict[str, Any])
async def analyze_chanlun(
    symbol: str = Query("热卷主连", description="期货代码"),
    period: Literal["daily", "weekly", "monthly"] = Query("daily", description="周期"),
    start_date: str = Query("20240101", description="开始日期 YYYYMMDD"),
    end_date: str = Query("20241231", description="结束日期 YYYYMMDD"),
):
    """
    对指定品种和周期进行缠论分析
    
    返回数据包括:
    - bars_raw: 原始K线数据
    - bars_ubi: 未完成笔的K线
    - bi_list: 笔列表
    - fx_list: 分型列表
    
    示例:
    ```
    GET /czsc/analyze?symbol=热卷主连&period=daily&start_date=20240101&end_date=20241231
    ```
    """
    try:
        # 导入 CZSC 相关模块
        try:
            from czsc import CZSC, RawBar, Freq
        except ImportError as e:
            logger.error(f"CZSC 库导入失败: {e}")
            raise HTTPException(
                status_code=500,
                detail="CZSC 库未安装或导入失败，请确保 czsc 库已正确安装"
            )
        
        logger.info(f"开始缠论分析: symbol={symbol}, period={period}, start={start_date}, end={end_date}")
        
        # 1. 直接调用 akshare 库获取 K 线数据
        # 使用 futures_zh_daily_sina 获取新浪期货数据
        try:
            df = futures_main_sina(symbol=symbol, start_date=start_date, end_date=end_date)
            logger.info(f"获取到 {len(df)} 条数据，列名: {df.columns.tolist()}")
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
        
        # 按日期范围过滤（兼容不同的列名）
        date_col = None
        for col in ['日期', 'date', 'trading_date', 'datetime']:
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
        
        # 2. 转换为 CZSC 所需的 RawBar 格式
        # 新浪期货数据格式: {'日期': datetime, '开盘价': float, '最高价': float, '最低价': float, '收盘价': float, '成交量': int, ...}
        
        # 定义周期映射
        freq_map = {
            "daily": Freq.D,
            "weekly": Freq.W,
            "monthly": Freq.M,
        }
        freq = freq_map.get(period, Freq.D)
        
        # 构建列名映射
        column_mapping = {
            'date': date_col,
            'open': None,
            'close': None,
            'high': None,
            'low': None,
            'volume': None,
        }
        
        # 寻找价格列
        for col in ['开盘价', 'open']:
            if col in df.columns:
                column_mapping['open'] = col
                break
        
        for col in ['收盘价', 'close']:
            if col in df.columns:
                column_mapping['close'] = col
                break
                
        for col in ['最高价', 'high']:
            if col in df.columns:
                column_mapping['high'] = col
                break
                
        for col in ['最低价', 'low']:
            if col in df.columns:
                column_mapping['low'] = col
                break
                
        for col in ['成交量', 'volume', 'vol']:
            if col in df.columns:
                column_mapping['volume'] = col
                break
        
        logger.info(f"列名映射: {column_mapping}")
        
        # 检查必需列是否存在
        missing_cols = [k for k, v in column_mapping.items() if v is None and k != 'volume']
        if missing_cols:
            logger.error(f"缺少必需的列: {missing_cols}, 可用列: {df.columns.tolist()}")
            raise HTTPException(
                status_code=500,
                detail=f"数据格式错误：缺少列 {missing_cols}。可用列: {df.columns.tolist()}"
            )
        
        bars = []
        error_count = 0
        for idx, row in df.iterrows():
            try:
                bar = RawBar(
                    symbol=symbol,
                    id=idx,
                    dt=row[column_mapping['date']],
                    freq=freq,
                    open=float(row[column_mapping['open']]),
                    close=float(row[column_mapping['close']]),
                    high=float(row[column_mapping['high']]),
                    low=float(row[column_mapping['low']]),
                    vol=float(row.get(column_mapping['volume'], 0)) if column_mapping['volume'] else 0,
                    amount=float(row.get('持仓量', 0)),
                )
                bars.append(bar)
            except Exception as e:
                error_count += 1
                if error_count <= 3:  # 只记录前3个错误
                    logger.error(f"转换第 {idx} 行数据失败: {e}, 行数据: {row.to_dict()}", exc_info=True)
                continue
        
        logger.info(f"转换了 {len(bars)} 根 K 线，跳过 {error_count} 个错误")
        
        if len(bars) == 0:
            raise HTTPException(
                status_code=404,
                detail="没有可用的K线数据"
            )
        
        # 3. 进行缠论分析
        # CZSC 使用 bars_raw 参数传入 K 线列表
        czsc = CZSC(bars_raw=bars, max_bi_num=1000)
        
        logger.info(f"缠论分析完成: {len(czsc.bi_list)} 笔, {len(czsc.fx_list)} 个分型")
        
        # 4. 转换为 JSON 格式
        result = convert_czsc_data_to_json(czsc)
        
        # 添加统计信息
        result["stats"] = {
            "total_bars": len(bars),
            "total_bi": len(czsc.bi_list),
            "total_fx": len(czsc.fx_list),
            "last_update": datetime.now().isoformat(),
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"缠论分析失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"缠论分析失败: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, str])
async def health_check():
    """
    健康检查端点
    """
    try:
        from czsc import __version__
        return {
            "status": "ok",
            "czsc_version": __version__,
        }
    except ImportError:
        return {
            "status": "error",
            "message": "CZSC 库未安装"
        }
