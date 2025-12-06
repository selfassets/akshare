from typing import Optional, List, Dict, Any, Literal, Callable
import logging
import requests

from fastapi import APIRouter, HTTPException, Query, Response
import pandas as pd

from akshare import futures_fees_info
from akshare.futures.futures_hist_em import futures_hist_em, futures_hist_table_em, __fetch_exchange_symbol_raw_em as fetch_exchange_symbol_raw_em, fetch_futures_market_info_em, fetch_futures_market_details_em, futures_hist_em_v1
from akshare.futures.futures_inventory_99 import futures_inventory_99
from akshare.futures.futures_comm_qihuo import futures_comm_info
from akshare.futures_derivative.futures_index_sina import futures_display_main_sina
from akshare.futures.futures_zh_sina import futures_zh_daily_sina

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()


def _handle_api_request(func: Callable, **kwargs) -> Response:
    """
    Helper function to handle API requests, logging, and error handling.
    Optimized for memory usage by using direct JSON serialization.
    """
    func_name = func.__name__
    logger.info(f"Requesting {func_name} with args: {kwargs}")
    try:
        df = func(**kwargs)

        if df.empty:
            logger.warning(f"No data found for {func_name} with args: {kwargs}")
            return Response(content="[]", media_type="application/json")

        # Use to_json to serialize directly to string, avoiding large intermediate dicts
        # force_ascii=False ensures Chinese characters are not escaped
        json_str = df.to_json(orient="records", force_ascii=False, date_format="iso")
        return Response(content=json_str, media_type="application/json")

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed in {func_name}: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"External service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in {func_name}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/futures_hist_em", response_model=List[Dict[str, Any]])
async def get_futures_hist_em(
    symbol: str = Query("热卷主连", description="期货代码"),
    period: Literal["daily", "weekly", "monthly"] = Query("daily", description="周期: daily, weekly, monthly"),
    start_date: str = Query("19900101", description="开始日期 YYYYMMDD"),
    end_date: str = Query("20500101", description="结束日期 YYYYMMDD"),
):
    """
    获取东方财富网-期货行情-行情数据
    """
    return _handle_api_request(
        futures_hist_em,
        symbol=symbol,
        period=period,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/futures_fees_info", response_model=List[Dict[str, Any]])
async def get_futures_fees_info():
    """
    获取 OpenCTP 期货交易费用参照表

    返回期货交易费用信息，包括：
    - 合约代码
    - 交易所
    - 手续费
    - 更新时间
    """
    return _handle_api_request(futures_fees_info)


@router.get("/futures_inventory_99", response_model=List[Dict[str, Any]])
async def get_futures_inventory_99(
    symbol: str = Query("豆一", description="交易所对应的具体品种; 如：大连商品交易所的 豆一"),
):
    """
    获取 99 期货网-大宗商品库存数据
    """
    return _handle_api_request(futures_inventory_99, symbol=symbol)


@router.get("/futures_comm_info", response_model=List[Dict[str, Any]])
async def get_futures_comm_info(
    symbol: Literal[
        "所有", "上海期货交易所", "大连商品交易所", "郑州商品交易所", "上海国际能源交易中心", "中国金融期货交易所", "广州期货交易所"
    ] = Query(
        "所有",
        description="交易所范围: '所有', '上海期货交易所', '大连商品交易所', '郑州商品交易所', '上海国际能源交易中心', '中国金融期货交易所', '广州期货交易所'",
    ),
):
    """
    获取九期网-期货手续费
    """
    return _handle_api_request(futures_comm_info, symbol=symbol)


@router.get("/futures_hist_table_em", response_model=List[Dict[str, Any]])
async def get_futures_hist_table_em():
    """
    获取东方财富网-期货行情-交易所品种对照表
    """
    return _handle_api_request(futures_hist_table_em)



@router.get("/futures_exchange_symbol_raw_em", response_model=List[Dict[str, Any]])
async def get_futures_exchange_symbol_raw_em():
    """
    获取东方财富网-期货行情-交易所品种对照表原始数据
    """
    return _handle_api_request(lambda: pd.DataFrame(fetch_exchange_symbol_raw_em()))


@router.get("/futures_market_info_em", response_model=List[Dict[str, Any]])
async def get_futures_market_info_em():
    """
    获取东方财富网-期货行情-市场信息
    """
    return _handle_api_request(lambda: pd.DataFrame(fetch_futures_market_info_em()))


@router.get("/futures_market_details_em", response_model=List[Dict[str, Any]])
async def get_futures_market_details_em(
    market_id: str = Query("113", description="市场 ID"),
):
    """
    获取东方财富网-期货行情-市场详情
    """
    return _handle_api_request(lambda: pd.DataFrame(fetch_futures_market_details_em(market_id=market_id)))



@router.get("/futures_hist_em_v1", response_model=List[Dict[str, Any]])
async def get_futures_hist_em_v1(
    period: Literal["daily", "weekly", "monthly"] = Query("daily", description="周期: daily, weekly, monthly"),
    start_date: str = Query("19900101", description="开始日期 YYYYMMDD"),
    end_date: str = Query("20500101", description="结束日期 YYYYMMDD"),
    sec_id: str = Query("20500101", description="sec_id"),
):
    """
    获取东方财富网-期货行情-行情数据 v1
    """
    return _handle_api_request(
        futures_hist_em_v1,
        period=period,
        start_date=start_date,
        end_date=end_date,
        sec_id=sec_id
    )


@router.get("/futures_display_main_sina", response_model=List[Dict[str, Any]])
async def get_futures_display_main_sina():
    """
    获取新浪财经-主力连续合约品种一览表
    
    返回新浪财经主力连续合约品种信息，包括:
    - 所有交易所(dce, czce, shfe, cffex, gfex)的主力连续合约品种
    """
    return _handle_api_request(futures_display_main_sina)


@router.get("/futures_zh_daily_sina", response_model=List[Dict[str, Any]])
async def get_futures_zh_daily_sina(
    symbol: str = Query("RB0", description="期货代码, 可以通过 futures_display_main_sina 获取"),
):
    """
    获取中国各品种期货日频率数据 (新浪财经)
    """
    return _handle_api_request(futures_zh_daily_sina, symbol=symbol)



def _handle_api_request(func: Callable, **kwargs) -> Response:
    """
    Helper function to handle API requests, logging, and error handling.
    Optimized for memory usage by using direct JSON serialization.
    """
    func_name = func.__name__
    logger.info(f"Requesting {func_name} with args: {kwargs}")
    try:
        df = func(**kwargs)

        if df.empty:
            logger.warning(f"No data found for {func_name} with args: {kwargs}")
            return Response(content="[]", media_type="application/json")

        # Use to_json to serialize directly to string, avoiding large intermediate dicts
        # force_ascii=False ensures Chinese characters are not escaped
        json_str = df.to_json(orient="records", force_ascii=False, date_format="iso")
        return Response(content=json_str, media_type="application/json")

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed in {func_name}: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"External service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in {func_name}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/open", response_model=List[Dict[str, Any]])
async def get_futures_data(
    action: Literal[
        "hist_em",
        "fees_info",
        "inventory_99",
        "comm_info",
        "hist_table_em",
        "exchange_symbol_raw_em",
        "market_info_em",
        "market_details_em",
        "hist_em_v1",
        "display_main_sina",
        "zh_daily_sina"
    ] = Query(..., description="操作类型"),
    
    # 通用参数
    symbol: Optional[str] = Query(None, description="期货代码或品种"),
    
    # 时间参数 (用于 hist_em, hist_em_v1, zh_daily_sina)
    period: Optional[Literal["daily", "weekly", "monthly"]] = Query(None, description="周期: daily, weekly, monthly"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYYMMDD"),
    
    # 特定参数
    market_id: Optional[str] = Query(None, description="市场 ID (用于 market_details_em)"),
    sec_id: Optional[str] = Query(None, description="sec_id (用于 hist_em_v1)"),
):
    """
    统一的期货数据接口
    
    支持的操作类型 (action):
    - hist_em: 获取东方财富网-期货行情-行情数据
    - fees_info: 获取 OpenCTP 期货交易费用参照表
    - inventory_99: 获取 99 期货网-大宗商品库存数据
    - comm_info: 获取九期网-期货手续费
    - hist_table_em: 获取东方财富网-期货行情-交易所品种对照表
    - exchange_symbol_raw_em: 获取东方财富网-期货行情-交易所品种对照表原始数据
    - market_info_em: 获取东方财富网-期货行情-市场信息
    - market_details_em: 获取东方财富网-期货行情-市场详情
    - hist_em_v1: 获取东方财富网-期货行情-行情数据 v1
    - display_main_sina: 获取新浪财经-主力连续合约品种一览表
    - zh_daily_sina: 获取中国各品种期货日频率数据 (新浪财经)
    
    参数说明:
    - symbol: 期货代码或品种 (根据不同 action 有不同含义)
    - period: 周期 (daily/weekly/monthly)
    - start_date/end_date: 日期范围 (格式: YYYYMMDD)
    - market_id: 市场 ID
    - sec_id: sec_id 参数
    """
    
    # 根据 action 调用不同的函数
    if action == "hist_em":
        # 获取东方财富网-期货行情-行情数据
        symbol = symbol or "热卷主连"
        period = period or "daily"
        start_date = start_date or "19900101"
        end_date = end_date or "20500101"
        return _handle_api_request(
            futures_hist_em,
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
    
    elif action == "fees_info":
        # 获取 OpenCTP 期货交易费用参照表
        return _handle_api_request(futures_fees_info)
    
    elif action == "inventory_99":
        # 获取 99 期货网-大宗商品库存数据
        symbol = symbol or "豆一"
        return _handle_api_request(futures_inventory_99, symbol=symbol)
    
    elif action == "comm_info":
        # 获取九期网-期货手续费
        # symbol 可以是: '所有', '上海期货交易所', '大连商品交易所', '郑州商品交易所', 
        # '上海国际能源交易中心', '中国金融期货交易所', '广州期货交易所'
        symbol = symbol or "所有"
        return _handle_api_request(futures_comm_info, symbol=symbol)
    
    elif action == "hist_table_em":
        # 获取东方财富网-期货行情-交易所品种对照表
        return _handle_api_request(futures_hist_table_em)
    
    elif action == "exchange_symbol_raw_em":
        # 获取东方财富网-期货行情-交易所品种对照表原始数据
        return _handle_api_request(lambda: pd.DataFrame(fetch_exchange_symbol_raw_em()))
    
    elif action == "market_info_em":
        # 获取东方财富网-期货行情-市场信息
        return _handle_api_request(lambda: pd.DataFrame(fetch_futures_market_info_em()))
    
    elif action == "market_details_em":
        # 获取东方财富网-期货行情-市场详情
        market_id = market_id or "113"
        return _handle_api_request(lambda: pd.DataFrame(fetch_futures_market_details_em(market_id=market_id)))
    
    elif action == "hist_em_v1":
        # 获取东方财富网-期货行情-行情数据 v1
        period = period or "daily"
        start_date = start_date or "19900101"
        end_date = end_date or "20500101"
        sec_id = sec_id or "20500101"
        return _handle_api_request(
            futures_hist_em_v1,
            period=period,
            start_date=start_date,
            end_date=end_date,
            sec_id=sec_id
        )
    
    elif action == "display_main_sina":
        # 获取新浪财经-主力连续合约品种一览表
        return _handle_api_request(futures_display_main_sina)
    
    elif action == "zh_daily_sina":
        # 获取中国各品种期货日频率数据 (新浪财经)
        symbol = symbol or "RB0"
        return _handle_api_request(futures_zh_daily_sina, symbol=symbol)
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的操作类型: {action}"
        )

