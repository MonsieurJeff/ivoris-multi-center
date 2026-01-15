# Advanced Methodology (Multi-Database with LLM)

The 4-phase approach for mapping schemas across multiple databases with LLM semantic classification.

---

## The 4-Phase Approach

For organizations with multiple databases (e.g., dental centers with different software versions), a more sophisticated approach is needed.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MULTI-DATABASE SCHEMA MATCHING                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Phase 1              Phase 2              Phase 3              Phase 4  │
│  ┌──────────┐        ┌──────────┐        ┌──────────┐        ┌────────┐ │
│  │  SCHEMA  │        │   LLM    │        │  CROSS-  │        │ AUTO   │ │
│  │ PROFILER │───────▶│ SEMANTIC │───────▶│ DATABASE │───────▶│VALIDATE│ │
│  └──────────┘        └──────────┘        └──────────┘        └────────┘ │
│                                                                          │
│  Extract metadata    Classify with       Match against        Test with  │
│  + sample values     domain context      known mappings       real joins │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### When This Runs

**Important:** This pipeline runs only at **client initialization** (onboarding), not on every data extraction.

| Trigger | What Happens |
|---------|--------------|
| **New client onboarding** | Full 4-phase pipeline on entire schema |
| **Schema update detected** | Only new/changed tables and columns go through Phases 2-4 |
| **Daily extraction** | Uses stored, human-verified mappings (no LLM calls) |

### LLM Usage is Minimal

The LLM (Phase 2) is only invoked for columns that:
1. Are not in the canonical schema's `known_names`
2. Have not been previously classified and human-verified
3. Appear for the first time in a schema update

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         LLM INVOCATION LOGIC                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  New Column Found                                                        │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────────┐  YES   ┌─────────────┐                                 │
│  │ In canonical│───────▶│ Auto-match  │──▶ No LLM needed                │
│  │ known_names?│        │ (high conf) │                                 │
│  └─────────────┘        └─────────────┘                                 │
│       │ NO                                                               │
│       ▼                                                                  │
│  ┌─────────────┐  YES   ┌─────────────┐                                 │
│  │ Previously  │───────▶│ Use cached  │──▶ No LLM needed                │
│  │ classified? │        │ classification│                               │
│  └─────────────┘        └─────────────┘                                 │
│       │ NO                                                               │
│       ▼                                                                  │
│  ┌─────────────┐                                                        │
│  │ Call LLM    │──▶ Classify ──▶ Human Review ──▶ Store verified        │
│  │ (Phase 2)   │                                                        │
│  └─────────────┘                                                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Cost implication:** For a typical new client with 487 tables:
- First client: ~50-100 LLM calls (batched, unknown columns only)
- Subsequent clients: ~5-20 LLM calls (only truly new column names)
- Daily operations: 0 LLM calls (uses stored mappings)

---

## Phase 1: Schema Profiler (Automated)

### Goal
Extract rich metadata beyond `INFORMATION_SCHEMA` - including actual data patterns.

### Why Profiling Matters

The actual data is often more informative than column names:
- Seeing "DAK Gesundheit" tells you it's an insurance company
- A column with 847 distinct values in 12,503 rows suggests a foreign key
- `YYYYMMDD` pattern in VARCHAR reveals date storage

### Schema Profiler Query

```sql
-- Generate rich profile for each column
WITH ColumnStats AS (
    SELECT
        c.TABLE_SCHEMA,
        c.TABLE_NAME,
        c.COLUMN_NAME,
        c.DATA_TYPE,
        c.CHARACTER_MAXIMUM_LENGTH,
        c.IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS c
    WHERE c.TABLE_SCHEMA = 'ck'
)
SELECT
    cs.*,
    -- These would be computed per-column with dynamic SQL:
    -- COUNT(DISTINCT col) as distinct_count,
    -- COUNT(*) as total_count,
    -- NULL percentage
    -- Sample values (TOP 5 DISTINCT)
    -- Format detection patterns
FROM ColumnStats cs;
```

### Full Profiler (Dynamic SQL)

```sql
-- For each table/column, generate profile
DECLARE @sql NVARCHAR(MAX);
DECLARE @table_name NVARCHAR(128) = 'KARTEI';
DECLARE @column_name NVARCHAR(128) = 'PATNR';
DECLARE @schema_name NVARCHAR(128) = 'ck';

SET @sql = N'
SELECT
    ''' + @schema_name + ''' as table_schema,
    ''' + @table_name + ''' as table_name,
    ''' + @column_name + ''' as column_name,
    COUNT(*) as total_count,
    COUNT(DISTINCT ' + QUOTENAME(@column_name) + ') as distinct_count,
    SUM(CASE WHEN ' + QUOTENAME(@column_name) + ' IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as null_pct,
    (SELECT STRING_AGG(CAST(val as NVARCHAR(100)), '', '')
     FROM (SELECT DISTINCT TOP 5 ' + QUOTENAME(@column_name) + ' as val
           FROM ' + QUOTENAME(@schema_name) + '.' + QUOTENAME(@table_name) +
           ' WHERE ' + QUOTENAME(@column_name) + ' IS NOT NULL) t) as sample_values
FROM ' + QUOTENAME(@schema_name) + '.' + QUOTENAME(@table_name);

EXEC sp_executesql @sql;
```

### Profile Output Format

```json
{
  "schema": "ck",
  "table": "KARTEI",
  "column": "PATNR",
  "data_type": "int",
  "max_length": null,
  "nullable": "NO",
  "distinct_count": 847,
  "total_count": 12503,
  "null_pct": 0.0,
  "sample_values": ["1", "2", "3", "15", "28"],
  "detected_patterns": {
    "is_numeric": true,
    "is_unique": false,
    "cardinality": "moderate",
    "likely_fk": true
  }
}
```

### Pattern Detection Rules

```python
def detect_patterns(profile):
    """Detect data patterns from profile statistics"""
    patterns = {}

    # Cardinality classification
    ratio = profile['distinct_count'] / profile['total_count']
    if ratio > 0.95:
        patterns['cardinality'] = 'unique'  # Likely PK
    elif ratio > 0.1:
        patterns['cardinality'] = 'moderate'  # Likely FK
    else:
        patterns['cardinality'] = 'low'  # Likely categorical

    # Date pattern detection
    samples = profile['sample_values']
    if all(re.match(r'^\d{8}$', s) for s in samples):
        patterns['format'] = 'DATE_YYYYMMDD'
    elif all(re.match(r'^\d{4}-\d{2}-\d{2}', s) for s in samples):
        patterns['format'] = 'DATE_ISO'

    # FK detection heuristics
    if (profile['data_type'] in ['int', 'bigint'] and
        patterns['cardinality'] == 'moderate' and
        profile['column'].endswith(('ID', 'NR', 'KEY'))):
        patterns['likely_fk'] = True

    return patterns
```

---

## Phase 2: LLM Semantic Classification

### Goal
Use LLM to understand the *meaning* of columns, not just string similarity.

### Why LLM Works Here

| Challenge | LLM Advantage |
|-----------|---------------|
| German abbreviations | Understands `PATNR` = "Patient Nummer" |
| Domain terminology | Knows `BEMERKUNG` = "remark/note" in medical context |
| Value interpretation | Recognizes "DAK Gesundheit" as insurance company |
| Synonym detection | Maps `EINTRAG` and `BEMERKUNG` to same concept |

### Classification Prompt Template

```
You are a dental practice database analyst. Given this column profile
from a German dental software system, classify its business meaning.

## Column Profile
- Table: {table_name}
- Column: {column_name}
- Data Type: {data_type}
- Sample Values: {sample_values}
- Distinct Count: {distinct_count} of {total_count} rows
- Null Percentage: {null_pct}%
- Detected Patterns: {patterns}

## Classification Task
What business concept does this column represent?

Select ONE from:
- patient_id: Unique patient identifier
- patient_name: Patient's name
- date: Date field (appointment, treatment, etc.)
- insurance_type: Insurance classification (GKV/PKV)
- insurance_name: Insurance company name
- insurance_id: Insurance company identifier
- chart_note: Medical notes or remarks
- service_code: Treatment/procedure code
- diagnosis_code: Diagnosis or condition code
- practitioner_id: Doctor/staff identifier
- amount: Monetary amount
- soft_delete: Deletion flag
- audit_timestamp: Record modification tracking
- junction_key: Foreign key in junction table
- other: None of the above

## Response Format (JSON)
{
  "classification": "<selected_category>",
  "confidence": "high|medium|low",
  "reasoning": "<brief explanation>",
  "alternative": "<second_best_category_if_uncertain>"
}
```

### Example LLM Classifications

**Input: ck.KARTEI.PATNR**
```json
{
  "classification": "patient_id",
  "confidence": "high",
  "reasoning": "PATNR is German abbreviation for 'Patient Nummer'. Integer type with moderate cardinality (847 distinct in 12,503 rows) suggests foreign key to patient table. Column name pattern ends with 'NR' (number).",
  "alternative": null
}
```

**Input: ck.KARTEI.BEMERKUNG**
```json
{
  "classification": "chart_note",
  "confidence": "high",
  "reasoning": "BEMERKUNG means 'remark' or 'note' in German. VARCHAR(-1) indicates large text field. In KARTEI (chart/index card) table context, this is clearly medical notes.",
  "alternative": null
}
```

**Input: ck.KASSEN.ART**
```json
{
  "classification": "insurance_type",
  "confidence": "high",
  "reasoning": "ART means 'type' in German. In KASSEN (insurance) table. Sample values show 'P' and numeric codes 1-9, matching German insurance classification (P=Private/PKV, 1-9=various GKV types).",
  "alternative": null
}
```

**Input: ck.KARTEI.DELKZ**
```json
{
  "classification": "soft_delete",
  "confidence": "high",
  "reasoning": "DELKZ is abbreviation for 'Delete Kennzeichen' (delete flag). BIT type with values 0/1. Common pattern in German enterprise software for soft deletion.",
  "alternative": null
}
```

### LLM Integration Code

```python
import json
from typing import Optional
import anthropic  # or openai

class SchemaClassifier:
    def __init__(self, client, model="claude-3-haiku-20240307"):
        self.client = client
        self.model = model
        self.prompt_template = """..."""  # Template from above

    def classify_column(self, profile: dict) -> dict:
        """Classify a single column using LLM"""
        prompt = self.prompt_template.format(**profile)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON response
        result = json.loads(response.content[0].text)
        result['column'] = f"{profile['schema']}.{profile['table']}.{profile['column']}"
        return result

    def classify_batch(self, profiles: list, batch_size: int = 10) -> list:
        """Classify multiple columns efficiently"""
        results = []

        # Batch columns to reduce API calls
        for i in range(0, len(profiles), batch_size):
            batch = profiles[i:i+batch_size]
            batch_prompt = self._create_batch_prompt(batch)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": batch_prompt}]
            )

            batch_results = json.loads(response.content[0].text)
            results.extend(batch_results)

        return results

    def _create_batch_prompt(self, profiles: list) -> str:
        """Create prompt for batch classification"""
        columns_text = "\n\n".join([
            f"### Column {i+1}: {p['table']}.{p['column']}\n"
            f"Type: {p['data_type']}, Samples: {p['sample_values']}, "
            f"Distinct: {p['distinct_count']}/{p['total_count']}"
            for i, p in enumerate(profiles)
        ])

        return f"""Classify these {len(profiles)} columns from a German dental database.

{columns_text}

Return a JSON array with classification for each column."""
```

---

## Phase 3: Cross-Database Matching

### Goal
Learn from previous mappings to accelerate new database onboarding.

### Canonical Schema Definition

Build a "golden reference" of expected fields:

```yaml
# canonical-dental-schema.yml
version: "1.0"
domain: "dental_practice_management"

entities:
  patient_id:
    description: "Unique patient identifier"
    known_names:
      - PATNR
      - PATIENTID
      - PAT_ID
      - PATIENTNR
      - ID_PATIENT
      - PATIENT_NR
    expected_types: [int, bigint]
    cardinality: moderate
    nullable: false

  date:
    description: "Date of treatment or appointment"
    known_names:
      - DATUM
      - DATE
      - BEHANDLUNGSDATUM
      - TERMIN_DATUM
      - APPOINTMENT_DATE
    expected_types: [date, datetime, varchar]
    formats:
      - "YYYY-MM-DD"
      - "YYYYMMDD"
      - "DD.MM.YYYY"

  insurance_type:
    description: "Insurance classification (public/private)"
    known_names:
      - ART
      - TYP
      - KASSENART
      - INS_TYPE
      - VERSICHERUNGSART
      - INSURANCE_TYPE
    expected_types: [char, varchar, int]
    expected_values:
      private: ["P", "PKV", "PRIVATE", "2"]
      public: ["G", "GKV", "PUBLIC", "1", "1-9"]
      self_pay: ["S", "SELBST", "SELF", "0"]

  chart_note:
    description: "Medical notes or remarks"
    known_names:
      - BEMERKUNG
      - EINTRAG
      - NOTIZ
      - NOTE
      - COMMENT
      - REMARKS
      - ANMERKUNG
    expected_types: [varchar, text, nvarchar]
    cardinality: high

  service_code:
    description: "Treatment or procedure code"
    known_names:
      - LEISTUNG
      - SERVICE
      - PROCEDURE
      - BEHANDLUNG
      - CODE
      - ZIFFER
    expected_types: [varchar, char]

  soft_delete:
    description: "Deletion flag for soft deletes"
    known_names:
      - DELKZ
      - DELETED
      - DEL_FLAG
      - IS_DELETED
      - GELOESCHT
    expected_types: [bit, boolean, int, tinyint]
    expected_values: [0, 1, true, false]

relationships:
  patient_insurance:
    description: "Link between patient and insurance"
    patterns:
      - direct_fk: "PATIENT.KASSE_ID → KASSEN.ID"
      - junction_table: "PATKASSE(PATNR, KASSENID)"
```

### Cross-Database Matcher

```python
import yaml
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ColumnMapping:
    source_column: str
    canonical_entity: str
    confidence: float
    match_reasons: List[str]

class CrossDatabaseMatcher:
    def __init__(self, canonical_schema_path: str):
        with open(canonical_schema_path) as f:
            self.canonical = yaml.safe_load(f)
        self.learned_mappings = {}  # center_id -> mappings

    def match_column(self, profile: dict, llm_classification: dict) -> ColumnMapping:
        """Match a profiled column against canonical schema"""
        scores = {}

        for entity_name, entity_def in self.canonical['entities'].items():
            score, reasons = self._score_match(profile, llm_classification, entity_def)
            scores[entity_name] = (score, reasons)

        # Get best match
        best_entity = max(scores, key=lambda k: scores[k][0])
        best_score, reasons = scores[best_entity]

        return ColumnMapping(
            source_column=f"{profile['schema']}.{profile['table']}.{profile['column']}",
            canonical_entity=best_entity,
            confidence=best_score,
            match_reasons=reasons
        )

    def _score_match(self, profile: dict, llm_class: dict, entity: dict) -> tuple:
        """Score how well a column matches a canonical entity"""
        score = 0.0
        reasons = []

        # 1. LLM classification match (35%)
        if llm_class['classification'] == entity.get('maps_to', llm_class['classification']):
            llm_weight = {'high': 0.35, 'medium': 0.25, 'low': 0.15}
            score += llm_weight.get(llm_class['confidence'], 0.15)
            reasons.append(f"LLM classified as {llm_class['classification']}")

        # 2. Column name in known_names (25%)
        col_upper = profile['column'].upper()
        if col_upper in [n.upper() for n in entity.get('known_names', [])]:
            score += 0.25
            reasons.append(f"Column name matches known name")
        elif any(known.upper() in col_upper for known in entity.get('known_names', [])):
            score += 0.15
            reasons.append(f"Column name partially matches")

        # 3. Data type match (15%)
        if profile['data_type'] in entity.get('expected_types', []):
            score += 0.15
            reasons.append(f"Data type {profile['data_type']} matches expected")

        # 4. Value pattern match (15%)
        if 'expected_values' in entity:
            sample_match = self._check_value_patterns(
                profile['sample_values'],
                entity['expected_values']
            )
            if sample_match:
                score += 0.15
                reasons.append(f"Sample values match expected patterns")

        # 5. Cross-database consistency (10%)
        consistency_score = self._check_cross_db_consistency(
            profile['column'],
            entity.get('known_names', [])
        )
        score += consistency_score * 0.10
        if consistency_score > 0:
            reasons.append(f"Consistent with {int(consistency_score*100)}% of other centers")

        return score, reasons

    def _check_value_patterns(self, samples: list, expected: dict) -> bool:
        """Check if sample values match expected patterns"""
        all_expected = []
        if isinstance(expected, dict):
            for values in expected.values():
                all_expected.extend(values)
        else:
            all_expected = expected

        return any(str(s) in all_expected for s in samples)

    def _check_cross_db_consistency(self, column_name: str, known_names: list) -> float:
        """Check if this column name was mapped consistently in other databases"""
        if not self.learned_mappings:
            return 0.0

        matches = 0
        total = len(self.learned_mappings)

        for center_id, mappings in self.learned_mappings.items():
            for mapping in mappings:
                if (column_name.upper() in mapping.source_column.upper() and
                    any(kn.upper() in mapping.source_column.upper() for kn in known_names)):
                    matches += 1
                    break

        return matches / total if total > 0 else 0.0

    def learn_mapping(self, center_id: str, verified_mappings: List[ColumnMapping]):
        """Store verified mappings for future cross-database matching"""
        self.learned_mappings[center_id] = verified_mappings

        # Update canonical schema with new column names
        for mapping in verified_mappings:
            if mapping.confidence > 0.8:
                entity = self.canonical['entities'].get(mapping.canonical_entity)
                if entity:
                    col_name = mapping.source_column.split('.')[-1]
                    if col_name not in entity['known_names']:
                        entity['known_names'].append(col_name)
```

### Known Mappings Storage

```yaml
# mappings/center_munich.yml
center_id: "munich_001"
database: "DentalDB_Munich"
schema: "ck"
mapped_date: "2024-01-15"
verified_by: "data_team"

mappings:
  - source: "ck.KARTEI.PATNR"
    canonical: "patient_id"
    confidence: 0.95
    verified: true

  - source: "ck.KARTEI.DATUM"
    canonical: "date"
    confidence: 0.92
    format: "YYYYMMDD"
    verified: true

  - source: "ck.KASSEN.ART"
    canonical: "insurance_type"
    confidence: 0.88
    value_mapping:
      "P": "private"
      "1-9": "public"
    verified: true

discoveries:
  - "Uses PATKASSE as junction table for patient-insurance relationship"
  - "All tables have DELKZ soft delete flag"
  - "Dates stored as VARCHAR(8) in YYYYMMDD format"
```

---

**Next:** [Value Banks](03-value-banks.md) - Learn from verified values to reduce LLM calls.
