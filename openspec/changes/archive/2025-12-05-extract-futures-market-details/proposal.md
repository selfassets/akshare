# Change: Extract Futures Market Details API

## Why

User requested to extract the market details fetching logic (lines 81-98 of `futures_hist_em.py`) into a dedicated function and expose it as a new API endpoint.

## What Changes

- **New Function**: `fetch_futures_market_details_em(market_id)` in `akshare/futures/futures_hist_em.py`.
- **New API**: `/futures_market_details_em` in `akshare/api/routers/futures.py` accepting `market_id` query param.

## Impact

- **Affected specs**: `futures`
- **Affected code**: `akshare/futures/futures_hist_em.py`, `akshare/api/routers/futures.py`
