# Change: Revert Futures Raw Refactor

## Why

User requested to revert the refactoring of `__fetch_exchange_symbol_raw_em` in `akshare/futures/futures_hist_em.py`. It should not be modified to use new helper functions.

## What Changes

- Revert logic in `__fetch_exchange_symbol_raw_em` to its original state (self-contained fetching and looping).
- Keep `fetch_futures_market_info_em` and `fetch_futures_market_details_em` as they are needed for the new API endpoints.

## Impact

- **Affected code**: `akshare/futures/futures_hist_em.py`
