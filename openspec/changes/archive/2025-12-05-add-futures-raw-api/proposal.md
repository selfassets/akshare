# Change: Add Futures Exchange Symbol Raw API

## Why

User requested to expose the `__fetch_exchange_symbol_raw_em` function as an API interface. This allows consumers to access the raw exchange symbol data directly via HTTP.

## What Changes

- **Rename**: `__fetch_exchange_symbol_raw_em` -> `fetch_exchange_symbol_raw_em` in `akshare/futures/futures_hist_em.py` to make it public.
- **New API**: Add `/futures_exchange_symbol_raw_em` endpoint in `akshare/api/routers/futures.py`.

## Impact

- **Affected specs**: `futures`
- **Affected code**:
  - `akshare/futures/futures_hist_em.py`
  - `akshare/api/routers/futures.py`
