# Acceptance Criteria: Automatic Schema Matching

**Feature:** Automatic Schema Matching
**Version:** 2.0
**Last Updated:** 2024-01-14

---

## Overview

This document contains all acceptance criteria for the Automatic Schema Matching feature, organized by component.

### Pipeline Flow

```
Phase 1: Schema Profiling ─────────────────────────────────────────────►
                                                                        │
Phase 1b: Column Quality Detection ──────► [flagged → review queue] ───►
                                                                        │
Phase 2: LLM Classification ─────────────► [low conf → review queue] ──►
                                                                        │
Phase 3: Cross-DB Matching ──────────────► [med conf → review queue] ──►
                                                                        │
Phase 4: Auto-Validation ────────────────► [warnings → review queue] ──►
                                                                        │
                                           ┌────────────────────────────┤
                                           │  REVIEW QUEUE              │
                                           │  (trust-based filtering)   │
                                           └────────────────────────────┤
                                                                        │
                                           ┌────────────────────────────┤
                                           │  FINAL APPROVAL GATE       │
                                           │  (before production)       │
                                           └────────────────────────────┘
```

### Components Covered

| # | Component | Description | Documentation |
|---|-----------|-------------|---------------|
| 1 | Trust & Review Config | Trust profiles, risk classes, adaptive trust | — |
| 2 | Schema Profiling | Phase 1: Extract metadata and sample values | [02-advanced-methodology.md](02-advanced-methodology.md) |
| 3 | Column Quality | Phase 1b: Detect empty/abandoned columns | [03-value-banks.md](03-value-banks.md) |
| 4 | LLM Classification | Phase 2: Semantic classification of columns | [02-advanced-methodology.md](02-advanced-methodology.md) |
| 5 | Cross-Database Matching | Phase 3: Match against canonical schema | [02-advanced-methodology.md](02-advanced-methodology.md) |
| 6 | Auto-Validation | Phase 4: Verify mappings with real queries | [04-validation.md](04-validation.md) |
| 7 | Value Banks | Learned value clusters for matching | [03-value-banks.md](03-value-banks.md) |
| 8 | ML Enhancement | Machine learning improvements | [06-ml-enhancement.md](06-ml-enhancement.md) |
| 9 | Pipeline Orchestration | End-to-end pipeline flow | [05-implementation.md](05-implementation.md) |
| 10 | Integration Tests | System validation tests | — |

---

## 1. Trust & Review Configuration

```gherkin
Feature: Trust & Review Configuration
  As a system administrator
  I need to configure trust levels and review requirements
  So that automation is balanced with appropriate human oversight

  # ─────────────────────────────────────────────────────────────────────
  # TRUST PROFILES (Organizational Setting)
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Configure conservative trust profile
    Given a new client with unknown schema patterns
    When I set trust_profile = "conservative"
    Then auto_accept_threshold should be 0.99
    And review_required_before_production should be true
    And nearly all decisions should require human review

  Scenario: Configure standard trust profile
    Given an established client with known patterns
    When I set trust_profile = "standard"
    Then auto_accept_threshold should be 0.85
    And review_required_before_production should be true
    And high-confidence decisions should auto-accept

  Scenario: Configure permissive trust profile
    Given a well-known schema (e.g., 10th Ivoris client)
    When I set trust_profile = "permissive"
    Then auto_accept_threshold should be 0.70
    And review_required_before_production should be false
    And most decisions should auto-accept with audit logging

  Scenario: Select trust profile for new client
    Given I am onboarding a new client
    When I configure the pipeline
    Then I should be prompted to select a trust profile
    And the default should be "standard"
    And the selection should be logged for audit

  # ─────────────────────────────────────────────────────────────────────
  # RISK CLASSES (Per Entity)
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Define critical risk class
    Given entities where errors break the system
    When I assign risk_class = "critical" to [patient_id, date, soft_delete]
    Then minimum_confidence should be 0.85 (regardless of profile)
    And validation should always be required
    And these entities should never use permissive profile alone

  Scenario: Define important risk class
    Given entities where errors cause data quality issues
    When I assign risk_class = "important" to [insurance_type, insurance_name]
    Then minimum_confidence should be 0.75
    And validation should be required
    And any trust profile can be used

  Scenario: Define optional risk class
    Given entities where errors are minor inconveniences
    When I assign risk_class = "optional" to [chart_note, remarks]
    Then minimum_confidence should be 0.60
    And validation can be skipped
    And any trust profile can be used

  Scenario: Calculate effective threshold
    Given trust_profile = "permissive" (threshold 0.70)
    And entity "patient_id" has risk_class = "critical" (min 0.85)
    When effective threshold is calculated
    Then it should be max(0.70, 0.85) = 0.85
    And the entity minimum overrides the permissive profile

  # ─────────────────────────────────────────────────────────────────────
  # REVIEW TRIGGERS (Per Phase)
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Define review triggers for each phase
    Given the trust configuration is loaded
    Then review should be triggered when:
      | phase                | trigger_condition                    |
      | Column Quality (1b)  | label in [mostly_empty, abandoned, misused] |
      | LLM Classification   | confidence < effective_threshold     |
      | Cross-DB Matching    | confidence < effective_threshold     |
      | Validation           | result contains warnings or errors   |
      | Value Bank           | value status = "pending"             |

  Scenario: Items meeting threshold bypass review queue
    Given a matching result with confidence = 0.92
    And effective_threshold = 0.85
    When the decision is made
    Then the item should auto-accept
    And it should NOT appear in review queue
    And it should be logged for audit

  Scenario: Items below threshold enter review queue
    Given a matching result with confidence = 0.78
    And effective_threshold = 0.85
    When the decision is made
    Then the item should enter the review queue
    And it should be marked as "pending_review"
    And a human must approve or reject

  # ─────────────────────────────────────────────────────────────────────
  # ADAPTIVE TRUST (Earned Over Time)
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Track accuracy per phase
    Given adaptive_trust is enabled
    When decisions are made and later verified
    Then the system should track:
      | metric              | description                    |
      | decisions_made      | Count of auto-accepted items   |
      | verified_correct    | Count verified as correct      |
      | verified_incorrect  | Count verified as incorrect    |
      | accuracy            | verified_correct / total       |
    And accuracy should be calculated per phase

  Scenario: Auto-tighten trust on accuracy drop
    Given accuracy drops below 0.90 for 50 decisions
    When the adaptive trust check runs
    Then the system should auto-tighten threshold by 0.10
    And log the automatic adjustment
    And notify administrators
    And NOT require human approval (safety measure)

  Scenario: Suggest relaxing trust on high accuracy
    Given accuracy is >= 0.98 for 100 decisions
    When the adaptive trust check runs
    Then the system should suggest relaxing threshold by 0.05
    And this suggestion should require human approval
    And the current threshold should NOT change until approved

  Scenario: Reset adaptive tracking for new client
    Given a new client is being onboarded
    When the pipeline initializes
    Then adaptive trust counters should start at zero
    And the client should use the selected trust profile
    And trust should be earned through verified decisions

  # ─────────────────────────────────────────────────────────────────────
  # REVIEW QUEUE MANAGEMENT
  # ─────────────────────────────────────────────────────────────────────

  Scenario: View consolidated review queue
    Given items from multiple phases need review
    When I open the review queue
    Then I should see all pending items across phases:
      | source              | count | priority |
      | Column Quality      | 15    | high     |
      | LLM Classification  | 8     | medium   |
      | Cross-DB Matching   | 12    | medium   |
      | Validation Warnings | 3     | high     |
      | Pending Values      | 25    | low      |
    And items should be sorted by priority, then confidence (lowest first)

  Scenario: Filter review queue by phase
    Given 50 items in the review queue
    When I filter by phase = "LLM Classification"
    Then I should see only items from that phase
    And I can bulk-approve/reject within the filter

  Scenario: Filter review queue by entity
    Given 50 items in the review queue
    When I filter by entity = "patient_id"
    Then I should see only items related to that entity
    And I can review all patient_id decisions together

  # ─────────────────────────────────────────────────────────────────────
  # FINAL APPROVAL GATE
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Final approval required before production
    Given trust_profile = "standard" or "conservative"
    And all pipeline phases have completed
    And review queue is empty (all items reviewed)
    When requesting production deployment
    Then a final approval screen should be shown
    And it should summarize:
      | metric              | value  |
      | total_mappings      | 2,450  |
      | auto_accepted       | 2,100  |
      | human_reviewed      | 350    |
      | human_overrides     | 12     |
      | validation_passed   | 100%   |
    And a human must click [Approve for Production]

  Scenario: Skip final approval for permissive profile
    Given trust_profile = "permissive"
    And all pipeline phases have completed
    When the pipeline finishes
    Then mappings should be auto-deployed to production
    And a detailed audit log should be created
    And notification should be sent to administrators

  Scenario: Block production on pending reviews
    Given review queue has 5 pending items
    When requesting production deployment
    Then the request should be blocked
    And message should be "5 items require review before deployment"
    And the review queue should be highlighted

  # ─────────────────────────────────────────────────────────────────────
  # AUDIT LOGGING
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Log all decisions regardless of trust level
    Given any trust profile is configured
    When a decision is made (auto-accept or human-reviewed)
    Then an audit log entry should be created with:
      | field           | example                      |
      | timestamp       | 2024-01-14T10:30:00Z         |
      | decision_type   | auto_accept / human_approve  |
      | phase           | cross_db_matching            |
      | entity          | patient_id                   |
      | confidence      | 0.92                         |
      | threshold       | 0.85                         |
      | trust_profile   | standard                     |
      | reviewed_by     | null / "john@example.com"    |

  Scenario: Query audit history for compliance
    Given 10,000 decisions have been logged
    When I query for "all human overrides in last 30 days"
    Then I should receive a filtered list
    And each entry should show original vs final decision
    And export to CSV should be available
```

---

## 2. Schema Profiling (Phase 1)

```gherkin
Feature: Schema Profiling
  As a schema matching system
  I need to extract rich metadata from database columns
  So that I have sufficient information for accurate classification

  # ─────────────────────────────────────────────────────────────────────
  # BASIC PROFILING
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Profile all columns in a schema
    Given a database connection to client "munich_001"
    And the target schema is "ck"
    When the schema profiler runs
    Then it should profile all columns in all tables
    And each profile should contain:
      | field              | description                    |
      | schema             | Schema name (e.g., "ck")       |
      | table              | Table name                     |
      | column             | Column name                    |
      | data_type          | SQL data type                  |
      | max_length         | Character maximum length       |
      | nullable           | Whether NULL is allowed        |
      | distinct_count     | Count of distinct values       |
      | total_count        | Total row count                |
      | null_pct           | Percentage of NULL values      |
      | sample_values      | Up to 5 distinct sample values |

  Scenario: Detect data patterns in samples
    Given a column profile with sample_values ["20220118", "20220119", "20220120"]
    When pattern detection runs
    Then it should detect:
      | pattern       | value         |
      | format        | DATE_YYYYMMDD |
      | is_numeric    | true          |
      | cardinality   | high          |

  Scenario: Classify cardinality from statistics
    Given a column with distinct_count = 847 and total_count = 12503
    When cardinality is calculated
    Then the ratio should be 0.068 (847/12503)
    And cardinality should be classified as "moderate" (likely FK)

  Scenario: Classify cardinality as unique (likely PK)
    Given a column with distinct_count = 12503 and total_count = 12503
    When cardinality is calculated
    Then the ratio should be 1.0
    And cardinality should be classified as "unique" (likely PK)

  Scenario: Classify cardinality as low (categorical)
    Given a column with distinct_count = 5 and total_count = 12503
    When cardinality is calculated
    Then the ratio should be 0.0004
    And cardinality should be classified as "low" (categorical)

  # ─────────────────────────────────────────────────────────────────────
  # SAMPLE VALUE EXTRACTION
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Extract representative sample values
    Given a column "INSURANCE_NAME" with 500 distinct values
    When sample extraction runs
    Then it should return exactly 5 distinct non-null values
    And values should be representative (not just first 5 alphabetically)

  Scenario: Handle columns with all NULL values
    Given a column "UNUSED_FIELD" where 100% of values are NULL
    When sample extraction runs
    Then sample_values should be an empty array []
    And null_pct should be 100.0

  Scenario: Handle columns with sensitive data
    Given a column "PATIENT_SSN" flagged as potentially sensitive
    When sample extraction runs
    Then sample values should be masked or excluded
    And a flag "contains_sensitive_data" should be set

  # ─────────────────────────────────────────────────────────────────────
  # PERFORMANCE
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Profile large schema efficiently
    Given a schema with 487 tables and ~5000 columns
    When the schema profiler runs
    Then profiling should complete within 10 minutes
    And memory usage should not exceed 500MB

  Scenario: Use sampling for large tables
    Given a table with 10 million rows
    When profiling this table
    Then distinct_count should be estimated from a sample
    And sample_values should be extracted from the sample
    And an "estimated" flag should be set on the profile
```

---

## 3. Column Quality Detection (Phase 1b)

```gherkin
Feature: Column Quality Detection
  As a schema matching system
  I need to detect and label empty, abandoned, or misused columns
  So that they are excluded from matching and don't pollute value banks

  # ─────────────────────────────────────────────────────────────────────
  # EMPTY COLUMN DETECTION
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Detect fully empty column
    Given a column "NOTES_OLD" with 100% NULL values
    When column quality analysis runs
    Then the column should be labeled as "empty"
    And status should be "auto_excluded"
    And it should be excluded without human review (low risk)

  Scenario: Detect mostly empty column
    Given a column "FAX_NUMBER" with 97% NULL values
    And mostly_empty_threshold = 95%
    When column quality analysis runs
    Then the column should be labeled as "mostly_empty"
    And status should be "flagged"
    And it should enter the review queue

  Scenario: Accept sparse but valid column
    Given a column "EMERGENCY_CONTACT" with 80% NULL values
    And mostly_empty_threshold = 95%
    When column quality analysis runs
    Then the column should NOT be labeled as "mostly_empty"
    And it should proceed to Phase 2 (LLM classification)

  # ─────────────────────────────────────────────────────────────────────
  # ABANDONED COLUMN DETECTION
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Detect abandoned column by date
    Given a column "OLD_STATUS" with non-null values
    And all values are from records older than 24 months
    And the table has recent records with NULL for this column
    When column quality analysis runs
    Then the column should be labeled as "abandoned"
    And last_value_date should be recorded
    And it should enter the review queue

  Scenario: Accept active column with old data
    Given a column "INSURANCE_TYPE" with values from 2015 to present
    And recent records (within 6 months) have non-null values
    When column quality analysis runs
    Then the column should NOT be labeled as "abandoned"

  # ─────────────────────────────────────────────────────────────────────
  # MISUSED COLUMN DETECTION
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Detect misused date column
    Given a column "DATUM" (suggests date)
    And 40% of values are free-text like "cancelled"
    When column quality analysis runs
    Then the column should be labeled as "misused"
    And type_mismatch_percentage should be 40%
    And it should enter the review queue

  Scenario: Detect column with inconsistent patterns
    Given a column "PHONE" where:
      - 70% match phone number patterns
      - 30% contain notes like "no phone"
    When column quality analysis runs
    Then the column should be labeled as "inconsistent_usage"
    And pattern_mismatch_percentage should be 30%
    And it should enter the review queue

  # ─────────────────────────────────────────────────────────────────────
  # TEST DATA DETECTION
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Detect test-only column
    Given a column "DEBUG_FLAG" where all values are "TEST", "XXX", "DUMMY"
    When column quality analysis runs
    Then the column should be labeled as "test_only"
    And it should enter the review queue

  # ─────────────────────────────────────────────────────────────────────
  # TRUST-BASED REVIEW (References Section 1)
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Review queue shows flagged columns
    Given 10 columns are flagged for quality review
    When a human opens the column quality review queue
    Then they should see all flagged columns with:
      | field            | example                          |
      | column           | KARTEI.OLD_STATUS                |
      | label            | abandoned                        |
      | key_metric       | last_value: 2019-03-15           |
      | null_percentage  | 45%                              |
      | recommendation   | EXCLUDE: No values in 24+ months |
    And actions should be [Include] or [Exclude]

  Scenario: Human includes flagged column
    Given a column "RARE_FLAG" was labeled as "mostly_empty"
    When the human selects [Include] with reason "Valid field, sparse by design"
    Then status should change to "verified_include"
    And the override should be logged with reason
    And the column should proceed to Phase 2

  Scenario: Human excludes flagged column
    Given a column "DEFUNCT_CODE" was labeled as "abandoned"
    When the human confirms and selects [Exclude]
    Then status should change to "verified_exclude"
    And the column should be excluded from all subsequent phases

  Scenario: Conservative profile reviews all flagged columns
    Given trust_profile = "conservative"
    And 15 columns are flagged
    When the pipeline attempts Phase 2
    Then it should pause until all 15 are reviewed
    And notification should be sent to reviewers

  Scenario: Permissive profile auto-excludes flagged columns
    Given trust_profile = "permissive"
    And 15 columns are flagged
    When the pipeline runs
    Then flagged columns should be auto-excluded
    And an audit log should record each exclusion
    And the pipeline should continue without pausing

  # ─────────────────────────────────────────────────────────────────────
  # CONFIGURATION
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Configurable thresholds
    Given these configured thresholds:
      | threshold              | value |
      | mostly_empty_threshold | 95%   |
      | abandoned_months       | 24    |
      | test_data_threshold    | 80%   |
    When a column has 96% NULL values
    Then it should be labeled as "mostly_empty"

  Scenario: Per-entity threshold override
    Given entity "chart_note" has mostly_empty_threshold = 99%
    When a chart_note column has 97% NULL values
    Then it should NOT be flagged as "mostly_empty"
```

---

## 4. LLM Semantic Classification (Phase 2)

```gherkin
Feature: LLM Semantic Classification
  As a schema matching system
  I need to use LLM to understand column semantics
  So that I can classify columns that don't match known patterns

  # ─────────────────────────────────────────────────────────────────────
  # CLASSIFICATION
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Classify German column name correctly
    Given a column profile:
      | field         | value                    |
      | table         | KARTEI                   |
      | column        | PATNR                    |
      | data_type     | int                      |
      | sample_values | [1, 2, 3, 15, 28]        |
      | distinct_count| 847                      |
      | total_count   | 12503                    |
    When LLM classification runs
    Then the result should be:
      | field          | value                              |
      | classification | patient_id                         |
      | confidence     | 0.95                               |
      | reasoning      | Contains "PAT" + "NR" pattern      |

  Scenario: Classify column by value content
    Given a column "BEZEICHNUNG" with sample_values ["DAK Gesundheit", "AOK Bayern", "BARMER"]
    When LLM classification runs
    Then the result should be:
      | field          | value                              |
      | classification | insurance_name                     |
      | confidence     | 0.92                               |
      | reasoning      | Values are German insurance names  |

  Scenario: Provide alternative classification when uncertain
    Given a column "CODE" with ambiguous sample values ["A1", "B2", "C3"]
    When LLM classification runs
    And confidence is below effective_threshold
    Then the result should include:
      | field       | value         |
      | primary     | service_code  |
      | alternative | diagnosis_code|
      | confidence  | 0.65          |
    And the column should enter the review queue

  # ─────────────────────────────────────────────────────────────────────
  # TRUST-BASED REVIEW (References Section 1)
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Auto-accept high confidence classification
    Given LLM returns confidence = 0.92
    And effective_threshold = 0.85
    When the decision is made
    Then classification should be auto-accepted
    And it should NOT enter review queue
    And it should be logged for audit

  Scenario: Queue low confidence for review
    Given LLM returns confidence = 0.72
    And effective_threshold = 0.85
    When the decision is made
    Then classification should enter review queue
    And human must select correct entity
    And the correction should be learned

  Scenario: Risk class affects threshold
    Given entity "patient_id" has risk_class = "critical"
    And trust_profile = "permissive" (threshold 0.70)
    When classifying a patient_id column
    Then effective_threshold should be 0.85 (critical minimum)
    And lower confidence results should require review

  # ─────────────────────────────────────────────────────────────────────
  # FILTERING (MINIMIZE LLM CALLS)
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Skip LLM for known column names
    Given a column "PATNR"
    And "PATNR" exists in canonical schema known_names for "patient_id"
    When the LLM filter runs
    Then the column should NOT be sent to LLM
    And it should be auto-matched to "patient_id" with confidence 0.95

  Scenario: Skip LLM for previously classified columns
    Given a column "KASSENBEZEICHNUNG"
    And this column name was classified as "insurance_name" for client "berlin_002"
    When processing client "hamburg_003"
    Then the column should NOT be sent to LLM
    And it should use the cached classification

  Scenario: Skip LLM when value bank matches
    Given a column with sample_values ["DAK Gesundheit", "AOK Bayern"]
    And these values exist in the "insurance_name" value bank
    When the LLM filter runs
    Then the column should NOT be sent to LLM
    And it should be matched via value bank with high confidence

  Scenario: Send only unknown columns to LLM
    Given 100 columns to classify
    And 85 match known_names or value banks
    And 10 match cached classifications
    When the LLM filter runs
    Then only 5 columns should be sent to LLM
    And a log should record "Skipped 95 columns (85 known, 10 cached)"

  # ─────────────────────────────────────────────────────────────────────
  # BATCHING
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Batch columns for efficient LLM calls
    Given 50 columns need LLM classification
    And batch_size is configured as 10
    When LLM classification runs
    Then it should make exactly 5 API calls
    And each call should classify 10 columns

  Scenario: Handle partial batch
    Given 23 columns need LLM classification
    And batch_size is configured as 10
    When LLM classification runs
    Then it should make 3 API calls
    And the last batch should contain 3 columns

  # ─────────────────────────────────────────────────────────────────────
  # ERROR HANDLING
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Retry on API failure
    Given an LLM API call fails with a transient error
    When retry logic executes
    Then it should retry up to 3 times
    And use exponential backoff (1s, 2s, 4s)

  Scenario: Handle malformed LLM response
    Given the LLM returns invalid JSON
    When parsing the response
    Then it should log the error
    And mark the column for manual classification (enters review queue)
    And NOT crash the pipeline

  Scenario: Handle rate limiting
    Given the LLM API returns a rate limit error
    When the error is detected
    Then it should wait for the specified retry-after duration
    And resume processing
```

---

## 5. Cross-Database Matching (Phase 3)

```gherkin
Feature: Cross-Database Matching
  As a schema matching system
  I need to match columns against a canonical schema
  So that I can leverage knowledge from previous clients

  # ─────────────────────────────────────────────────────────────────────
  # CANONICAL SCHEMA
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Load canonical schema
    Given a canonical schema file "canonical-dental-schema.yml"
    When the matcher initializes
    Then it should load all entities with their:
      | property       | example                          |
      | description    | "Unique patient identifier"      |
      | known_names    | [PATNR, PATIENTID, PAT_ID]       |
      | expected_types | [int, bigint]                    |
      | cardinality    | moderate                         |
      | risk_class     | critical                         |

  Scenario: Match by exact column name
    Given a column "PATNR"
    And "PATNR" is in known_names for entity "patient_id"
    When matching runs
    Then it should match to "patient_id"
    And confidence should be >= 0.90
    And match_reason should include "Column name matches known name"

  Scenario: Match by partial column name
    Given a column "PATIENT_NUMMER"
    And "PATIENT" is a substring of known_names for "patient_id"
    When matching runs
    Then it should match to "patient_id"
    And confidence should be >= 0.70
    And match_reason should include "Column name partially matches"

  # ─────────────────────────────────────────────────────────────────────
  # SCORING
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Calculate composite score
    Given a column with the following signals:
      | signal           | score |
      | value_bank_match | 0.80  |
      | column_name      | 0.50  |
      | data_type        | 1.00  |
      | cross_db         | 0.60  |
    And scoring weights are:
      | signal           | weight |
      | value_bank_match | 0.40   |
      | column_name      | 0.25   |
      | data_type        | 0.20   |
      | cross_db         | 0.15   |
    When composite score is calculated
    Then the score should be:
      (0.80 × 0.40) + (0.50 × 0.25) + (1.00 × 0.20) + (0.60 × 0.15) = 0.635

  # ─────────────────────────────────────────────────────────────────────
  # TRUST-BASED DECISIONS (References Section 1)
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Auto-accept high confidence match
    Given a column matches with confidence = 0.92
    And effective_threshold = 0.85
    When the decision is made
    Then the action should be "auto_accept"
    And it should be logged for audit
    And no human review required

  Scenario: Queue medium confidence for quick review
    Given a column matches with confidence = 0.78
    And effective_threshold = 0.85
    When the decision is made
    Then the action should be "review_required"
    And the column should appear in the review queue
    And suggested match should be shown for confirmation

  Scenario: Queue low confidence for investigation
    Given a column matches with confidence = 0.55
    And effective_threshold = 0.85
    When the decision is made
    Then the action should be "investigation_required"
    And the column should be highlighted in review queue
    And multiple potential matches should be shown

  Scenario: Critical entity gets stricter threshold
    Given entity "patient_id" has risk_class = "critical"
    And trust_profile = "standard" (threshold 0.85)
    When a match confidence is 0.86
    Then the match should be auto-accepted
    But if confidence was 0.83, it should require review

  # ─────────────────────────────────────────────────────────────────────
  # CROSS-DATABASE LEARNING
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Learn from verified mapping
    Given a column "NOTIZ" was verified as "chart_note" for client "berlin_002"
    And "NOTIZ" was not in the canonical known_names
    When the mapping is stored
    Then "NOTIZ" should be added to known_names for "chart_note"
    And future clients should auto-match "NOTIZ" columns

  Scenario: Track cross-database consistency
    Given "PATNR" has been mapped to "patient_id" for 5 clients
    When consistency is calculated
    Then cross_db_consistency for "PATNR" should be 100%
    And this should boost confidence for new clients

  Scenario: Detect inconsistent mappings across clients
    Given "STATUS" was mapped to "insurance_type" for client A
    And "STATUS" was mapped to "soft_delete" for client B
    When a new client has a "STATUS" column
    Then it should be flagged for human review
    And both previous mappings should be shown as options
```

---

## 6. Auto-Validation (Phase 4)

```gherkin
Feature: Auto-Validation
  As a schema matching system
  I need to validate proposed mappings with real queries
  So that I catch errors before storing mappings

  # ─────────────────────────────────────────────────────────────────────
  # FK VALIDATION
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Validate FK join produces results
    Given a mapping where KARTEI.PATNR → patient_id
    And PATIENT.ID is the patient primary key
    When FK validation runs
    Then it should execute a JOIN query
    And the query should return > 0 rows
    And validation should pass

  Scenario: Fail validation when FK join produces no results
    Given a mapping where KARTEI.WRONG_COL → patient_id
    And no records match between tables
    When FK validation runs
    Then the query should return 0 rows
    And validation should fail with severity "error"
    And message should be "FK join produced 0 rows - check relationship"

  # ─────────────────────────────────────────────────────────────────────
  # DATE VALIDATION
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Validate date column format
    Given a mapping where KARTEI.DATUM → date
    And the column contains YYYYMMDD format strings
    When date validation runs
    Then it should check what percentage can be parsed as dates
    And if > 95% are valid, validation should pass

  Scenario: Warn on partially valid dates
    Given a date column where 85% of values are valid dates
    When date validation runs
    Then validation should pass with severity "warning"
    And message should indicate "85% valid - some invalid dates present"
    And warning should enter review queue

  Scenario: Fail validation on invalid date column
    Given a date column where only 50% of values are valid dates
    When date validation runs
    Then validation should fail with severity "error"
    And message should be "Only 50% valid - check date format"

  # ─────────────────────────────────────────────────────────────────────
  # INSURANCE VALIDATION
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Validate insurance type values
    Given a mapping where KASSEN.ART → insurance_type
    When insurance validation runs
    Then it should check for expected values (P, 1-9, GKV, PKV)
    And if matches found, validation should pass

  Scenario: Warn on unexpected insurance values
    Given an insurance_type column with values ["X", "Y", "Z"]
    And none match expected patterns
    When insurance validation runs
    Then validation should fail with severity "warning"
    And message should include the unexpected values

  # ─────────────────────────────────────────────────────────────────────
  # SOFT DELETE VALIDATION
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Validate soft delete column
    Given a mapping where KARTEI.DELKZ → soft_delete
    When soft delete validation runs
    Then it should count active (0/NULL) vs deleted (1) records
    And report the distribution
    And validation should pass if active_ratio >= 0.5

  Scenario: Warn on high deletion rate
    Given a soft_delete column where 90% of records are deleted
    When soft delete validation runs
    Then validation should pass with severity "warning"
    And message should indicate unusual deletion rate

  # ─────────────────────────────────────────────────────────────────────
  # TRUST-BASED HANDLING (References Section 1)
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Validation errors always require review
    Given validation completed with 2 errors
    And trust_profile = "permissive"
    When the decision is made
    Then errors should enter review queue regardless of profile
    And mappings with errors should NOT be auto-deployed

  Scenario: Validation warnings respect trust profile
    Given validation completed with 3 warnings
    And trust_profile = "permissive"
    When the decision is made
    Then warnings should be auto-accepted
    And an audit log should record the warnings

  Scenario: Conservative profile reviews all warnings
    Given validation completed with 3 warnings
    And trust_profile = "conservative"
    When the decision is made
    Then warnings should enter review queue
    And human must acknowledge each warning

  # ─────────────────────────────────────────────────────────────────────
  # VALIDATION REPORT
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Generate validation report
    Given validation has completed with:
      | test              | result  | severity |
      | fk_join           | passed  | info     |
      | date_validity     | passed  | warning  |
      | insurance_values  | passed  | info     |
      | soft_delete       | passed  | info     |
      | extraction_query  | passed  | info     |
    When the validation report is generated
    Then it should show:
      | metric      | value |
      | total_tests | 5     |
      | passed      | 5     |
      | warnings    | 1     |
      | errors      | 0     |

  Scenario: Report with errors blocks production
    Given validation has 2 errors
    When the validation report is generated
    Then recommendation should be "Mapping has errors - requires investigation"
    And the mapping should NOT be auto-approved regardless of trust profile
```

---

## 7. Value Banks

```gherkin
Feature: Value Banks
  As a schema matching system
  I need to learn from verified values
  So that I can match columns without LLM calls

  # ─────────────────────────────────────────────────────────────────────
  # VALUE MATCHING
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Match column by value bank
    Given a column with sample_values ["DAK Gesundheit", "AOK Bayern", "BARMER"]
    And the insurance_name value bank contains these values (status = verified)
    When value bank matching runs
    Then it should match to "insurance_name"
    And match_score should be >= 0.80
    And llm_used should be false

  Scenario: Partial value bank match
    Given a column with sample_values ["DAK Gesundheit", "New Insurance Co", "BARMER"]
    And 2 of 3 values exist in insurance_name value bank
    When value bank matching runs
    Then match_score should be 0.67 (2/3)
    And the column should be flagged for review

  Scenario: No value bank match
    Given a column with sample_values ["ABC", "DEF", "GHI"]
    And no values exist in any value bank
    When value bank matching runs
    Then match_score should be 0.0
    And the column should proceed to LLM classification

  # ─────────────────────────────────────────────────────────────────────
  # VALUE LEARNING
  # ─────────────────────────────────────────────────────────────────────

  Scenario: New values start as pending
    Given new values are discovered during profiling
    And no human has reviewed them yet
    When values are added to bank
    Then status should be "pending"
    And they should NOT be used for matching until verified

  Scenario: Learn new values from verified mapping
    Given a column mapped to "insurance_name"
    And sample_values include "New Insurance GmbH" (not in bank)
    When the mapping is verified by human
    Then "New Insurance GmbH" should be added to value bank
    And status should be "verified"
    And source_client should be recorded

  Scenario: Increment occurrence count for existing value
    Given "DAK Gesundheit" exists in value bank with occurrence_count = 5
    When the value is seen for a new client
    Then occurrence_count should be updated to 6
    And last_seen_at should be updated

  # ─────────────────────────────────────────────────────────────────────
  # VALUE QUALITY CONTROL
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Reject test data value
    Given a pending value "TEST" in insurance_name bank
    When a human reviews and rejects it
    Then status should change to "rejected"
    And rejection_reason should be "test_data"
    And it should be excluded from future matching

  Scenario: Reject data entry error
    Given a pending value "DAK Gesundheit " (trailing space)
    When a human reviews and rejects it
    Then status should change to "rejected"
    And rejection_reason should be "data_entry_error"
    And the corrected value "DAK Gesundheit" should be verified

  Scenario: Auto-flag suspicious values
    Given a new value "XXXX" is discovered
    When quality analysis runs
    Then it should be flagged with quality_flags ["test_pattern"]
    And recommendation should be "REJECT: Likely test data"

  Scenario: Only verified values used for matching
    Given a value bank with:
      | value           | status   |
      | DAK Gesundheit  | verified |
      | TEST            | rejected |
      | New Insurance   | pending  |
    When value bank matching runs
    Then only "DAK Gesundheit" should be used for matching
    And "TEST" and "New Insurance" should be excluded

  # ─────────────────────────────────────────────────────────────────────
  # TRUST-BASED VALUE REVIEW (References Section 1)
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Conservative profile requires value review
    Given trust_profile = "conservative"
    And 50 pending values discovered
    When value bank is used
    Then pending values should NOT match
    And all 50 should appear in review queue

  Scenario: Permissive profile auto-verifies high-occurrence values
    Given trust_profile = "permissive"
    And a pending value has occurrence_count >= 5 across clients
    When auto-verification runs
    Then the value should be auto-verified
    And an audit log should record the auto-verification

  # ─────────────────────────────────────────────────────────────────────
  # COLUMN NAME VARIANTS
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Learn new column name variant
    Given a column "PATIENTNUMMER" mapped to "patient_id"
    And "PATIENTNUMMER" is not in known_names
    When the mapping is verified
    Then "PATIENTNUMMER" should be added to column_variants
    And future columns named "PATIENTNUMMER" should auto-match

  Scenario: Reject wrong column name mapping
    Given "BEMERKUNG" was incorrectly mapped to "patient_id"
    When a human reviews and rejects the column variant
    Then the variant should be marked as rejected
    And rejection_reason should be "wrong_entity"
    And "BEMERKUNG" should NOT auto-match to "patient_id"
```

---

## 8. ML Enhancement

```gherkin
Feature: ML Enhancement
  As a schema matching system
  I need to leverage machine learning
  So that matching improves as more data is collected

  # ─────────────────────────────────────────────────────────────────────
  # EMBEDDING-BASED MATCHING
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Match values using embeddings
    Given sample_values ["DAK-Gesundheit", "AOK Baden-Wuerttemberg", "TK"]
    And the value bank contains ["DAK Gesundheit", "AOK Baden-Württemberg", "Techniker Krankenkasse"]
    When embedding-based matching runs
    Then it should find semantic similarity:
      | sample                  | match                      | similarity |
      | DAK-Gesundheit          | DAK Gesundheit             | ~0.95      |
      | AOK Baden-Wuerttemberg  | AOK Baden-Württemberg      | ~0.90      |
      | TK                      | Techniker Krankenkasse     | ~0.75      |
    And the column should match to "insurance_name"

  Scenario: Index value bank embeddings at startup
    Given a value bank with 500 verified values
    When the embedding matcher initializes
    Then it should pre-compute embeddings for all values
    And indexing should complete within 30 seconds
    And embeddings should be cached for fast lookup

  # ─────────────────────────────────────────────────────────────────────
  # FEW-SHOT LLM PROMPTING
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Include verified examples in LLM prompt
    Given 3 verified mappings for entity "chart_note":
      - KARTEI.BEMERKUNG → chart_note
      - PATIENT.NOTIZ → chart_note
      - BEHANDLUNG.ANMERKUNG → chart_note
    When classifying a new column "KOMMENTAR"
    Then the LLM prompt should include these examples
    And LLM accuracy should improve by 10-20%

  Scenario: Update few-shot examples automatically
    Given a new mapping NOTES.TEXT → chart_note is verified
    When the few-shot example cache refreshes
    Then the new example should be available for future prompts

  # ─────────────────────────────────────────────────────────────────────
  # FEATURE LOGGING
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Log ML features on verification
    Given a column mapping is verified
    When feature logging runs
    Then it should extract and store:
      | feature               | example_value |
      | name_length           | 8             |
      | has_id_suffix         | 1             |
      | is_varchar            | 0             |
      | cardinality_ratio     | 0.068         |
      | has_date_pattern      | 0             |
    And the canonical_entity label should be stored

  Scenario: Retrieve training data for ML
    Given 2500 verified mappings have been logged
    When training data is retrieved
    Then it should return features (X) and labels (y)
    And data should be ready for sklearn training

  # ─────────────────────────────────────────────────────────────────────
  # TRADITIONAL ML (PHASE 2+)
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Evaluate ML readiness
    Given 750 logged examples across 15 clients
    When readiness is evaluated
    Then it should report:
      | metric           | value |
      | total_examples   | 750   |
      | is_ready         | false |
      | recommendation   | "Need 250 more examples. Continue with rule-based." |

  Scenario: Train ML model when ready
    Given 2500 logged examples with >= 50 per class
    When ML training runs
    Then it should:
      - Run 5-fold cross-validation
      - Train RandomForest classifier
      - Report test accuracy
    And if cv_accuracy >= 0.70, model should be saved

  Scenario: Use ML prediction in scoring
    Given a trained ML model with 85% accuracy
    And ML weight is configured as 0.15
    When matching a column
    Then ML prediction should be included in composite score
    And ML confidence should affect the final score
```

---

## 9. Pipeline Orchestration

```gherkin
Feature: Pipeline Orchestration
  As a schema matching system
  I need to orchestrate the multi-phase pipeline
  So that client onboarding is automated and consistent

  # ─────────────────────────────────────────────────────────────────────
  # FULL PIPELINE
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Run full pipeline for new client
    Given a new client "munich_001" with database "DentalDB"
    And trust_profile = "standard"
    When the pipeline runs
    Then it should execute in order:
      1. Phase 1: Profile schema (extract metadata + samples)
      2. Phase 1b: Column quality detection (filter bad columns)
      3. Phase 2: LLM classification (for unknown columns only)
      4. Phase 3: Cross-database matching (against canonical)
      5. Phase 4: Auto-validation (test with real queries)
    And items below effective_threshold should enter review queue
    And final approval should be required before production

  Scenario: Pipeline pauses for review queue
    Given trust_profile = "standard" or "conservative"
    And 50 items are in the review queue
    When the pipeline completes Phase 4
    Then status should be "AWAITING_REVIEW"
    And notification should be sent to reviewers
    And the pipeline should not proceed to final approval

  Scenario: Pipeline continues when review complete
    Given pipeline status = "AWAITING_REVIEW"
    And all review queue items have been reviewed
    When the review is complete
    Then pipeline should proceed to final approval
    And status should change to "AWAITING_APPROVAL"

  Scenario: Permissive profile runs without pausing
    Given trust_profile = "permissive"
    When the pipeline runs
    Then it should auto-accept items above threshold
    And auto-exclude flagged columns
    And deploy to production without pausing
    And create detailed audit log

  # ─────────────────────────────────────────────────────────────────────
  # ERROR HANDLING
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Pipeline handles partial failure
    Given Phase 2 fails for 3 columns due to LLM error
    When error handling runs
    Then the pipeline should continue with remaining columns
    And failed columns should enter review queue
    And the final report should indicate partial completion

  Scenario: Resume interrupted pipeline
    Given a pipeline was interrupted at Phase 3
    When I resume the pipeline
    Then it should skip completed phases
    And continue from Phase 3
    And not re-run LLM classification

  # ─────────────────────────────────────────────────────────────────────
  # INCREMENTAL UPDATES
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Detect schema changes
    Given client "munich_001" was onboarded 6 months ago
    And 5 new columns have been added to the schema
    When schema change detection runs
    Then it should identify the 5 new columns
    And only these columns should go through the pipeline
    And existing mappings should be preserved

  Scenario: Handle renamed columns
    Given column "PATNR" was renamed to "PATIENT_NR"
    When schema change detection runs
    Then it should detect the rename (based on similar data)
    And suggest updating the mapping
    And flag for human confirmation

  # ─────────────────────────────────────────────────────────────────────
  # REPORTING
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Generate onboarding report
    Given pipeline has completed for client "munich_001"
    When the report is generated
    Then it should include:
      | section              | content                    |
      | total_columns        | 2,450                      |
      | auto_accepted        | 2,100 (86%)                |
      | human_reviewed       | 300 (12%)                  |
      | excluded (quality)   | 50 (2%)                    |
      | llm_calls_made       | 45                         |
      | validation_passed    | 15/15                      |
      | trust_profile        | standard                   |
      | recommendation       | Ready for final approval   |

  Scenario: Track onboarding metrics across clients
    Given 10 clients have been onboarded
    When cross-client metrics are generated
    Then it should show:
      | metric                | value |
      | avg_auto_accept_rate  | 89%   |
      | avg_onboarding_time   | 25 min|
      | total_llm_calls       | 320   |
      | total_llm_cost        | $1.60 |
      | adaptive_trust_trend  | +5%   |

  # ─────────────────────────────────────────────────────────────────────
  # DAILY OPERATIONS
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Daily extraction uses stored mappings
    Given client "munich_001" has verified mappings
    When daily extraction runs
    Then it should load mappings from storage
    And execute the extraction query
    And make NO LLM API calls
    And output should be consistent with onboarding validation

  Scenario: Daily extraction handles missing mapping
    Given a new column appeared that wasn't mapped
    When daily extraction runs
    Then it should log a warning
    And skip the unmapped column
    And flag the column for pipeline re-run
```

---

## 10. Integration Tests

```gherkin
Feature: Integration Tests
  As a developer
  I need end-to-end tests
  So that I can verify the system works correctly

  # ─────────────────────────────────────────────────────────────────────
  # END-TO-END SCENARIOS
  # ─────────────────────────────────────────────────────────────────────

  Scenario: First client onboarding (seed database)
    Given no prior clients have been onboarded
    And client "seed_001" has the standard Ivoris schema
    And trust_profile = "conservative"
    When the full pipeline runs
    Then all phases should complete successfully
    And most items should enter review queue (conservative)
    And after human review, mappings should be created for key columns:
      | column         | entity          |
      | KARTEI.PATNR   | patient_id      |
      | KARTEI.DATUM   | date            |
      | KARTEI.BEMERKUNG| chart_note     |
      | KASSEN.ART     | insurance_type  |
      | KARTEI.DELKZ   | soft_delete     |
    And value banks should be initialized
    And canonical schema should be updated

  Scenario: Second client benefits from first
    Given client "seed_001" has been onboarded and verified
    And trust_profile = "standard"
    When client "second_001" is onboarded
    Then auto-accept rate should be >= 80%
    And LLM calls should be < 20% of first client
    And onboarding time should be < 50% of first client
    And adaptive trust should show positive trend

  Scenario: Handle schema variation
    Given client "variant_001" uses different column names:
      | standard  | variant          |
      | PATNR     | PATIENT_NUMMER   |
      | BEMERKUNG | NOTIZ            |
      | DELKZ     | GELOESCHT        |
    When the pipeline runs
    Then LLM should correctly classify the variants
    And after verification, variants should be learned
    And future clients with these names should auto-match

  Scenario: Reject bad data gracefully
    Given a client database with:
      - 50% empty columns
      - Test data in multiple columns
      - Abandoned legacy columns
    When the pipeline runs
    Then column quality detection should flag bad columns
    And value quality should flag test data
    And the report should clearly indicate data quality issues
    And the system should NOT learn from bad data

  Scenario: Test trust profile differences
    Given the same schema is onboarded 3 times with different profiles
    When comparing results:
      | profile      | auto_accept_rate | review_queue_size | time_to_production |
      | conservative | 5%               | 95%               | requires all review |
      | standard     | 85%              | 15%               | requires approval   |
      | permissive   | 95%              | 5%                | immediate           |
    Then all three should produce correct final mappings
    And audit logs should reflect the different automation levels

  Scenario: Adaptive trust improves over time
    Given 5 clients have been onboarded with trust_profile = "standard"
    And accuracy has been 98% across 500 verified decisions
    When the adaptive trust check runs
    Then the system should suggest relaxing threshold by 0.05
    And after approval, the 6th client should have higher auto-accept rate
```

---

## Appendix: Configuration Reference

```yaml
# schema-matching-config.yml

# ─────────────────────────────────────────────────────────────────────
# TRUST PROFILES
# ─────────────────────────────────────────────────────────────────────

trust_profiles:
  conservative:
    description: "Review everything, learn the schema"
    auto_accept_threshold: 0.99
    review_required_before_production: true
    auto_exclude_flagged_columns: false
    auto_verify_high_occurrence_values: false

  standard:
    description: "Confidence-based automation"
    auto_accept_threshold: 0.85
    review_required_before_production: true
    auto_exclude_flagged_columns: false
    auto_verify_high_occurrence_values: false

  permissive:
    description: "Auto-accept most, review outliers"
    auto_accept_threshold: 0.70
    review_required_before_production: false
    auto_exclude_flagged_columns: true
    auto_verify_high_occurrence_values: true

# Default profile for new clients
default_trust_profile: standard

# ─────────────────────────────────────────────────────────────────────
# ENTITY RISK CLASSES
# ─────────────────────────────────────────────────────────────────────

entity_risk_classes:
  critical:
    description: "Errors break the system"
    entities: [patient_id, date, soft_delete]
    minimum_confidence: 0.85
    validation_required: true

  important:
    description: "Errors cause data quality issues"
    entities: [insurance_type, insurance_name, service_code]
    minimum_confidence: 0.75
    validation_required: true

  optional:
    description: "Errors are minor inconveniences"
    entities: [chart_note, remarks, description]
    minimum_confidence: 0.60
    validation_required: false

# ─────────────────────────────────────────────────────────────────────
# ADAPTIVE TRUST
# ─────────────────────────────────────────────────────────────────────

adaptive_trust:
  enabled: true

  accuracy_tracking:
    window_size: 100              # Last N decisions
    accuracy_target: 0.95         # Target accuracy

  auto_tighten:
    trigger_accuracy: 0.90        # Tighten if below this
    trigger_decisions: 50         # After this many decisions
    adjustment: 0.10              # Increase threshold by this
    requires_approval: false      # Auto-apply (safety)

  suggest_relax:
    trigger_accuracy: 0.98        # Suggest if above this
    trigger_decisions: 100        # After this many decisions
    adjustment: 0.05              # Decrease threshold by this
    requires_approval: true       # Human must approve

# ─────────────────────────────────────────────────────────────────────
# PHASE 1: PROFILING
# ─────────────────────────────────────────────────────────────────────

profiling:
  sample_size: 5
  max_distinct_for_full_scan: 10000
  large_table_threshold: 1000000

# ─────────────────────────────────────────────────────────────────────
# PHASE 1B: COLUMN QUALITY
# ─────────────────────────────────────────────────────────────────────

column_quality:
  empty_threshold: 1.00              # 100% NULL = auto-exclude
  mostly_empty_threshold: 0.95       # 95%+ NULL = flag
  abandoned_months: 24               # No values in N months
  test_data_threshold: 0.80          # 80%+ test values
  type_mismatch_threshold: 0.30      # 30%+ mismatched types

  # Per-entity overrides
  entity_overrides:
    chart_note:
      mostly_empty_threshold: 0.99

# ─────────────────────────────────────────────────────────────────────
# PHASE 2: LLM
# ─────────────────────────────────────────────────────────────────────

llm:
  provider: anthropic
  model: claude-3-haiku-20240307
  batch_size: 10
  max_retries: 3
  retry_backoff: [1, 2, 4]  # seconds

# ─────────────────────────────────────────────────────────────────────
# PHASE 3: MATCHING
# ─────────────────────────────────────────────────────────────────────

matching:
  weights:
    value_bank: 0.40
    column_name: 0.25
    data_type: 0.20
    cross_db: 0.15
    ml_prediction: 0.00  # Enable when ML ready

# ─────────────────────────────────────────────────────────────────────
# PHASE 4: VALIDATION
# ─────────────────────────────────────────────────────────────────────

validation:
  date_validity_threshold: 0.95
  fk_join_required: true

  # Validation errors always require review (regardless of trust profile)
  errors_always_require_review: true

# ─────────────────────────────────────────────────────────────────────
# VALUE BANKS
# ─────────────────────────────────────────────────────────────────────

value_bank:
  high_occurrence_threshold: 5      # Auto-verify if seen N+ times (permissive)
  test_data_patterns:
    - "^test"
    - "^xxx+"
    - "^asdf"
    - "^12345$"
    - "^dummy"

# ─────────────────────────────────────────────────────────────────────
# NOTIFICATIONS
# ─────────────────────────────────────────────────────────────────────

notifications:
  review_queue_threshold: 10        # Notify when queue reaches N items
  review_timeout_hours: 48          # Escalate if not reviewed in N hours
  channels:
    - email
    - slack
```

---

*Version 2.0 - Restructured with Trust & Review Configuration model*
*Last updated: 2024-01-14*
