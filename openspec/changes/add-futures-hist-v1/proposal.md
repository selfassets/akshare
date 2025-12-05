# Change: Add Futures History V1 API

## Why

User added a new function `futures_hist_em_v1` to `akshare/futures/futures_hist_em.py` and requested to expose it as an API endpoint.

## What Changes

- Add `/futures_hist_em_v1` endpoint to `akshare/api/routers/futures.py`.
- Import `futures_hist_em_v1` from `akshare/futures/futures_hist_em.py` in the router.

## Impact

- **Affected code**: `akshare/api/routers/futures.py`
