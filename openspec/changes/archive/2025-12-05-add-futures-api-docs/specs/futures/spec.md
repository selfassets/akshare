## ADDED Requirements

### Requirement: Futures Fee Information

The system SHALL provide an API to fetch futures fee information.

#### Scenario: Fetch Fee Info

- **WHEN** a GET request is made to `/futures_comm_info`
- **THEN** returns fee information
- **AND** parameter descriptions are in Chinese

## ADDED Requirements

### Requirement: API Localization

All API endpoint parameters SHALL have Chinese descriptions.

#### Scenario: Check Descriptions

- **WHEN** inspecting the OpenAPI schema
- **THEN** parameter descriptions are in Chinese
