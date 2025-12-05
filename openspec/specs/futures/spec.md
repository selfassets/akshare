# futures Specification

## Purpose
TBD - created by archiving change add-futures-raw-api. Update Purpose after archive.
## Requirements
### Requirement: Futures Exchange Symbol Raw Data

The system SHALL provide an API endpoint to fetch raw exchange symbol data from EastMoney.

#### Scenario: Fetch Raw Data

- **WHEN** a GET request is made to `/futures_exchange_symbol_raw_em`
- **THEN** return a list of exchange symbol objects

### Requirement: API Localization

All API endpoint parameters SHALL have Chinese descriptions.

#### Scenario: Check Descriptions

- **WHEN** inspecting the OpenAPI schema
- **THEN** parameter descriptions are in Chinese

