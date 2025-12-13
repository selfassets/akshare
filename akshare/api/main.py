import logging
import uvicorn
import os
from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from akshare.api.routers import futures,open,czsc,chanlun

# 获取日志级别，默认为 INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AKShare API",
    description="AKShare HTTP API interface",
    version="0.0.1",
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
app.include_router(czsc.router, prefix="/czsc", tags=["czsc"])
app.include_router(chanlun.router, prefix="/chanlun", tags=["chanlun"])

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
            "/czsc",
            "/chanlun"
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

