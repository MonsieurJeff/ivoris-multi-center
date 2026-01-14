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

## Mapping Requirements to Tables

### Field 1: Datum (Date)

**Search:** Which tables have a date column?

```sql
SELECT TABLE_NAME, COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE DATA_TYPE = 'date'
ORDER BY TABLE_NAME;
GO
```

**Result:**
```
TABLE_NAME  COLUMN_NAME
----------  -----------
KARTEI      DATUM         ← Chart entry date
LEISTUNG    DATUM         ← Service date
PATIENT     GEBDAT        ← Birth date (not relevant)
```

**Decision:** Use `KARTEI.DATUM` - the date of the chart entry.

---

### Field 2: Pat-ID (Patient ID)

**Search:** Which tables have PATIENTID?

```sql
SELECT TABLE_NAME, COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE COLUMN_NAME LIKE '%PATIENT%'
ORDER BY TABLE_NAME;
GO
```

**Result:**
```
TABLE_NAME  COLUMN_NAME
----------  -----------
KARTEI      PATIENTID
LEISTUNG    PATIENTID
PATIENT     PATIENTID
```

**Decision:** Use `KARTEI.PATIENTID` - directly from the chart entry.

---

> **💬 Talking Points - Insurance Status**
> - "This is the interesting one - insurance status requires a JOIN"
> - "GKV = public insurance, PKV = private insurance, NULL = self-pay"
> - "Understanding German healthcare system helps here"

### Field 3: Versicherungsstatus (Insurance Status)

**Search:** Where is insurance information?

```sql
-- Look at KASSE table
SELECT * FROM KASSE;
GO
```

**Result:**
```
KASSEID  NAME                   TYP
-------  ---------------------  ---
1        AOK Bayern             G
2        DAK Gesundheit         G
3        Techniker Krankenkasse G
4        PRIVAT                 P
5        Debeka                 P
```

**TYP values:**
- `G` = GKV (Gesetzliche Krankenversicherung) - Public
- `P` = PKV (Private Krankenversicherung) - Private
- `NULL` = Selbstzahler (Self-payer)

**Path to insurance:**
```
KARTEI.PATIENTID → PATIENT.PATIENTID
PATIENT.KASSEID → KASSE.KASSEID
KASSE.TYP → Insurance type
```

**Decision:** Join KARTEI → PATIENT → KASSE, use `KASSE.TYP`

---

### Field 4: Karteikarteneintrag (Chart Entry)

**Search:** Which column contains medical notes?

```sql
SELECT TOP 3 EINTRAG FROM KARTEI;
GO
```

**Result:**
```
EINTRAG
-----------------------------------------
Kontrolle, Befund unauffällig
Zahnreinigung durchgeführt
Füllungstherapie Zahn 36
```

**Decision:** Use `KARTEI.EINTRAG`

---

> **💬 Talking Points - Service Codes**
> - "One patient visit can have multiple services - we need aggregation"
> - "STRING_AGG is like Python's ', '.join() - concatenates values"
> - "This is the trickiest part of the query"

### Field 5: Leistungen (Service Codes)

**Search:** Where are service codes?

```sql
SELECT TOP 5 * FROM LEISTUNG;
GO
```

**Result:**
```
LEISTUNGID  PATIENTID  DATUM       LEISTUNG
----------  ---------  ----------  --------
1           1          2022-01-18  01
2           1          2022-01-18  1040
3           2          2022-01-18  13b
4           3          2022-01-18  Ä935
```

**Challenge:** One chart entry can have multiple services.

```sql
-- Count services per patient per date
SELECT PATIENTID, DATUM, COUNT(*) as SERVICE_COUNT
FROM LEISTUNG
GROUP BY PATIENTID, DATUM
ORDER BY PATIENTID, DATUM;
GO
```

**Result:**
```
PATIENTID  DATUM       SERVICE_COUNT
---------  ----------  -------------
1          2022-01-18  2
2          2022-01-18  1
3          2022-01-18  1
```

**Decision:** Aggregate services into comma-separated list using `STRING_AGG()`

---

## Summary: Table Mapping

| Requirement | Source |
|-------------|--------|
| Datum | `KARTEI.DATUM` |
| Pat-ID | `KARTEI.PATIENTID` |
| Versicherungsstatus | `KASSE.TYP` (via PATIENT) |
| Karteikarteneintrag | `KARTEI.EINTRAG` |
| Leistungen | `LEISTUNG.LEISTUNG` (aggregated) |

---

> **💬 Talking Points - JOIN Strategy**
> - "KARTEI is our starting point - that's where the chart entries are"
> - "LEFT JOIN preserves all chart entries even if no insurance or services"
> - "This is a 3-table JOIN plus a correlated subquery"

## Join Path

```
KARTEI (main table)
  ├── JOIN PATIENT ON KARTEI.PATIENTID = PATIENT.PATIENTID
  │     └── LEFT JOIN KASSE ON PATIENT.KASSEID = KASSE.KASSEID
  └── LEFT JOIN LEISTUNG ON KARTEI.PATIENTID = LEISTUNG.PATIENTID
                        AND KARTEI.DATUM = LEISTUNG.DATUM
```

**Why LEFT JOIN for KASSE?**
- Some patients may have no insurance (Selbstzahler)
- We don't want to lose those records

**Why LEFT JOIN for LEISTUNG?**
- Some chart entries may have no services
- We still want those entries in output

---

## Insurance Status Logic

```sql
CASE KASSE.TYP
    WHEN 'G' THEN 'GKV'
    WHEN 'P' THEN 'PKV'
    ELSE 'Selbstzahler'
END AS insurance_status
```

---

## Next Step

→ [05-build-extraction-query.md](./05-build-extraction-query.md) - Build the complete SQL query
