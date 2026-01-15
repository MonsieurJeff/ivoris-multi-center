# Coding Exercises: Interview Preparation

**Purpose:** Practice problems for schema matching / scalability interviews
**Level:** Senior Engineer / Tech Lead

---

## Table of Contents

1. [String Similarity Algorithms](#1-string-similarity-algorithms)
2. [Data Structure Design](#2-data-structure-design)
3. [SQL Schema Discovery](#3-sql-schema-discovery)
4. [System Design](#4-system-design)
5. [Code Review Exercises](#5-code-review-exercises)
6. [Whiteboard Diagrams](#6-whiteboard-diagrams)

---

## 1. String Similarity Algorithms

### Exercise 1.1: Levenshtein Distance (Edit Distance)

**Problem:** Implement a function that calculates the minimum number of single-character edits (insert, delete, replace) to transform one string into another.

**Why they ask:** Core algorithm for fuzzy matching. Shows dynamic programming skills.

```python
# TODO: Implement this
def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate edit distance between two strings.

    Examples:
        levenshtein_distance("PATNR", "PATIENTNR") -> 4
        levenshtein_distance("PATNR", "PATNR") -> 0
        levenshtein_distance("kitten", "sitting") -> 3
    """
    pass
```

<details>
<summary>Solution (click to expand)</summary>

```python
def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate edit distance between two strings.
    Time: O(m*n), Space: O(min(m,n))
    """
    # Ensure s1 is the shorter string for space optimization
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    m, n = len(s1), len(s2)

    # Only need two rows at a time
    prev = list(range(m + 1))
    curr = [0] * (m + 1)

    for j in range(1, n + 1):
        curr[0] = j
        for i in range(1, m + 1):
            if s1[i-1] == s2[j-1]:
                curr[i] = prev[i-1]  # No edit needed
            else:
                curr[i] = 1 + min(
                    prev[i],      # Delete
                    curr[i-1],    # Insert
                    prev[i-1]     # Replace
                )
        prev, curr = curr, prev

    return prev[m]

def levenshtein_similarity(s1: str, s2: str) -> float:
    """Convert distance to similarity score (0-1)."""
    if not s1 and not s2:
        return 1.0
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return 1 - (distance / max_len)
```

**Key points to mention in interview:**
- Time complexity: O(m*n)
- Space optimization: O(min(m,n)) using two rows
- Similarity = 1 - (distance / max_length)

</details>

---

### Exercise 1.2: Jaro-Winkler Similarity

**Problem:** Implement Jaro-Winkler similarity, which gives higher scores to strings that match from the beginning.

**Why they ask:** Better for names/identifiers where prefixes matter (PATIENT vs PAT).

```python
# TODO: Implement this
def jaro_winkler(s1: str, s2: str, prefix_weight: float = 0.1) -> float:
    """
    Calculate Jaro-Winkler similarity (0-1).

    Examples:
        jaro_winkler("PATNR", "PATIENTNR") -> ~0.82
        jaro_winkler("DIXON", "DICKSONX") -> ~0.81
    """
    pass
```

<details>
<summary>Solution (click to expand)</summary>

```python
def jaro_similarity(s1: str, s2: str) -> float:
    """Calculate base Jaro similarity."""
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    len1, len2 = len(s1), len(s2)

    # Match window
    match_distance = max(len1, len2) // 2 - 1
    match_distance = max(0, match_distance)

    s1_matches = [False] * len1
    s2_matches = [False] * len2

    matches = 0
    transpositions = 0

    # Find matches
    for i in range(len1):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, len2)

        for j in range(start, end):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    # Count transpositions
    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    jaro = (
        matches / len1 +
        matches / len2 +
        (matches - transpositions / 2) / matches
    ) / 3

    return jaro

def jaro_winkler(s1: str, s2: str, prefix_weight: float = 0.1) -> float:
    """
    Calculate Jaro-Winkler similarity.
    Boosts score for common prefixes (up to 4 chars).
    """
    jaro = jaro_similarity(s1, s2)

    # Find common prefix (max 4 characters)
    prefix_len = 0
    for i in range(min(len(s1), len(s2), 4)):
        if s1[i] == s2[i]:
            prefix_len += 1
        else:
            break

    return jaro + prefix_len * prefix_weight * (1 - jaro)
```

**Key points to mention:**
- Jaro: Based on matching characters and transpositions
- Winkler: Adds prefix bonus (up to 4 chars, weight typically 0.1)
- Better for names where prefix matters

</details>

---

### Exercise 1.3: Token-Based Similarity (Jaccard)

**Problem:** Implement Jaccard similarity for tokenized strings.

**Why they ask:** Better for compound column names like `PATIENT_BIRTH_DATE`.

```python
# TODO: Implement this
def jaccard_similarity(s1: str, s2: str) -> float:
    """
    Calculate Jaccard similarity based on tokens.

    Examples:
        jaccard_similarity("PATIENT_NR", "PATIENT_NUMBER") -> 0.5
        jaccard_similarity("BIRTH_DATE", "DATE_OF_BIRTH") -> 0.5
    """
    pass
```

<details>
<summary>Solution (click to expand)</summary>

```python
import re

def tokenize(s: str) -> set:
    """
    Split string into tokens.
    Handles: snake_case, camelCase, PascalCase, numbers
    """
    # Split on underscores and spaces
    tokens = re.split(r'[_\s]+', s)

    # Split camelCase
    expanded = []
    for token in tokens:
        # Split on case transitions: 'patientNumber' -> ['patient', 'Number']
        parts = re.split(r'(?<=[a-z])(?=[A-Z])', token)
        expanded.extend(parts)

    # Normalize: lowercase, filter empty
    return {t.lower() for t in expanded if t}

def jaccard_similarity(s1: str, s2: str) -> float:
    """
    Calculate Jaccard similarity: |A ∩ B| / |A ∪ B|
    """
    tokens1 = tokenize(s1)
    tokens2 = tokenize(s2)

    if not tokens1 and not tokens2:
        return 1.0
    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    return len(intersection) / len(union)

# Bonus: Weighted Jaccard for important tokens
def weighted_jaccard(s1: str, s2: str, important_tokens: set = None) -> float:
    """
    Jaccard with higher weight for important domain tokens.
    """
    if important_tokens is None:
        important_tokens = {'patient', 'id', 'date', 'name', 'number', 'insurance'}

    tokens1 = tokenize(s1)
    tokens2 = tokenize(s2)

    if not tokens1 and not tokens2:
        return 1.0

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    # Weight important tokens higher
    def weight(token):
        return 2.0 if token in important_tokens else 1.0

    weighted_intersection = sum(weight(t) for t in intersection)
    weighted_union = sum(weight(t) for t in union)

    return weighted_intersection / weighted_union if weighted_union > 0 else 0.0
```

**Key points to mention:**
- Tokenization handles multiple naming conventions
- Jaccard is set-based: order doesn't matter
- Can weight domain-specific tokens

</details>

---

### Exercise 1.4: Combined Similarity Score

**Problem:** Combine multiple similarity algorithms into a single score.

**Why they ask:** Real systems use multiple signals. Shows you understand trade-offs.

```python
# TODO: Implement this
def combined_similarity(s1: str, s2: str) -> dict:
    """
    Calculate multiple similarity scores and combine them.

    Returns:
        {
            'levenshtein': 0.82,
            'jaro_winkler': 0.85,
            'jaccard': 0.67,
            'combined': 0.80,
            'best_match': True  # if combined >= 0.75
        }
    """
    pass
```

<details>
<summary>Solution (click to expand)</summary>

```python
def combined_similarity(
    s1: str,
    s2: str,
    weights: dict = None
) -> dict:
    """
    Calculate multiple similarity scores and combine them.

    Default weights optimized for column name matching:
    - Jaro-Winkler: 0.4 (prefix-sensitive, good for abbreviations)
    - Levenshtein: 0.3 (overall edit distance)
    - Jaccard: 0.3 (token overlap, good for compound names)
    """
    if weights is None:
        weights = {
            'levenshtein': 0.3,
            'jaro_winkler': 0.4,
            'jaccard': 0.3
        }

    # Normalize strings for comparison
    s1_norm = s1.upper().strip()
    s2_norm = s2.upper().strip()

    # Calculate individual scores
    lev = levenshtein_similarity(s1_norm, s2_norm)
    jw = jaro_winkler(s1_norm, s2_norm)
    jac = jaccard_similarity(s1_norm, s2_norm)

    # Weighted combination
    combined = (
        lev * weights['levenshtein'] +
        jw * weights['jaro_winkler'] +
        jac * weights['jaccard']
    )

    return {
        'levenshtein': round(lev, 3),
        'jaro_winkler': round(jw, 3),
        'jaccard': round(jac, 3),
        'combined': round(combined, 3),
        'best_match': combined >= 0.75
    }

# Test cases
test_cases = [
    ("PATNR", "PATIENT_NR"),
    ("PATNR", "PATIENTENNUMMER"),
    ("GEBDAT", "GEBURTSDATUM"),
    ("BIRTH_DATE", "DATE_OF_BIRTH"),
    ("KASSE", "INSURANCE"),  # Different language - should be low
]

for s1, s2 in test_cases:
    result = combined_similarity(s1, s2)
    print(f"{s1:20} vs {s2:20} -> {result['combined']:.2f} ({'✓' if result['best_match'] else '✗'})")
```

**Key points to mention:**
- Different algorithms excel at different patterns
- Weights can be tuned based on your data
- Threshold (0.75) is configurable via trust profiles

</details>

---

## 2. Data Structure Design

### Exercise 2.1: Value Bank Implementation

**Problem:** Design a data structure for efficient column name lookup with fuzzy matching.

**Why they ask:** Tests data structure choice, trade-offs between memory and speed.

```python
# TODO: Implement this
class ValueBank:
    """
    Efficient storage and lookup for learned column name patterns.

    Requirements:
    - O(1) exact match lookup
    - Efficient fuzzy matching (< 100ms for 10,000 variants)
    - Support adding new variants
    - Track occurrence counts
    """

    def __init__(self):
        pass

    def add_variant(self, entity: str, column_name: str, source: str) -> None:
        """Add a new column name variant."""
        pass

    def exact_match(self, column_name: str) -> dict | None:
        """O(1) exact match lookup."""
        pass

    def fuzzy_match(self, column_name: str, threshold: float = 0.75) -> list:
        """Find similar column names above threshold."""
        pass
```

<details>
<summary>Solution (click to expand)</summary>

```python
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional
import heapq

@dataclass
class VariantInfo:
    entity: str
    column_name: str
    normalized: str
    occurrences: int = 1
    sources: set = field(default_factory=set)

class ValueBank:
    """
    Efficient storage and lookup for learned column name patterns.

    Data structures:
    - exact_lookup: dict for O(1) exact match
    - by_entity: dict for grouping variants by entity
    - all_variants: list for fuzzy search iteration
    - token_index: inverted index for fast candidate filtering
    """

    def __init__(self):
        # O(1) exact lookup by normalized name
        self.exact_lookup: dict[str, VariantInfo] = {}

        # Group variants by entity
        self.by_entity: dict[str, list[VariantInfo]] = defaultdict(list)

        # All variants for iteration
        self.all_variants: list[VariantInfo] = []

        # Inverted index: token -> set of variant indices
        # Enables fast candidate filtering for fuzzy match
        self.token_index: dict[str, set[int]] = defaultdict(set)

    def _normalize(self, name: str) -> str:
        """Normalize column name for comparison."""
        return name.upper().strip()

    def _tokenize(self, name: str) -> set[str]:
        """Extract tokens for indexing."""
        import re
        tokens = re.split(r'[_\s]+', name.upper())
        expanded = []
        for token in tokens:
            parts = re.split(r'(?<=[a-z])(?=[A-Z])', token)
            expanded.extend(parts)
        return {t.lower() for t in expanded if t and len(t) > 1}

    def add_variant(self, entity: str, column_name: str, source: str) -> None:
        """Add a new column name variant."""
        normalized = self._normalize(column_name)

        # Check if already exists
        if normalized in self.exact_lookup:
            variant = self.exact_lookup[normalized]
            variant.occurrences += 1
            variant.sources.add(source)
            return

        # Create new variant
        variant = VariantInfo(
            entity=entity,
            column_name=column_name,
            normalized=normalized,
            occurrences=1,
            sources={source}
        )

        # Add to all data structures
        self.exact_lookup[normalized] = variant
        self.by_entity[entity].append(variant)

        idx = len(self.all_variants)
        self.all_variants.append(variant)

        # Index tokens
        for token in self._tokenize(column_name):
            self.token_index[token].add(idx)

    def exact_match(self, column_name: str) -> Optional[dict]:
        """O(1) exact match lookup."""
        normalized = self._normalize(column_name)
        variant = self.exact_lookup.get(normalized)

        if variant:
            return {
                'entity': variant.entity,
                'column_name': variant.column_name,
                'confidence': 1.0,
                'occurrences': variant.occurrences,
                'match_type': 'exact'
            }
        return None

    def fuzzy_match(
        self,
        column_name: str,
        threshold: float = 0.75,
        limit: int = 5
    ) -> list[dict]:
        """
        Find similar column names above threshold.

        Optimization: Use token index to filter candidates first,
        then compute similarity only for candidates.
        """
        # Get candidate indices via token overlap
        query_tokens = self._tokenize(column_name)
        candidate_indices = set()

        for token in query_tokens:
            candidate_indices.update(self.token_index.get(token, set()))

        # If no token overlap, fall back to full scan (rare)
        if not candidate_indices:
            candidate_indices = set(range(len(self.all_variants)))

        # Score candidates
        results = []
        for idx in candidate_indices:
            variant = self.all_variants[idx]
            score = combined_similarity(column_name, variant.column_name)['combined']

            if score >= threshold:
                results.append({
                    'entity': variant.entity,
                    'column_name': variant.column_name,
                    'confidence': score,
                    'occurrences': variant.occurrences,
                    'match_type': 'fuzzy'
                })

        # Return top matches
        results.sort(key=lambda x: (-x['confidence'], -x['occurrences']))
        return results[:limit]

    def get_stats(self) -> dict:
        """Return statistics about the value bank."""
        return {
            'total_variants': len(self.all_variants),
            'unique_entities': len(self.by_entity),
            'index_tokens': len(self.token_index),
            'avg_occurrences': sum(v.occurrences for v in self.all_variants) / len(self.all_variants) if self.all_variants else 0
        }


# Usage example
bank = ValueBank()
bank.add_variant('patient_id', 'PATNR', 'client_001')
bank.add_variant('patient_id', 'PATIENT_NR', 'client_002')
bank.add_variant('patient_id', 'PAT_ID', 'client_003')
bank.add_variant('birth_date', 'GEBDAT', 'client_001')
bank.add_variant('birth_date', 'GEBURTSDATUM', 'client_002')

# Test lookups
print(bank.exact_match('PATNR'))
print(bank.fuzzy_match('PATIENTNUMMER'))
print(bank.get_stats())
```

**Key points to mention:**
- Multiple data structures for different access patterns
- Token index reduces fuzzy search from O(n) to O(candidates)
- Trade-off: more memory for faster lookup

</details>

---

### Exercise 2.2: Confidence Aggregation

**Problem:** Design a system that aggregates confidence from multiple signals.

```python
# TODO: Implement this
class ConfidenceAggregator:
    """
    Combine confidence scores from multiple sources:
    - Column name similarity
    - Data type match
    - Value pattern match
    - Historical accuracy

    Output: Single confidence score with explanation
    """
    pass
```

<details>
<summary>Solution (click to expand)</summary>

```python
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class SignalType(Enum):
    COLUMN_NAME = "column_name"
    DATA_TYPE = "data_type"
    VALUE_PATTERN = "value_pattern"
    HISTORICAL = "historical"

@dataclass
class Signal:
    type: SignalType
    confidence: float  # 0-1
    weight: float      # importance
    evidence: str      # explanation

class ConfidenceAggregator:
    """
    Combine confidence scores from multiple sources.

    Strategy:
    1. Weighted average of all signals
    2. Boost for multiple agreeing signals
    3. Penalty for conflicting signals
    4. Historical accuracy calibration
    """

    DEFAULT_WEIGHTS = {
        SignalType.COLUMN_NAME: 0.40,
        SignalType.DATA_TYPE: 0.20,
        SignalType.VALUE_PATTERN: 0.25,
        SignalType.HISTORICAL: 0.15,
    }

    def __init__(self, weights: dict = None):
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.signals: list[Signal] = []

    def add_signal(
        self,
        signal_type: SignalType,
        confidence: float,
        evidence: str,
        weight: float = None
    ) -> None:
        """Add a confidence signal."""
        if weight is None:
            weight = self.weights.get(signal_type, 0.1)

        self.signals.append(Signal(
            type=signal_type,
            confidence=max(0, min(1, confidence)),  # Clamp to 0-1
            weight=weight,
            evidence=evidence
        ))

    def aggregate(self) -> dict:
        """
        Calculate final confidence score.

        Returns:
            {
                'confidence': 0.87,
                'signals_used': 3,
                'explanation': [...],
                'adjustments': {...}
            }
        """
        if not self.signals:
            return {
                'confidence': 0.0,
                'signals_used': 0,
                'explanation': ['No signals provided'],
                'adjustments': {}
            }

        # Weighted average
        total_weight = sum(s.weight for s in self.signals)
        if total_weight == 0:
            return {'confidence': 0.0, 'signals_used': 0, 'explanation': ['All weights are zero'], 'adjustments': {}}

        weighted_sum = sum(s.confidence * s.weight for s in self.signals)
        base_confidence = weighted_sum / total_weight

        # Adjustments
        adjustments = {}

        # Boost for multiple agreeing signals (agreement bonus)
        high_confidence_count = sum(1 for s in self.signals if s.confidence >= 0.8)
        if high_confidence_count >= 2:
            agreement_boost = min(0.05, 0.02 * (high_confidence_count - 1))
            adjustments['agreement_boost'] = agreement_boost
            base_confidence += agreement_boost

        # Penalty for conflicting signals
        confidences = [s.confidence for s in self.signals]
        if len(confidences) >= 2:
            variance = sum((c - base_confidence) ** 2 for c in confidences) / len(confidences)
            if variance > 0.1:  # High disagreement
                conflict_penalty = min(0.1, variance * 0.5)
                adjustments['conflict_penalty'] = -conflict_penalty
                base_confidence -= conflict_penalty

        # Clamp final score
        final_confidence = max(0, min(0.99, base_confidence))

        # Build explanation
        explanation = []
        for s in sorted(self.signals, key=lambda x: -x.confidence):
            explanation.append(f"{s.type.value}: {s.confidence:.2f} ({s.evidence})")

        return {
            'confidence': round(final_confidence, 3),
            'signals_used': len(self.signals),
            'explanation': explanation,
            'adjustments': adjustments
        }

    def reset(self):
        """Clear signals for next column."""
        self.signals = []


# Usage example
agg = ConfidenceAggregator()

# Column "PATNR" analysis
agg.add_signal(SignalType.COLUMN_NAME, 0.95, "Exact match in value bank")
agg.add_signal(SignalType.DATA_TYPE, 0.90, "INT matches patient_id type")
agg.add_signal(SignalType.VALUE_PATTERN, 0.85, "Sequential integers 1001-9999")
agg.add_signal(SignalType.HISTORICAL, 0.92, "92% accuracy on similar columns")

result = agg.aggregate()
print(f"Final confidence: {result['confidence']}")
for exp in result['explanation']:
    print(f"  - {exp}")
```

**Key points to mention:**
- Multiple signals reduce false positives
- Weighting reflects signal reliability
- Agreement/conflict adjustments add nuance
- Explainability is built-in

</details>

---

## 3. SQL Schema Discovery

### Exercise 3.1: Find Columns by Pattern

**Problem:** Write SQL to find all columns matching a pattern across all tables.

```sql
-- TODO: Find all columns containing 'PAT' in their name
-- Return: schema, table, column, data_type, is_nullable
```

<details>
<summary>Solution (click to expand)</summary>

```sql
-- SQL Server
SELECT
    TABLE_SCHEMA,
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE COLUMN_NAME LIKE '%PAT%'
ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION;

-- PostgreSQL (same syntax works)
SELECT
    table_schema,
    table_name,
    column_name,
    data_type,
    is_nullable,
    character_maximum_length
FROM information_schema.columns
WHERE column_name ILIKE '%pat%'  -- Case-insensitive
  AND table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY table_schema, table_name, ordinal_position;

-- MySQL
SELECT
    TABLE_SCHEMA,
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE COLUMN_NAME LIKE '%PAT%'
  AND TABLE_SCHEMA NOT IN ('mysql', 'information_schema', 'performance_schema')
ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION;
```

</details>

---

### Exercise 3.2: Column Statistics

**Problem:** Write SQL to get null percentage and distinct count for a column.

```sql
-- TODO: Get statistics for PATIENT.PATNR
-- Return: total_rows, null_count, null_percentage, distinct_count
```

<details>
<summary>Solution (click to expand)</summary>

```sql
-- Single query for all stats
SELECT
    COUNT(*) as total_rows,
    COUNT(*) - COUNT(PATNR) as null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(PATNR)) / NULLIF(COUNT(*), 0), 2) as null_percentage,
    COUNT(DISTINCT PATNR) as distinct_count,
    MIN(PATNR) as min_value,
    MAX(PATNR) as max_value
FROM PATIENT;

-- Generic version with dynamic SQL (SQL Server)
DECLARE @table_name NVARCHAR(128) = 'PATIENT';
DECLARE @column_name NVARCHAR(128) = 'PATNR';
DECLARE @sql NVARCHAR(MAX);

SET @sql = N'
SELECT
    ''' + @table_name + ''' as table_name,
    ''' + @column_name + ''' as column_name,
    COUNT(*) as total_rows,
    SUM(CASE WHEN ' + QUOTENAME(@column_name) + ' IS NULL THEN 1 ELSE 0 END) as null_count,
    ROUND(100.0 * SUM(CASE WHEN ' + QUOTENAME(@column_name) + ' IS NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) as null_pct,
    COUNT(DISTINCT ' + QUOTENAME(@column_name) + ') as distinct_count
FROM ' + QUOTENAME(@table_name);

EXEC sp_executesql @sql;
```

</details>

---

### Exercise 3.3: Sample Values with Frequency

**Problem:** Get representative sample values with their frequency.

```sql
-- TODO: Get top 10 most common values with counts
-- Useful for detecting patterns (enums, codes, etc.)
```

<details>
<summary>Solution (click to expand)</summary>

```sql
-- Top N most frequent values
SELECT TOP 10
    KASSE_TYP as value,
    COUNT(*) as frequency,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
FROM PATIENT
WHERE KASSE_TYP IS NOT NULL
GROUP BY KASSE_TYP
ORDER BY COUNT(*) DESC;

-- PostgreSQL version
SELECT
    kasse_typ as value,
    COUNT(*) as frequency,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
FROM patient
WHERE kasse_typ IS NOT NULL
GROUP BY kasse_typ
ORDER BY COUNT(*) DESC
LIMIT 10;

-- Stratified sample (common + rare + random)
WITH ranked AS (
    SELECT
        KASSE_TYP,
        COUNT(*) as freq,
        ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) as rank_desc,
        ROW_NUMBER() OVER (ORDER BY COUNT(*) ASC) as rank_asc
    FROM PATIENT
    WHERE KASSE_TYP IS NOT NULL
    GROUP BY KASSE_TYP
)
SELECT KASSE_TYP, freq, 'common' as sample_type FROM ranked WHERE rank_desc <= 3
UNION ALL
SELECT KASSE_TYP, freq, 'rare' FROM ranked WHERE rank_asc <= 2
UNION ALL
SELECT KASSE_TYP, freq, 'random' FROM ranked
WHERE rank_desc > 3 AND rank_asc > 2
ORDER BY NEWID()  -- Random from middle
OFFSET 0 ROWS FETCH NEXT 5 ROWS ONLY;
```

</details>

---

### Exercise 3.4: Find Foreign Key Candidates

**Problem:** Find columns that might be foreign keys (matching names/values in other tables).

```sql
-- TODO: Find potential FK relationships
-- Look for columns with matching names/patterns across tables
```

<details>
<summary>Solution (click to expand)</summary>

```sql
-- Find columns that might reference each other by name pattern
WITH potential_pks AS (
    SELECT
        TABLE_NAME,
        COLUMN_NAME,
        DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE COLUMN_NAME LIKE '%ID'
       OR COLUMN_NAME LIKE '%NR'
       OR COLUMN_NAME LIKE '%_PK'
),
potential_fks AS (
    SELECT
        c.TABLE_NAME as fk_table,
        c.COLUMN_NAME as fk_column,
        c.DATA_TYPE as fk_type,
        pk.TABLE_NAME as pk_table,
        pk.COLUMN_NAME as pk_column
    FROM INFORMATION_SCHEMA.COLUMNS c
    JOIN potential_pks pk
        ON c.COLUMN_NAME LIKE '%' + pk.TABLE_NAME + '%'
        OR c.COLUMN_NAME LIKE pk.TABLE_NAME + '%ID'
        OR c.COLUMN_NAME LIKE pk.TABLE_NAME + '%NR'
    WHERE c.TABLE_NAME != pk.TABLE_NAME
      AND c.DATA_TYPE = pk.DATA_TYPE
)
SELECT * FROM potential_fks
ORDER BY fk_table, fk_column;

-- Verify by checking value overlap (expensive but accurate)
-- Example: Does KARTEI.PATNR reference PATIENT.PATNR?
SELECT
    'KARTEI.PATNR -> PATIENT.PATNR' as relationship,
    COUNT(DISTINCT k.PATNR) as fk_distinct_values,
    COUNT(DISTINCT p.PATNR) as pk_distinct_values,
    SUM(CASE WHEN p.PATNR IS NOT NULL THEN 1 ELSE 0 END) as matching_values,
    ROUND(100.0 * SUM(CASE WHEN p.PATNR IS NOT NULL THEN 1 ELSE 0 END) /
          NULLIF(COUNT(DISTINCT k.PATNR), 0), 2) as match_percentage
FROM KARTEI k
LEFT JOIN PATIENT p ON k.PATNR = p.PATNR;
```

</details>

---

### Exercise 3.5: Detect Empty/Abandoned Columns

**Problem:** Find columns that are mostly empty or haven't been updated.

```sql
-- TODO: Find columns with >90% NULL values
-- Also detect columns with no recent updates (if timestamp available)
```

<details>
<summary>Solution (click to expand)</summary>

```sql
-- Generate dynamic SQL to check all columns (SQL Server)
DECLARE @sql NVARCHAR(MAX) = '';

SELECT @sql = @sql + '
SELECT
    ''' + TABLE_NAME + ''' as table_name,
    ''' + COLUMN_NAME + ''' as column_name,
    ''' + DATA_TYPE + ''' as data_type,
    COUNT(*) as total_rows,
    SUM(CASE WHEN ' + QUOTENAME(COLUMN_NAME) + ' IS NULL THEN 1 ELSE 0 END) as null_count,
    ROUND(100.0 * SUM(CASE WHEN ' + QUOTENAME(COLUMN_NAME) + ' IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as null_pct
FROM ' + QUOTENAME(TABLE_NAME) + '
UNION ALL '
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'dbo'
ORDER BY TABLE_NAME, ORDINAL_POSITION;

-- Remove trailing UNION ALL
SET @sql = LEFT(@sql, LEN(@sql) - 10);

-- Wrap in CTE to filter
SET @sql = '
WITH all_stats AS (' + @sql + ')
SELECT * FROM all_stats
WHERE null_pct >= 90
ORDER BY null_pct DESC, table_name, column_name';

EXEC sp_executesql @sql;

-- Detect abandoned columns (with timestamp check)
SELECT
    'PATIENT' as table_name,
    'FAX' as column_name,
    MAX(UPDATED_AT) as last_non_null_update,
    DATEDIFF(day, MAX(UPDATED_AT), GETDATE()) as days_since_update
FROM PATIENT
WHERE FAX IS NOT NULL
HAVING MAX(UPDATED_AT) < DATEADD(year, -1, GETDATE());  -- No updates in 1 year
```

</details>

---

## 4. System Design

### Exercise 4.1: Whiteboard the Architecture

**Problem:** Draw the schema matching service architecture on a whiteboard.

**Time limit:** 15 minutes

**What to include:**
1. Components and their responsibilities
2. Data flow
3. Storage choices
4. Scalability points

<details>
<summary>Reference Diagram</summary>

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LOAD BALANCER                                   │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────────────┐
│                              API SERVERS                                     │
│                         (Stateless, horizontally scalable)                   │
│                                                                              │
│  POST /map      GET /status     GET /mappings     POST /review              │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
          ┌─────────▼─────────┐       ┌────────▼────────┐
          │    JOB QUEUE      │       │    DATABASE     │
          │     (Redis)       │       │  (PostgreSQL)   │
          │                   │       │                 │
          │  - Mapping jobs   │       │ - Value bank    │
          │  - Column tasks   │       │ - Mappings      │
          │  - Priorities     │       │ - Audit log     │
          └─────────┬─────────┘       │ - Review queue  │
                    │                 └─────────────────┘
          ┌─────────▼─────────────────────┐
          │         WORKER POOL           │
          │     (Celery, N workers)       │
          │                               │
          │  ┌─────────┐  ┌─────────┐    │
          │  │Worker 1 │  │Worker N │    │
          │  └────┬────┘  └────┬────┘    │
          │       │            │          │
          │  ┌────▼────────────▼────┐    │
          │  │   MATCHING ENGINE    │    │
          │  │                      │    │
          │  │ - Schema Profiler    │    │
          │  │ - Similarity Scorer  │    │
          │  │ - Confidence Calc    │    │
          │  └──────────────────────┘    │
          └───────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │      CLIENT DATABASES       │
          │   (Read-only connections)   │
          │                             │
          │  ┌───┐ ┌───┐ ┌───┐ ┌───┐  │
          │  │DB1│ │DB2│ │...│ │DBN│  │
          │  └───┘ └───┘ └───┘ └───┘  │
          └─────────────────────────────┘
```

**Key talking points:**

1. **Stateless API servers** → Horizontal scaling
2. **Job queue** → Async processing, don't block API
3. **Worker pool** → Parallel table/column processing
4. **PostgreSQL** → ACID for audit trail
5. **Redis** → Fast job queue, optional caching
6. **Client DB connections** → Read-only, pooled

</details>

---

### Exercise 4.2: Design the Database Schema

**Problem:** Design tables for the value bank and mapping system.

**Requirements:**
- Support learning from multiple clients
- Track confidence and verification
- Audit trail for compliance
- Efficient lookup

<details>
<summary>Reference Schema (ERD)</summary>

```
┌─────────────────────────┐       ┌─────────────────────────┐
│   canonical_entities    │       │    column_variants      │
├─────────────────────────┤       ├─────────────────────────┤
│ id (PK)                 │◄──────│ entity_id (FK)          │
│ name (UNIQUE)           │       │ id (PK)                 │
│ category                │       │ column_name             │
│ data_type               │       │ normalized (INDEX)      │
│ is_critical             │       │ occurrence_count        │
│ description             │       │ confidence              │
└─────────────────────────┘       │ status                  │
                                  │ source_client_id        │
                                  │ verified_by             │
                                  └─────────────────────────┘
                                            │
                                            │ (learned from)
                                            ▼
┌─────────────────────────┐       ┌─────────────────────────┐
│    client_mappings      │       │      review_items       │
├─────────────────────────┤       ├─────────────────────────┤
│ id (PK)                 │       │ id (PK)                 │
│ client_id (INDEX)       │       │ client_id               │
│ entity_id (FK)          │       │ source_table            │
│ source_table            │       │ source_column           │
│ source_column           │       │ proposed_entity_id (FK) │
│ confidence              │       │ confidence              │
│ status                  │       │ sample_values (JSONB)   │
│ reasoning               │       │ status (INDEX)          │
│ verified_at             │       │ priority                │
│ verified_by             │       │ resolved_by             │
└─────────────────────────┘       └─────────────────────────┘
         │
         │ (audit)
         ▼
┌─────────────────────────┐
│   mapping_audit_log     │
├─────────────────────────┤
│ id (PK)                 │
│ client_id               │
│ action                  │
│ entity_id               │
│ old_value (JSONB)       │
│ new_value (JSONB)       │
│ actor_type              │
│ actor_id                │
│ timestamp (INDEX)       │
└─────────────────────────┘
```

</details>

---

### Exercise 4.3: Estimate Capacity

**Problem:** Size the system for 100 clients, 500 tables each, 50 columns per table.

**Calculate:**
- Total columns to process
- Value bank size
- Processing time estimate
- Storage requirements

<details>
<summary>Solution</summary>

```
INPUTS:
- Clients: 100
- Tables per client: 500
- Columns per table: 50
- Overlap: ~70% (similar schemas)

CALCULATIONS:

1. Total columns
   100 × 500 × 50 = 2,500,000 columns total

   With 70% overlap:
   Unique patterns ≈ 2,500,000 × 0.3 = 750,000

2. Value bank size
   - Assume 10 variants per entity
   - Assume 100 canonical entities
   - Max variants: 100 × 10 = 1,000 (but grows with discovery)

   After 100 clients: ~5,000-10,000 variants
   Storage: ~50KB per 1,000 variants = ~500KB

3. Processing time (per client)
   - Schema profiling: 500 tables × 0.1s = 50s
   - Column analysis: 25,000 columns × 0.05s = 1,250s (~20 min)
   - Parallel with 10 workers: ~2-3 min

   First client: Slowest (empty value bank, more review)
   Later clients: Faster (value bank matches, auto-accept)

4. Storage requirements
   - Mappings: 2,500,000 × 200 bytes = 500MB
   - Audit log: 10× mappings = 5GB
   - Value bank: 500KB
   - Total: ~6GB PostgreSQL

5. Scaling considerations
   - Workers: 1 per 10 concurrent clients
   - Redis: 100MB for job queue
   - API servers: 2+ for HA
```

</details>

---

## 5. Code Review Exercises

### Exercise 5.1: Spot the Scalability Issues

**Problem:** Review this code and identify scalability problems.

```python
def match_all_columns(client_id: str, connection_string: str):
    """Map all columns for a client."""
    conn = connect(connection_string)

    # Get all tables
    tables = conn.execute("SELECT * FROM INFORMATION_SCHEMA.TABLES").fetchall()

    results = []
    for table in tables:
        # Get all columns
        columns = conn.execute(
            f"SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table.name}'"
        ).fetchall()

        for column in columns:
            # Get all sample values
            samples = conn.execute(
                f"SELECT {column.name} FROM {table.name}"
            ).fetchall()

            # Check against entire value bank
            value_bank = load_entire_value_bank()

            for variant in value_bank:
                score = calculate_similarity(column.name, variant.name)
                if score > 0.8:
                    results.append({
                        'column': column.name,
                        'match': variant.entity,
                        'score': score
                    })

    save_results(results)
    return results
```

<details>
<summary>Issues and Fixes</summary>

```python
# ISSUES IDENTIFIED:

# 1. SQL INJECTION (Security + breaks at scale)
#    f"SELECT * FROM ... WHERE TABLE_NAME = '{table.name}'"
#    FIX: Use parameterized queries

# 2. FETCHING ALL ROWS (Memory explosion)
#    "SELECT {column.name} FROM {table.name}" - fetches ALL data
#    FIX: Use LIMIT and sampling

# 3. LOADING ENTIRE VALUE BANK PER COLUMN (O(n×m) memory)
#    load_entire_value_bank() called in inner loop
#    FIX: Load once, pass as parameter

# 4. NO BATCHING (Network overhead)
#    One query per table, one per column
#    FIX: Batch queries

# 5. SYNCHRONOUS PROCESSING (Slow)
#    Sequential loops
#    FIX: Async/parallel processing

# 6. NO CONNECTION POOLING
#    Single connection for everything
#    FIX: Use connection pool

# FIXED VERSION:

from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

def match_all_columns_v2(client_id: str, connection_string: str):
    """Map all columns for a client - scalable version."""

    # Connection pool
    engine = create_engine(
        connection_string,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10
    )

    # Load value bank ONCE
    value_bank = ValueBank.load()

    # Get all tables in single query
    with engine.connect() as conn:
        tables = conn.execute(text("""
            SELECT TABLE_NAME, TABLE_SCHEMA
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
        """)).fetchall()

    # Process tables in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(process_table, engine, table, value_bank)
            for table in tables
        ]

        results = []
        for future in futures:
            results.extend(future.result())

    # Batch save
    save_results_batch(results)
    return results

def process_table(engine, table, value_bank):
    """Process single table - parallelizable."""
    results = []

    with engine.connect() as conn:
        # Get columns with stats in single query
        columns = conn.execute(text("""
            SELECT
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = :table_name
        """), {'table_name': table.TABLE_NAME}).fetchall()

        for column in columns:
            # SAMPLE values, don't fetch all
            samples = conn.execute(text(f"""
                SELECT TOP 100 {column.COLUMN_NAME}
                FROM {table.TABLE_NAME}
                WHERE {column.COLUMN_NAME} IS NOT NULL
                ORDER BY NEWID()
            """)).fetchall()

            # Use value bank (already loaded)
            match = value_bank.find_best_match(column.COLUMN_NAME)
            if match and match['confidence'] > 0.8:
                results.append({
                    'table': table.TABLE_NAME,
                    'column': column.COLUMN_NAME,
                    'match': match['entity'],
                    'confidence': match['confidence']
                })

    return results
```

**Key issues to mention:**
1. SQL injection → parameterized queries
2. Memory explosion → sampling
3. Repeated loading → cache/pass reference
4. Sequential → parallel processing
5. No pooling → connection pool

</details>

---

### Exercise 5.2: Design Review

**Problem:** Review this API design and suggest improvements.

```
POST /api/match
Body: { "client_id": "abc", "connection_string": "..." }
Response: { "mappings": [...all mappings...] }
```

<details>
<summary>Issues and Improvements</summary>

```
ISSUES:

1. SYNCHRONOUS RESPONSE
   - Mapping can take minutes
   - HTTP timeout will kill it

2. CONNECTION STRING IN REQUEST
   - Security risk (logged, exposed)
   - Should reference stored credentials

3. ALL MAPPINGS IN RESPONSE
   - Could be thousands of mappings
   - Response too large

4. NO PROGRESS VISIBILITY
   - Client can't track progress

5. NO IDEMPOTENCY
   - What if called twice?

IMPROVED DESIGN:

# Start mapping (async)
POST /api/schema-matching/runs
Body: {
    "client_id": "abc",
    "connection_id": "conn_123",  # Reference, not raw string
    "trust_profile": "standard",
    "tables": ["PATIENT", "KARTEI"]  # Optional filter
}
Response: {
    "run_id": "run_456",
    "status": "queued",
    "links": {
        "status": "/api/schema-matching/runs/run_456",
        "cancel": "/api/schema-matching/runs/run_456/cancel"
    }
}
Status: 202 Accepted

# Check status
GET /api/schema-matching/runs/{run_id}
Response: {
    "run_id": "run_456",
    "status": "running",  # queued/running/pending_review/completed/failed
    "progress": {
        "tables_total": 50,
        "tables_complete": 23,
        "percent": 46
    },
    "current_table": "KARTEI",
    "started_at": "2024-01-15T10:00:00Z",
    "estimated_completion": "2024-01-15T10:05:00Z"
}

# Get mappings (paginated)
GET /api/schema-matching/runs/{run_id}/mappings?page=1&limit=50
Response: {
    "mappings": [...50 mappings...],
    "pagination": {
        "page": 1,
        "limit": 50,
        "total": 234,
        "pages": 5
    }
}

# Webhook for completion (optional)
POST /api/schema-matching/runs
Body: {
    ...,
    "webhook_url": "https://client.com/callback"
}
# System POSTs to webhook when complete
```

**Key improvements:**
1. Async with status polling
2. Connection reference, not raw string
3. Paginated results
4. Progress visibility
5. Webhook option for completion

</details>

---

## 6. Whiteboard Diagrams

### Diagram 6.1: Matching Flow

Practice drawing this in under 5 minutes:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   COLUMN     │     │    VALUE     │     │   MATCHING   │
│   INPUT      │────▶│    BANK      │────▶│   ENGINE     │
│              │     │   LOOKUP     │     │              │
│ "PATNR"      │     │              │     │              │
│ INT          │     │ Exact? ─────────▶ 95% confidence │
│ [1001,1002]  │     │ Fuzzy? ─────────▶ 82% confidence │
└──────────────┘     │ Pattern? ────────▶ 78% confidence│
                     └──────────────┘     └──────┬───────┘
                                                 │
                                                 ▼
                     ┌──────────────────────────────────────┐
                     │          DECISION ENGINE             │
                     │                                      │
                     │  Combined: 89%                       │
                     │                                      │
                     │  ≥90% ──────▶ AUTO-ACCEPT           │
                     │  70-89% ────▶ REVIEW QUEUE          │
                     │  <70% ──────▶ REJECT                │
                     └──────────────────────────────────────┘
```

---

### Diagram 6.2: Learning Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                        LEARNING LOOP                             │
│                                                                  │
│    ┌─────────┐                              ┌─────────┐         │
│    │ Client  │                              │  Value  │         │
│    │   DB    │                              │  Bank   │         │
│    └────┬────┘                              └────▲────┘         │
│         │                                        │               │
│         │  1. Profile                           │               │
│         ▼                                        │               │
│    ┌─────────┐      2. Match      ┌─────────┐  │               │
│    │ Schema  │─────────────────▶│ Matching │  │               │
│    │ Profiler│                    │ Engine  │  │               │
│    └─────────┘                    └────┬────┘  │               │
│                                        │        │               │
│                            3. Propose  │        │ 5. Learn      │
│                                        ▼        │               │
│                                   ┌─────────┐   │               │
│                                   │ Review  │───┘               │
│                                   │  Queue  │                   │
│                                   └────┬────┘                   │
│                                        │                        │
│                            4. Human    │                        │
│                               Review   ▼                        │
│                                   ┌─────────┐                   │
│                                   │ VERIFIED│                   │
│                                   │ MAPPING │                   │
│                                   └─────────┘                   │
└─────────────────────────────────────────────────────────────────┘

Client 1: Empty value bank → Many reviews
Client 5: Growing value bank → Fewer reviews
Client 15: Mature value bank → Mostly auto-accept
```

---

### Diagram 6.3: Trust Profiles

```
CONFIDENCE THRESHOLDS BY TRUST PROFILE

100% ┼─────────────────────────────────────────────
     │
 99% ┼─ ─ ─ ─ ─ ─ ─ ─ ─ ─ CONSERVATIVE ─ ─ ─ ─ ─ ─   AUTO-ACCEPT
     │                                                    ▲
 90% ┼─ ─ ─ ─ ─ ─ STANDARD ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─       │
     │                                                    │
 80% ┼─ PERMISSIVE ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─       │
     │ │                                                  │
 70% ┼─│─ ─ ─ ─ ─ STANDARD ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  HUMAN REVIEW
     │ │                                                  ▲
 60% ┼─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─       │
     │ │                                                  │
 50% ┼─│─ PERMISSIVE ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─       │
     │ │ │                                                │
     │ │ │                                                │
  0% ┼─┴─┴────────────────────────────────────────   REJECT
     └─────────────────────────────────────────────

USE CASES:
- Conservative: First client, critical data, regulated industry
- Standard: Normal operations, balanced risk
- Permissive: Trusted schemas, demos, internal tools
```

---

## Quick Reference Card

Print this and review before the interview:

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTERVIEW QUICK REFERENCE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SIMILARITY ALGORITHMS                                          │
│  ├─ Levenshtein: Edit distance, O(m×n), good for typos         │
│  ├─ Jaro-Winkler: Prefix-weighted, good for abbreviations      │
│  └─ Jaccard: Token overlap, good for compound names            │
│                                                                  │
│  SCALABILITY PATTERNS                                           │
│  ├─ Async processing: Don't block API, use job queue           │
│  ├─ Parallel workers: Process tables/columns concurrently      │
│  ├─ Value bank caching: Load once, reuse                       │
│  └─ Connection pooling: Reuse DB connections                   │
│                                                                  │
│  DATA STRUCTURES                                                │
│  ├─ HashMap: O(1) exact lookup                                 │
│  ├─ Inverted index: Fast fuzzy candidate filtering             │
│  └─ Priority queue: Review queue ordering                      │
│                                                                  │
│  SQL ESSENTIALS                                                 │
│  ├─ INFORMATION_SCHEMA.COLUMNS: Column metadata                │
│  ├─ COUNT(*) - COUNT(col): Null count                          │
│  ├─ COUNT(DISTINCT col): Cardinality                           │
│  └─ TOP N / LIMIT N: Sampling                                  │
│                                                                  │
│  CONFIDENCE FORMULA                                             │
│  └─ combined = (lev × 0.3) + (jw × 0.4) + (jaccard × 0.3)     │
│                                                                  │
│  TRUST THRESHOLDS (Standard)                                    │
│  ├─ ≥90%: Auto-accept                                          │
│  ├─ 70-89%: Human review                                       │
│  └─ <70%: Reject                                               │
│                                                                  │
│  KEY METRICS                                                    │
│  ├─ Auto-match rate: % auto-accepted                           │
│  ├─ Review queue size: Pending human decisions                 │
│  └─ Value bank coverage: % patterns recognized                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Practice Schedule

| Day | Focus | Time |
|-----|-------|------|
| **Day 1** | Similarity algorithms (1.1-1.4) | 2 hours |
| **Day 2** | Data structures (2.1-2.2) | 2 hours |
| **Day 3** | SQL exercises (3.1-3.5) | 1.5 hours |
| **Day 4** | System design (4.1-4.3) | 2 hours |
| **Day 5** | Code review (5.1-5.2) | 1 hour |
| **Day 6** | Whiteboard practice (6.1-6.3) | 1 hour |
| **Day 7** | Full mock interview | 2 hours |

---

*Good luck with the interview!*
