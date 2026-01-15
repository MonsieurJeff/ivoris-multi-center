# Glossary: Schema Matching Terminology

**Purpose:** Quick reference for all technical terms used in this proposal
**Use:** Interview prep, team onboarding, documentation consistency

---

## Core Concepts

### Schema Matching

| Term | Definition |
|------|------------|
| **Schema Matching** | The process of identifying correspondences between columns in a source database and a canonical data model |
| **Source Column** | A column in a client database that needs to be mapped (e.g., PATNR, GEBDAT) |
| **Target Entity** | A standardized concept we map source columns to (e.g., patient_id, birth_date) |
| **Canonical Entity** | Same as target entity - the standard name in our unified model |
| **Mapping** | A confirmed correspondence between a source column and canonical entity |

---

### Similarity & Matching

| Term | Definition | Example |
|------|------------|---------|
| **String Similarity** | A measure (0-1) of how alike two strings are | "PATNR" vs "PAT_NR" = 0.86 |
| **Levenshtein Distance** | Count of single-character edits to transform one string to another | "PATNR" → "PAT_NR" = 2 edits |
| **Jaro-Winkler** | Similarity metric that weights prefix matches more heavily | Good for abbreviated names |
| **Jaccard Similarity** | Overlap of character sets divided by union | Good for reordered tokens |
| **Fuzzy Matching** | Approximate string matching using similarity algorithms | Finds "PATIENTNR" when searching "PATNR" |
| **Exact Match** | 100% string equality | "PATNR" == "PATNR" |

---

### Value Bank

| Term | Definition |
|------|------------|
| **Value Bank** | Database of learned column name patterns and their verified mappings |
| **Column Variant** | A known alternative name for a canonical entity (PATNR, PAT_NR, PATIENTENNUMMER all map to patient_id) |
| **Occurrence Count** | How many times a variant has been seen across all clients |
| **Verified Mapping** | A human-confirmed column-to-entity mapping stored in the value bank |
| **Pattern Learning** | The process of adding new verified mappings to the value bank |

---

### Confidence & Trust

| Term | Definition | Range |
|------|------------|-------|
| **Confidence Score** | System's certainty that a mapping is correct | 0.0 - 1.0 (0% - 100%) |
| **Trust Profile** | Configuration that controls automation vs human review thresholds | Conservative, Standard, Permissive |
| **Auto-Accept Threshold** | Confidence level above which mappings are accepted without human review | 90% (standard) |
| **Review Threshold** | Confidence level above which mappings go to human review queue | 70% (standard) |
| **Rejection Threshold** | Confidence level below which mappings are automatically rejected | < 70% (standard) |

---

### Human Review

| Term | Definition |
|------|------------|
| **Review Queue** | List of uncertain mappings awaiting human decision |
| **Pending Review** | Mapping status when confidence is between review and auto-accept thresholds |
| **Human-in-the-Loop** | System design where humans validate machine decisions |
| **Feedback Loop** | Process where human decisions improve future system accuracy |
| **Critical Entity** | A canonical entity (like patient_id) that always requires human review regardless of confidence |

---

### System Components

| Term | Definition |
|------|------------|
| **Mapping Run** | A single execution of schema matching against a client database |
| **Schema Profiler** | Component that analyzes source schema (table names, column types, statistics) |
| **Similarity Engine** | Component that computes similarity scores between source and target |
| **Confidence Aggregator** | Component that combines multiple signals into a single confidence score |
| **Audit Log** | Complete record of all mapping decisions, who made them, and when |

---

## Database & Schema Terms

### Ivoris-Specific

| Term | Definition | Example |
|------|------------|---------|
| **Ivoris** | German dental practice management software | Source system for schema matching |
| **PATNR** | Patient Number (German: Patientennummer) | Primary patient identifier |
| **GEBDAT** | Birth Date (German: Geburtsdatum) | Patient date of birth |
| **KASSE** | Insurance (German: Krankenkasse) | Health insurance provider |
| **BEMERKUNG** | Remark/Note (German) | Clinical notes field |
| **TERMIN** | Appointment (German) | Scheduling data |
| **BEHANDLER** | Practitioner/Provider (German) | Treating dentist |

### General Database

| Term | Definition |
|------|------------|
| **INFORMATION_SCHEMA** | SQL standard metadata tables describing database structure |
| **Column Metadata** | Information about a column: name, data type, nullability, etc. |
| **Foreign Key** | Column referencing another table's primary key |
| **Cardinality** | Number of distinct values in a column |
| **Data Type** | Column's storage type (VARCHAR, INTEGER, DATE, etc.) |

---

## Signal Types

| Signal | What It Measures | Weight |
|--------|------------------|--------|
| **Name Similarity** | How similar column names are to known patterns | High (0.4) |
| **Data Type Match** | Whether column type matches expected type for entity | Medium (0.2) |
| **Value Pattern** | Whether sample values match expected patterns (dates, IDs, etc.) | Medium (0.2) |
| **Statistical Profile** | Null percentage, cardinality, value distribution | Low (0.1) |
| **Historical Match** | Whether this exact column name was seen before | High (0.1) |

---

## Processing Terms

| Term | Definition |
|------|------------|
| **Async Processing** | Running matching jobs in background without blocking |
| **Task Queue** | System for managing background jobs (e.g., Celery + Redis) |
| **Worker** | Process that executes background tasks |
| **Batch Processing** | Processing multiple columns/tables in a single operation |
| **Incremental Mapping** | Re-running matching on only new/changed columns |

---

## ML Terms (Phase 4)

| Term | Definition |
|------|------------|
| **Embeddings** | Vector representations of text that capture semantic meaning |
| **Semantic Similarity** | Similarity based on meaning, not just character patterns |
| **Classification Model** | ML model that predicts which entity a column maps to |
| **Training Data** | Verified mappings used to train ML models |
| **Feature Vector** | Numeric representation of a column used as ML input |
| **Ground Truth** | Human-verified correct mappings used for evaluation |

---

## German Column Name Patterns

### Common Suffixes

| Suffix | Meaning | Example |
|--------|---------|---------|
| **-NR** | Number/ID | PATNR (patient number) |
| **-DAT** | Date | GEBDAT (birth date) |
| **-KZ** | Kennzeichen (flag/indicator) | DELKZ (delete flag) |
| **-ART** | Type/Kind | KASSENART (insurance type) |
| **-NAME** | Name | KASSENNAME (insurance name) |

### Common Prefixes

| Prefix | Meaning | Example |
|--------|---------|---------|
| **GEB-** | Birth | GEBDAT, GEBURTSDATUM |
| **PAT-** | Patient | PATNR, PATNAME |
| **KAS-** | Insurance (Kasse) | KASSENR, KASSENART |
| **BEH-** | Treatment (Behandlung) | BEHANDLER |

---

## Status Values

### Mapping Status

| Status | Meaning |
|--------|---------|
| **auto_accepted** | Automatically approved (high confidence) |
| **pending_review** | Awaiting human decision |
| **human_approved** | Manually approved by reviewer |
| **human_rejected** | Manually rejected by reviewer |
| **rejected** | Automatically rejected (low confidence) |

### Run Status

| Status | Meaning |
|--------|---------|
| **running** | Mapping in progress |
| **completed** | All mappings processed |
| **failed** | Error occurred during processing |
| **partial** | Some tables completed, some failed |

---

## Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Auto-Match Rate** | % of mappings auto-accepted | 90%+ (at maturity) |
| **Review Rate** | % of mappings requiring human review | < 10% (at maturity) |
| **Accuracy** | % of auto-accepted mappings that are correct | > 99% |
| **False Positive Rate** | % of auto-accepted mappings that are wrong | < 1% |
| **Coverage** | % of source columns successfully mapped | > 95% |

---

## Quick Reference: Threshold Defaults

| Profile | Auto-Accept | Review | Reject |
|---------|-------------|--------|--------|
| **Conservative** | ≥ 99% | ≥ 80% | < 80% |
| **Standard** | ≥ 90% | ≥ 70% | < 70% |
| **Permissive** | ≥ 80% | ≥ 50% | < 50% |

---

## Acronyms

| Acronym | Expansion |
|---------|-----------|
| **ETL** | Extract, Transform, Load |
| **PII** | Personally Identifiable Information |
| **GKV** | Gesetzliche Krankenversicherung (German public health insurance) |
| **PKV** | Private Krankenversicherung (German private health insurance) |
| **BEMA** | Bewertungsmaßstab für zahnärztliche Leistungen (German dental fee schedule - public) |
| **GOZ** | Gebührenordnung für Zahnärzte (German dental fee schedule - private) |
| **ICD** | International Classification of Diseases |
| **UUID** | Universally Unique Identifier |
| **API** | Application Programming Interface |
| **ROI** | Return on Investment |

---

*Use this glossary to speak the language. Consistent terminology shows you've done your homework.*
