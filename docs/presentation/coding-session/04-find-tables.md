# Step 4: Find the Right Tables

> **💬 Talking Points**
> - "Now we map the business requirements to actual database columns"
> - "This is where domain knowledge meets technical knowledge"
> - "The customer said 'Versicherungsstatus' - we need to find where that lives"

---

## The Requirement

Extract these 5 fields daily:

| # | German | English | We need to find... |
|---|--------|---------|-------------------|
| 1 | Datum | Date | Date of chart entry |
| 2 | Pat-ID | Patient ID | Patient identifier |
| 3 | Versicherungsstatus | Insurance Status | GKV/PKV/Selbstzahler |
| 4 | Karteikarteneintrag | Chart Entry | Medical notes |
| 5 | Leistungen (Ziffern) | Services | Treatment codes |

---

## Mapping Requirements to Real Schema

### Field 1: Datum (Date)

```sql
-- Which tables have date-like columns?
SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ck'
  AND (COLUMN_NAME LIKE '%DATUM%' OR COLUMN_NAME LIKE '%DATE%')
ORDER BY TABLE_NAME;
GO
```

**Found:** `ck.KARTEI.DATUM` (VARCHAR 8, format YYYYMMDD)

**Important:** Need to convert from `'20220118'` to `'2022-01-18'`

---

### Field 2: Pat-ID (Patient ID)

```sql
-- Where is patient ID referenced?
SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ck'
  AND (COLUMN_NAME LIKE '%PAT%' OR COLUMN_NAME = 'ID')
  AND TABLE_NAME IN ('KARTEI', 'PATIENT', 'LEISTUNG', 'PATKASSE')
ORDER BY TABLE_NAME, COLUMN_NAME;
GO
```

**Found:**
- `ck.KARTEI.PATNR` → references patient
- `ck.PATIENT.ID` → patient primary key
- `ck.LEISTUNG.PATIENTID` → references patient (different name!)

**Decision:** Use `ck.KARTEI.PATNR` as our patient_id

---

> **💬 Talking Points - Insurance Status**
> - "This is the interesting one - insurance status requires TWO joins"
> - "GKV = public insurance, PKV = private insurance, NULL = self-pay"
> - "The ART column uses codes, not simple G/P values"

### Field 3: Versicherungsstatus (Insurance Status)

```sql
-- Look at insurance type distribution
SELECT ART, COUNT(*) as cnt
FROM ck.KASSEN
WHERE DELKZ = 0 OR DELKZ IS NULL
GROUP BY ART
ORDER BY cnt DESC;
GO
```

**ART values discovered:**
- `'P'` = PKV (Private insurance) - 54 records
- `'1'` to `'9'` = Various GKV types (public insurance) - ~30,000 records
- Other codes (B, C, D, etc.) = Special cases

**Path to insurance:**
```
ck.KARTEI.PATNR → ck.PATKASSE.PATNR
ck.PATKASSE.KASSENID → ck.KASSEN.ID
ck.KASSEN.ART → Insurance type code
```

**Decision:**
- `ART = 'P'` → PKV
- `ART IN ('1'-'9')` → GKV
- `NULL` or no match → Selbstzahler

---

### Field 4: Karteikarteneintrag (Chart Entry)

```sql
-- Find the text column in KARTEI
SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ck' AND TABLE_NAME = 'KARTEI'
  AND DATA_TYPE IN ('varchar', 'nvarchar', 'text')
  AND (CHARACTER_MAXIMUM_LENGTH > 100 OR CHARACTER_MAXIMUM_LENGTH = -1);
GO
```

**Found:** `ck.KARTEI.BEMERKUNG` (varchar MAX)

**Note:** Column is called `BEMERKUNG` (remark), not `EINTRAG` (entry)!

---

> **💬 Talking Points - Service Codes**
> - "One patient visit can have multiple services - we need aggregation"
> - "STRING_AGG combines them into one comma-separated string"
> - "Watch out: LEISTUNG uses PATIENTID, but KARTEI uses PATNR"

### Field 5: Leistungen (Service Codes)

```sql
-- Sample service codes
SELECT TOP 10 PATIENTID, DATUM, LEISTUNG
FROM ck.LEISTUNG
WHERE (DELKZ = 0 OR DELKZ IS NULL)
ORDER BY DATUM DESC;
GO
```

**Found:** `ck.LEISTUNG.LEISTUNG` contains codes like '01', '1040', 'Ä935'

**Challenge:** Multiple services per patient per date - need `STRING_AGG()`

**Join condition:**
```sql
WHERE l.PATIENTID = k.PATNR  -- Note: different column names!
  AND l.DATUM = k.DATUM
```

---

## Summary: Real Schema Mapping

| Requirement | Real Source | Notes |
|-------------|-------------|-------|
| Datum | `ck.KARTEI.DATUM` | VARCHAR(8), needs formatting |
| Pat-ID | `ck.KARTEI.PATNR` | INT |
| Versicherungsstatus | `ck.KASSEN.ART` via PATKASSE | 'P'=PKV, 1-9=GKV |
| Karteikarteneintrag | `ck.KARTEI.BEMERKUNG` | VARCHAR(MAX) |
| Leistungen | `ck.LEISTUNG.LEISTUNG` | Aggregated with STRING_AGG |

---

> **💬 Talking Points - JOIN Strategy**
> - "KARTEI is our starting point - that's where the chart entries are"
> - "We need PATKASSE as a bridge to get insurance info"
> - "LEFT JOINs preserve entries even if no insurance or services"

## Join Path (Real Schema)

```
ck.KARTEI (main table)
  │
  ├── JOIN ck.PATKASSE ON KARTEI.PATNR = PATKASSE.PATNR
  │     │
  │     └── LEFT JOIN ck.KASSEN ON PATKASSE.KASSENID = KASSEN.ID
  │
  └── Subquery: ck.LEISTUNG WHERE PATIENTID = KARTEI.PATNR AND DATUM = KARTEI.DATUM
```

**Why PATKASSE junction?**
- Patient can have multiple insurance records over time
- Links patient to their current insurance

**Why LEFT JOINs?**
- Some patients may have no insurance (Selbstzahler)
- Some chart entries may have no services
- We still want those entries in output

---

## Insurance Status Logic

```sql
CASE
    WHEN ka.ART = 'P' THEN 'PKV'
    WHEN ka.ART IN ('1','2','3','4','5','6','7','8','9') THEN 'GKV'
    ELSE 'Selbstzahler'
END AS insurance_status
```

---

## Date Formatting Logic

```sql
-- Convert YYYYMMDD to YYYY-MM-DD
SUBSTRING(k.DATUM, 1, 4) + '-' +
SUBSTRING(k.DATUM, 5, 2) + '-' +
SUBSTRING(k.DATUM, 7, 2) AS date
```

---

## Don't Forget: Soft Delete Filter!

Every query must include:
```sql
WHERE (DELKZ = 0 OR DELKZ IS NULL)
```

---

## Next Step

→ [05-build-extraction-query.md](./05-build-extraction-query.md) - Build the complete SQL query
