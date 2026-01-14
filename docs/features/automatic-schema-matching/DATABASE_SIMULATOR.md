# Database Simulator

**Purpose:** Generate realistic test databases for Automatic Schema Matching development and demos.
**Format:** Docker SQL Server containers
**Scale:** 10 simulated dental centers

---

## Overview

### Goals

1. **Testing:** Verify detection limits, thresholds, and edge cases
2. **Demo:** Showcase the feature with realistic data
3. **Cross-DB Learning:** Demonstrate how the system improves with each center
4. **Ground Truth:** Every database has a manifest of expected results

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Docker Compose Environment                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐     ┌──────────┐           │
│  │ Center 1 │ │ Center 2 │ │ Center 3 │ ... │ Center 10│           │
│  │ Munich   │ │ Berlin   │ │ Hamburg  │     │ Vienna   │           │
│  │ :1433    │ │ :1434    │ │ :1435    │     │ :1442    │           │
│  └──────────┘ └──────────┘ └──────────┘     └──────────┘           │
│       │            │            │                 │                 │
│       └────────────┴────────────┴─────────────────┘                 │
│                              │                                       │
│                    ┌─────────────────┐                              │
│                    │  Ground Truth   │                              │
│                    │  Manifests      │                              │
│                    │  (YAML files)   │                              │
│                    └─────────────────┘                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Ground Truth Manifest Format

Every simulated database has a companion YAML file defining expected results.

```yaml
# ground_truth/center_01_munich.yml

center:
  id: "center_01"
  name: "Munich Dental Center"
  schema: "ck"
  language: "german"
  data_quality: "clean"  # clean | moderate | messy

expected_mappings:
  KARTEI:
    PATNR:
      canonical_entity: patient_id
      expected_confidence: ">=0.90"
      risk_class: critical
      match_reason: "Known column name"
    DATUM:
      canonical_entity: date
      expected_confidence: ">=0.85"
      format: YYYYMMDD
      validation: date_format
    BEMERKUNG:
      canonical_entity: chart_note
      expected_confidence: ">=0.80"
    DELKZ:
      canonical_entity: soft_delete
      expected_confidence: ">=0.85"
      values: [0, 1]

  KASSEN:
    KASESSION:
      canonical_entity: insurance_id
      expected_confidence: ">=0.90"
    BEZEICHNUNG:
      canonical_entity: insurance_name
      expected_confidence: ">=0.85"
      sample_values: ["DAK Gesundheit", "AOK Bayern", "BARMER"]
    ART:
      canonical_entity: insurance_type
      expected_confidence: ">=0.80"
      values: ["P", "1", "2", "3"]

expected_quality_flags:
  KARTEI.OLD_STATUS:
    label: abandoned
    reason: "No values after 2019-03-15"
  KARTEI.UNUSED_FIELD:
    label: empty
    reason: "100% NULL"
  PATIENT.FAX:
    label: mostly_empty
    reason: "97% NULL"
  KARTEI.DEBUG_COL:
    label: test_only
    reason: "All values match test patterns"

expected_value_bank_contributions:
  insurance_name:
    - "DAK Gesundheit"
    - "AOK Bayern"
    - "BARMER"
    - "Techniker Krankenkasse"
  insurance_type:
    - "P"
    - "1"
    - "2"

statistics:
  total_tables: 50
  total_columns: 487
  expected_auto_match_rate: "85%"
  expected_review_queue_size: 73
  expected_excluded_columns: 45
```

---

## The 10 Centers

### Design Philosophy

| Centers | Purpose | Characteristics |
|---------|---------|-----------------|
| 1-2 | **Baseline/Seed** | Clean data, standard naming, seeds the system |
| 3-4 | **Naming Variations** | Different column names for same concepts |
| 5-6 | **Data Quality Issues** | Abandoned, empty, misused columns |
| 7-8 | **Threshold Edge Cases** | Values at exact detection limits |
| 9-10 | **Realistic Messy** | Combination of all issues, like real production |

---

### Center 1: Munich (Baseline - Clean)

**Purpose:** Seed the system with clean, well-structured data.

```yaml
center_id: center_01
name: "Munich Dental Center"
port: 1433
schema: ck
quality: clean
```

**Schema (Ivoris-realistic):**

| Table | Description | Key Columns |
|-------|-------------|-------------|
| PATIENT | Patient master | PATNR (PK), NAME, VORNAME, GEBDAT |
| KARTEI | Chart entries | KARESSION (PK), PATNR (FK), DATUM, BEMERKUNG, DELKZ |
| KASSEN | Insurance companies | KASESSION (PK), BEZEICHNUNG, ART |
| PATKASSE | Patient-Insurance link | PATNR (FK), KASESSION (FK), GUELTIG_AB |
| LEISTUNG | Services/Procedures | LEISESSION (PK), BEZEICHNUNG, GEBUEHR |
| BEHANDLUNG | Treatments | BEHSESSION (PK), PATNR (FK), DATUM, LEISESSION (FK) |

**Data Characteristics:**
- 1,000 patients
- 15,000 chart entries
- 50 insurance companies
- Clean date formats (YYYYMMDD)
- No abandoned columns
- <5% NULL in optional fields
- Standard German column names

**Expected Results:**
- Auto-match rate: 90%+
- Review queue: <50 items
- Excluded columns: <10

---

### Center 2: Berlin (Baseline - Clean, Slight Variations)

**Purpose:** Second clean center to establish cross-DB consistency.

```yaml
center_id: center_02
name: "Berlin Dental Center"
port: 1434
schema: ck
quality: clean
```

**Variations from Center 1:**
- Soft delete column: `DELETED` instead of `DELKZ`
- Some additional columns not in Center 1
- Different insurance company names (regional)

**Expected Results:**
- System learns `DELETED` → soft_delete
- Cross-DB consistency tracking begins
- Auto-match rate: 92%+ (benefits from Center 1)

---

### Center 3: Hamburg (Naming Variations)

**Purpose:** Test cross-database learning with different column names.

```yaml
center_id: center_03
name: "Hamburg Dental Center"
port: 1435
schema: dental
quality: moderate
```

**Column Name Variations:**

| Canonical | Center 1 | Center 3 |
|-----------|----------|----------|
| patient_id | PATNR | PATIENT_NR |
| date | DATUM | EINTRAG_DATUM |
| chart_note | BEMERKUNG | NOTIZ |
| soft_delete | DELKZ | GELOESCHT |
| insurance_name | BEZEICHNUNG | KASSEN_NAME |

**Expected Results:**
- LLM correctly classifies new names
- After verification, new names added to known_names
- Future centers benefit from learned variants

---

### Center 4: Frankfurt (Naming Variations + English Mix)

**Purpose:** Test mixed German/English naming conventions.

```yaml
center_id: center_04
name: "Frankfurt Dental Center"
port: 1436
schema: dbo
quality: moderate
```

**Column Name Variations:**

| Canonical | Center 1 | Center 4 |
|-----------|----------|----------|
| patient_id | PATNR | PATIENT_ID |
| date | DATUM | ENTRY_DATE |
| chart_note | BEMERKUNG | NOTES |
| soft_delete | DELKZ | IS_DELETED |
| insurance_type | ART | TYPE |

**Expected Results:**
- System handles English column names
- Value bank matching still works (German insurance names)
- Confidence slightly lower due to name/value language mismatch

---

### Center 5: Cologne (Data Quality - Abandoned Columns)

**Purpose:** Test abandoned column detection.

```yaml
center_id: center_05
name: "Cologne Dental Center"
port: 1437
schema: ck
quality: poor
```

**Data Quality Issues:**

| Column | Issue | Last Value Date | Detection |
|--------|-------|-----------------|-----------|
| KARTEI.OLD_STATUS | Abandoned | 2019-03-15 | Should flag |
| KARTEI.LEGACY_CODE | Abandoned | 2020-01-01 | Should flag |
| PATIENT.OLD_ADDRESS | Abandoned | 2018-06-30 | Should flag |
| BEHANDLUNG.V1_FLAG | Abandoned | 2017-12-31 | Should flag |

**Active Columns with Old Data (Should NOT flag):**

| Column | Data Range | Recent Values | Detection |
|--------|------------|---------------|-----------|
| KASSEN.GRUENDUNG | 1990-2023 | Yes (new insurances added) | Should NOT flag |

**Expected Results:**
- 4 columns flagged as abandoned
- Threshold test: 24 months cutoff works correctly
- Active columns with old data not falsely flagged

---

### Center 6: Düsseldorf (Data Quality - Empty & Mostly Empty)

**Purpose:** Test empty and mostly-empty column detection.

```yaml
center_id: center_06
name: "Düsseldorf Dental Center"
port: 1438
schema: ck
quality: poor
```

**Data Quality Issues:**

| Column | NULL % | Expected Label | Notes |
|--------|--------|----------------|-------|
| PATIENT.FAX | 100% | empty | Auto-exclude |
| PATIENT.TELEX | 100% | empty | Auto-exclude |
| KARTEI.UNUSED_1 | 100% | empty | Auto-exclude |
| PATIENT.MOBILE | 97% | mostly_empty | Flag for review |
| PATIENT.EMAIL | 96% | mostly_empty | Flag for review |
| PATIENT.EMERGENCY | 94% | (valid) | Should NOT flag (below 95%) |
| KARTEI.OPTIONAL_NOTE | 80% | (valid) | Should NOT flag |

**Threshold Edge Cases:**

| Column | NULL % | Expected |
|--------|--------|----------|
| TEST_94 | 94.0% | NOT flagged |
| TEST_95 | 95.0% | Flagged (at threshold) |
| TEST_96 | 96.0% | Flagged |

**Expected Results:**
- 3 columns auto-excluded (100% empty)
- 2 columns flagged for review (95-99% empty)
- Threshold boundary tested precisely

---

### Center 7: Stuttgart (Data Quality - Misused & Test Data)

**Purpose:** Test misused column and test data detection.

```yaml
center_id: center_07
name: "Stuttgart Dental Center"
port: 1439
schema: ck
quality: poor
```

**Misused Columns:**

| Column | Name Suggests | Actual Content | Mismatch % |
|--------|---------------|----------------|------------|
| KARTEI.DATUM | Date | Mix of dates + "cancelled", "pending" | 35% |
| PATIENT.PHONE | Phone | Mix of phones + "no phone", "call later" | 28% |
| BEHANDLUNG.PREIS | Price/Number | Mix of numbers + "TBD", "free" | 40% |

**Test Data Columns:**

| Column | Values | Pattern |
|--------|--------|---------|
| KARTEI.DEBUG_FLAG | "TEST", "XXX", "DEBUG" | test_pattern |
| PATIENT.TEST_COL | "DUMMY", "ASDF", "12345" | test_pattern |
| BEHANDLUNG.DEV_NOTE | "TODO", "FIXME", "TEST" | test_pattern |

**Expected Results:**
- 3 columns flagged as misused (type mismatch >30%)
- 3 columns flagged as test_only
- System learns to exclude test patterns

---

### Center 8: Leipzig (Threshold Edge Cases)

**Purpose:** Test exact threshold boundaries for all detection types.

```yaml
center_id: center_08
name: "Leipzig Dental Center"
port: 1440
schema: test
quality: synthetic
```

**Synthetic Threshold Tests:**

| Test | Column | Value | Expected Result |
|------|--------|-------|-----------------|
| Empty threshold | EMPTY_100 | 100% NULL | auto_excluded |
| Empty threshold | EMPTY_99 | 99% NULL | mostly_empty (flagged) |
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

**Expected Results:**
- All threshold boundaries correctly identified
- Useful for regression testing
- Documents exact system behavior

---

### Center 9: Zurich (Realistic Messy - Swiss Practice)

**Purpose:** Realistic messy database combining multiple issues.

```yaml
center_id: center_09
name: "Zurich Dental Clinic"
port: 1441
schema: praxis
quality: messy
language: german_swiss
```

**Characteristics:**
- Swiss German variations in data
- Mix of German, French column names (Swiss multilingual)
- 15% abandoned columns
- 10% empty columns
- 5% misused columns
- Some test data mixed in
- Different insurance system (Swiss insurances)

**Schema Variations:**

| Canonical | Swiss Name | Notes |
|-----------|------------|-------|
| patient_id | PATIENT_NR | Standard |
| insurance_name | KRANKENKASSE | Swiss term |
| insurance_type | VERSICHERUNGSART | Different values (Grundversicherung, Zusatz) |

**Swiss Insurance Values:**
- "CSS Versicherung"
- "Helsana"
- "Swica"
- "Concordia"
- "Visana"

**Expected Results:**
- System handles Swiss variations
- Value bank learns Swiss insurance names
- Lower auto-match rate due to complexity (~70%)
- Higher review queue (~150 items)

---

### Center 10: Vienna (Realistic Messy - Austrian Practice)

**Purpose:** Final stress test with Austrian variations and maximum complexity.

```yaml
center_id: center_10
name: "Vienna Dental Practice"
port: 1442
schema: ordination
quality: messy
language: german_austrian
```

**Characteristics:**
- Austrian German variations
- Legacy system migration artifacts
- Multiple soft-delete conventions in same DB
- Duplicate columns (old and new versions)
- Some columns with mixed encodings
- Austrian insurance system

**Maximum Complexity:**

| Issue Type | Count | Examples |
|------------|-------|----------|
| Abandoned columns | 25 | Legacy migration artifacts |
| Empty columns | 15 | Never-used fields |
| Mostly empty | 10 | Rarely-used optional fields |
| Misused | 8 | Date fields with text |
| Test data | 5 | Debug columns |
| Duplicate (old/new) | 6 | ADDR_OLD, ADDR_NEW pairs |
| Encoding issues | 3 | Mixed UTF-8/Latin-1 |

**Austrian Insurance Values:**
- "Österreichische Gesundheitskasse (ÖGK)"
- "BVAEB"
- "SVS"
- "Wiener Städtische"
- "Uniqa"

**Expected Results:**
- Lowest auto-match rate (~60%)
- Largest review queue (~200 items)
- Most excluded columns (~70)
- Tests system at realistic worst-case
- Demonstrates value of human-in-the-loop

---

## Data Generation Specifications

### Row Counts per Center

| Table | Rows | Notes |
|-------|------|-------|
| PATIENT | 500-2,000 | Varies by center size |
| KARTEI | 5,000-20,000 | ~10 entries per patient |
| KASSEN | 30-80 | German/Swiss/Austrian insurances |
| PATKASSE | 600-2,500 | ~1.2 insurances per patient |
| LEISTUNG | 200-500 | Dental procedure catalog |
| BEHANDLUNG | 3,000-15,000 | Treatment records |

### Date Ranges

| Center | Data Start | Data End | Notes |
|--------|------------|----------|-------|
| 1-4 | 2018-01-01 | Present | Normal range |
| 5-6 | 2015-01-01 | Present | Includes abandoned columns |
| 7-8 | 2010-01-01 | Present | Wide range for testing |
| 9-10 | 2012-01-01 | Present | Realistic messy |

### Value Generation Rules

**Patient Names:**
```python
# German name generator
first_names = ["Hans", "Klaus", "Peter", "Maria", "Anna", "Sophie", ...]
last_names = ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", ...]
```

**Insurance Names:**
```python
german_insurances = [
    "DAK Gesundheit",
    "AOK Bayern",
    "AOK Baden-Württemberg",
    "BARMER",
    "Techniker Krankenkasse",
    "IKK classic",
    "KKH",
    "hkk",
    "Debeka",
    "Allianz Private",
    # ... 70+ real German insurances
]

swiss_insurances = [
    "CSS Versicherung",
    "Helsana",
    "Swica",
    "Concordia",
    "Visana",
    # ... Swiss insurances
]

austrian_insurances = [
    "Österreichische Gesundheitskasse (ÖGK)",
    "BVAEB",
    "SVS",
    # ... Austrian insurances
]
```

**Date Formats:**
```python
# Center 1-8: Standard YYYYMMDD
date_format = "%Y%m%d"  # "20220118"

# Center 9-10: Mixed formats (realistic mess)
date_formats = [
    "%Y%m%d",      # "20220118"
    "%d.%m.%Y",    # "18.01.2022"
    "%Y-%m-%d",    # "2022-01-18"
]
```

---

## Docker Compose Configuration

```yaml
# docker-compose.simulator.yml

version: '3.8'

services:
  # Center 1: Munich (Baseline)
  center_01_munich:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_munich
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

  # Center 2: Berlin
  center_02_berlin:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_berlin
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=SimTest123!
      - MSSQL_PID=Developer
    ports:
      - "1434:1433"
    volumes:
      - ./data/center_02:/var/opt/mssql/data
      - ./scripts/center_02:/docker-entrypoint-initdb.d

  # Center 3: Hamburg
  center_03_hamburg:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_hamburg
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=SimTest123!
      - MSSQL_PID=Developer
    ports:
      - "1435:1433"
    volumes:
      - ./data/center_03:/var/opt/mssql/data
      - ./scripts/center_03:/docker-entrypoint-initdb.d

  # Center 4: Frankfurt
  center_04_frankfurt:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_frankfurt
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=SimTest123!
      - MSSQL_PID=Developer
    ports:
      - "1436:1433"
    volumes:
      - ./data/center_04:/var/opt/mssql/data
      - ./scripts/center_04:/docker-entrypoint-initdb.d

  # Center 5: Cologne
  center_05_cologne:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_cologne
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=SimTest123!
      - MSSQL_PID=Developer
    ports:
      - "1437:1433"
    volumes:
      - ./data/center_05:/var/opt/mssql/data
      - ./scripts/center_05:/docker-entrypoint-initdb.d

  # Center 6: Düsseldorf
  center_06_dusseldorf:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_dusseldorf
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=SimTest123!
      - MSSQL_PID=Developer
    ports:
      - "1438:1433"
    volumes:
      - ./data/center_06:/var/opt/mssql/data
      - ./scripts/center_06:/docker-entrypoint-initdb.d

  # Center 7: Stuttgart
  center_07_stuttgart:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_stuttgart
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=SimTest123!
      - MSSQL_PID=Developer
    ports:
      - "1439:1433"
    volumes:
      - ./data/center_07:/var/opt/mssql/data
      - ./scripts/center_07:/docker-entrypoint-initdb.d

  # Center 8: Leipzig
  center_08_leipzig:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_leipzig
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=SimTest123!
      - MSSQL_PID=Developer
    ports:
      - "1440:1433"
    volumes:
      - ./data/center_08:/var/opt/mssql/data
      - ./scripts/center_08:/docker-entrypoint-initdb.d

  # Center 9: Zurich (Swiss)
  center_09_zurich:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_zurich
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=SimTest123!
      - MSSQL_PID=Developer
    ports:
      - "1441:1433"
    volumes:
      - ./data/center_09:/var/opt/mssql/data
      - ./scripts/center_09:/docker-entrypoint-initdb.d

  # Center 10: Vienna (Austrian)
  center_10_vienna:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: schema_sim_vienna
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
│   ├── center_01_munich.yml
│   ├── center_02_berlin.yml
│   ├── center_03_hamburg.yml
│   ├── center_04_frankfurt.yml
│   ├── center_05_cologne.yml
│   ├── center_06_dusseldorf.yml
│   ├── center_07_stuttgart.yml
│   ├── center_08_leipzig.yml
│   ├── center_09_zurich.yml
│   └── center_10_vienna.yml
│
├── scripts/                           # SQL initialization scripts
│   ├── center_01/
│   │   ├── 01_create_schema.sql
│   │   ├── 02_create_tables.sql
│   │   └── 03_insert_data.sql
│   ├── center_02/
│   │   └── ...
│   └── .../
│
├── generators/                        # Python data generators
│   ├── __init__.py
│   ├── base.py                       # Base generator class
│   ├── patients.py                   # Patient data generator
│   ├── insurances.py                 # Insurance data generator
│   ├── chart_entries.py              # Chart entry generator
│   ├── quality_issues.py             # Inject quality issues
│   └── center_configs/               # Per-center configuration
│       ├── center_01.py
│       ├── center_02.py
│       └── ...
│
├── validation/                        # Validation scripts
│   ├── validate_ground_truth.py      # Compare results to expected
│   └── generate_report.py            # Generate validation report
│
└── data/                             # Generated data (gitignored)
    ├── center_01/
    ├── center_02/
    └── ...
```

---

## Generator Script Example

```python
# generators/base.py

from dataclasses import dataclass
from typing import List, Dict, Optional
import random
from datetime import datetime, timedelta

@dataclass
class CenterConfig:
    center_id: str
    name: str
    schema: str
    language: str
    quality: str  # clean, moderate, poor, messy
    patient_count: int
    date_range_start: datetime
    column_name_mapping: Dict[str, str]
    quality_issues: Dict[str, dict]

class DatabaseGenerator:
    """Generate realistic test database for a center."""

    def __init__(self, config: CenterConfig):
        self.config = config
        self.random = random.Random(hash(config.center_id))  # Reproducible

    def generate_sql(self) -> str:
        """Generate complete SQL script for the center."""
        sql_parts = [
            self._generate_schema(),
            self._generate_tables(),
            self._generate_patients(),
            self._generate_insurances(),
            self._generate_chart_entries(),
            self._inject_quality_issues(),
        ]
        return "\n\n".join(sql_parts)

    def _generate_schema(self) -> str:
        return f"CREATE SCHEMA [{self.config.schema}];"

    def _generate_tables(self) -> str:
        # Use column name mapping for this center
        patient_id_col = self.config.column_name_mapping.get('patient_id', 'PATNR')
        date_col = self.config.column_name_mapping.get('date', 'DATUM')
        # ... etc

    def _inject_quality_issues(self) -> str:
        """Inject configured quality issues into the data."""
        sql = []

        for column, issue in self.config.quality_issues.items():
            if issue['type'] == 'abandoned':
                sql.append(self._make_column_abandoned(column, issue['last_date']))
            elif issue['type'] == 'empty':
                sql.append(self._make_column_empty(column))
            elif issue['type'] == 'mostly_empty':
                sql.append(self._make_column_mostly_empty(column, issue['null_pct']))
            elif issue['type'] == 'misused':
                sql.append(self._inject_misused_values(column, issue['bad_values']))
            elif issue['type'] == 'test_data':
                sql.append(self._inject_test_data(column))

        return "\n".join(sql)
```

---

## Usage

### Start All Centers

```bash
# Start all 10 centers
docker-compose -f docker-compose.simulator.yml up -d

# Wait for all to be healthy
docker-compose -f docker-compose.simulator.yml ps

# Check specific center
docker-compose -f docker-compose.simulator.yml logs center_01_munich
```

### Start Subset for Development

```bash
# Start only baseline centers
docker-compose -f docker-compose.simulator.yml up -d center_01_munich center_02_berlin

# Start centers 1-5
docker-compose -f docker-compose.simulator.yml up -d \
  center_01_munich center_02_berlin center_03_hamburg \
  center_04_frankfurt center_05_cologne
```

### Regenerate Data

```bash
# Regenerate all centers
python -m generators.generate_all

# Regenerate specific center
python -m generators.generate_center --center 5

# Regenerate with different seed (different random data)
python -m generators.generate_all --seed 42
```

### Validate Results

```bash
# Run schema matching pipeline on center
python -m schema_matching.pipeline --center center_01_munich

# Compare results to ground truth
python -m validation.validate_ground_truth \
  --center center_01_munich \
  --results output/center_01_results.json \
  --ground-truth ground_truth/center_01_munich.yml

# Generate full report
python -m validation.generate_report --all-centers
```

---

## Expected Demo Flow

### Demo Script: Progressive Onboarding

1. **Center 1 (Munich):** Baseline onboarding
   - Show full pipeline execution
   - ~90% auto-match
   - Review queue walkthrough
   - Final approval

2. **Center 2 (Berlin):** Second client benefit
   - Show faster onboarding
   - Higher auto-match rate
   - "DELETED" column learned

3. **Center 3 (Hamburg):** Naming variations
   - Show LLM classification of new names
   - Cross-DB learning in action

4. **Center 5 (Cologne):** Data quality issues
   - Show abandoned column detection
   - Review queue for flagged columns

5. **Center 9 (Zurich):** Realistic complexity
   - Show system handling messy data
   - Value bank with Swiss insurances
   - Human-in-the-loop importance

### Demo Metrics to Show

| After Center | Learned Column Names | Value Bank Size | Avg Auto-Match |
|--------------|---------------------|-----------------|----------------|
| 1 | 15 | 50 | 90% |
| 2 | 20 | 80 | 92% |
| 3 | 35 | 100 | 88% |
| 5 | 40 | 120 | 85% |
| 9 | 55 | 180 | 82% |

---

## Validation Acceptance Criteria

```gherkin
Feature: Database Simulator Validation

  Scenario: Ground truth matches actual structure
    Given center "center_01_munich" is running
    When I query the schema structure
    Then it should match the ground truth manifest
    And all expected tables should exist
    And all expected columns should exist

  Scenario: Quality issues are correctly injected
    Given center "center_06_dusseldorf" is running
    When I query column "PATIENT.FAX"
    Then NULL percentage should be exactly 100%
    When I query column "PATIENT.MOBILE"
    Then NULL percentage should be exactly 97%

  Scenario: Threshold edge cases are precise
    Given center "center_08_leipzig" is running
    When I query column "NULL_94"
    Then NULL percentage should be exactly 94.0%
    When I query column "NULL_95"
    Then NULL percentage should be exactly 95.0%

  Scenario: Data is reproducible
    Given center "center_01_munich" is regenerated twice
    Then both generations should produce identical data
    And row counts should match
    And sample values should match
```

---

## References

- [ACCEPTANCE.md](ACCEPTANCE.md) - Feature acceptance criteria
- [03-value-banks.md](03-value-banks.md) - Value bank and quality detection
- [ARCHITECTURE.md](ARCHITECTURE.md) - Backend architecture

---

*Created: 2024-01-14*
*Status: Planning*
