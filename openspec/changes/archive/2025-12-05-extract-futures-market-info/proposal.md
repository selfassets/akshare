# Change: Extract Futures Market Info API

## Why

User requested to extract the market information fetching logic (lines 49-59 of `futures_hist_em.py`) into a dedicated function and expose it as a new API endpoint.

## What Changes

- **New Function**: `fetch_futures_market_info_em` in `akshare/futures/futures_hist_em.py`.
- **New API**: `/futures_market_info_em` in `akshare/api/routers/futures.py`.

## Impact

- **Affected specs**: `futures`
- **Affected code**: `akshare/futures/futures_hist_em.py`, `akshare/api/routers/futures.py`
