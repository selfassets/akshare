from typing import Optional, List, Dict, Any, Literal, Callable
import logging
import requests

from fastapi import APIRouter, HTTPException, Query, Response
import pandas as pd

from akshare import futures_fees_info
from akshare.futures.futures_hist_em import futures_hist_em, futures_hist_table_em
from akshare.futures.futures_inventory_99 import futures_inventory_99
from akshare.futures.futures_comm_qihuo import futures_comm_info

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/futures", tags=["futures"])


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
        description='choice of {"所有", "上海期货交易所", "大连商品交易所", "郑州商品交易所", "上海国际能源交易中心", "中国金融期货交易所", "广州期货交易所"}',
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


