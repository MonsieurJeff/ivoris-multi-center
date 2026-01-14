# Reference

Case study, checklists, SQL templates, and bibliography.

---

## Case Study: Ivoris Multi-Center

### The Challenge
- 487 tables in `ck` schema per center
- German column names with abbreviations
- No documentation
- 5 dental centers with slight schema variations
- Need consistent extraction across all centers

### Results with 4-Phase Approach

**Center 1 (Munich) - Manual baseline:**
- Time: 4 hours manual investigation
- Accuracy: 100% (human verified)
- Discoveries: PATKASSE junction, DELKZ flags, YYYYMMDD dates

**Center 2 (Berlin) - With learned mappings:**
- Time: 15 minutes (mostly validation)
- Auto-matched: 92% of columns
- Manual review: 8% edge cases
- New discovery: Different soft-delete column name (DELETED vs DELKZ)

**Center 3-5 - Production mode:**
- Time: 5 minutes each
- Auto-matched: 97% of columns
- Canonical schema updated with new variants

### What We Expected vs. What We Found

| Requirement | Expected | Center 1 | Center 2 | Center 3 |
|-------------|----------|----------|----------|----------|
| Schema | `dbo` | `ck` | `ck` | `dental` |
| Patient ID | `PATIENTID` | `PATNR` | `PATNR` | `PAT_NR` |
| Chart Entry | `EINTRAG` | `BEMERKUNG` | `BEMERKUNG` | `NOTIZ` |
| Soft Delete | None | `DELKZ` | `DELETED` | `DEL_FLAG` |

### Key Lessons

1. **LLM understands context** - Correctly classified `NOTIZ` as chart_note despite different name
2. **Cross-DB learning works** - Center 3+ benefited from Center 1-2 mappings
3. **Validation catches errors** - Flagged Center 2's different soft-delete column
4. **Confidence thresholds save time** - 97% auto-accepted = 97% less manual work

---

## Checklist: Multi-Database Schema Discovery

### Initial Setup
- [ ] Configure LLM client (API key, model selection)
- [ ] Initialize canonical schema with domain knowledge
- [ ] Set up database connections for all centers
- [ ] Configure confidence thresholds

### Per-Database Process

#### Phase 1: Profile
- [ ] Run schema profiler on target database
- [ ] Review profile output for anomalies
- [ ] Note any tables with unusual patterns

#### Phase 2: Classify
- [ ] Run LLM classification on all columns
- [ ] Review low-confidence classifications
- [ ] Validate German/domain term interpretations

#### Phase 3: Match
- [ ] Match against canonical schema
- [ ] Review cross-database consistency scores
- [ ] Identify new column name variants

#### Phase 4: Validate
- [ ] Run all validation tests
- [ ] Fix any blocking errors
- [ ] Review warnings
- [ ] Generate validation report

### Post-Mapping
- [ ] Store verified mappings for future use
- [ ] Update canonical schema with new discoveries
- [ ] Document center-specific quirks
- [ ] Generate extraction query

---

## Quick Reference: SQL Queries

### Find Everything About a Schema
```sql
-- Tables and row counts (approximate)
SELECT t.TABLE_NAME,
       (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS c
        WHERE c.TABLE_NAME = t.TABLE_NAME) as col_count
FROM INFORMATION_SCHEMA.TABLES t
WHERE t.TABLE_SCHEMA = 'ck' AND t.TABLE_TYPE = 'BASE TABLE'
ORDER BY t.TABLE_NAME;
```

### Find Foreign Key Relationships
```sql
SELECT
    fk.name AS FK_name,
    tp.name AS parent_table,
    cp.name AS parent_column,
    tr.name AS referenced_table,
    cr.name AS referenced_column
FROM sys.foreign_keys fk
INNER JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
INNER JOIN sys.tables tr ON fk.referenced_object_id = tr.object_id
INNER JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
INNER JOIN sys.columns cp ON fkc.parent_column_id = cp.column_id AND fkc.parent_object_id = cp.object_id
INNER JOIN sys.columns cr ON fkc.referenced_column_id = cr.column_id AND fkc.referenced_object_id = cr.object_id;
```

### Profile a Column's Values
```sql
-- See distinct values and counts
SELECT TOP 20 column_name as value, COUNT(*) as cnt
FROM schema_name.table_name
GROUP BY column_name
ORDER BY cnt DESC;
```

### Detect Date Formats
```sql
-- Check if column contains YYYYMMDD dates
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN column_name LIKE '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'
             AND LEN(column_name) = 8 THEN 1 ELSE 0 END) as yyyymmdd_count
FROM schema_name.table_name;
```

### List All Schemas
```sql
SELECT DISTINCT TABLE_SCHEMA, COUNT(*) as table_count
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
GROUP BY TABLE_SCHEMA
ORDER BY table_count DESC;
```

### Find Tables by Keyword
```sql
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

### Find Columns by Keyword
```sql
SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ck'
  AND (COLUMN_NAME LIKE '%DATUM%'
    OR COLUMN_NAME LIKE '%DATE%'
    OR COLUMN_NAME LIKE '%PAT%'
    OR COLUMN_NAME LIKE '%KASSE%'
    OR COLUMN_NAME LIKE '%EINTRAG%'
    OR COLUMN_NAME LIKE '%BEMERK%'
    OR COLUMN_NAME LIKE '%LEIST%')
ORDER BY TABLE_NAME, COLUMN_NAME;
```

---

## German Terms Reference

| German | English |
|--------|---------|
| KARTEI | Chart / Index card |
| KASSEN | Insurance companies |
| PATKASSE | Patient-Insurance link |
| LEISTUNG | Service / Procedure |
| BEMERKUNG | Remark / Note |
| PATNR | Patient number |
| ART | Type (insurance type) |
| DELKZ | Delete flag (soft delete) |
| GKV | Public health insurance |
| PKV | Private health insurance |
| Selbstzahler | Self-pay patient |
| DATUM | Date |
| EINTRAG | Entry |
| NOTIZ | Note |
| BEZEICHNUNG | Description |
| KENNZEICHEN | Identifier / Flag |

---

## References

### Academic
- **Schema Matching** - Rahm, E., & Bernstein, P. A. (2001). A survey of approaches to automatic schema matching.
- **String Similarity** - Cohen, W. W., et al. (2003). A comparison of string distance metrics for name-matching tasks.
- **Data Integration** - Doan, A., Halevy, A., & Ives, Z. (2012). Principles of Data Integration.

### LLM-Based Approaches
- **Text-to-SQL** - Leveraging LLMs for database understanding
- **Schema Linking** - Using semantic models for schema element matching
- **Few-shot Learning** - Teaching LLMs domain-specific classification with examples

### Tools
- **OpenAI/Anthropic APIs** - For LLM classification
- **Ollama/vLLM** - For local LLM deployment
- **pandas-profiling** - For automated data profiling
- **fuzzywuzzy/rapidfuzz** - For string similarity in Python
- **sentence-transformers** - For embedding-based value matching

---

*This methodology was developed through real-world schema discovery on the Ivoris dental practice management system (487+ tables, German column names, no documentation) and extended for multi-center deployments with LLM-enhanced classification.*
