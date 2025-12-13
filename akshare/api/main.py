import logging
import uvicorn
import os
import signal
import atexit
from contextlib import asynccontextmanager
from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from akshare.api.routers import futures,open,chanlun,tdx
from akshare.api.routers.tdx import shutdown_connections

# 获取日志级别，默认为 INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 标记是否已清理
_cleanup_done = False


def cleanup():
    """清理函数 - 断开所有 TDX 连接"""
    global _cleanup_done
    if _cleanup_done:
        return
    _cleanup_done = True
    logger.info("正在关闭 TDX 连接...")
    shutdown_connections()
    logger.info("TDX 连接已关闭")


def signal_handler(signum, frame):
    """信号处理器 - 捕获 SIGTERM 和 SIGINT"""
    sig_name = signal.Signals(signum).name
    logger.info(f"收到信号 {sig_name}，正在优雅关闭...")
    cleanup()
    # 重新引发信号以便正常退出
    signal.signal(signum, signal.SIG_DFL)
    os.kill(os.getpid(), signum)


# 注册信号处理器
signal.signal(signal.SIGTERM, signal_handler)  # kill 命令默认信号
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C

# 注册 atexit 作为最后保障
atexit.register(cleanup)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("AKShare API 启动中...")
    yield
    # 应用关闭时断开所有 TDX 连接
    cleanup()
    logger.info("AKShare API 已关闭")


app = FastAPI(
    title="AKShare API",
    description="AKShare HTTP API interface",
    version="0.0.1",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(futures.router, prefix="/futures", tags=["futures"])
app.include_router(open.router, prefix="/open", tags=["open"])
app.include_router(chanlun.router, prefix="/chanlun", tags=["chanlun"])
app.include_router(tdx.router, prefix="/tdx", tags=["tdx"])

@app.get("/")
async def root(request: Request):
    return {
        "name": "AKShare API",
        "ip_address": request.headers["host"],
        "version": "0.0.1",
        "description": "AKShare HTTP API interface",
        "documentation": "/docs",
        "endpoints": [
            "/futures",
            "/chanlun",
            "/tdx"
        ]
    }


if __name__ == "__main__":
    logger.info(f"启动 AKShare API 服务器... Log Level: {LOG_LEVEL}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=LOG_LEVEL.lower(),
        reload=False
    )
