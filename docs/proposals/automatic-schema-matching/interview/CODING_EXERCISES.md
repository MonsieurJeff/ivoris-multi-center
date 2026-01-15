# Coding Exercises: Interview Preparation

**Purpose:** Practice problems for schema matching / scalability interviews
**Level:** Senior Engineer / Tech Lead

---

## Philosophy: Senior-Level Approach

> "We used to search StackOverflow. Now we use LLMs. The skill isn't memorizing algorithms—it's knowing **when** to use them, **evaluating** suggestions critically, and **integrating** them correctly."

### What Senior Interviews Actually Test

| Junior Approach | Senior Approach |
|-----------------|-----------------|
| "Implement Levenshtein from scratch" | "Which similarity algorithm fits this use case?" |
| Memorize syntax | Evaluate trade-offs |
| Write code in isolation | Integrate with existing systems |
| Pass test cases | Defend architectural decisions |

### How to Use This Document

1. **Understand the algorithms** - Know what they do, not how to code them from memory
2. **Know the trade-offs** - When to use Levenshtein vs Jaro-Winkler vs Jaccard
3. **Evaluate LLM output** - The solutions below are what an LLM might generate; know how to verify them
4. **Focus on integration** - How would you plug this into a production system?

### Interview Talking Point

> "I'd ask an LLM for the implementation, then verify it handles edge cases, check the complexity matches our scale requirements, and ensure it integrates with our existing patterns. The value I bring is knowing *which* algorithm to request and *how* to validate the result."

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

### When to Use What (Decision Framework)

| Algorithm | Best For | Weakness | Use When |
|-----------|----------|----------|----------|
| **Levenshtein** | Typos, small edits | Slow on long strings | Short identifiers (PATNR → PAT_NR) |
| **Jaro-Winkler** | Prefix matching | Less intuitive scoring | Abbreviations (PAT → PATIENT) |
| **Jaccard** | Token overlap | Ignores order | Compound names (BIRTH_DATE → DATE_OF_BIRTH) |
| **Soundex/Metaphone** | Phonetic similarity | English-centric | Names that sound alike |
| **TF-IDF + Cosine** | Document similarity | Overkill for short strings | Long descriptions |

### Senior Interview Question

> "We need to match German column names like PATNR to PATIENTENNUMMER. Which algorithm would you choose and why?"

**Your answer:** "I'd use a **weighted combination**:
- Jaro-Winkler (40%) - catches the PAT prefix match
- Jaccard on tokens (30%) - catches shared tokens after splitting
- Levenshtein (30%) - catches overall similarity

I'd ask an LLM to generate the implementations, then validate against test cases from our actual data."

---

### Exercise 1.1: Algorithm Selection (Not Implementation)

**Scenario:** You're building a column name matcher. An LLM gives you these three functions. Your job: **evaluate which to use when**.

```python
# LLM-generated code - your job is to EVALUATE, not write from scratch
```

<details>
<summary>LLM-Generated: Levenshtein (click to review)</summary>

```python
def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate edit distance between two strings.
    Time: O(m*n), Space: O(min(m,n))
    """
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    m, n = len(s1), len(s2)
    prev = list(range(m + 1))
    curr = [0] * (m + 1)

    for j in range(1, n + 1):
        curr[0] = j
        for i in range(1, m + 1):
            if s1[i-1] == s2[j-1]:
                curr[i] = prev[i-1]
            else:
                curr[i] = 1 + min(prev[i], curr[i-1], prev[i-1])
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

**Evaluation checklist:**
- ✅ Space-optimized (two rows instead of full matrix)
- ✅ Handles empty strings
- ✅ Returns normalized 0-1 score
- ⚠️ O(m×n) - may be slow for very long strings (but column names are short)
- ✅ Suitable for our use case

</details>

<details>
<summary>LLM-Generated: Jaro-Winkler (click to review)</summary>

```python
def jaro_similarity(s1: str, s2: str) -> float:
    """Calculate base Jaro similarity."""
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    len1, len2 = len(s1), len(s2)
    match_distance = max(len1, len2) // 2 - 1
    match_distance = max(0, match_distance)

    s1_matches = [False] * len1
    s2_matches = [False] * len2
    matches = 0
    transpositions = 0

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

    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    return (matches/len1 + matches/len2 + (matches - transpositions/2)/matches) / 3

def jaro_winkler(s1: str, s2: str, prefix_weight: float = 0.1) -> float:
    """Jaro-Winkler: boosts score for common prefixes."""
    jaro = jaro_similarity(s1, s2)
    prefix_len = 0
    for i in range(min(len(s1), len(s2), 4)):
        if s1[i] == s2[i]:
            prefix_len += 1
        else:
            break
    return jaro + prefix_len * prefix_weight * (1 - jaro)
```

**Evaluation checklist:**
- ✅ Handles edge cases (empty, identical)
- ✅ Prefix boost capped at 4 characters (standard)
- ✅ Returns 0-1 score
- ⚠️ More complex than Levenshtein - verify with test cases
- ✅ Good for abbreviations (PAT → PATIENT)

</details>

<details>
<summary>LLM-Generated: Jaccard on Tokens (click to review)</summary>

```python
import re

def tokenize(s: str) -> set:
    """Split column name into tokens."""
    tokens = re.split(r'[_\s]+', s)
    expanded = []
    for token in tokens:
        parts = re.split(r'(?<=[a-z])(?=[A-Z])', token)
        expanded.extend(parts)
    return {t.lower() for t in expanded if t}

def jaccard_similarity(s1: str, s2: str) -> float:
    """Jaccard: |intersection| / |union| of token sets."""
    tokens1 = tokenize(s1)
    tokens2 = tokenize(s2)

    if not tokens1 and not tokens2:
        return 1.0
    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    return len(intersection) / len(union)
```

**Evaluation checklist:**
- ✅ Handles snake_case, camelCase, PascalCase
- ✅ Case-insensitive
- ✅ Returns 0-1 score
- ⚠️ Ignores token order (DATE_OF_BIRTH = BIRTH_DATE_OF)
- ✅ Good for reordered compound names

</details>

---

### Exercise 1.2: Integration Decision

**Question:** How would you combine these in production?

<details>
<summary>Senior Answer</summary>

```python
def combined_similarity(s1: str, s2: str) -> dict:
    """
    Production integration: weighted combination of algorithms.

    Weights tuned for German column names based on our data analysis.
    """
    # Normalize once
    s1_norm = s1.upper().strip()
    s2_norm = s2.upper().strip()

    # Get individual scores
    lev = levenshtein_similarity(s1_norm, s2_norm)
    jw = jaro_winkler(s1_norm, s2_norm)
    jac = jaccard_similarity(s1_norm, s2_norm)

    # Weighted combination (tuned for our domain)
    combined = (lev * 0.30) + (jw * 0.40) + (jac * 0.30)

    return {
        'combined': round(combined, 3),
        'components': {'levenshtein': lev, 'jaro_winkler': jw, 'jaccard': jac},
        'recommendation': 'match' if combined >= 0.75 else 'review' if combined >= 0.60 else 'no_match'
    }
```

**Why this approach:**
1. **Jaro-Winkler weighted highest** - Our data has many abbreviations (PAT, GEB, VERS)
2. **Threshold at 0.75** - Based on false positive analysis of our 15 databases
3. **Return components** - For explainability in review queue

**What I'd tell the interviewer:**
> "I wouldn't implement these from scratch. I'd use `jellyfish` or `rapidfuzz` libraries in production—they're optimized in C. But I need to understand the algorithms to choose the right weights and thresholds."

</details>

---

### Key Points to Remember

| Point | What to Say |
|-------|-------------|
| **Don't memorize** | "I'd generate this with an LLM and verify it" |
| **Know trade-offs** | "Levenshtein is O(n²), Jaro-Winkler handles prefixes better" |
| **Use libraries** | "In production I'd use `rapidfuzz` for performance" |
| **Tune weights** | "Weights come from analyzing our actual data" |
| **Explain choices** | "Jaro-Winkler is weighted higher because of German abbreviations" |

---

### Production Libraries (What You'd Actually Use)

In production, don't implement these yourself. Use battle-tested libraries:

```python
# Python - Production Choice
from rapidfuzz import fuzz, distance

# Fast, C-optimized implementations
fuzz.ratio("PATNR", "PATIENT_NR")           # Levenshtein-based
fuzz.partial_ratio("PAT", "PATIENT")        # Partial matching
fuzz.token_sort_ratio("A B C", "C B A")     # Token-based

# Alternative: jellyfish (pure Python, simpler API)
import jellyfish
jellyfish.levenshtein_distance("PATNR", "PATIENT_NR")
jellyfish.jaro_winkler_similarity("PATNR", "PATIENT_NR")
```

**Interview talking point:**
> "I'd use `rapidfuzz` in production—it's C-optimized and handles edge cases. I know the algorithms well enough to choose the right one and tune the thresholds, but I'm not going to hand-roll Levenshtein when a library does it 100x faster."

---

## 2. Data Structure Design

### Senior Approach: Design Discussions, Not Implementations

Data structure questions at the senior level are about **trade-off discussions**, not whiteboard coding:

| They Ask | You Discuss |
|----------|-------------|
| "Design a data structure for X" | Storage vs speed trade-offs, what scales |
| "How would you implement this?" | Existing solutions, when to build vs buy |
| "What's the complexity?" | Why it matters for our scale, where bottlenecks are |

---

### Exercise 2.1: Value Bank Design Discussion

**Scenario:** You need to store 10,000 learned column name variants and look them up efficiently.

**Senior Question:** "Walk me through your design decisions."

<details>
<summary>How to Answer</summary>

**Step 1: Clarify Requirements**
> "Before I design, let me understand: How many lookups per second? How often do we add new variants? Is memory constrained?"

**Step 2: Discuss Trade-offs**

| Approach | Pros | Cons | When to Use |
|----------|------|------|-------------|
| **HashMap** | O(1) exact lookup | No fuzzy matching | Exact matches only |
| **Trie** | Prefix search | Memory overhead | Autocomplete use case |
| **Inverted Index** | Fast candidate filtering | Extra storage | When fuzzy is common |
| **Vector DB** | Semantic similarity | Overkill, latency | Huge datasets |

**Step 3: Propose Solution**
> "For 10K variants, I'd use a HashMap for exact matches plus an inverted token index for fuzzy candidate filtering. The token index reduces fuzzy search from O(n) to O(candidates)."

**Step 4: Acknowledge Alternatives**
> "If we're at 1M variants, I'd consider a vector database. But for our scale, in-memory structures are fine."

</details>

---

### Reference Implementation (LLM-Generated)

**Context:** This is what you'd get from an LLM. Know how to **evaluate** it, not memorize it.

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
│               SENIOR INTERVIEW QUICK REFERENCE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MINDSET                                                        │
│  ├─ "I'd use an LLM to generate, then verify and integrate"    │
│  ├─ "Let me discuss the trade-offs first"                      │
│  └─ "In production, I'd use [library] because..."              │
│                                                                  │
│  ALGORITHM SELECTION (Know When, Not How)                       │
│  ├─ Levenshtein: Typos, short strings → use `rapidfuzz`        │
│  ├─ Jaro-Winkler: Abbreviations, prefixes matter               │
│  ├─ Jaccard: Compound names, order doesn't matter              │
│  └─ Combined: Weight based on YOUR data analysis               │
│                                                                  │
│  SCALABILITY PATTERNS                                           │
│  ├─ Async: Job queue (Redis/Celery), don't block API           │
│  ├─ Parallel: Workers process tables/columns concurrently      │
│  ├─ Caching: Load value bank once, reuse across requests       │
│  └─ Pooling: Connection pools, not new connections per query   │
│                                                                  │
│  DESIGN DISCUSSION FRAMEWORK                                    │
│  ├─ 1. Clarify requirements (scale, constraints)               │
│  ├─ 2. Discuss trade-offs (not just one solution)              │
│  ├─ 3. Propose with rationale                                  │
│  └─ 4. Acknowledge alternatives and when they'd be better      │
│                                                                  │
│  TRUST THRESHOLDS (Configurable, Not Hardcoded)                │
│  ├─ Conservative: 99% auto-accept (new client, critical)       │
│  ├─ Standard: 90% auto-accept, 70% review threshold            │
│  └─ Permissive: 80% auto-accept (demos, trusted schemas)       │
│                                                                  │
│  KEY LIBRARIES (Don't Reinvent)                                │
│  ├─ rapidfuzz: Fast fuzzy matching (C-optimized)               │
│  ├─ jellyfish: Simple Python fuzzy matching                    │
│  ├─ SQLAlchemy: DB connections, pooling, ORM                   │
│  └─ Celery/Redis: Async job processing                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Preparation Approach

### What to Focus On

| Priority | Focus | Why |
|----------|-------|-----|
| **High** | Trade-off discussions | Senior interviews test judgment |
| **High** | System design whiteboarding | Draw architecture, explain decisions |
| **Medium** | SQL schema discovery | Quick wins, shows practical knowledge |
| **Medium** | Code review skills | Spot scalability issues |
| **Low** | Algorithm implementation | Use LLMs, know when to apply |

### Key Questions to Prepare

1. **"How would you scale this to 1000 clients?"**
   - Async processing, value bank learning, parallel workers

2. **"What happens when the algorithm is wrong?"**
   - Trust profiles, human review, audit trail

3. **"Why this algorithm over alternatives?"**
   - Data-driven: "We analyzed our 15 databases and found..."

4. **"Walk me through the architecture."**
   - Draw it: API → Queue → Workers → DB
   - Explain each decision

### Day Before Interview

1. Review TECHNICAL_SOLUTION.md - know your architecture
2. Practice drawing the system diagram (5 min max)
3. Prepare 2-3 questions to ask THEM about their rewrite challenges
4. Remember: You're not a junior being tested. You're a senior discussing solutions.

---

*You've built real systems. You've worked with real databases. Show that experience.*
