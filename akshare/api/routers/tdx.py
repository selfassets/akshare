"""
通达信数据接口 (TDX) API 路由

提供标准行情和扩展行情的 HTTP API 接口
基于 pytdx 库实现

使用连接池模式保持连接，应用关闭时自动断开
"""

from typing import List, Dict, Any, Literal, Optional
from contextlib import asynccontextmanager
import logging
import threading

from fastapi import APIRouter, HTTPException, Query, Response
from pytdx.hq import TdxHq_API
from pytdx.exhq import TdxExHq_API

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

# 服务器配置
HQ_SERVERS = [
    {"ip": "116.205.171.132", "port": 7709, "name": "通达信广州双线主站6"},
    {"ip": "121.37.207.165", "port": 7709, "name": "通达信备用服务器"},
]

EXHQ_SERVERS = [
    {"ip": "116.205.143.214", "port": 7727, "name": "扩展市场广州双线1"},
]


class TdxConnectionManager:
    """通达信连接管理器 - 单例模式保持连接"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._hq_api: Optional[TdxHq_API] = None
        self._exhq_api: Optional[TdxExHq_API] = None
        self._hq_lock = threading.Lock()
        self._exhq_lock = threading.Lock()
    
    def _connect_hq(self) -> TdxHq_API:
        """连接标准行情服务器"""
        api = TdxHq_API()
        for server in HQ_SERVERS:
            try:
                api.connect(server["ip"], server["port"])
                logger.info(f"已连接标准行情服务器: {server['name']}")
                return api
            except Exception as e:
                logger.warning(f"连接 {server['name']} 失败: {e}")
        raise HTTPException(status_code=503, detail="无法连接到行情服务器")
    
    def _connect_exhq(self) -> TdxExHq_API:
        """连接扩展行情服务器"""
        api = TdxExHq_API()
        for server in EXHQ_SERVERS:
            try:
                api.connect(server["ip"], server["port"])
                logger.info(f"已连接扩展行情服务器: {server['name']}")
                return api
            except Exception as e:
                logger.warning(f"连接 {server['name']} 失败: {e}")
        raise HTTPException(status_code=503, detail="无法连接到扩展行情服务器")
    
    def get_hq_api(self) -> TdxHq_API:
        """获取标准行情 API (自动重连)"""
        with self._hq_lock:
            if self._hq_api is None:
                self._hq_api = self._connect_hq()
            else:
                # 检查连接是否有效，如果无效则重连
                try:
                    # 简单测试连接
                    self._hq_api.get_security_count(0)
                except Exception:
                    logger.warning("标准行情连接已断开，正在重连...")
                    self._hq_api = self._connect_hq()
            return self._hq_api
    
    def get_exhq_api(self) -> TdxExHq_API:
        """获取扩展行情 API (自动重连)"""
        with self._exhq_lock:
            if self._exhq_api is None:
                self._exhq_api = self._connect_exhq()
            else:
                # 检查连接是否有效
                try:
                    self._exhq_api.get_instrument_count()
                except Exception:
                    logger.warning("扩展行情连接已断开，正在重连...")
                    self._exhq_api = self._connect_exhq()
            return self._exhq_api
    
    def disconnect_all(self):
        """断开所有连接"""
        with self._hq_lock:
            if self._hq_api:
                try:
                    self._hq_api.disconnect()
                    logger.info("已断开标准行情连接")
                except Exception as e:
                    logger.error(f"断开标准行情连接失败: {e}")
                self._hq_api = None
        
        with self._exhq_lock:
            if self._exhq_api:
                try:
                    self._exhq_api.disconnect()
                    logger.info("已断开扩展行情连接")
                except Exception as e:
                    logger.error(f"断开扩展行情连接失败: {e}")
                self._exhq_api = None


# 全局连接管理器实例
connection_manager = TdxConnectionManager()


def get_hq_api() -> TdxHq_API:
    """获取标准行情 API 连接"""
    return connection_manager.get_hq_api()


def get_exhq_api() -> TdxExHq_API:
    """获取扩展行情 API 连接"""
    return connection_manager.get_exhq_api()


def shutdown_connections():
    """关闭所有连接 - 供 FastAPI 生命周期调用"""
    connection_manager.disconnect_all()


def _df_to_response(df) -> Response:
    """将 DataFrame 转换为 JSON Response"""
    if df is None or (hasattr(df, 'empty') and df.empty):
        return Response(content="[]", media_type="application/json")
    
    if isinstance(df, list):
        import pandas as pd
        df = pd.DataFrame(df)
    
    json_str = df.to_json(orient="records", force_ascii=False, date_format="iso")
    return Response(content=json_str, media_type="application/json")


# ============================================================
# 标准行情接口 (股票)
# ============================================================

@router.get("/stock/quotes", response_model=List[Dict[str, Any]])
async def get_stock_quotes(
    codes: str = Query("000001,600000", description="股票代码，逗号分隔，如: 000001,600000"),
):
    """
    获取股票实时行情
    
    - codes: 股票代码列表，逗号分隔
    - 深圳股票代码以 0/3 开头，上海股票代码以 6 开头
    """
    api = get_hq_api()
    try:
        code_list = [c.strip() for c in codes.split(",")]
        # 根据代码判断市场: 0=深圳, 1=上海
        params = []
        for code in code_list:
            market = 1 if code.startswith("6") else 0
            params.append((market, code))
        
        data = api.get_security_quotes(params)
        return _df_to_response(api.to_df(data) if data else None)
    except Exception as e:
        logger.error(f"获取股票行情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/bars", response_model=List[Dict[str, Any]])
async def get_stock_bars(
    code: str = Query("000001", description="股票代码"),
    market: int = Query(0, description="市场: 0=深圳, 1=上海"),
    category: int = Query(9, description="K线类型: 0=5分钟, 1=15分钟, 2=30分钟, 3=1小时, 4=日线, 9=日线"),
    start: int = Query(0, description="起始位置"),
    count: int = Query(100, description="获取数量，最大800"),
):
    """获取股票K线数据"""
    api = get_hq_api()
    try:
        data = api.get_security_bars(category, market, code, start, min(count, 800))
        return _df_to_response(api.to_df(data) if data else None)
    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/count")
async def get_stock_count(
    market: int = Query(0, description="市场: 0=深圳, 1=上海"),
):
    """获取市场股票数量"""
    api = get_hq_api()
    try:
        count = api.get_security_count(market)
        return {"market": market, "count": count}
    except Exception as e:
        logger.error(f"获取股票数量失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/list", response_model=List[Dict[str, Any]])
async def get_stock_list(
    market: int = Query(0, description="市场: 0=深圳, 1=上海"),
    start: int = Query(0, description="起始位置"),
):
    """获取股票列表"""
    api = get_hq_api()
    try:
        data = api.get_security_list(market, start)
        return _df_to_response(api.to_df(data) if data else None)
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/index_bars", response_model=List[Dict[str, Any]])
async def get_index_bars(
    code: str = Query("000001", description="指数代码"),
    market: int = Query(1, description="市场: 1=上海"),
    category: int = Query(9, description="K线类型: 9=日线"),
    start: int = Query(0, description="起始位置"),
    count: int = Query(100, description="获取数量"),
):
    """获取指数K线数据"""
    api = get_hq_api()
    try:
        data = api.get_index_bars(category, market, code, start, min(count, 800))
        return _df_to_response(api.to_df(data) if data else None)
    except Exception as e:
        logger.error(f"获取指数K线失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/minute", response_model=List[Dict[str, Any]])
async def get_stock_minute(
    code: str = Query("000001", description="股票代码"),
    market: int = Query(0, description="市场: 0=深圳, 1=上海"),
):
    """查询分时行情"""
    api = get_hq_api()
    try:
        data = api.get_minute_time_data(market, code)
        return _df_to_response(api.to_df(data) if data else None)
    except Exception as e:
        logger.error(f"获取分时行情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/transaction", response_model=List[Dict[str, Any]])
async def get_stock_transaction(
    code: str = Query("000001", description="股票代码"),
    market: int = Query(0, description="市场: 0=深圳, 1=上海"),
    start: int = Query(0, description="起始位置"),
    count: int = Query(100, description="获取数量"),
):
    """查询分笔成交"""
    api = get_hq_api()
    try:
        data = api.get_transaction_data(market, code, start, count)
        return _df_to_response(api.to_df(data) if data else None)
    except Exception as e:
        logger.error(f"获取分笔成交失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/xdxr", response_model=List[Dict[str, Any]])
async def get_stock_xdxr(
    code: str = Query("000001", description="股票代码"),
    market: int = Query(0, description="市场: 0=深圳, 1=上海"),
):
    """读取除权除息信息"""
    api = get_hq_api()
    try:
        data = api.get_xdxr_info(market, code)
        return _df_to_response(api.to_df(data) if data else None)
    except Exception as e:
        logger.error(f"获取除权除息信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/finance")
async def get_stock_finance(
    code: str = Query("000001", description="股票代码"),
    market: int = Query(0, description="市场: 0=深圳, 1=上海"),
):
    """读取财务信息"""
    api = get_hq_api()
    try:
        data = api.get_finance_info(market, code)
        return data if data else {}
    except Exception as e:
        logger.error(f"获取财务信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 扩展行情接口 (期货)
# ============================================================

@router.get("/futures/markets", response_model=List[Dict[str, Any]])
async def get_futures_markets():
    """获取期货市场列表"""
    api = get_exhq_api()
    try:
        data = api.get_markets()
        return _df_to_response(api.to_df(data) if data else None)
    except Exception as e:
        logger.error(f"获取市场列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/futures/instrument_count")
async def get_futures_instrument_count():
    """获取合约数量"""
    api = get_exhq_api()
    try:
        count = api.get_instrument_count()
        return {"count": count}
    except Exception as e:
        logger.error(f"获取合约数量失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/futures/instruments", response_model=List[Dict[str, Any]])
async def get_futures_instruments(
    start: int = Query(0, description="起始位置"),
    count: int = Query(100, description="获取数量"),
):
    """获取合约信息列表"""
    api = get_exhq_api()
    try:
        data = api.get_instrument_info(start, count)
        return _df_to_response(api.to_df(data) if data else None)
    except Exception as e:
        logger.error(f"获取合约信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/futures/quote", response_model=List[Dict[str, Any]])
async def get_futures_quote(
    code: str = Query("IFL0", description="合约代码"),
    market: int = Query(47, description="市场ID，可通过 /futures/markets 获取"),
):
    """查询期货五档行情"""
    api = get_exhq_api()
    try:
        data = api.get_instrument_quote(market, code)
        return _df_to_response(api.to_df(data) if data else None)
    except Exception as e:
        logger.error(f"获取五档行情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/futures/minute", response_model=List[Dict[str, Any]])
async def get_futures_minute(
    code: str = Query("IFL0", description="合约代码"),
    market: int = Query(47, description="市场ID"),
):
    """查询期货分时行情"""
    api = get_exhq_api()
    try:
        data = api.get_minute_time_data(market, code)
        return _df_to_response(api.to_df(data) if data else None)
    except Exception as e:
        logger.error(f"获取分时行情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/futures/bars", response_model=List[Dict[str, Any]])
async def get_futures_bars(
    code: str = Query("IFL0", description="合约代码"),
    market: int = Query(47, description="市场ID"),
    category: int = Query(0, description="K线类型: 0=5分钟, 1=15分钟, 2=30分钟, 3=1小时, 4=日线"),
    start: int = Query(0, description="起始位置"),
    count: int = Query(100, description="获取数量"),
):
    """查询期货K线数据"""
    api = get_exhq_api()
    try:
        data = api.get_instrument_bars(category, market, code, start, count)
        return _df_to_response(api.to_df(data) if data else None)
    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/futures/transaction", response_model=List[Dict[str, Any]])
async def get_futures_transaction(
    code: str = Query("IFL0", description="合约代码"),
    market: int = Query(47, description="市场ID"),
    start: int = Query(0, description="起始位置"),
    count: int = Query(100, description="获取数量"),
):
    """查询期货分笔成交"""
    api = get_exhq_api()
    try:
        data = api.get_transaction_data(market, code, start, count)
        return _df_to_response(api.to_df(data) if data else None)
    except Exception as e:
        logger.error(f"获取分笔成交失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
