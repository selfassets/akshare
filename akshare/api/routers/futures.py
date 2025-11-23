from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
import pandas as pd
from akshare.futures.futures_hist_em import futures_hist_em

router = APIRouter(prefix="/futures", tags=["futures"])


@router.get("/futures_hist_em", response_model=List[Dict[str, Any]])
async def get_futures_hist_em(
		symbol: str = Query("热卷主连", description="期货代码"),
		period: str = Query("daily", description="周期: daily, weekly, monthly"),
		start_date: str = Query("19900101", description="开始日期 YYYYMMDD"),
		end_date: str = Query("20500101", description="结束日期 YYYYMMDD"),
):
	"""
	获取东方财富网-期货行情-行情数据
	"""
	try:
		df = futures_hist_em(
			symbol=symbol,
			period=period,
			start_date=start_date,
			end_date=end_date
		)
		if df.empty:
			return []

		# Convert DataFrame to list of dicts, handling date serialization
		data = df.to_dict(orient="records")
		return data
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))
