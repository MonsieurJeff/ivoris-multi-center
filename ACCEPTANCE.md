# Acceptance Criteria

**Ivoris Extraction Pipeline** | Unified Gherkin Scenarios

---

## Overview

| Part | Challenge | Scenarios | Status |
|------|-----------|-----------|--------|
| **Part 1** | Daily Extraction Pipeline | 7 scenarios | ✅ All pass |
| **Part 2** | Multi-Center Scale | 12 scenarios | ✅ All pass |

---

# Part 1: Daily Extraction Pipeline

## Feature: Daily Chart Entry Extraction

```gherkin
Feature: Daily Chart Entry Extraction
  As a dental practice administrator
  I want to extract daily chart entries with patient and insurance information
  So that I can transfer data to external systems automatically
```

### Scenario 1.1: Extract chart entries for a specific date ✅

```gherkin
Scenario: Extract chart entries for a specific date
  Given the Ivoris database is connected
  And chart entries exist for date "2022-01-18"
  When I run the daily extraction for "2022-01-18"
  Then the output should contain all chart entries from that date
  And each entry should include:
    | Field            | Description                    |
    | date             | Entry date (ISO 8601)          |
    | patient_id       | Patient identifier             |
    | insurance_status | GKV/PKV/Selbstzahler           |
    | chart_entry      | Medical record text            |
    | service_codes    | Treatment codes                |
```

### Scenario 1.2: Output to CSV format ✅

```gherkin
Scenario: Output to CSV format
  Given chart entries exist for the target date
  When I run extraction with "--format csv"
  Then a CSV file should be created at "data/output/ivoris_chart_entries_YYYY-MM-DD.csv"
  And the CSV should have headers:
    | date | patient_id | insurance_status | insurance_name | chart_entry | service_codes |
  And German characters (ä, ö, ü, ß) should be encoded as UTF-8
```

### Scenario 1.3: Output to JSON format ✅

```gherkin
Scenario: Output to JSON format
  Given chart entries exist for the target date
  When I run extraction with "--format json"
  Then a JSON file should be created at "data/output/ivoris_chart_entries_YYYY-MM-DD.json"
  And the JSON should have structure:
    {
      "extraction_timestamp": "...",
      "target_date": "2022-01-18",
      "record_count": N,
      "entries": [...]
    }
  And service_codes should be an array of strings
```

### Scenario 1.4: Insurance status mapping ✅

```gherkin
Scenario: Insurance status mapping
  Given a patient has KASSE.TYP = "G"
  Then insurance_status should be "GKV"

  Given a patient has KASSE.TYP = "P"
  Then insurance_status should be "PKV"

  Given a patient has no insurance reference (KASSEID is NULL)
  Then insurance_status should be "Selbstzahler"
```

### Scenario 1.5: Link services to chart entries ✅

```gherkin
Scenario: Link services to chart entries
  Given a chart entry exists for patient 1 on date "2022-01-18"
  And treatments exist in LEISTUNG for patient 1 on date "2022-01-18":
    | LEISTUNG |
    | 01       |
    | Ä1       |
    | 2060     |
  When the daily extraction runs
  Then the entry should have service_codes = ["01", "Ä1", "2060"]
```

### Scenario 1.6: Handle empty results ✅

```gherkin
Scenario: Handle empty results
  Given no chart entries exist for date "2026-12-25"
  When I run the daily extraction for "2026-12-25"
  Then the output file should be created
  And it should contain zero entries
  And the extraction should complete successfully (exit code 0)
```

### Scenario 1.7: Default to yesterday ✅

```gherkin
Scenario: Default to yesterday
  Given today is "2026-01-13"
  When I run extraction without specifying a date
  Then the extraction should target "2026-01-12" (yesterday)
```

---

# Part 2: Multi-Center Scale

## Feature: Schema Auto-Discovery

```gherkin
Feature: Schema Auto-Discovery
  As a data engineer
  I want to automatically discover database schemas
  So that I can extract data without manual configuration
```

### Scenario 2.1: Discover tables from database ✅

```gherkin
Scenario: Discover tables from database
  Given a database "DentalDB_01" with randomly suffixed tables
  When I run schema discovery
  Then I should discover table "KARTEI_MN" as canonical "KARTEI"
  And I should discover table "PATIENT_XY" as canonical "PATIENT"
  And I should discover table "KASSEN_AB" as canonical "KASSEN"
```

### Scenario 2.2: Discover columns from tables ✅

```gherkin
Scenario: Discover columns from tables
  Given table "KARTEI_MN" exists with columns "PATNR_NAN6", "DATUM_3A4", "BEMERKUNG_X7K"
  When I introspect the table
  Then I should map "PATNR_NAN6" to canonical "PATNR"
  And I should map "DATUM_3A4" to canonical "DATUM"
  And I should map "BEMERKUNG_X7K" to canonical "BEMERKUNG"
```

### Scenario 2.3: Generate SQL with discovered names ✅

```gherkin
Scenario: Generate SQL with discovered names
  Given I have discovered schema for "center_01" with suffix "MN"
  When I generate a query for chart entries
  Then the SQL should reference "KARTEI_MN" not "KARTEI"
  And the SQL should reference "PATNR_NAN6" not "PATNR"
```

## Feature: Multi-Center Extraction

```gherkin
Feature: Multi-Center Extraction
  As an operations manager
  I want to extract data from all 30 dental centers
  So that I have a unified view of daily activity
```

### Scenario 2.4: Extract from all centers ✅

```gherkin
Scenario: Extract from all centers
  Given 30 dental center databases are configured
  And each has chart entries for "2022-01-18"
  When I run extraction with "--date 2022-01-18"
  Then I should receive entries from all 30 centers
  And each entry should have a "center_id" field
  And the output should be in canonical format
```

### Scenario 2.5: Extract from specific center ✅

```gherkin
Scenario: Extract from specific center
  Given center "center_03" is configured
  When I run extraction with "-c center_03 --date 2022-01-18"
  Then I should only receive entries from "center_03"
```

### Scenario 2.6: Handle missing center gracefully ✅

```gherkin
Scenario: Handle missing center gracefully
  Given center "center_99" does not exist
  When I run extraction with "-c center_99"
  Then I should receive an error message
  And the exit code should be non-zero
```

## Feature: Human Review Workflow

```gherkin
Feature: Human Review Workflow
  As a production administrator
  I want to review schema mappings before extraction
  So that I can catch errors before they corrupt data
```

### Scenario 2.7: Mappings generated with review flag ✅

```gherkin
Scenario: Mappings generated with review flag
  Given I run "generate-mappings" for center_01
  When the mapping file is created
  Then it should have "reviewed: false" by default
  And it should be in JSON format for human readability
```

### Scenario 2.8: Show mapping for review ✅

```gherkin
Scenario: Show mapping for review
  Given a mapping file exists for center_01
  When I run "show-mapping center_01"
  Then I should see the canonical → actual name mappings
  And I should see the "reviewed" status
```

## Feature: Performance

```gherkin
Feature: Performance
  As an operations manager
  I want fast extraction from all centers
  So that daily reports are available quickly
```

### Scenario 2.9: Parallel extraction meets target ✅

```gherkin
Scenario: Parallel extraction meets target
  Given 30 centers each with chart entries
  When I run benchmark
  Then the total extraction time should be less than 5 seconds
  And extraction should use parallel connections
```

## Feature: Unified Output Format

```gherkin
Feature: Unified Output Format
  As a data consumer
  I want unified output regardless of source
  So that downstream systems work consistently
```

### Scenario 2.10: JSON output includes center metadata ✅

```gherkin
Scenario: JSON output includes center metadata
  Given I extract from all centers
  When I output as JSON
  Then each entry should have:
    | field            | type   |
    | center_id        | string |
    | center_name      | string |
    | date             | string |
    | patient_id       | int    |
    | insurance_status | string |
    | chart_entry      | string |
    | service_codes    | array  |
```

### Scenario 2.11: CSV output is flat ✅

```gherkin
Scenario: CSV output is flat
  Given I extract from all centers
  When I output as CSV
  Then the CSV should have columns:
    | center_id | center_name | date | patient_id | insurance_status | chart_entry | service_codes |
  And all rows should follow the same format
```

### Scenario 2.12: Web UI available for exploration ✅

```gherkin
Scenario: Web UI available for exploration
  Given the web server is running
  When I navigate to http://localhost:8000/explore
  Then I should see a list of centers
  And I should be able to view schema mappings
  And I should be able to extract data for a selected date
```

---

# Summary

## Part 1 Results

| # | Scenario | Status |
|---|----------|--------|
| 1.1 | Extract chart entries for date | ✅ Pass |
| 1.2 | CSV output format | ✅ Pass |
| 1.3 | JSON output format | ✅ Pass |
| 1.4 | Insurance status mapping | ✅ Pass |
| 1.5 | Link services to entries | ✅ Pass |
| 1.6 | Handle empty results | ✅ Pass |
| 1.7 | Default to yesterday | ✅ Pass |

## Part 2 Results

| # | Scenario | Status |
|---|----------|--------|
| 2.1 | Discover tables | ✅ Pass |
| 2.2 | Discover columns | ✅ Pass |
| 2.3 | Generate SQL with discovered names | ✅ Pass |
| 2.4 | Extract from all centers | ✅ Pass |
| 2.5 | Extract from specific center | ✅ Pass |
| 2.6 | Handle missing center | ✅ Pass |
| 2.7 | Mappings with review flag | ✅ Pass |
| 2.8 | Show mapping for review | ✅ Pass |
| 2.9 | Parallel extraction performance | ✅ Pass |
| 2.10 | JSON output with center metadata | ✅ Pass |
| 2.11 | CSV output is flat | ✅ Pass |
| 2.12 | Web UI available | ✅ Pass |

---

## Test Commands

### Part 1: ivoris-pipeline

```bash
cd ~/Projects/outre_base/sandbox/ivoris-pipeline

# Test database connection
python src/main.py --test-connection

# Run extraction
python src/main.py --daily-extract --date 2022-01-18

# Verify output
cat data/output/ivoris_chart_entries_2022-01-18.json
```

### Part 2: ivoris-multi-center

```bash
cd ~/Projects/outre_base/sandbox/ivoris-multi-center

# List centers
python -m src.cli list

# Discover raw schema
python -m src.cli discover-raw -c center_01

# Show mapping
python -m src.cli show-mapping center_01

# Extract
python -m src.cli extract --date 2022-01-18

# Benchmark
python -m src.cli benchmark

# Web UI
python -m src.cli web
```

---

## Definition of Done

Both challenges are complete when:

### Part 1
- [x] All 7 scenarios pass
- [x] CLI command `--daily-extract` works
- [x] CSV output file is correct
- [x] JSON output file is correct
- [x] Insurance status is properly resolved
- [x] Service codes are linked to chart entries

### Part 2
- [x] All 12 scenarios pass
- [x] 30 centers discovered and mapped
- [x] Pattern matching works for random schemas
- [x] Human review workflow implemented
- [x] Benchmark passes (<5s target, actual ~466ms)
- [x] Web UI functional
