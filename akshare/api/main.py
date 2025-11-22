from fastapi import FastAPI
from akshare.api.routers import futures

app = FastAPI(
    title="AKShare API",
    description="AKShare HTTP API interface",
    version="0.0.1",
)

app.include_router(futures.router, prefix="/futures", tags=["futures"])

@app.get("/")
async def root():
    return {"message": "Welcome to AKShare API"}
