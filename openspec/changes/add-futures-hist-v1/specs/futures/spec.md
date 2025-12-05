## ADDED Requirements

### Requirement: Futures History V1

The system SHALL provide a V1 API endpoint for futures history data.

#### Scenario: Get History

- **WHEN** GET `/futures_hist_em_v1` is called with parameters `symbol`, `period`, `start_date`, `end_date`, `sec_id`
- **THEN** returns historical data as JSON
