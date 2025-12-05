## ADDED Requirements

### Requirement: Futures Exchange Symbol Raw Data

The system SHALL provide an API endpoint to fetch raw exchange symbol data from EastMoney.

#### Scenario: Fetch Raw Data

- **WHEN** a GET request is made to `/futures_exchange_symbol_raw_em`
- **THEN** return a list of exchange symbol objects
