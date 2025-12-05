# Project Context

## Purpose

AKShare is a Python-based financial data interface library that simplifies the process of fetching financial data. It aims to provide a unified interface for various financial data sources (stocks, futures, funds, bonds, etc.) for quantitative research and data analysis.
"Write less, get more!"

## Tech Stack

- **Primary Language**: Python (3.9+)
- **Data Handling**: Pandas, Requests
- **Plotting**: Matplotlib, mplfinance

## Project Conventions

### Code Style

- **Formatter**: [Ruff](https://github.com/astral-sh/ruff) is used for code formatting and linting.
- **Configuration**: See `pyproject.toml` for specific Ruff rules (e.g., line-length 88, double quotes).

### Architecture Patterns

- **Modular Data Fetching**: Data fetching logic is organized by data source/market type (e.g., `akshare/api/routers/futures.py`).
- **Unified Interface**: Functions typically return Pandas DataFrames.

### Testing Strategy

- **Local Testing**: Users can run test scripts locally.
- **CI/CD**: GitHub Actions used for release and deployment `release_and_deploy.yml`.

### Git Workflow

- **Pull Requests**: Contributions via PRs are welcome.
- **Branching**: Standard fork-and-pull model used.

## Domain Context

- **Financial Markets**: Chinese stocks (A-share), US stocks, Futures, Funds, Bonds, Macroeconomic data.
- **Quant Research**: Data is structured for easy integration with backtesting and analysis tools.

## Important Constraints

- **Data Dependence**: Relies on external third-party data sources which may change or become unavailable.
- **Academic/Research Use**: Data is primarily for research; investment decisions should be cautious.

## External Dependencies

- **Data Sources**: EastMoney, Sina Finance, Jin10, etc. (See README Acknowledgement).
