# Acceptance Criteria: Automatic Schema Matching

**Architecture:** MCP-Native Agent
**Status:** Design

---

## Overview

These acceptance criteria validate the MCP-native schema matching agent.

---

## 1. Agent Core Behavior

### 1.1 Schema Exploration

```gherkin
Feature: Schema Exploration

  Scenario: Agent lists tables
    Given a connected database with 10 tables
    When the agent starts mapping
    Then it should call list_tables
    And identify tables relevant to dental practice

  Scenario: Agent examines columns
    Given the agent has identified table "PATIENT"
    When it explores the table
    Then it should call describe_table
    And sample relevant columns
    And check column names against value bank

  Scenario: Agent handles empty database
    Given a database with no tables
    When the agent starts mapping
    Then it should report "No tables found"
    And complete without errors
```

### 1.2 Mapping Proposals

```gherkin
Feature: Mapping Proposals

  Scenario: High-confidence auto-accept
    Given trust profile "standard" (threshold 0.90)
    When the agent finds column "PATNR" with INT values 1001, 1002, 1003
    And value bank confirms "PATNR" → patient_id
    Then confidence should be >= 0.95
    And mapping should be auto-accepted

  Scenario: Medium-confidence review
    Given trust profile "standard" (threshold 0.90)
    When the agent finds column "NOTIZEN" with text values
    And value bank has no exact match
    But fuzzy match suggests "chart_note" at 0.82 confidence
    Then mapping should be marked "pending_review"
    And a review item should be created

  Scenario: Low-confidence rejection
    Given trust profile "standard" (review threshold 0.70)
    When the agent finds column "XYZ123" with random values
    And no value bank matches
    And confidence is 0.45
    Then mapping should be rejected
    And reason should be recorded
```

### 1.3 Problem Detection

```gherkin
Feature: Problem Detection

  Scenario: Detect empty column
    Given column "FAX" with 100% NULL values
    When the agent analyzes the column
    Then it should call flag_column with issue "empty"
    And the column should be auto-excluded

  Scenario: Detect mostly empty column
    Given column "MOBILE" with 97% NULL values
    When the agent analyzes the column
    Then it should call flag_column with issue "mostly_empty"
    And a review item should be created

  Scenario: Detect abandoned column
    Given column "OLD_STATUS" with no values after 2022-01-01
    When the agent analyzes the column
    Then it should call flag_column with issue "abandoned"
    And evidence should include last update date

  Scenario: Detect test data
    Given column "DEBUG_FLAG" with values "TEST", "XXX", "DEBUG"
    When the agent analyzes the column
    Then it should call flag_column with issue "test_data"
```

---

## 2. MCP Servers

### 2.1 Database Server

```gherkin
Feature: Database Server Tools

  Scenario: list_tables returns metadata
    Given a database with tables PATIENT, KARTEI, KASSEN
    When I call list_tables()
    Then I should receive 3 table objects
    And each should have table_name and row_count

  Scenario: describe_table returns columns
    Given table PATIENT with columns PATNR, NAME, GEBDAT
    When I call describe_table("PATIENT")
    Then I should receive 3 column objects
    And each should have column_name, data_type, nullable
    And PATNR should be marked as primary_key

  Scenario: sample_column returns values
    Given column PATIENT.NAME with 100 distinct values
    When I call sample_column("PATIENT", "NAME", limit=10)
    Then I should receive up to 10 sample values
    And null_count should be provided
    And distinct_count should be provided

  Scenario: column_stats returns statistics
    Given column PATIENT.MOBILE with 97% NULL
    When I call column_stats("PATIENT", "MOBILE")
    Then null_percentage should be approximately 97
    And distinct_count should be provided
```

### 2.2 Value Bank Server

```gherkin
Feature: Value Bank Server

  Scenario: check_column_name finds exact match
    Given value bank contains "PATNR" → patient_id
    When I call check_column_name("PATNR")
    Then matches should include patient_id
    And confidence should be 1.0
    And source should be "exact"

  Scenario: check_column_name finds fuzzy match
    Given value bank contains "PATNR" → patient_id
    When I call check_column_name("PAT_NR")
    Then matches should include patient_id
    And confidence should be > 0.8
    And source should be "fuzzy"

  Scenario: check_values finds known insurance names
    Given value bank contains insurance names ["DAK", "AOK", "BARMER"]
    When I call check_values(["DAK Gesundheit", "BARMER", "Unknown"])
    Then matches should include insurance_name
    And matched_values should include "DAK Gesundheit", "BARMER"

  Scenario: add_column_name learns new variant
    Given value bank does not contain "PATIENTENNR"
    When I call add_column_name("patient_id", "PATIENTENNR", "client_123")
    Then success should be true
    And subsequent check_column_name("PATIENTENNR") should match patient_id
```

### 2.3 Review Server

```gherkin
Feature: Review Server

  Scenario: propose_mapping auto-accepts high confidence
    Given trust profile with auto_accept_threshold 0.90
    When I call propose_mapping(confidence=0.95)
    Then status should be "auto_accepted"

  Scenario: propose_mapping creates review for medium confidence
    Given trust profile with auto_accept_threshold 0.90, review_threshold 0.70
    When I call propose_mapping(confidence=0.82)
    Then status should be "pending_review"
    And a review item should exist

  Scenario: ask_human creates review item
    When I call ask_human(
      question="Is BEMERKUNG a chart note?",
      options=["Yes, chart_note", "No, something else", "Skip"],
      context={sample_values: ["Patient called", "Checkup complete"]}
    )
    Then a review item should be created with status "pending"

  Scenario: flag_column auto-excludes empty
    When I call flag_column(issue="empty")
    Then requires_review should be false
    And auto_excluded should be true

  Scenario: flag_column requires review for abandoned
    When I call flag_column(issue="abandoned")
    Then requires_review should be true
```

---

## 3. Trust Profiles

```gherkin
Feature: Trust Profiles

  Scenario: Conservative profile
    Given trust profile "conservative"
    Then auto_accept_threshold should be 0.99
    And critical entities should always require human review

  Scenario: Standard profile
    Given trust profile "standard"
    Then auto_accept_threshold should be 0.90
    And review_threshold should be 0.70

  Scenario: Permissive profile
    Given trust profile "permissive"
    Then auto_accept_threshold should be 0.80
    And most mappings should be auto-accepted
```

---

## 4. End-to-End Scenarios

### 4.1 First Client Onboarding

```gherkin
Feature: First Client Onboarding

  Scenario: Map a clean database
    Given database "center_08_munich" (Zone D - clean baseline)
    And trust profile "standard"
    When the agent maps the entire database
    Then auto_match_rate should be >= 95%
    And pending_reviews should be <= 30
    And flagged_columns should be <= 5
    And no false positives in auto-accepted mappings

  Scenario: Learn from first client
    Given database "center_08_munich" has been mapped
    And human has verified all mappings
    When I query the value bank
    Then it should contain learned column names
    And it should contain learned insurance names
```

### 4.2 Cross-Database Learning

```gherkin
Feature: Cross-Database Learning

  Scenario: Second client benefits from first
    Given database "center_08_munich" has been fully mapped
    And value bank contains verified mappings
    When the agent maps "center_09_berlin" (same schema)
    Then auto_match_rate should be >= 96%
    And processing should be faster than center_08
    And known column names should match immediately

  Scenario: New column name is learned
    Given value bank contains "PATNR" → patient_id
    When the agent encounters "PATIENTENNUMMER" in a new database
    And human verifies it maps to patient_id
    Then value bank should now contain "PATIENTENNUMMER"
    And future databases with "PATIENTENNUMMER" should auto-match
```

### 4.3 Handling Chaos

```gherkin
Feature: Handling Chaotic Databases

  Scenario: Agent handles Zone B database
    Given database "center_03_vienna" (Zone B - legacy chaos)
    When the agent maps the database
    Then it should not crash
    And auto_match_rate should be between 50-65%
    And problematic columns should be flagged
    And agent reasoning should be logged

  Scenario: Agent flags but doesn't force bad mappings
    Given a column with ambiguous content
    When confidence is below threshold
    Then agent should ask_human or flag_column
    And should NOT auto-accept with low confidence
```

---

## 5. Agent Reasoning

```gherkin
Feature: Agent Reasoning

  Scenario: Agent explains its decisions
    When the agent proposes a mapping
    Then reasoning should be provided
    And reasoning should reference evidence (samples, value bank, patterns)

  Scenario: Agent log is stored
    When a mapping run completes
    Then full agent conversation should be stored
    And it should be retrievable for audit

  Scenario: Agent handles interruption
    Given the agent is mid-mapping
    When a human review is required
    And human provides decision
    Then agent should resume from where it stopped
```

---

## 6. API

```gherkin
Feature: API Endpoints

  Scenario: Start mapping
    When I POST to /api/schema-matching/map
    With connection_string and client_id
    Then I should receive a run_id
    And status should be "running"

  Scenario: Check status
    Given an active mapping run
    When I GET /api/schema-matching/status/{run_id}
    Then I should see progress percentage
    And pending_reviews count
    And mappings_complete count

  Scenario: Submit review
    Given a pending review item
    When I POST to /api/schema-matching/review/{item_id}
    With decision and reasoning
    Then the review should be recorded
    And if resume_agent is true, agent should continue
```

---

## 7. Validation by Zone

| Zone | Pass Criteria | Failure Response |
|------|--------------|------------------|
| **A (Synthetic)** | No crashes, all extremes flagged | Bug in error handling |
| **B (Realistic Extreme)** | Graceful handling, 50-65% match | Improve edge case detection |
| **C (Variations)** | 75-85% match, learning works | Expand value bank |
| **D (Clean)** | 95%+ match, zero false positives | **SERIOUS BUG** - investigate |

---

## References

- [MCP_ARCHITECTURE.md](MCP_ARCHITECTURE.md) - Technical architecture
- [DATABASE_SIMULATOR.md](DATABASE_SIMULATOR.md) - Test databases
- [DISCUSSION_LOG.md](DISCUSSION_LOG.md) - Design decisions

---

*Created: 2024-01-15*
*Status: Design*
