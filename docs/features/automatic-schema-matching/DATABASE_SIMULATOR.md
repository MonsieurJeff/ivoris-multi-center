# Database Simulator

**Purpose:** Generate realistic test databases for Automatic Schema Matching development and demos.
**Format:** Docker SQL Server containers
**Scale:** 10 simulated dental centers
**Ordering:** Extreme → Normal (stress-first approach)

---

## Overview

### Goals

1. **Robustness Testing:** Start with extreme cases to find breaking points
2. **Accuracy Validation:** Progress to realistic scenarios to verify matching quality
3. **Demo:** Showcase feature handling worst-to-best cases
4. **Ground Truth:** Every database has a manifest of expected results

### Design Philosophy: Extreme → Normal

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SIMULATION PROGRESSION                           │
│                                                                          │
│   EXTREME ──────────────────────────────────────────────────► NORMAL    │
│                                                                          │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│   │   ZONE A    │  │   ZONE B    │  │   ZONE C    │  │   ZONE D    │   │
│   │  Synthetic  │  │  Realistic  │  │  Moderate   │  │   Clean     │   │
│   │  Extremes   │  │  Extremes   │  │ Variations  │  │  Baselines  │   │
│   │             │  │             │  │             │  │             │   │
│   │ POSSIBILI-  │  │  OBSERVED   │  │   COMMON    │  │   IDEAL     │   │
│   │   TIES      │  │ WORST CASES │  │  REALITIES  │  │   STATE     │   │
│   │             │  │             │  │             │  │             │   │
│   │ Centers 1-2 │  │ Centers 3-4 │  │ Centers 5-7 │  │ Centers 8-10│   │
│   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                                          │
│   "Can it break?"  "Can it handle   "Can it adapt?"  "Is it accurate?"  │
│                     real chaos?"                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Why Extreme → Normal?

| Principle | Rationale |
|-----------|-----------|
| **Fail Fast** | Discover breaking points before investing in "easy" cases |
| **Defensive Design** | If it handles chaos, normal is trivial |
| **Confidence Building** | Passing edge cases = high confidence in robustness |
| **Regression Priority** | Edge cases break first during refactoring |

### Possibilities vs Realities Framework

| Type | Definition | Purpose | Zone |
|------|------------|---------|------|
| **Possibilities (Synthetic)** | Constructed worst-case scenarios that *could* exist | Test detection limits, boundary conditions | A |
| **Realities (Observed)** | Patterns from actual Ivoris databases | Validate real-world handling | B, C, D |

---

## The 10 Centers

### Summary Table

| Zone | Centers | Type | Purpose | Expected Auto-Match |
|------|---------|------|---------|---------------------|
| **A** | 1-2 | Synthetic Extremes | Break the system | 0-40% (expected failures) |
| **B** | 3-4 | Realistic Extremes | Handle chaos gracefully | 50-65% |
| **C** | 5-7 | Moderate Variations | Test adaptability | 75-85% |
| **D** | 8-10 | Clean Baselines | Verify accuracy | 90-98% |

---

## ZONE A: SYNTHETIC EXTREMES (Possibilities)

**Purpose:** Test the boundaries of detection. These scenarios may never exist in reality but prove system robustness.

---

### Center 1: Pathological (Threshold Edge Cases)

**Purpose:** Test exact threshold boundaries for all detection types.

```yaml
center_id: center_01
name: "Pathological Edge Cases"
port: 1433
schema: test
quality: synthetic
type: possibilities
```

**Threshold Boundary Tests:**

| Test | Column | Value | Expected Result |
|------|--------|-------|-----------------|
| Empty at 100% | EMPTY_100 | 100% NULL | auto_excluded |
| Empty below | EMPTY_99 | 99% NULL | mostly_empty (flagged) |
| Mostly empty below | NULL_94 | 94% NULL | NOT flagged |
| Mostly empty at | NULL_95 | 95% NULL | flagged |
| Mostly empty above | NULL_96 | 96% NULL | flagged |
| Abandoned below | RECENT_23M | 23 months ago | NOT flagged |
| Abandoned at | OLD_24M | 24 months ago | flagged |
| Abandoned above | OLD_25M | 25 months ago | flagged |
| Type mismatch below | MISMATCH_29 | 29% wrong type | NOT flagged |
| Type mismatch at | MISMATCH_30 | 30% wrong type | flagged |
| Type mismatch above | MISMATCH_31 | 31% wrong type | flagged |
| Test data below | TEST_79 | 79% test patterns | NOT flagged |
| Test data at | TEST_80 | 80% test patterns | flagged |
| Test data above | TEST_81 | 81% test patterns | flagged |

**Extreme Value Tests:**

| Column | Test | Expected |
|--------|------|----------|
| SINGLE_VALUE | 100% identical values | Flag as constant |
| MAX_LENGTH_NAME | 128-char column name | Handle gracefully |
| UNICODE_VALUES | Full Unicode spectrum | No encoding errors |
| EMPTY_STRING_COL | All values = '' | Distinct from NULL |
| ZERO_ROWS_TABLE | Table with 0 rows | Handle gracefully |

**Expected Results:**
- All threshold boundaries correctly identified
- System doesn't crash on edge cases
- Useful for regression testing
- Auto-match rate: ~20% (most are synthetic test columns)

---

### Center 2: Adversarial (Hostile Naming)

**Purpose:** Test system resilience against malformed, hostile, or unexpected naming patterns.

```yaml
center_id: center_02
name: "Adversarial Naming"
port: 1434
schema: dbo
quality: synthetic
type: possibilities
```

**Adversarial Column Names:**

| Category | Examples | Expected Behavior |
|----------|----------|-------------------|
| SQL Injection | `SELECT`, `DROP`, `'; DELETE FROM` | Escaped, no execution |
| Unicode | `Ärztëdätën`, `患者ID`, `αβγ` | Handled correctly |
| Special Characters | `col#1`, `data@2023`, `name\tstuff` | Escaped properly |
| Reserved Keywords | `SELECT`, `FROM`, `WHERE`, `NULL` | Quoted, no conflicts |
| Empty/Whitespace | ` `, `\t`, `col name` | Flagged as invalid |
| Very Long | 128+ character names | Truncated/flagged |
| Numeric Start | `123column`, `1st_name` | Handled correctly |
| Similar Names | `PATNR`, `PAT_NR`, `PATNR2` | Distinguished correctly |

**Adversarial Data Values:**

| Column | Hostile Values | Expected |
|--------|---------------|----------|
| PATIENT_NAME | `<script>alert('xss')</script>` | Sanitized |
| NOTES | `'; DROP TABLE patients; --` | Not executed |
| DATE_COL | `9999-99-99`, `-1`, `tomorrow` | Validation fails |
| AMOUNT | `1e308`, `NaN`, `Infinity` | Handled gracefully |

**Expected Results:**
- No SQL injection vulnerabilities
- No crashes on hostile input
- All columns flagged for manual review
- Auto-match rate: ~10% (adversarial naming defeats matching)

---

## ZONE B: REALISTIC EXTREMES (Observed Worst Cases)

**Purpose:** Handle patterns observed in actual messy databases. These are real scenarios we've encountered.

---

### Center 3: Vienna (Legacy Chaos - Austrian)

**Purpose:** Maximum complexity observed in real legacy systems. Based on actual Austrian dental practice migration.

```yaml
center_id: center_03
name: "Vienna Dental Practice"
port: 1435
schema: ordination
quality: messy
language: german_austrian
type: realities
```

**Observed Issues (Realistic):**

| Issue Type | Count | Examples |
|------------|-------|----------|
| Abandoned columns | 25 | Legacy migration artifacts |
| Empty columns | 15 | Never-used fields |
| Mostly empty | 10 | Rarely-used optional fields |
| Misused | 8 | Date fields with text |
| Test data | 5 | Debug columns left in production |
| Duplicate (old/new) | 6 | ADDR_OLD, ADDR_NEW pairs |
| Encoding issues | 3 | Mixed UTF-8/Latin-1 |

**Schema Complexity:**
- Multiple soft-delete conventions in same DB (`DELETED`, `DELKZ`, `IS_REMOVED`)
- Duplicate columns for same concept (migration artifacts)
- Mixed encodings causing garbled umlauts

**Austrian Insurance Values:**
```python
austrian_insurances = [
    "Österreichische Gesundheitskasse (ÖGK)",
    "BVAEB",
    "SVS",
    "Wiener Städtische",
    "Uniqa",
]
```

**Expected Results:**
- Auto-match rate: ~55%
- Review queue: ~200 items
- Excluded columns: ~70
- Demonstrates value of human-in-the-loop

---

### Center 4: Zurich (Data Type Disasters - Swiss)

**Purpose:** Test handling of severe data type mismatches and format inconsistencies.

```yaml
center_id: center_04
name: "Zurich Dental Clinic"
port: 1436
schema: praxis
quality: messy
language: german_swiss
type: realities
```

**Data Type Disasters:**

| Column | Name Suggests | Actual Content | Issue |
|--------|---------------|----------------|-------|
| GEBDAT | Date (birth) | VARCHAR(8) `YYYYMMDD` | Wrong type |
| AKTIV | Boolean | CHAR(1) `J`/`N` | German boolean |
| PREIS | Decimal | VARCHAR with `CHF 150.00` | Currency in string |
| PATIENT_FK | Integer FK | VARCHAR `PAT-00123` | String FK |
| TELEFON | Phone | Mix of formats | Inconsistent |
| TIMESTAMP | DateTime | Unix epoch as VARCHAR | Wrong type |

**Misused Columns (Observed):**

| Column | Expected Type | Actual Content | Mismatch % |
|--------|---------------|----------------|------------|
| DATUM | Date | Mix of dates + "cancelled", "pending" | 35% |
| TELEFON | Phone | Mix of phones + "no phone", "call back" | 28% |
| BETRAG | Decimal | Mix of numbers + "TBD", "gratis" | 40% |

**Swiss Variations:**
- Different insurance terminology (Krankenkasse vs Versicherung)
- French column names mixed with German
- Different date formats (DD.MM.YYYY common)

**Swiss Insurance Values:**
```python
swiss_insurances = [
    "CSS Versicherung",
    "Helsana",
    "Swica",
    "Concordia",
    "Visana",
]
```

**Expected Results:**
- Auto-match rate: ~60%
- High type mismatch flags
- Demonstrates type detection value
- Review queue: ~150 items

---

## ZONE C: MODERATE VARIATIONS (Common Realities)

**Purpose:** Test adaptability to normal variance encountered in typical databases.

---

### Center 5: Hamburg (German Naming Variations)

**Purpose:** Test cross-database learning with standard German column name variations.

```yaml
center_id: center_05
name: "Hamburg Dental Center"
port: 1437
schema: dental
quality: moderate
language: german
type: realities
```

**Column Name Variations (Common):**

| Canonical | Standard | Hamburg Variant |
|-----------|----------|-----------------|
| patient_id | PATNR | PATIENT_NR |
| date | DATUM | EINTRAG_DATUM |
| chart_note | BEMERKUNG | NOTIZ |
| soft_delete | DELKZ | GELOESCHT |
| insurance_name | BEZEICHNUNG | KASSEN_NAME |
| birth_date | GEBDAT | GEBURTSDATUM |

**Compound German Names:**

| Column | Meaning |
|--------|---------|
| PATIENTENSTAMMDATEN | Patient master data |
| BEHANDLUNGSHISTORIE | Treatment history |
| VERSICHERUNGSNUMMER | Insurance number |
| ZAHLUNGSEINGANG | Payment receipt |

**Expected Results:**
- LLM correctly classifies German compound names
- After verification, new names added to value bank
- Auto-match rate: ~80%
- Review queue: ~80 items

---

### Center 6: Frankfurt (Mixed German/English)

**Purpose:** Test mixed language naming conventions (modernized practice).

```yaml
center_id: center_06
name: "Frankfurt Dental Center"
port: 1438
schema: dbo
quality: moderate
language: mixed
type: realities
```

**Mixed Naming Convention:**

| Canonical | German (old) | English (new) | Frankfurt (mixed) |
|-----------|--------------|---------------|-------------------|
| patient_id | PATNR | PATIENT_ID | patient_id |
| date | DATUM | ENTRY_DATE | entry_date |
| chart_note | BEMERKUNG | NOTES | notes |
| soft_delete | DELKZ | IS_DELETED | is_deleted |
| insurance_type | ART | TYPE | type |

**Partial Modernization Patterns:**
- Old tables use German naming (KARTEI, PATIENT)
- New tables use English naming (appointments, billing)
- Some tables have mixed column names

**Expected Results:**
- System handles English column names
- Value bank matching still works (German insurance names in English-named columns)
- Auto-match rate: ~78%
- Slight confidence drop due to name/value language mismatch

---

### Center 7: Cologne (Data Quality - Abandoned & Empty)

**Purpose:** Test abandoned column and empty column detection with clear-cut cases.

```yaml
center_id: center_07
name: "Cologne Dental Center"
port: 1439
schema: ck
quality: poor
type: realities
```

**Abandoned Columns (Clear Cases):**

| Column | Last Value Date | Months Ago | Detection |
|--------|-----------------|------------|-----------|
| KARTEI.OLD_STATUS | 2022-01-15 | 36 | Should flag |
| KARTEI.LEGACY_CODE | 2022-06-01 | 31 | Should flag |
| PATIENT.OLD_ADDRESS | 2021-06-30 | 43 | Should flag |
| BEHANDLUNG.V1_FLAG | 2020-12-31 | 49 | Should flag |

**Active Columns with Old Data (Should NOT flag):**

| Column | Data Range | Recent Values | Detection |
|--------|------------|---------------|-----------|
| KASSEN.GRUENDUNG | 1990-2024 | Yes (new insurances) | NOT flagged |
| PATIENT.GEBDAT | 1920-2024 | Yes (births) | NOT flagged |

**Empty & Mostly Empty:**

| Column | NULL % | Expected Label |
|--------|--------|----------------|
| PATIENT.FAX | 100% | empty (auto-exclude) |
| PATIENT.TELEX | 100% | empty (auto-exclude) |
| KARTEI.UNUSED_1 | 100% | empty (auto-exclude) |
| PATIENT.MOBILE | 92% | valid (below threshold) |
| PATIENT.EMAIL | 88% | valid (below threshold) |

**Expected Results:**
- 4 columns flagged as abandoned
- 3 columns auto-excluded (100% empty)
- No false positives on old-but-active data
- Auto-match rate: ~75%

---

## ZONE D: CLEAN BASELINES (Ideal State)

**Purpose:** Establish ground truth and verify no false positives. If these fail, something is seriously wrong.

---

### Center 8: Munich (Reference Implementation)

**Purpose:** Canonical Ivoris schema with perfect data. The gold standard.

```yaml
center_id: center_08
name: "Munich Dental Center"
port: 1440
schema: ck
quality: clean
type: realities
```

**Schema (Ivoris Standard):**

| Table | Description | Key Columns |
|-------|-------------|-------------|
| PATIENT | Patient master | PATNR (PK), NAME, VORNAME, GEBDAT |
| KARTEI | Chart entries | KARESSION (PK), PATNR (FK), DATUM, BEMERKUNG, DELKZ |
| KASSEN | Insurance companies | KASESSION (PK), BEZEICHNUNG, ART |
| PATKASSE | Patient-Insurance link | PATNR (FK), KASESSION (FK), GUELTIG_AB |
| LEISTUNG | Services/Procedures | LEISESSION (PK), BEZEICHNUNG, GEBUEHR |
| BEHANDLUNG | Treatments | BEHSESSION (PK), PATNR (FK), DATUM, LEISESSION (FK) |

**Data Characteristics:**
- 1,500 patients
- 20,000 chart entries
- 50 insurance companies (German)
- Clean date formats (YYYYMMDD)
- No abandoned columns
- <5% NULL in optional fields
- Standard German column names

**Expected Results:**
- Auto-match rate: **95%+**
- Review queue: <30 items
- Excluded columns: <5
- Zero false positives

---

### Center 9: Berlin (Clean + Volume)

**Purpose:** Same quality as Munich but with high volume. Tests performance, not correctness.

```yaml
center_id: center_09
name: "Berlin Dental Center"
port: 1441
schema: ck
quality: clean
type: realities
```

**Volume:**
- 10,000 patients (10x Munich)
- 150,000 chart entries
- 80 insurance companies

**Same Schema as Munich, Testing:**
- Profiling performance at scale
- Sample value selection accuracy
- Query timeout handling
- Memory usage during analysis

**Expected Results:**
- Auto-match rate: **96%+** (benefits from Munich learning)
- Review queue: <25 items
- Performance: Complete profiling in <2 minutes
- Cross-DB learning demonstrated

---

### Center 10: Stuttgart (Minimal Viable)

**Purpose:** Minimum required tables/columns. Tests handling of sparse but valid data.

```yaml
center_id: center_10
name: "Stuttgart Dental Center"
port: 1442
schema: minimal
quality: clean
type: realities
```

**Minimal Schema:**

| Table | Columns | Rows |
|-------|---------|------|
| PATIENT | PATNR, NAME, VORNAME | 100 |
| KARTEI | KARESSION, PATNR, DATUM, BEMERKUNG | 500 |
| KASSEN | KASESSION, BEZEICHNUNG | 10 |

**Testing:**
- No optional columns
- Minimum viable data
- System works without "nice to have" fields
- New practice onboarding scenario

**Expected Results:**
- Auto-match rate: **98%** (only essential columns)
- Review queue: <10 items
- Demonstrates quick onboarding for simple practices
- Zero complexity

---

## Ground Truth Manifest Format

Every simulated database has a companion YAML file defining expected results.

```yaml
# ground_truth/center_01_pathological.yml

center:
  id: "center_01"
  name: "Pathological Edge Cases"
  zone: "A"
  type: "synthetic"
  purpose: "threshold_testing"

expected_detections:
  # Threshold boundary tests
  NULL_94:
    expected_flag: false
    actual_null_pct: 94.0
    note: "Below 95% threshold"
  NULL_95:
    expected_flag: true
    flag_type: "mostly_empty"
    actual_null_pct: 95.0
    note: "At threshold"
  NULL_96:
    expected_flag: true
    flag_type: "mostly_empty"
    actual_null_pct: 96.0
    note: "Above threshold"

  OLD_24M:
    expected_flag: true
    flag_type: "abandoned"
    last_value_months: 24
    note: "At 24-month threshold"

  MISMATCH_30:
    expected_flag: true
    flag_type: "misused"
    mismatch_pct: 30.0
    note: "At 30% threshold"

validation_rules:
  - name: "threshold_precision"
    description: "All threshold boundaries must be exact"
    tolerance: 0.1%

statistics:
  total_columns: 50
  expected_flags: 25
  expected_auto_exclude: 5
  expected_auto_match_rate: "20%"
```

---

## Validation Strategy by Zone

| Zone | Pass Criteria | Failure Response |
|------|--------------|------------------|
| **A (Synthetic)** | Correctly flags/rejects extremes, no crashes | Bug in detection logic or error handling |
| **B (Realistic Extreme)** | Handles gracefully, appropriate review flags | Improve edge case handling |
| **C (Variations)** | Auto-matches with reasonable confidence | Expand value banks, improve LLM prompts |
| **D (Clean)** | 95%+ auto-match, zero false positives | **SERIOUS REGRESSION** - stop and investigate |

---

## Docker Compose Configuration

```yaml
# docker-compose.simulator.yml

version: '3.8'

services:
  # ══════════════════════════════════════════════════════════════════════
  # ZONE A: SYNTHETIC EXTREMES
  # ══════════════════════════════════════════════════════════════════════

  # Center 1: Pathological Edge Cases
  center_01_pathological:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_pathological
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=SimTest123!
      - MSSQL_PID=Developer
    ports:
      - "1433:1433"
    volumes:
      - ./data/center_01:/var/opt/mssql/data
      - ./scripts/center_01:/docker-entrypoint-initdb.d
    healthcheck:
      test: /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P SimTest123! -Q "SELECT 1"
      interval: 10s
      timeout: 5s
      retries: 5

  # Center 2: Adversarial Naming
  center_02_adversarial:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_adversarial
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=SimTest123!
      - MSSQL_PID=Developer
    ports:
      - "1434:1433"
    volumes:
      - ./data/center_02:/var/opt/mssql/data
      - ./scripts/center_02:/docker-entrypoint-initdb.d

  # ══════════════════════════════════════════════════════════════════════
  # ZONE B: REALISTIC EXTREMES
  # ══════════════════════════════════════════════════════════════════════

  # Center 3: Vienna (Legacy Chaos)
  center_03_vienna:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_vienna
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=SimTest123!
      - MSSQL_PID=Developer
    ports:
      - "1435:1433"
    volumes:
      - ./data/center_03:/var/opt/mssql/data
      - ./scripts/center_03:/docker-entrypoint-initdb.d

  # Center 4: Zurich (Data Type Disasters)
  center_04_zurich:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_zurich
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=SimTest123!
      - MSSQL_PID=Developer
    ports:
      - "1436:1433"
    volumes:
      - ./data/center_04:/var/opt/mssql/data
      - ./scripts/center_04:/docker-entrypoint-initdb.d

  # ══════════════════════════════════════════════════════════════════════
  # ZONE C: MODERATE VARIATIONS
  # ══════════════════════════════════════════════════════════════════════

  # Center 5: Hamburg (German Naming Variations)
  center_05_hamburg:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_hamburg
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=SimTest123!
      - MSSQL_PID=Developer
    ports:
      - "1437:1433"
    volumes:
      - ./data/center_05:/var/opt/mssql/data
      - ./scripts/center_05:/docker-entrypoint-initdb.d

  # Center 6: Frankfurt (Mixed German/English)
  center_06_frankfurt:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_frankfurt
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=SimTest123!
      - MSSQL_PID=Developer
    ports:
      - "1438:1433"
    volumes:
      - ./data/center_06:/var/opt/mssql/data
      - ./scripts/center_06:/docker-entrypoint-initdb.d

  # Center 7: Cologne (Abandoned & Empty)
  center_07_cologne:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_cologne
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=SimTest123!
      - MSSQL_PID=Developer
    ports:
      - "1439:1433"
    volumes:
      - ./data/center_07:/var/opt/mssql/data
      - ./scripts/center_07:/docker-entrypoint-initdb.d

  # ══════════════════════════════════════════════════════════════════════
  # ZONE D: CLEAN BASELINES
  # ══════════════════════════════════════════════════════════════════════

  # Center 8: Munich (Reference Implementation)
  center_08_munich:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_munich
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=SimTest123!
      - MSSQL_PID=Developer
    ports:
      - "1440:1433"
    volumes:
      - ./data/center_08:/var/opt/mssql/data
      - ./scripts/center_08:/docker-entrypoint-initdb.d

  # Center 9: Berlin (Clean + Volume)
  center_09_berlin:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_berlin
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=SimTest123!
      - MSSQL_PID=Developer
    ports:
      - "1441:1433"
    volumes:
      - ./data/center_09:/var/opt/mssql/data
      - ./scripts/center_09:/docker-entrypoint-initdb.d

  # Center 10: Stuttgart (Minimal Viable)
  center_10_stuttgart:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_stuttgart
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=SimTest123!
      - MSSQL_PID=Developer
    ports:
      - "1442:1433"
    volumes:
      - ./data/center_10:/var/opt/mssql/data
      - ./scripts/center_10:/docker-entrypoint-initdb.d

networks:
  default:
    name: schema_simulator_network
```

---

## Directory Structure

```
simulator/
├── docker-compose.simulator.yml
├── README.md                          # Quick start guide
│
├── ground_truth/                      # Expected results for validation
│   ├── center_01_pathological.yml     # Zone A
│   ├── center_02_adversarial.yml      # Zone A
│   ├── center_03_vienna.yml           # Zone B
│   ├── center_04_zurich.yml           # Zone B
│   ├── center_05_hamburg.yml          # Zone C
│   ├── center_06_frankfurt.yml        # Zone C
│   ├── center_07_cologne.yml          # Zone C
│   ├── center_08_munich.yml           # Zone D
│   ├── center_09_berlin.yml           # Zone D
│   └── center_10_stuttgart.yml        # Zone D
│
├── scripts/                           # SQL initialization scripts
│   ├── center_01/                     # Pathological
│   │   ├── 01_create_schema.sql
│   │   ├── 02_create_tables.sql
│   │   └── 03_insert_threshold_data.sql
│   ├── center_02/                     # Adversarial
│   │   └── ...
│   └── .../
│
├── generators/                        # Python data generators
│   ├── __init__.py
│   ├── base.py                       # Base generator class
│   ├── threshold_generator.py        # Zone A: synthetic extremes
│   ├── chaos_generator.py            # Zone B: realistic mess
│   ├── variation_generator.py        # Zone C: naming variations
│   ├── clean_generator.py            # Zone D: baselines
│   └── center_configs/
│       ├── zone_a.py
│       ├── zone_b.py
│       ├── zone_c.py
│       └── zone_d.py
│
├── validation/                        # Validation scripts
│   ├── validate_ground_truth.py
│   ├── zone_validators/
│   │   ├── zone_a_validator.py       # Threshold precision
│   │   ├── zone_b_validator.py       # Graceful handling
│   │   ├── zone_c_validator.py       # Adaptability
│   │   └── zone_d_validator.py       # Accuracy (strictest)
│   └── generate_report.py
│
└── data/                             # Generated data (gitignored)
    ├── center_01/
    ├── center_02/
    └── ...
```

---

## Usage

### Run by Zone

```bash
# Start Zone A only (synthetic extremes - robustness testing)
docker-compose -f docker-compose.simulator.yml up -d \
  center_01_pathological center_02_adversarial

# Start Zone D only (clean baselines - accuracy testing)
docker-compose -f docker-compose.simulator.yml up -d \
  center_08_munich center_09_berlin center_10_stuttgart

# Start all
docker-compose -f docker-compose.simulator.yml up -d
```

### Validate by Zone

```bash
# Zone A: Must not crash (allow low match rate)
python -m validation.zone_validators.zone_a_validator --centers 1,2

# Zone D: Must achieve 95%+ match rate
python -m validation.zone_validators.zone_d_validator --centers 8,9,10

# Full validation
python -m validation.validate_all --report
```

---

## Expected Demo Flow (Extreme → Normal)

### Demo Script: Proving Robustness

**1. Start with Zone D (Clean) - Establish Baseline**
```
"First, let's see the system working on clean data."
→ Center 8 (Munich): 95% auto-match
→ "This is our target quality."
```

**2. Show Zone A (Synthetic) - Prove Robustness**
```
"Now let's stress-test with pathological cases."
→ Center 1: Threshold edge cases
→ "See how it correctly identifies the 95% boundary."
→ Center 2: Adversarial naming
→ "No crashes, all flagged for review."
```

**3. Show Zone B (Realistic Extreme) - Handle Chaos**
```
"These are real scenarios from legacy migrations."
→ Center 3 (Vienna): 55% match, 200 review items
→ "Human-in-the-loop is essential here."
```

**4. Show Zone C (Variations) - Demonstrate Learning**
```
"Watch the system learn from variations."
→ Center 5 (Hamburg): German naming variations
→ Center 6 (Frankfurt): Mixed German/English
→ "Value bank grows with each center."
```

**5. Return to Zone D - Show Improvement**
```
"After learning from all centers..."
→ Center 9 (Berlin): 96% match (improved from 95%)
→ "Cross-DB learning in action."
```

### Demo Metrics Progression

| Center | Zone | Auto-Match | Review Queue | Learning |
|--------|------|------------|--------------|----------|
| 8 Munich | D | 95% | 30 | Baseline |
| 1 Pathological | A | 20% | 40 | Thresholds |
| 2 Adversarial | A | 10% | 50 | Security |
| 3 Vienna | B | 55% | 200 | Chaos handling |
| 4 Zurich | B | 60% | 150 | Type detection |
| 5 Hamburg | C | 80% | 80 | German names |
| 6 Frankfurt | C | 78% | 85 | Mixed languages |
| 7 Cologne | C | 75% | 90 | Quality detection |
| 9 Berlin | D | 96% | 25 | **Improved** |
| 10 Stuttgart | D | 98% | 10 | Minimal case |

---

## Validation Acceptance Criteria

```gherkin
Feature: Database Simulator Validation

  # ════════════════════════════════════════════════════════════════
  # ZONE A: SYNTHETIC EXTREMES
  # ════════════════════════════════════════════════════════════════

  Scenario: Threshold boundaries are precise
    Given center "center_01_pathological" is running
    When I query column "NULL_94"
    Then NULL percentage should be exactly 94.0%
    And it should NOT be flagged
    When I query column "NULL_95"
    Then NULL percentage should be exactly 95.0%
    And it should be flagged as "mostly_empty"

  Scenario: Adversarial input doesn't crash system
    Given center "center_02_adversarial" is running
    When I run schema profiling
    Then no SQL injection should occur
    And no unhandled exceptions should be thrown
    And all columns should be flagged for manual review

  # ════════════════════════════════════════════════════════════════
  # ZONE B: REALISTIC EXTREMES
  # ════════════════════════════════════════════════════════════════

  Scenario: Legacy chaos is handled gracefully
    Given center "center_03_vienna" is running
    When I run the full pipeline
    Then auto-match rate should be between 50-65%
    And review queue should contain 150-250 items
    And no columns should be incorrectly auto-approved

  # ════════════════════════════════════════════════════════════════
  # ZONE C: MODERATE VARIATIONS
  # ════════════════════════════════════════════════════════════════

  Scenario: German naming variations are learned
    Given center "center_05_hamburg" has been processed
    When I process center "center_06_frankfurt"
    Then previously learned column names should match faster
    And value bank should contain German insurance names

  # ════════════════════════════════════════════════════════════════
  # ZONE D: CLEAN BASELINES (STRICTEST)
  # ════════════════════════════════════════════════════════════════

  Scenario: Clean baseline achieves high accuracy
    Given center "center_08_munich" is running
    When I run the full pipeline
    Then auto-match rate should be >= 95%
    And review queue should contain <= 30 items
    And there should be ZERO false positives

  Scenario: Cross-DB learning improves results
    Given center "center_08_munich" has been processed
    When I process center "center_09_berlin"
    Then auto-match rate should be >= 96%
    And processing time should be < center_08 time
```

---

## References

- [ACCEPTANCE.md](ACCEPTANCE.md) - Feature acceptance criteria
- [03-value-banks.md](03-value-banks.md) - Value bank and quality detection
- [ARCHITECTURE.md](ARCHITECTURE.md) - Backend architecture
- [DISCUSSION_LOG.md](DISCUSSION_LOG.md) - Design decision history

---

*Created: 2024-01-14*
*Updated: 2024-01-14 (Extreme → Normal restructure)*
*Status: Planning*
