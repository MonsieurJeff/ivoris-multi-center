# Acceptance Criteria

**Ivoris Multi-Center Extraction Pipeline** (Extension Challenge)

---

## Context: Two-Part Challenge

This acceptance criteria covers the **extension challenge**. The main challenge acceptance criteria is in [ivoris-pipeline/ACCEPTANCE.md](../ivoris-pipeline/ACCEPTANCE.md).

| Challenge | Output Fields | Acceptance Status |
|-----------|---------------|-------------------|
| **Main (ivoris-pipeline)** | date, patient_id, insurance_status, chart_entry, service_codes | ✅ All scenarios pass |
| **Extension (this)** | Same fields + center_id, center_name | ✅ All scenarios pass |

---

## Feature: Schema Auto-Discovery

```gherkin
Feature: Schema Auto-Discovery
  As a data engineer
  I want to automatically discover database schemas
  So that I can extract data without manual configuration

  Scenario: Discover tables from database
    Given a database "DentalDB_A1" with tables suffixed "_A1"
    When I run schema introspection
    Then I should discover table "KARTEI_A1" as canonical "KARTEI"
    And I should discover table "PATIENT_A1" as canonical "PATIENT"
    And I should discover table "KASSEN_A1" as canonical "KASSEN"

  Scenario: Discover columns from tables
    Given table "KARTEI_A1" exists with columns "PATNR_A1", "DATUM_A1", "BEMERKUNG_A1"
    When I introspect the table
    Then I should map "PATNR_A1" to canonical "PATNR"
    And I should map "DATUM_A1" to canonical "DATUM"
    And I should map "BEMERKUNG_A1" to canonical "BEMERKUNG"

  Scenario: Generate SQL with discovered names
    Given I have discovered schema for "center_01" with suffix "A1"
    When I generate a query for chart entries
    Then the SQL should reference "KARTEI_A1" not "KARTEI"
    And the SQL should reference "PATNR_A1" not "PATNR"

  Scenario: Cache discovered schema
    Given I have introspected "center_01" once
    When I request the schema again
    Then it should return from cache
    And no database query should be made
```

---

## Feature: Multi-Center Extraction

```gherkin
Feature: Multi-Center Extraction
  As an operations manager
  I want to extract data from all 10 dental centers
  So that I have a unified view of daily activity

  Scenario: Extract from all centers
    Given 10 dental center databases are configured
    And each has chart entries for "2022-01-18"
    When I run extraction with "--extract-all --date 2022-01-18"
    Then I should receive entries from all 10 centers
    And each entry should have a "center_id" field
    And the output should be in canonical format

  Scenario: Extract from specific center
    Given center "center_03" is configured
    When I run extraction with "--center center_03 --date 2022-01-18"
    Then I should only receive entries from "center_03"

  Scenario: Handle missing center gracefully
    Given center "center_99" does not exist
    When I run extraction with "--center center_99"
    Then I should receive an error message
    And the exit code should be non-zero
```

---

## Feature: Performance

```gherkin
Feature: Performance
  As an operations manager
  I want fast extraction from all centers
  So that daily reports are available quickly

  Scenario: Parallel extraction meets target
    Given 10 centers each with 1000 chart entries
    When I run extraction with "--extract-all --benchmark"
    Then the total extraction time should be less than 5 seconds
    And extraction should use parallel connections

  Scenario: Connection pooling is efficient
    Given I extract from the same center 10 times
    When I measure connection overhead
    Then connections should be reused
    And total time should be less than 10 individual connections
```

---

## Feature: Adapter Pattern

```gherkin
Feature: Adapter Pattern
  As a developer
  I want clean separation between centers
  So that adding new centers is easy

  Scenario: Factory creates adapter via introspection
    Given database "DentalDB_C3" exists
    When I request an adapter for "center_03"
    Then the factory should introspect the database
    And return a CenterAdapter with discovered schema
    And the adapter should be cached for reuse

  Scenario: Add new center without code changes
    Given a new database "DentalDB_K1" is created
    And it follows the naming pattern with suffix "_K1"
    When I add connection config for "center_11"
    And run extraction with "--center center_11"
    Then schema should be auto-discovered
    And extraction should work without code changes

  Scenario: Adapter generates correct queries
    Given an adapter for "center_03" with suffix "_C3"
    When I call extract_chart_entries(date)
    Then the generated SQL should use "KARTEI_C3"
    And join with "PATIENT_C3" on "PATNR_C3"
```

---

## Feature: Output Format

```gherkin
Feature: Output Format
  As a data consumer
  I want unified output regardless of source
  So that downstream systems work consistently

  Scenario: JSON output includes center metadata
    Given I extract from all centers
    When I output as JSON
    Then each entry should have:
      | field            | type   |
      | center_id        | string |
      | date             | string |
      | patient_id       | int    |
      | insurance_status | string |
      | chart_entry      | string |
      | service_codes    | array  |

  Scenario: CSV output is flat
    Given I extract from all centers
    When I output as CSV
    Then the CSV should have columns:
      | center_id | date | patient_id | insurance_status | chart_entry | service_codes |
    And all rows should follow the same format
```

---

## Quality Gates

| Check | Requirement |
|-------|-------------|
| `npm run check:sandbox` | ✅ Pass |
| No print() statements | ✅ Pass |
| No bare except clauses | ✅ Pass |
| All functions <50 lines | ✅ Pass |
| Parallel extraction works | ✅ Pass |
| <5s for 10 centers | ✅ Pass |
