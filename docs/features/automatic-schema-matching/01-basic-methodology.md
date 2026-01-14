# Basic Methodology (Single Database)

The 3-phase approach for mapping unknown schemas when working with a single database.

---

## The 3-Phase Approach

```
┌─────────────────────────────────────────────────────────────────┐
│                    BASIC SCHEMA MATCHING                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 1              Phase 2              Phase 3               │
│  ┌──────────┐        ┌──────────┐        ┌──────────┐           │
│  │  TOKEN   │        │SIMILARITY│        │COMPOSITE │           │
│  │  SEARCH  │───────▶│ SCORING  │───────▶│ RANKING  │           │
│  └──────────┘        └──────────┘        └──────────┘           │
│                                                                  │
│  Find candidates     Score each          Rank by                 │
│  by keyword          candidate           combined score          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Token-Based Candidate Search

### Goal
Find all tables and columns that might match a requirement using keyword tokens.

### SQL Queries for Schema Exploration

#### 1. List All Schemas
```sql
SELECT DISTINCT TABLE_SCHEMA, COUNT(*) as table_count
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
GROUP BY TABLE_SCHEMA
ORDER BY table_count DESC;
```

#### 2. Find Tables by Keyword
```sql
-- Search for tables containing 'PATIENT', 'PAT', 'KART', etc.
SELECT TABLE_SCHEMA, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
  AND (TABLE_NAME LIKE '%PATIENT%'
    OR TABLE_NAME LIKE '%PAT%'
    OR TABLE_NAME LIKE '%KART%'
    OR TABLE_NAME LIKE '%KASSE%'
    OR TABLE_NAME LIKE '%LEIST%')
ORDER BY TABLE_NAME;
```

#### 3. Find Columns by Keyword
```sql
-- Search for columns containing target keywords
SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ck'  -- Target schema
  AND (COLUMN_NAME LIKE '%DATUM%'
    OR COLUMN_NAME LIKE '%DATE%'
    OR COLUMN_NAME LIKE '%PAT%'
    OR COLUMN_NAME LIKE '%KASSE%'
    OR COLUMN_NAME LIKE '%EINTRAG%'
    OR COLUMN_NAME LIKE '%BEMERK%'
    OR COLUMN_NAME LIKE '%LEIST%')
ORDER BY TABLE_NAME, COLUMN_NAME;
```

#### 4. Get All Columns for Candidate Tables
```sql
-- Once you have candidate tables, get all their columns
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE,
       CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ck'
  AND TABLE_NAME IN ('KARTEI', 'PATIENT', 'KASSEN', 'PATKASSE', 'LEISTUNG')
ORDER BY TABLE_NAME, ORDINAL_POSITION;
```

### Token Search Strategy

1. **Start broad** - Use short tokens (3-4 chars)
2. **Include variants** - German/English, abbreviations
3. **Check data types** - DATE columns, VARCHAR for text, INT for IDs
4. **Note relationships** - Columns ending in `ID`, `NR`, `KEY`

---

## Phase 2: Similarity Scoring

### Goal
Score how well each candidate matches the requirement.

### Common Algorithms

| Algorithm | Best For | Score Range |
|-----------|----------|-------------|
| **Levenshtein** | Typos, minor variations | 0.0 - 1.0 |
| **Jaro-Winkler** | Prefix matches | 0.0 - 1.0 |
| **Jaccard** | Token overlap | 0.0 - 1.0 |
| **Soundex** | Phonetic similarity | Match/No match |

### Levenshtein Distance (Edit Distance)

Counts the minimum edits (insert, delete, substitute) to transform one string into another.

```
"PATIENTID" → "PATNR"
- Delete 'I', 'E', 'N', 'T', 'I', 'D'  = 6 deletions
- Levenshtein distance = 6
- Normalized score = 1 - (6 / max(9, 5)) = 1 - 0.67 = 0.33
```

### Jaro-Winkler Similarity

Weighted toward matching prefixes (good for column names that often share prefixes).

```
"PATIENTID" vs "PATNR"
- Common prefix: "PAT" (3 chars)
- Jaro-Winkler gives bonus for matching prefix
- Score ≈ 0.65
```

### Jaccard Similarity (Token-Based)

Compares sets of tokens (words, n-grams).

```
"PATIENT_ID" tokens: {PATIENT, ID}
"PAT_NR" tokens: {PAT, NR}

Intersection: {} (no exact matches)
Union: {PATIENT, ID, PAT, NR}
Jaccard = 0 / 4 = 0.0

With substring matching:
PAT ⊂ PATIENT → partial match
Adjusted Jaccard ≈ 0.25
```

### Practical Scoring (SQL Server Example)

```sql
-- Simple substring match scoring
SELECT
    c.TABLE_NAME,
    c.COLUMN_NAME,
    'PATIENTID' as search_term,
    CASE
        WHEN c.COLUMN_NAME = 'PATIENTID' THEN 1.0
        WHEN c.COLUMN_NAME LIKE '%PATIENT%' THEN 0.8
        WHEN c.COLUMN_NAME LIKE '%PAT%' THEN 0.5
        WHEN c.COLUMN_NAME LIKE '%ID%' OR c.COLUMN_NAME LIKE '%NR%' THEN 0.3
        ELSE 0.0
    END as similarity_score
FROM INFORMATION_SCHEMA.COLUMNS c
WHERE c.TABLE_SCHEMA = 'ck'
  AND c.COLUMN_NAME LIKE '%PAT%'
ORDER BY similarity_score DESC;
```

---

## Phase 3: Composite Scoring & Ranking

### Goal
Combine multiple signals to rank candidates.

### Scoring Matrix

| Factor | Weight | Description |
|--------|--------|-------------|
| Column name similarity | 40% | How well column name matches requirement |
| Table name similarity | 30% | How well table name matches domain |
| Data type match | 20% | Expected type vs actual type |
| Context bonus | 10% | FK relationships, naming conventions |

### Composite Score Formula

```
Score = (col_sim × 0.4) + (tbl_sim × 0.3) + (type_match × 0.2) + (context × 0.1)
```

### Example Ranking

Searching for "Patient ID":

| Table | Column | Col Score | Tbl Score | Type | Context | **Total** |
|-------|--------|-----------|-----------|------|---------|-----------|
| KARTEI | PATNR | 0.5 | 0.3 | 1.0 (int) | 0.5 | **0.53** |
| LEISTUNG | PATIENTID | 1.0 | 0.2 | 1.0 (int) | 0.3 | **0.63** |
| PATIENT | ID | 0.3 | 1.0 | 1.0 (int) | 1.0 | **0.62** |

**Winner:** LEISTUNG.PATIENTID or PATIENT.ID (investigate both)

---

## Limitations of Basic Approach

| Limitation | Problem |
|------------|---------|
| **String-only matching** | `PATNR` vs `PATIENTID` scores low despite same meaning |
| **No data profiling** | Ignores the most valuable signal - actual values |
| **Single-database focus** | No learning from previous mappings |
| **Manual scoring** | Requires expert to interpret every candidate |
| **No semantic layer** | Can't understand German terms or domain context |

---

**Next:** [Advanced Methodology](02-advanced-methodology.md) - 4-phase pipeline with LLM for multi-database scenarios.
