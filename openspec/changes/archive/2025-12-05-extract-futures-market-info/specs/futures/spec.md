## ADDED Requirements

### Requirement: Futures Market Information

The system SHALL provide an API endpoint to fetch futures market information (list of markets).

#### Scenario: Fetch Market Info

- **WHEN** a GET request is made to `/futures_market_info_em`
- **THEN** returns a list of market information objects (containing mktid, mktname, etc.)
