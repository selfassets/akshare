import logging
import uvicorn
from fastapi import FastAPI
from akshare.api.routers import futures

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AKShare API",
    description="AKShare HTTP API interface",
    version="0.0.1",
)

app.include_router(futures.router, prefix="/futures", tags=["futures"])

@app.get("/")
async def root():
    return {
        "name": "AKShare API",
        "version": "0.0.1",
        "description": "AKShare HTTP API interface",
        "documentation": "/docs",
        "endpoints": [
            "/futures"
        ]
    }


if __name__ == "__main__":
    logger.info("启动 AKShare API 服务器...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )

