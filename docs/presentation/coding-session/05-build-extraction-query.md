# Step 5: Build the Extraction Query

> **💬 Talking Points**
> - "Now we build the query step by step - not all at once"
> - "I'll show you how I approach complex queries incrementally"
> - "Each step adds one more piece until we have the full solution"

---

## Goal

Build a SQL query that extracts:
- Date, Patient ID, Insurance Status, Chart Entry, Service Codes
- For a specific date
- Output as JSON

---

## Step-by-Step Query Building

> **💬 Talking Points - Step 1**
> - "Always start simple - just the main table with the core fields"
> - "Remember: tables are in `ck` schema, dates are VARCHAR YYYYMMDD"
> - "We must filter soft-deleted rows with DELKZ"

### Step 1: Start with KARTEI (base table)

```sql
SELECT
    k.DATUM,
    k.PATNR,
    LEFT(k.BEMERKUNG, 50) AS bemerkung
FROM ck.KARTEI k
WHERE (k.DELKZ = 0 OR k.DELKZ IS NULL)
  AND k.DATUM = '20220118'
ORDER BY k.PATNR;
GO
```

**Result:**
```
DATUM     PATNR  bemerkung
--------  -----  --------------------------------------------------
20220118  1      Kontrolle,
```

**Note:** Date is stored as `'20220118'` not `'2022-01-18'`!

✅ We have date, patient ID, and chart entry (BEMERKUNG).

---

### Step 2: Format the date

> **💬 Talking Points**
> - "YYYYMMDD needs to be converted to readable format"
> - "SUBSTRING extracts parts: positions 1-4, 5-6, 7-8"
> - "This is a common pattern with legacy databases"

```sql
SELECT
    SUBSTRING(k.DATUM, 1, 4) + '-' +
    SUBSTRING(k.DATUM, 5, 2) + '-' +
    SUBSTRING(k.DATUM, 7, 2) AS date,
    k.PATNR AS patient_id,
    LEFT(k.BEMERKUNG, 50) AS chart_entry
FROM ck.KARTEI k
WHERE (k.DELKZ = 0 OR k.DELKZ IS NULL)
  AND k.DATUM = '20220118';
GO
```

**Result:**
```
date        patient_id  chart_entry
----------  ----------  --------------------------------------------------
2022-01-18  1           Kontrolle,
```

✅ Date is now formatted properly.

---

> **💬 Talking Points - PATKASSE Junction**
> - "Here's the surprise: insurance isn't on PATIENT directly"
> - "We need to go through PATKASSE - a junction table"
> - "This allows patients to have multiple insurance records over time"

### Step 3: Add insurance through PATKASSE junction

```sql
SELECT
    SUBSTRING(k.DATUM, 1, 4) + '-' +
    SUBSTRING(k.DATUM, 5, 2) + '-' +
    SUBSTRING(k.DATUM, 7, 2) AS date,
    k.PATNR AS patient_id,
    pk.KASSENID,
    LEFT(k.BEMERKUNG, 50) AS chart_entry
FROM ck.KARTEI k
JOIN ck.PATKASSE pk ON k.PATNR = pk.PATNR
    AND (pk.DELKZ = 0 OR pk.DELKZ IS NULL)
WHERE (k.DELKZ = 0 OR k.DELKZ IS NULL)
  AND k.DATUM = '20220118';
GO
```

**Result:**
```
date        patient_id  KASSENID  chart_entry
----------  ----------  --------  --------------------------------------------------
2022-01-18  1           27813     Kontrolle,
```

✅ Now we have the link to insurance (KASSENID).

---

### Step 4: Add KASSEN for insurance details

```sql
SELECT
    SUBSTRING(k.DATUM, 1, 4) + '-' +
    SUBSTRING(k.DATUM, 5, 2) + '-' +
    SUBSTRING(k.DATUM, 7, 2) AS date,
    k.PATNR AS patient_id,
    ka.ART,
    ka.NAME AS insurance_name,
    LEFT(k.BEMERKUNG, 50) AS chart_entry
FROM ck.KARTEI k
JOIN ck.PATKASSE pk ON k.PATNR = pk.PATNR
    AND (pk.DELKZ = 0 OR pk.DELKZ IS NULL)
LEFT JOIN ck.KASSEN ka ON pk.KASSENID = ka.ID
WHERE (k.DELKZ = 0 OR k.DELKZ IS NULL)
  AND k.DATUM = '20220118';
GO
```

**Result:**
```
date        patient_id  ART  insurance_name  chart_entry
----------  ----------  ---  --------------  --------------------------------------------------
2022-01-18  1           4    DAK Gesundheit  Kontrolle,
```

**Key insight:** ART='4' means GKV (public insurance), not 'G'!

---

> **💬 Talking Points - CASE Statement**
> - "The ART column uses codes, not simple G/P values"
> - "'P' = PKV (private), '1' through '9' = various GKV types"
> - "CASE transforms these to user-friendly labels"

### Step 5: Transform ART to readable status

```sql
SELECT
    SUBSTRING(k.DATUM, 1, 4) + '-' +
    SUBSTRING(k.DATUM, 5, 2) + '-' +
    SUBSTRING(k.DATUM, 7, 2) AS date,
    k.PATNR AS patient_id,
    CASE
        WHEN ka.ART = 'P' THEN 'PKV'
        WHEN ka.ART IN ('1','2','3','4','5','6','7','8','9') THEN 'GKV'
        ELSE 'Selbstzahler'
    END AS insurance_status,
    ISNULL(ka.NAME, '') AS insurance_name,
    LEFT(k.BEMERKUNG, 50) AS chart_entry
FROM ck.KARTEI k
JOIN ck.PATKASSE pk ON k.PATNR = pk.PATNR
    AND (pk.DELKZ = 0 OR pk.DELKZ IS NULL)
LEFT JOIN ck.KASSEN ka ON pk.KASSENID = ka.ID
WHERE (k.DELKZ = 0 OR k.DELKZ IS NULL)
  AND k.DATUM = '20220118';
GO
```

**Result:**
```
date        patient_id  insurance_status  insurance_name  chart_entry
----------  ----------  ----------------  --------------  --------------------------------------------------
2022-01-18  1           GKV               DAK Gesundheit  Kontrolle,
```

✅ Insurance status is now human-readable.

---

> **💬 Talking Points - Aggregation**
> - "Here's the tricky part - one visit can have multiple billing codes"
> - "STRING_AGG combines them into one comma-separated string"
> - "Watch out: LEISTUNG uses PATIENTID, but KARTEI uses PATNR!"

### Step 6: Add service codes (with aggregation)

**Problem:** Multiple services per patient per date. We need to aggregate.

```sql
-- First, let's see the services for this date
SELECT PATIENTID, DATUM, LEISTUNG
FROM ck.LEISTUNG
WHERE DATUM = '20220118'
  AND (DELKZ = 0 OR DELKZ IS NULL)
ORDER BY PATIENTID;
GO
```

**Result:**
```
PATIENTID  DATUM     LEISTUNG
---------  --------  --------

(0 rows affected)
```

**Note:** No active LEISTUNG records for this date (all are soft-deleted with DELKZ=1).
LEISTUNG uses `PATIENTID`, KARTEI uses `PATNR` - same value, different names!

**Solution:** Use subquery with STRING_AGG()

```sql
SELECT
    SUBSTRING(k.DATUM, 1, 4) + '-' +
    SUBSTRING(k.DATUM, 5, 2) + '-' +
    SUBSTRING(k.DATUM, 7, 2) AS date,
    k.PATNR AS patient_id,
    CASE
        WHEN ka.ART = 'P' THEN 'PKV'
        WHEN ka.ART IN ('1','2','3','4','5','6','7','8','9') THEN 'GKV'
        ELSE 'Selbstzahler'
    END AS insurance_status,
    ISNULL(ka.NAME, '') AS insurance_name,
    LEFT(ISNULL(k.BEMERKUNG, ''), 100) AS chart_entry,
    ISNULL((
        SELECT STRING_AGG(l.LEISTUNG, ', ')
        FROM ck.LEISTUNG l
        WHERE l.PATIENTID = k.PATNR  -- Note: PATIENTID matches PATNR!
          AND l.DATUM = k.DATUM
          AND (l.DELKZ = 0 OR l.DELKZ IS NULL)
    ), '') AS service_codes
FROM ck.KARTEI k
JOIN ck.PATKASSE pk ON k.PATNR = pk.PATNR
    AND (pk.DELKZ = 0 OR pk.DELKZ IS NULL)
LEFT JOIN ck.KASSEN ka ON pk.KASSENID = ka.ID
WHERE (k.DELKZ = 0 OR k.DELKZ IS NULL)
  AND k.DATUM = '20220118';
GO
```

**Result:**
```
date        patient_id  insurance_status  insurance_name  chart_entry                                                                       service_codes
----------  ----------  ----------------  --------------  --------------------------------------------------------------------------------  -------------
2022-01-18  1           GKV               DAK Gesundheit  Ausführliche Aufklärung über Mundhygiene und Putztechnik, Röntgenauswertung OPG
2022-01-18  1           GKV               DAK Gesundheit  Ausführliche Aufklärung über Mundhygiene und Putztechnik,
2022-01-18  1           GKV               DAK Gesundheit  Kontrolle,
2022-01-18  1           GKV               DAK Gesundheit  Kontrolle,
```

✅ All 5 required fields! (Note: service_codes is empty - all LEISTUNG records are soft-deleted in this database)

---

> **💬 Talking Points - Final Query**
> - "FOR JSON PATH turns the result into JSON directly in SQL Server"
> - "This is a SQL Server feature - not all databases have it"
> - "For portability, we'll do JSON conversion in Python instead"

## Final Query with JSON Output

### Option 1: Tabular output (for Python processing)

```sql
SELECT
    SUBSTRING(k.DATUM, 1, 4) + '-' +
    SUBSTRING(k.DATUM, 5, 2) + '-' +
    SUBSTRING(k.DATUM, 7, 2) AS date,
    k.PATNR AS patient_id,
    CASE
        WHEN ka.ART = 'P' THEN 'PKV'
        WHEN ka.ART IN ('1','2','3','4','5','6','7','8','9') THEN 'GKV'
        ELSE 'Selbstzahler'
    END AS insurance_status,
    ISNULL(ka.NAME, '') AS insurance_name,
    LEFT(ISNULL(k.BEMERKUNG, ''), 500) AS chart_entry,
    ISNULL((
        SELECT STRING_AGG(l.LEISTUNG, ', ')
        FROM ck.LEISTUNG l
        WHERE l.PATIENTID = k.PATNR
          AND l.DATUM = k.DATUM
          AND (l.DELKZ = 0 OR l.DELKZ IS NULL)
    ), '') AS service_codes
FROM ck.KARTEI k
JOIN ck.PATKASSE pk ON k.PATNR = pk.PATNR
    AND (pk.DELKZ = 0 OR pk.DELKZ IS NULL)
LEFT JOIN ck.KASSEN ka ON pk.KASSENID = ka.ID
WHERE (k.DELKZ = 0 OR k.DELKZ IS NULL)
  AND k.DATUM = '20220118'
ORDER BY k.PATNR;
GO
```

### Option 2: JSON rows (SQL Server 2016+)

```sql
SELECT
    SUBSTRING(k.DATUM, 1, 4) + '-' +
    SUBSTRING(k.DATUM, 5, 2) + '-' +
    SUBSTRING(k.DATUM, 7, 2) AS date,
    k.PATNR AS patient_id,
    CASE
        WHEN ka.ART = 'P' THEN 'PKV'
        WHEN ka.ART IN ('1','2','3','4','5','6','7','8','9') THEN 'GKV'
        ELSE 'Selbstzahler'
    END AS insurance_status,
    ISNULL(ka.NAME, '') AS insurance_name,
    LEFT(ISNULL(k.BEMERKUNG, ''), 500) AS chart_entry,
    ISNULL((
        SELECT STRING_AGG(l.LEISTUNG, ', ')
        FROM ck.LEISTUNG l
        WHERE l.PATIENTID = k.PATNR
          AND l.DATUM = k.DATUM
          AND (l.DELKZ = 0 OR l.DELKZ IS NULL)
    ), '') AS service_codes
FROM ck.KARTEI k
JOIN ck.PATKASSE pk ON k.PATNR = pk.PATNR
    AND (pk.DELKZ = 0 OR pk.DELKZ IS NULL)
LEFT JOIN ck.KASSEN ka ON pk.KASSENID = ka.ID
WHERE (k.DELKZ = 0 OR k.DELKZ IS NULL)
  AND k.DATUM = '20220118'
FOR JSON PATH;
GO
```

**Output:**
```json
[
  {
    "date": "2022-01-18",
    "patient_id": 1,
    "insurance_status": "GKV",
    "insurance_name": "DAK Gesundheit",
    "chart_entry": "Ausführliche Aufklärung über Mundhygiene und Putztechnik, Röntgenauswertung OPG",
    "service_codes": ""
  },
  {
    "date": "2022-01-18",
    "patient_id": 1,
    "insurance_status": "GKV",
    "insurance_name": "DAK Gesundheit",
    "chart_entry": "Kontrolle,",
    "service_codes": ""
  }
]
```

---

## Python Implementation

```python
import pyodbc
import json
from datetime import date

def extract_daily_entries(target_date: date) -> list:
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=DentalDB;"
        "UID=sa;PWD=YourStrong@Passw0rd;"
        "TrustServerCertificate=yes"
    )

    # Convert date to YYYYMMDD format for query
    date_str = target_date.strftime('%Y%m%d')

    query = """
    SELECT
        SUBSTRING(k.DATUM, 1, 4) + '-' +
        SUBSTRING(k.DATUM, 5, 2) + '-' +
        SUBSTRING(k.DATUM, 7, 2) AS date,
        k.PATNR AS patient_id,
        CASE
            WHEN ka.ART = 'P' THEN 'PKV'
            WHEN ka.ART IN ('1','2','3','4','5','6','7','8','9') THEN 'GKV'
            ELSE 'Selbstzahler'
        END AS insurance_status,
        ISNULL(ka.NAME, '') AS insurance_name,
        LEFT(ISNULL(k.BEMERKUNG, ''), 500) AS chart_entry,
        ISNULL((
            SELECT STRING_AGG(l.LEISTUNG, ', ')
            FROM ck.LEISTUNG l
            WHERE l.PATIENTID = k.PATNR
              AND l.DATUM = k.DATUM
              AND (l.DELKZ = 0 OR l.DELKZ IS NULL)
        ), '') AS service_codes
    FROM ck.KARTEI k
    JOIN ck.PATKASSE pk ON k.PATNR = pk.PATNR
        AND (pk.DELKZ = 0 OR pk.DELKZ IS NULL)
    LEFT JOIN ck.KASSEN ka ON pk.KASSENID = ka.ID
    WHERE (k.DELKZ = 0 OR k.DELKZ IS NULL)
      AND k.DATUM = ?
    ORDER BY k.PATNR
    """

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute(query, date_str)

    entries = []
    for row in cursor.fetchall():
        entries.append({
            "date": row.date,
            "patient_id": row.patient_id,
            "insurance_status": row.insurance_status,
            "insurance_name": row.insurance_name,
            "chart_entry": row.chart_entry,
            "service_codes": row.service_codes.split(", ") if row.service_codes else []
        })

    cursor.close()
    conn.close()

    return entries


# Usage
if __name__ == "__main__":
    entries = extract_daily_entries(date(2022, 1, 18))
    print(json.dumps(entries, indent=2, ensure_ascii=False))
```

---

## Save to File

```python
from datetime import datetime

def save_output(entries: list, target_date: date, format: str = "json"):
    filename = f"ivoris_chart_entries_{target_date.isoformat()}.{format}"

    if format == "json":
        output = {
            "extraction_timestamp": datetime.now().isoformat(),
            "target_date": target_date.isoformat(),
            "record_count": len(entries),
            "entries": entries
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

    elif format == "csv":
        import csv
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "patient_id", "insurance_status",
                           "insurance_name", "chart_entry", "service_codes"])
            for e in entries:
                writer.writerow([
                    e["date"], e["patient_id"], e["insurance_status"],
                    e["insurance_name"], e["chart_entry"],
                    ", ".join(e["service_codes"])
                ])

    print(f"Saved {len(entries)} entries to {filename}")
```

---

## Key Schema Differences (What We Discovered)

| Expected | Actual | Notes |
|----------|--------|-------|
| `dbo` schema | `ck` schema | All tables in `ck.*` |
| `PATIENTID` | `PATNR` | In KARTEI and PATKASSE |
| `EINTRAG` | `BEMERKUNG` | Chart entry column |
| `KASSE.TYP` | `KASSEN.ART` | Different table AND column |
| `TYP = 'G'/'P'` | `ART = '1'-'9'/'P'` | Numbers for GKV types |
| Direct PATIENT→KASSE | PATKASSE junction | Extra table needed |
| DATE type | VARCHAR(8) | YYYYMMDD strings |
| No soft delete | `DELKZ` flag | Must filter everywhere |

---

## Next Step

→ [05b-extraction-script.md](./05b-extraction-script.md) - Create Python script for CSV/JSON output
