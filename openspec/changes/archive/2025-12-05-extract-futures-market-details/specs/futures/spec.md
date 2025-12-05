## ADDED Requirements

### Requirement: Futures Market Details

The system SHALL provide an API endpoint to fetch details for a specific futures market.

#### Scenario: Fetch Market Details

- **WHEN** a GET request is made to `/futures_market_details_em` with a `market_id`
- **THEN** returns a list of symbol details for that market
