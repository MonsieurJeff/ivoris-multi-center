# Value Banks (Matching Clusters)

Learn from verified values to improve schema matching accuracy and reduce LLM calls.

---

## Concept

A **Value Bank** is a learned collection of actual data values associated with each canonical schema element. Instead of relying solely on column names, value banks enable matching based on the **actual data content**.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         VALUE BANK ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Canonical Element: insurance_name                                       │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ Column Name Variants    │ Value Bank (learned)                     │ │
│  │ ────────────────────    │ ──────────────────────                   │ │
│  │ • NAME                  │ • "DAK Gesundheit"                       │ │
│  │ • KASSENNAME            │ • "AOK Baden-Württemberg"                │ │
│  │ • INSURANCE_NAME        │ • "BARMER"                               │ │
│  │ • BEZEICHNUNG           │ • "Techniker Krankenkasse"               │ │
│  │                         │ • "AOK Bayern"                           │ │
│  │                         │ • "IKK classic"                          │ │
│  │                         │ • ... (grows with each client)           │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  Matching Logic:                                                         │
│  Unknown column "KASSENBEZEICHNUNG" with values ["DAK Gesundheit"...]   │
│  → Values match insurance_name bank → Auto-classify (no LLM needed)     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Why Value Banks Matter

| Benefit | Impact |
|---------|--------|
| **Reduce LLM calls** | Value match = skip LLM entirely |
| **Higher confidence** | Value match is stronger signal than name similarity |
| **Domain knowledge accumulation** | Each client makes the system smarter |
| **Handle unknown column names** | Even if name is new, values reveal intent |
| **Cross-client intelligence** | Client B benefits from Client A's verified data |

---

## Value Quality Control: Rejecting Marginal Values

Not all learned data should be included in the matching clusters. Marginal, erroneous, or outlier entries can pollute the bank and reduce matching accuracy.

### What Gets Quality-Controlled

Value Banks store **three types of learned data**, each requiring quality control:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    VALUE BANK COMPONENTS                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. COLUMN NAME VARIANTS                                                │
│     ─────────────────────                                               │
│     What: Alternative column names that map to canonical entities       │
│     Examples: PATNR, PATIENTID, PAT_NR → patient_id                    │
│     Quality concerns: Typos, test names, wrong entity mappings          │
│                                                                          │
│  2. DATA VALUES                                                         │
│     ───────────                                                         │
│     What: Actual data content found in columns                          │
│     Examples: "DAK Gesundheit", "AOK Bayern" → insurance_name           │
│     Quality concerns: Test data, data entry errors, obsolete values     │
│                                                                          │
│  3. VALUE PATTERNS (Regex)                                              │
│     ──────────────────────                                              │
│     What: Format patterns for structured data                           │
│     Examples: ^\d{8}$ → date (YYYYMMDD format)                         │
│     Quality concerns: Developer-defined, rarely needs rejection         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Quality Control by Component Type

| Component | What to Reject | Example | Impact if Not Rejected |
|-----------|---------------|---------|------------------------|
| **Column Name Variant** | Typos in column names | "PATNR_TYPO" | False matches on unrelated columns |
| **Column Name Variant** | Test column names | "TEST_COL", "XXX" | Pollutes known_names lookup |
| **Column Name Variant** | Wrong entity mapping | "BEMERKUNG" mapped to patient_id | Cross-entity contamination |
| **Data Value** | Data entry errors | "DAK Gesundheit " (trailing space) | False negatives on exact match |
| **Data Value** | Test/dummy data | "TEST", "XXXX", "asdf" | False positives on unrelated columns |
| **Data Value** | Legacy/obsolete values | Defunct insurance companies | Matches old data incorrectly |
| **Data Value** | Edge cases | One-time exception values | Overfits to rare patterns |
| **Data Value** | Wrong entity values | Patient name in insurance field | Matches wrong column types |

### Detailed Examples

**Column Name Variants - What to Accept vs Reject:**

```
Entity: patient_id

ACCEPT (verified):
├── PATNR          ← Standard Ivoris name
├── PATIENTID      ← Standard English
├── PAT_NR         ← Variant from Center 3
├── PATIENTNR      ← No underscore variant
└── ID_PATIENT     ← Reversed order

REJECT:
├── PATNR_OLD      ← Legacy/test column (reason: obsolete)
├── PATIENT_TEST   ← Test column (reason: test_data)
├── BEMERKUNG      ← Wrong entity - this is chart_note (reason: wrong_entity)
├── PATNRR         ← Typo (reason: data_entry_error)
└── XXX            ← Garbage (reason: test_data)
```

**Data Values - What to Accept vs Reject:**

```
Entity: insurance_name

ACCEPT (verified):
├── "DAK Gesundheit"
├── "AOK Baden-Württemberg"
├── "BARMER"
├── "Techniker Krankenkasse"
└── "IKK classic"

REJECT:
├── "DAK Gesundheit "     ← Trailing space (reason: data_entry_error)
├── "TEST"                ← Test data (reason: test_data)
├── "asdfasdf"            ← Garbage (reason: test_data)
├── "Max Mustermann"      ← This is a patient name! (reason: wrong_entity)
├── "AOK Altmark"         ← Defunct since 2010 (reason: obsolete)
└── "12345"               ← Numeric in name field (reason: wrong_entity)
```

**Data Values - Entity-Specific Expectations:**

| Entity | Expected Values | Suspicious Values |
|--------|-----------------|-------------------|
| `insurance_name` | German company names (3-50 chars) | Single chars, numbers only, >100 chars |
| `insurance_type` | P, 1-9, GKV, PKV (1-3 chars) | Long strings, special characters |
| `date` | YYYYMMDD, YYYY-MM-DD patterns | Random strings, partial dates |
| `soft_delete` | 0, 1, true, false, Y, N | Long strings, numbers > 1 |
| `chart_note` | German text (20+ chars typical) | Single words, numeric only |
| `patient_id` | Integers, formatted IDs | Names, long text |

### Value States

Each value in the bank has one of three states:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         VALUE LIFECYCLE STATES                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐                     │
│  │ PENDING  │──────▶│ VERIFIED │       │ REJECTED │                     │
│  │          │       │          │       │          │                     │
│  └──────────┘       └──────────┘       └──────────┘                     │
│       │                  │                   ▲                           │
│       │                  │                   │                           │
│       └──────────────────┴───────────────────┘                          │
│                                                                          │
│  PENDING:  New value, awaiting human review                             │
│  VERIFIED: Confirmed as valid for matching                              │
│  REJECTED: Excluded from matching (with reason)                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Rejection Reasons

```python
class RejectionReason:
    """Standard rejection reasons for value bank entries"""

    DATA_ENTRY_ERROR = "data_entry_error"      # Typo, formatting issue
    TEST_DATA = "test_data"                     # Test/dummy values
    OBSOLETE = "obsolete"                       # No longer valid
    EDGE_CASE = "edge_case"                     # Too rare to be useful
    WRONG_ENTITY = "wrong_entity"               # Belongs to different entity
    DUPLICATE = "duplicate"                     # Variant of existing value
    LOW_QUALITY = "low_quality"                 # Generic quality issue
    OTHER = "other"                             # Custom reason
```

### Automatic Detection of Marginal Values

```python
class ValueQualityAnalyzer:
    """Detect potentially marginal values for review"""

    def __init__(self, value_bank: ValueBank):
        self.bank = value_bank

    def flag_suspicious_values(self, entity: str) -> List[dict]:
        """Identify values that might need rejection"""
        suspicious = []

        values = self.bank.get_all_values(entity, include_pending=True)

        for v in values:
            reasons = []

            # 1. Low occurrence count (seen only once across all clients)
            if v['occurrence_count'] == 1 and v['source_clients'] == 1:
                reasons.append("single_occurrence")

            # 2. Suspicious patterns
            val = v['value']
            if self._looks_like_test_data(val):
                reasons.append("test_pattern")
            if self._has_formatting_issues(val):
                reasons.append("formatting_issue")
            if self._is_too_short(val, entity):
                reasons.append("too_short")
            if self._is_too_long(val, entity):
                reasons.append("too_long")

            # 3. Outlier in value distribution
            if self._is_statistical_outlier(val, entity):
                reasons.append("statistical_outlier")

            if reasons:
                suspicious.append({
                    'value': val,
                    'entity': entity,
                    'flags': reasons,
                    'occurrence_count': v['occurrence_count'],
                    'recommendation': self._get_recommendation(reasons)
                })

        return suspicious

    def _looks_like_test_data(self, value: str) -> bool:
        """Detect common test data patterns"""
        test_patterns = [
            r'^test', r'^xxx+', r'^asdf', r'^123$', r'^abc$',
            r'^\s*$', r'^n/?a$', r'^tbd$', r'^todo$'
        ]
        val_lower = value.lower().strip()
        return any(re.match(p, val_lower) for p in test_patterns)

    def _has_formatting_issues(self, value: str) -> bool:
        """Detect formatting problems"""
        return (
            value != value.strip() or           # Leading/trailing whitespace
            '  ' in value or                    # Double spaces
            value != ' '.join(value.split())    # Inconsistent spacing
        )

    def _is_too_short(self, value: str, entity: str) -> bool:
        """Check if value is suspiciously short for entity type"""
        min_lengths = {
            'insurance_name': 3,
            'chart_note': 10,
            'patient_name': 2,
        }
        return len(value.strip()) < min_lengths.get(entity, 1)

    def _is_too_long(self, value: str, entity: str) -> bool:
        """Check if value is suspiciously long for entity type"""
        max_lengths = {
            'insurance_type': 10,
            'soft_delete': 5,
        }
        return len(value) > max_lengths.get(entity, 1000)

    def _is_statistical_outlier(self, value: str, entity: str) -> bool:
        """Check if value is statistically unusual"""
        # Could use embedding distance from cluster centroid
        # or length/character distribution analysis
        return False  # Implement based on needs

    def _get_recommendation(self, flags: List[str]) -> str:
        """Suggest action based on flags"""
        if 'test_pattern' in flags:
            return "REJECT: Likely test data"
        if 'formatting_issue' in flags:
            return "REVIEW: May need cleanup before verification"
        if 'single_occurrence' in flags:
            return "REVIEW: Rare value, verify authenticity"
        return "REVIEW: Manual inspection recommended"
```

### Human Review Workflow for Rejections

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    VALUE REJECTION WORKFLOW                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  New Value Detected                                                      │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────────────┐                                                    │
│  │ Auto-Analysis   │  Run ValueQualityAnalyzer                          │
│  └─────────────────┘                                                    │
│       │                                                                  │
│       ├─── No flags ────▶ Add as PENDING for normal review              │
│       │                                                                  │
│       └─── Flagged ─────▶ Present to human with recommendation:         │
│                          "Value 'XXXX' flagged as test_pattern"         │
│                          [Verify] [Reject] [Skip]                       │
│                                   │                                      │
│                          ┌────────┴────────┐                            │
│                          │                 │                            │
│                          ▼                 ▼                            │
│                     VERIFIED          REJECTED                          │
│                   (add to bank)    (store with reason)                  │
│                                                                          │
│  Bulk Review Mode:                                                       │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ Show all flagged values for entity:                                │ │
│  │ □ "TEST" (test_pattern) - Reject                                   │ │
│  │ □ "DAK Gesundheit " (formatting) - Clean & Verify                  │ │
│  │ □ "XYZ Insurance" (single_occurrence) - Verify                     │ │
│  │ [Apply All] [Review Individually]                                  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Enhanced Canonical Schema with Value Banks

```yaml
# canonical-schema-with-value-banks.yml
version: "1.0"
domain: "dental_practice_management"

entities:
  insurance_name:
    description: "Insurance company name"
    column_variants:
      - NAME
      - KASSENNAME
      - INSURANCE_NAME
      - BEZEICHNUNG
      - KASSE_NAME
    value_bank:
      verified_values:
        - "DAK Gesundheit"
        - "AOK Baden-Württemberg"
        - "AOK Bayern"
        - "BARMER"
        - "Techniker Krankenkasse"
        - "IKK classic"
        - "BKK"
        # ... grows over time
      patterns:
        - regex: ".*Krankenkasse.*"
        - regex: ".*BKK.*"
        - regex: "^AOK.*"
      source_clients: ["munich_001", "berlin_002"]

  insurance_type:
    description: "Insurance classification (GKV/PKV)"
    column_variants:
      - ART
      - TYP
      - KASSENART
      - INSURANCE_TYPE
    value_bank:
      verified_values: ["P", "1", "2", "3", "4", "5", "6", "7", "8", "9", "GKV", "PKV"]
      value_mappings:
        "P": "private"
        "1": "public"
        "2": "public"
        "GKV": "public"
        "PKV": "private"

  date:
    description: "Date fields"
    column_variants:
      - DATUM
      - DATE
      - BEHANDLUNGSDATUM
    value_bank:
      patterns:
        - format: "YYYYMMDD"
          regex: "^\\d{8}$"
          example: "20220118"
        - format: "YYYY-MM-DD"
          regex: "^\\d{4}-\\d{2}-\\d{2}$"
        - format: "DD.MM.YYYY"
          regex: "^\\d{2}\\.\\d{2}\\.\\d{4}$"

  chart_note:
    description: "Medical notes or remarks"
    column_variants:
      - BEMERKUNG
      - EINTRAG
      - NOTIZ
      - NOTE
    value_bank:
      patterns:
        - min_length: 20  # Notes are typically longer text
        - contains_medical_terms: true
      characteristics:
        cardinality: "high"  # Many unique values
        avg_length: "> 50 chars"

  soft_delete:
    description: "Deletion flag"
    column_variants:
      - DELKZ
      - DELETED
      - DEL_FLAG
      - IS_DELETED
      - GELOESCHT
    value_bank:
      verified_values: [0, 1, true, false, "Y", "N"]
      expected_distribution:
        active_ratio: ">= 0.7"  # Most records should be active
```

---

## Value Bank Matching Logic

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MATCHING WITH VALUE BANKS                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Unknown Column: "KASSENBEZEICHNUNG"                                    │
│  Sample Values: ["DAK Gesundheit", "AOK Bayern", "BARMER"]              │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────────────┐                                                    │
│  │ 1. Name Match   │  "KASSENBEZEICHNUNG" not in column_variants       │
│  │    Score: 0.2   │  (partial: "KASSEN" matches insurance domain)     │
│  └─────────────────┘                                                    │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────────────┐                                                    │
│  │ 2. Value Bank   │  3/3 values found in insurance_name.value_bank!   │
│  │    Score: 0.95  │  HIGH CONFIDENCE MATCH                            │
│  └─────────────────┘                                                    │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────────────┐                                                    │
│  │ 3. Combined     │  Value bank match is decisive                     │
│  │    Score: 0.85  │  → Auto-classify as insurance_name                │
│  └─────────────────┘                                                    │
│       │                                                                  │
│       ▼                                                                  │
│  NO LLM NEEDED - Value bank provided sufficient confidence              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Value Bank Implementation

```python
import re
from typing import Set, List, Dict, Optional
from dataclasses import dataclass

@dataclass
class ValueBankMatch:
    entity: str
    match_score: float
    matched_values: List[str]
    matched_patterns: List[str]

class ValueBank:
    """Manages learned value clusters for canonical elements"""

    def __init__(self, db_connection):
        self.db = db_connection
        self._cache = {}  # entity -> {values, patterns}

    def match_values(self, sample_values: list, entity: str) -> float:
        """Check how many sample values match the entity's value bank"""
        bank = self.get_value_bank(entity)

        if not bank['verified_values'] and not bank['patterns']:
            return 0.0

        matches = 0
        for value in sample_values:
            # Check exact match in verified values
            if str(value) in bank['verified_values']:
                matches += 1
                continue

            # Check pattern match
            for pattern in bank.get('patterns', []):
                if re.match(pattern['regex'], str(value)):
                    matches += 1
                    break

        return matches / len(sample_values) if sample_values else 0.0

    def find_best_match(self, sample_values: list) -> Optional[ValueBankMatch]:
        """Find the best matching entity for given sample values"""
        best_match = None
        best_score = 0.0

        for entity in self.get_all_entities():
            score = self.match_values(sample_values, entity)
            if score > best_score:
                best_score = score
                best_match = ValueBankMatch(
                    entity=entity,
                    match_score=score,
                    matched_values=[v for v in sample_values
                                   if str(v) in self.get_value_bank(entity)['verified_values']],
                    matched_patterns=[]
                )

        return best_match if best_score >= 0.5 else None

    def learn_values(self, entity: str, values: list, client_id: str,
                    verified_by: str = None, quality_analyzer: 'ValueQualityAnalyzer' = None):
        """Add newly discovered values to the bank

        Values start as 'pending' unless verified_by is provided.
        Quality flags are automatically detected if analyzer is provided.
        """
        for value in values:
            if value is None or str(value).strip() == '':
                continue

            str_value = str(value)

            # Detect quality issues if analyzer available
            quality_flags = None
            if quality_analyzer:
                flags = quality_analyzer._get_flags_for_value(str_value, entity)
                if flags:
                    quality_flags = json.dumps(flags)

            # Determine initial status
            if verified_by:
                status = 'verified'
            else:
                status = 'pending'

            self.db.execute("""
                INSERT INTO value_bank
                (entity, value, source_client, status, verified_by, quality_flags)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (entity, value) DO UPDATE
                SET occurrence_count = occurrence_count + 1,
                    last_seen_at = GETDATE()
            """, [entity, str_value, client_id, status, verified_by, quality_flags])

        # Invalidate cache
        self._cache.pop(entity, None)

    def get_value_bank(self, entity: str) -> dict:
        """Retrieve value bank for an entity (with caching)
        Only returns VERIFIED values - rejected values are excluded
        """
        if entity in self._cache:
            return self._cache[entity]

        # Only select verified values (exclude pending and rejected)
        values = self.db.execute("""
            SELECT value FROM value_bank
            WHERE entity = ? AND status = 'verified'
        """, [entity]).fetchall()

        patterns = self.db.execute("""
            SELECT regex, format, description FROM value_patterns
            WHERE entity = ? AND is_active = 1
        """, [entity]).fetchall()

        bank = {
            'verified_values': set(v['value'] for v in values),
            'patterns': [{'regex': p['regex'], 'format': p['format']} for p in patterns]
        }

        self._cache[entity] = bank
        return bank

    def reject_value(self, entity: str, value: str, reason: str,
                    rejected_by: str, note: str = None):
        """Reject a value from the bank (exclude from matching)"""
        self.db.execute("""
            UPDATE value_bank
            SET status = 'rejected',
                rejected_by = ?,
                rejected_at = GETDATE(),
                rejection_reason = ?,
                rejection_note = ?
            WHERE entity = ? AND value = ?
        """, [rejected_by, reason, note, entity, value])

        # Log the rejection for audit
        self.db.execute("""
            INSERT INTO value_rejection_log
            (entity, value, rejection_reason, rejection_note, rejected_by, source_client)
            SELECT ?, ?, ?, ?, ?,
                   (SELECT source_client FROM value_bank WHERE entity = ? AND value = ?)
        """, [entity, value, reason, note, rejected_by, entity, value])

        # Invalidate cache
        self._cache.pop(entity, None)

    def verify_value(self, entity: str, value: str, verified_by: str):
        """Verify a pending value (add to matching bank)"""
        self.db.execute("""
            UPDATE value_bank
            SET status = 'verified',
                verified_by = ?,
                verified_at = GETDATE()
            WHERE entity = ? AND value = ?
        """, [verified_by, entity, value])

        # Invalidate cache
        self._cache.pop(entity, None)

    def get_pending_values(self, entity: str = None) -> List[dict]:
        """Get all pending values awaiting review"""
        query = """
            SELECT entity, value, source_client, occurrence_count,
                   quality_flags, created_at
            FROM value_bank
            WHERE status = 'pending'
        """
        params = []
        if entity:
            query += " AND entity = ?"
            params.append(entity)

        return self.db.execute(query, params).fetchall()

    def get_rejected_values(self, entity: str = None) -> List[dict]:
        """Get all rejected values (for audit/review)"""
        query = """
            SELECT entity, value, rejection_reason, rejection_note,
                   rejected_by, rejected_at, source_client
            FROM value_bank
            WHERE status = 'rejected'
        """
        params = []
        if entity:
            query += " AND entity = ?"
            params.append(entity)

        return self.db.execute(query, params).fetchall()

    def get_all_entities(self) -> List[str]:
        """Get list of all canonical entities with value banks"""
        result = self.db.execute("""
            SELECT DISTINCT entity FROM value_bank
            UNION
            SELECT DISTINCT entity FROM value_patterns
        """).fetchall()
        return [r['entity'] for r in result]

    def get_statistics(self, entity: str) -> dict:
        """Get statistics about a value bank (including rejection stats)"""
        stats = self.db.execute("""
            SELECT
                COUNT(*) as total_values,
                SUM(CASE WHEN status = 'verified' THEN 1 ELSE 0 END) as verified_values,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_values,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected_values,
                COUNT(DISTINCT source_client) as source_clients,
                MAX(last_seen_at) as last_updated
            FROM value_bank
            WHERE entity = ?
        """, [entity]).fetchone()
        return dict(stats)

    def get_rejection_rate(self, entity: str) -> float:
        """Calculate rejection rate for an entity"""
        stats = self.get_statistics(entity)
        total = stats['verified_values'] + stats['rejected_values']
        if total == 0:
            return 0.0
        return stats['rejected_values'] / total
```

---

## Database Schema for Value Banks (Clinero)

```sql
-- Value bank storage (with rejection support)
CREATE TABLE value_bank (
    id INT IDENTITY PRIMARY KEY,
    entity VARCHAR(100) NOT NULL,          -- canonical element name
    value NVARCHAR(500) NOT NULL,          -- actual value seen
    source_client VARCHAR(100),            -- which client it came from
    occurrence_count INT DEFAULT 1,        -- how many times seen across clients

    -- Status: 'pending', 'verified', 'rejected'
    status VARCHAR(20) DEFAULT 'pending',

    -- Verification fields
    verified_by VARCHAR(100),              -- who verified it
    verified_at DATETIME,

    -- Rejection fields
    rejected_by VARCHAR(100),              -- who rejected it
    rejected_at DATETIME,
    rejection_reason VARCHAR(50),          -- e.g., 'test_data', 'data_entry_error'
    rejection_note VARCHAR(500),           -- optional human explanation

    -- Auto-detection flags (JSON array of detected issues)
    quality_flags VARCHAR(500),            -- e.g., '["test_pattern", "single_occurrence"]'

    last_seen_at DATETIME DEFAULT GETDATE(),
    created_at DATETIME DEFAULT GETDATE(),
    UNIQUE(entity, value)
);

-- Pattern definitions (regex-based matching)
CREATE TABLE value_patterns (
    id INT IDENTITY PRIMARY KEY,
    entity VARCHAR(100) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,     -- 'regex', 'length', 'cardinality'
    regex VARCHAR(500),                    -- regex pattern if applicable
    format VARCHAR(100),                   -- human-readable format name
    min_value INT,                         -- for numeric/length patterns
    max_value INT,
    description VARCHAR(500),
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE()
);

-- Column name variants (linked to value banks)
CREATE TABLE column_variants (
    id INT IDENTITY PRIMARY KEY,
    entity VARCHAR(100) NOT NULL,
    variant VARCHAR(200) NOT NULL,
    source_client VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'verified', 'rejected'
    verified_by VARCHAR(100),
    rejected_by VARCHAR(100),
    rejection_reason VARCHAR(50),
    created_at DATETIME DEFAULT GETDATE(),
    UNIQUE(entity, variant)
);

-- Track which clients contributed to each entity's bank
CREATE TABLE value_bank_sources (
    id INT IDENTITY PRIMARY KEY,
    entity VARCHAR(100) NOT NULL,
    client_id VARCHAR(100) NOT NULL,
    values_contributed INT DEFAULT 0,
    values_rejected INT DEFAULT 0,         -- track rejection rate per client
    last_contribution DATETIME,
    UNIQUE(entity, client_id)
);

-- Rejection audit log (track all rejections for analysis)
CREATE TABLE value_rejection_log (
    id INT IDENTITY PRIMARY KEY,
    entity VARCHAR(100) NOT NULL,
    value NVARCHAR(500) NOT NULL,
    rejection_reason VARCHAR(50) NOT NULL,
    rejection_note VARCHAR(500),
    rejected_by VARCHAR(100) NOT NULL,
    rejected_at DATETIME DEFAULT GETDATE(),
    source_client VARCHAR(100)
);

-- Indexes for fast lookup
CREATE INDEX idx_value_bank_entity ON value_bank(entity);
CREATE INDEX idx_value_bank_value ON value_bank(value);
CREATE INDEX idx_value_bank_status ON value_bank(entity, status);
CREATE INDEX idx_value_bank_verified ON value_bank(entity, status) WHERE status = 'verified';
CREATE INDEX idx_column_variants_variant ON column_variants(variant);
CREATE INDEX idx_value_patterns_entity ON value_patterns(entity);
CREATE INDEX idx_rejection_log_entity ON value_rejection_log(entity);
```

---

## Value Bank Growth Strategy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    VALUE BANK GROWTH OVER TIME                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  CLIENT 1 (Seed - Manual Effort)                                        │
│  ├─ Full LLM classification + human verification                        │
│  ├─ Human verifies ~100 unique values                                   │
│  ├─ Value bank initialized: 100 entries                                 │
│  └─ Time: 4 hours                                                       │
│                                                                          │
│  CLIENTS 2-5 (Rapid Improvement)                                        │
│  ├─ 80% auto-matched via value bank (no LLM)                           │
│  ├─ 15% auto-matched via column name variants                          │
│  ├─ 5% requires LLM + human review                                     │
│  ├─ ~50 new values added per client                                    │
│  ├─ Value bank grows to: 300 entries                                   │
│  └─ Time per client: 30 minutes                                        │
│                                                                          │
│  CLIENTS 6-20 (Near-Automatic)                                          │
│  ├─ 95% auto-matched via value bank                                    │
│  ├─ 4% auto-matched via column names                                   │
│  ├─ 1% requires LLM (truly novel values only)                         │
│  ├─ ~10 new values added per client                                    │
│  ├─ Value bank grows to: 500+ entries                                  │
│  └─ Time per client: 10 minutes                                        │
│                                                                          │
│  STEADY STATE (20+ Clients)                                             │
│  ├─ Value bank covers 99%+ of German dental domain                     │
│  ├─ New clients: near-instant matching                                 │
│  ├─ LLM: only for edge cases or new software versions                 │
│  └─ Time per client: 5 minutes (mostly validation)                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Integration with Matching Pipeline

```python
class EnhancedSchemaMatcher:
    """Schema matcher with value bank integration"""

    def __init__(self, canonical_schema, value_bank: ValueBank, llm_classifier):
        self.canonical = canonical_schema
        self.value_bank = value_bank
        self.llm = llm_classifier

    def match_column(self, profile: dict) -> ColumnMapping:
        """Match a column using all available signals"""

        # 1. Check column name variants (fastest)
        name_match = self._match_by_name(profile['column'])
        if name_match and name_match.confidence >= 0.9:
            return name_match

        # 2. Check value bank (high confidence, no LLM needed)
        value_match = self.value_bank.find_best_match(profile['sample_values'])
        if value_match and value_match.match_score >= 0.8:
            return ColumnMapping(
                source_column=f"{profile['table']}.{profile['column']}",
                canonical_entity=value_match.entity,
                confidence=value_match.match_score,
                match_reasons=[
                    f"Value bank match: {len(value_match.matched_values)} values matched",
                    f"Matched values: {value_match.matched_values[:3]}..."
                ],
                llm_used=False
            )

        # 3. Combine name + value signals
        combined_score = self._calculate_combined_score(name_match, value_match, profile)
        if combined_score >= 0.75:
            return ColumnMapping(
                source_column=f"{profile['table']}.{profile['column']}",
                canonical_entity=name_match.entity if name_match else value_match.entity,
                confidence=combined_score,
                match_reasons=["Combined name + value match"],
                llm_used=False
            )

        # 4. Fall back to LLM only if other methods inconclusive
        llm_result = self.llm.classify_column(profile)
        return ColumnMapping(
            source_column=f"{profile['table']}.{profile['column']}",
            canonical_entity=llm_result['classification'],
            confidence=self._llm_confidence_to_score(llm_result['confidence']),
            match_reasons=[f"LLM classification: {llm_result['reasoning']}"],
            llm_used=True
        )

    def _calculate_combined_score(self, name_match, value_match, profile) -> float:
        """Combine multiple signals into final confidence score"""
        score = 0.0

        # Value bank match (40% weight - highest signal)
        if value_match:
            score += value_match.match_score * 0.40

        # Column name match (25% weight)
        if name_match:
            score += name_match.confidence * 0.25

        # Data type match (20% weight)
        type_score = self._score_type_match(profile)
        score += type_score * 0.20

        # Cross-database consistency (15% weight)
        consistency = self._check_cross_db(profile['column'])
        score += consistency * 0.15

        return score
```

---

## Column Quality Detection: Empty & Abandoned Columns

Beyond value-level quality control, entire columns may need to be excluded from schema matching.

### Problem Statement

Some columns in source databases should be ignored entirely:

| Column State | Description | Example |
|--------------|-------------|---------|
| **Empty** | 100% NULL or empty string values | Column created but never populated |
| **Mostly Empty** | >95% NULL, sparse data | Optional field rarely used |
| **Abandoned** | Has old data, no recent updates | Developer stopped using column |
| **Misused** | Values don't match column's intended type | Date column used for notes |
| **Test-Only** | Contains only test/dummy data | Development artifacts |

### Acceptance Criteria

```gherkin
Feature: Column Quality Detection
  As a schema matching system
  I need to detect and label empty, abandoned, or misused columns
  So that they are excluded from matching and don't pollute the value banks

  # ─────────────────────────────────────────────────────────────────────
  # EMPTY COLUMN DETECTION
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Detect fully empty column
    Given a column "NOTES_OLD" in table "KARTEI"
    And the column has 10,000 rows
    And 100% of values are NULL or empty string
    When the column quality analyzer runs
    Then the column should be labeled as "empty"
    And the column should be excluded from schema matching
    And a quality flag "column_empty" should be recorded

  Scenario: Detect mostly empty column
    Given a column "FAX_NUMBER" in table "PATIENT"
    And the column has 10,000 rows
    And 97% of values are NULL or empty string
    When the column quality analyzer runs
    Then the column should be labeled as "mostly_empty"
    And the column should be flagged for review
    And the null_percentage (97%) should be recorded

  Scenario: Distinguish sparse but valid column
    Given a column "EMERGENCY_CONTACT" in table "PATIENT"
    And the column has 10,000 rows
    And 80% of values are NULL (within acceptable range)
    And the non-null values contain valid contact information
    When the column quality analyzer runs
    Then the column should NOT be labeled as "mostly_empty"
    And the column should proceed to normal schema matching

  # ─────────────────────────────────────────────────────────────────────
  # ABANDONED COLUMN DETECTION
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Detect abandoned column by date pattern
    Given a column "OLD_STATUS" in table "KARTEI"
    And the column has non-null values
    And all non-null values were last modified before 2020-01-01
    And the table has records modified after 2020-01-01
    When the column quality analyzer runs
    Then the column should be labeled as "abandoned"
    And the last_activity_date should be recorded
    And a quality flag "column_abandoned" should be recorded

  Scenario: Detect abandoned column by value staleness
    Given a column "LEGACY_CODE" in table "LEISTUNG"
    And the column has 500 distinct values
    And all 500 values appear only in records older than 3 years
    And newer records have NULL for this column
    When the column quality analyzer runs
    Then the column should be labeled as "abandoned"
    And the column should be excluded from schema matching

  Scenario: Distinguish active column with old data
    Given a column "INSURANCE_TYPE" in table "KASSEN"
    And the column has values spanning from 2015 to present
    And the column has recent values (within last 6 months)
    When the column quality analyzer runs
    Then the column should NOT be labeled as "abandoned"
    And the column should proceed to normal schema matching

  # ─────────────────────────────────────────────────────────────────────
  # MISUSED COLUMN DETECTION
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Detect column with mismatched data type
    Given a column "DATUM" with data type VARCHAR(8)
    And the column name suggests it should contain dates
    And 60% of values are valid YYYYMMDD dates
    And 40% of values are free-text notes like "cancelled", "see remarks"
    When the column quality analyzer runs
    Then the column should be labeled as "misused"
    And the type_mismatch_percentage (40%) should be recorded
    And a quality flag "column_misused" should be recorded

  Scenario: Detect numeric column used for text
    Given a column "PATIENT_ID" with data type INT
    And the column contains values like 999999, 000000, -1
    And these values appear to be placeholder/sentinel values
    And they represent more than 20% of the data
    When the column quality analyzer runs
    Then the column should be flagged for review
    And the sentinel_value_percentage should be recorded

  Scenario: Detect column with inconsistent value patterns
    Given a column "PHONE" in table "PATIENT"
    And 70% of values match phone number patterns
    And 30% of values contain notes like "call after 5pm", "no phone"
    When the column quality analyzer runs
    Then the column should be labeled as "inconsistent_usage"
    And the pattern_mismatch_percentage (30%) should be recorded

  # ─────────────────────────────────────────────────────────────────────
  # TEST DATA COLUMN DETECTION
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Detect column containing only test data
    Given a column "DEBUG_FLAG" in table "KARTEI"
    And all values match test data patterns ("TEST", "XXX", "DUMMY", "12345")
    When the column quality analyzer runs
    Then the column should be labeled as "test_only"
    And the column should be excluded from schema matching
    And a quality flag "column_test_only" should be recorded

  Scenario: Detect column with high test data ratio
    Given a column "COMMENT" in table "PATIENT"
    And 45% of non-null values match test data patterns
    When the column quality analyzer runs
    Then the column should be flagged for review
    And the test_data_percentage (45%) should be recorded

  # ─────────────────────────────────────────────────────────────────────
  # LABELING AND EXCLUSION
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Store column quality label
    Given a column "OLD_NOTES" has been analyzed
    And the column was labeled as "abandoned"
    When the label is stored
    Then the column_quality table should have a record with:
      | column_name | OLD_NOTES |
      | table_name  | KARTEI    |
      | status      | excluded  |
      | label       | abandoned |
      | reason      | No updates since 2019-03-15 |
    And the column should be excluded from all future matching runs

  Scenario: Exclude labeled columns from value bank learning
    Given a column "LEGACY_STATUS" is labeled as "abandoned"
    When new values are discovered in this column
    Then the values should NOT be added to the value bank
    And a log entry should record "Skipped: column excluded"

  Scenario: Exclude labeled columns from LLM classification
    Given a column "EMPTY_FIELD" is labeled as "empty"
    When the LLM classification phase runs
    Then this column should be skipped
    And no LLM API call should be made for this column

  # ─────────────────────────────────────────────────────────────────────
  # HUMAN REVIEW AND OVERRIDE
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Human reviews flagged column
    Given a column "SPECIAL_CODE" has been flagged as "mostly_empty"
    When a human reviewer examines the column
    Then they should see:
      | metric           | value |
      | null_percentage  | 96%   |
      | non_null_samples | "A1", "B2", "C3" |
      | distinct_values  | 15    |
    And they can choose to [Include] or [Exclude] the column

  Scenario: Human overrides automatic exclusion
    Given a column "RARE_FLAG" was automatically labeled as "mostly_empty"
    And a human determines the column is valid but rarely used
    When the human selects [Include] with reason "Valid sparse field"
    Then the column status should change to "verified"
    And the override should be logged with the human's justification
    And the column should proceed to normal schema matching

  Scenario: Human confirms automatic exclusion
    Given a column "DEFUNCT_CODE" was automatically labeled as "abandoned"
    And a human confirms the column is no longer in use
    When the human selects [Exclude] with reason "Confirmed legacy"
    Then the column status should remain "excluded"
    And the human confirmation should be recorded

  Scenario: Bulk review of flagged columns
    Given 15 columns have been flagged for review
    When a human opens the bulk review interface
    Then they should see a list sorted by confidence (lowest first)
    And each row should show: table, column, label, key metrics
    And they can select multiple columns for batch [Include] or [Exclude]

  # ─────────────────────────────────────────────────────────────────────
  # THRESHOLDS AND CONFIGURATION
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Configurable thresholds
    Given the following quality thresholds are configured:
      | threshold                | value |
      | empty_column_threshold   | 100%  |
      | mostly_empty_threshold   | 95%   |
      | abandoned_months         | 24    |
      | test_data_threshold      | 80%   |
      | type_mismatch_threshold  | 30%   |
    When a column has 96% null values
    Then it should be labeled as "mostly_empty" (above 95% threshold)
    And not as "empty" (below 100% threshold)

  Scenario: Per-entity threshold override
    Given the entity "chart_note" has custom threshold:
      | mostly_empty_threshold | 99% |
    Because chart notes are expected to be sparse
    When a chart_note column has 97% null values
    Then it should NOT be flagged as "mostly_empty"
    Because 97% < 99% custom threshold for this entity

  # ─────────────────────────────────────────────────────────────────────
  # REPORTING AND AUDIT
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Generate column quality report
    Given schema analysis has completed for client "munich_001"
    When the column quality report is generated
    Then it should include:
      | section              | content |
      | total_columns        | 2,450   |
      | excluded_columns     | 127     |
      | flagged_for_review   | 34      |
      | breakdown_by_label   | empty: 45, abandoned: 52, misused: 30 |
    And the report should list each excluded column with reason

  Scenario: Track exclusion rate across clients
    Given column quality analysis has run for 10 clients
    When the cross-client report is generated
    Then it should show:
      | metric                    | value |
      | avg_exclusion_rate        | 5.2%  |
      | clients_above_10%         | 2     |
      | most_common_exclusion     | abandoned (48%) |
    And clients with high exclusion rates should be flagged for review
```

### Column Quality Labels

| Label | Criteria | Auto-Action | Human Review |
|-------|----------|-------------|--------------|
| `empty` | 100% NULL/empty | Exclude | No |
| `mostly_empty` | >95% NULL/empty | Flag | Yes |
| `abandoned` | No updates in 24+ months | Exclude | Optional |
| `misused` | >30% values don't match type | Flag | Yes |
| `test_only` | >80% test data patterns | Exclude | Optional |
| `inconsistent_usage` | Mixed valid/invalid patterns | Flag | Yes |

### Column Quality Database Schema

```sql
-- Column-level quality tracking
CREATE TABLE column_quality (
    id INT IDENTITY PRIMARY KEY,
    client_id VARCHAR(100) NOT NULL,
    schema_name VARCHAR(100) NOT NULL,
    table_name VARCHAR(200) NOT NULL,
    column_name VARCHAR(200) NOT NULL,

    -- Quality assessment
    status VARCHAR(20) NOT NULL,           -- 'active', 'excluded', 'flagged', 'verified'
    label VARCHAR(50),                      -- 'empty', 'abandoned', 'misused', etc.

    -- Metrics
    null_percentage DECIMAL(5,2),
    distinct_count INT,
    total_count INT,
    last_value_date DATETIME,              -- Most recent non-null value date
    test_data_percentage DECIMAL(5,2),
    type_mismatch_percentage DECIMAL(5,2),

    -- Quality flags (JSON array)
    quality_flags VARCHAR(500),

    -- Human review
    reviewed_by VARCHAR(100),
    reviewed_at DATETIME,
    review_decision VARCHAR(20),           -- 'include', 'exclude'
    review_reason VARCHAR(500),

    -- Audit
    analyzed_at DATETIME DEFAULT GETDATE(),
    created_at DATETIME DEFAULT GETDATE(),

    UNIQUE(client_id, schema_name, table_name, column_name)
);

-- Index for finding columns needing review
CREATE INDEX idx_column_quality_status ON column_quality(status);
CREATE INDEX idx_column_quality_client ON column_quality(client_id, status);
```

---

**Next:** [Validation](04-validation.md) - Test mappings with real queries and confidence scoring.
