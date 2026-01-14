# Step 5: Build the Extraction Query

## Goal

Build a SQL query that extracts:
- Date, Patient ID, Insurance Status, Chart Entry, Service Codes
- For a specific date
- Output as JSON

---

## Step-by-Step Query Building

### Step 1: Start with KARTEI (base table)

```sql
SELECT
    k.DATUM,
    k.PATIENTID,
    k.EINTRAG
FROM KARTEI k
WHERE k.DATUM = '2022-01-18';
GO
```

**Result:**
```
DATUM       PATIENTID  EINTRAG
----------  ---------  ----------------------------------
2022-01-18  1          Kontrolle, Befund unauffällig
2022-01-18  1          Zahnreinigung durchgeführt
2022-01-18  2          Füllungstherapie Zahn 36
2022-01-18  3          Röntgenaufnahme OPG
2022-01-18  4          Beratung Zahnersatz
2022-01-18  5          Professionelle Zahnreinigung
```

✅ We have date, patient ID, and chart entry.

---

### Step 2: Add PATIENT (for insurance link)

```sql
SELECT
    k.DATUM,
    k.PATIENTID,
    p.NAME,
    p.KASSEID,
    k.EINTRAG
FROM KARTEI k
JOIN PATIENT p ON k.PATIENTID = p.PATIENTID
WHERE k.DATUM = '2022-01-18';
GO
```

**Result:**
```
DATUM       PATIENTID  NAME      KASSEID  EINTRAG
----------  ---------  --------  -------  ----------------------------------
2022-01-18  1          Müller    1        Kontrolle, Befund unauffällig
2022-01-18  1          Müller    1        Zahnreinigung durchgeführt
2022-01-18  2          Schmidt   2        Füllungstherapie Zahn 36
...
```

✅ Now we have the link to insurance (KASSEID).

---

### Step 3: Add KASSE (for insurance status)

```sql
SELECT
    k.DATUM,
    k.PATIENTID,
    ka.TYP,
    ka.NAME AS insurance_name,
    k.EINTRAG
FROM KARTEI k
JOIN PATIENT p ON k.PATIENTID = p.PATIENTID
LEFT JOIN KASSE ka ON p.KASSEID = ka.KASSEID
WHERE k.DATUM = '2022-01-18';
GO
```

**Result:**
```
DATUM       PATIENTID  TYP  insurance_name          EINTRAG
----------  ---------  ---  ----------------------  ----------------------------------
2022-01-18  1          G    AOK Bayern              Kontrolle, Befund unauffällig
2022-01-18  1          G    AOK Bayern              Zahnreinigung durchgeführt
2022-01-18  2          G    DAK Gesundheit          Füllungstherapie Zahn 36
2022-01-18  3          G    Techniker Krankenkasse  Röntgenaufnahme OPG
2022-01-18  4          P    PRIVAT                  Beratung Zahnersatz
2022-01-18  5          G    Barmer                  Professionelle Zahnreinigung
```

✅ Now we have insurance type (G/P).

---

### Step 4: Transform TYP to readable status

```sql
SELECT
    k.DATUM AS date,
    k.PATIENTID AS patient_id,
    CASE ka.TYP
        WHEN 'G' THEN 'GKV'
        WHEN 'P' THEN 'PKV'
        ELSE 'Selbstzahler'
    END AS insurance_status,
    ka.NAME AS insurance_name,
    k.EINTRAG AS chart_entry
FROM KARTEI k
JOIN PATIENT p ON k.PATIENTID = p.PATIENTID
LEFT JOIN KASSE ka ON p.KASSEID = ka.KASSEID
WHERE k.DATUM = '2022-01-18';
GO
```

**Result:**
```
date        patient_id  insurance_status  insurance_name          chart_entry
----------  ----------  ----------------  ----------------------  ----------------------------------
2022-01-18  1           GKV               AOK Bayern              Kontrolle, Befund unauffällig
2022-01-18  1           GKV               AOK Bayern              Zahnreinigung durchgeführt
2022-01-18  2           GKV               DAK Gesundheit          Füllungstherapie Zahn 36
2022-01-18  3           GKV               Techniker Krankenkasse  Röntgenaufnahme OPG
2022-01-18  4           PKV               PRIVAT                  Beratung Zahnersatz
2022-01-18  5           GKV               Barmer                  Professionelle Zahnreinigung
```

✅ Insurance status is now human-readable.

---

### Step 5: Add service codes (with aggregation)

**Problem:** Multiple services per patient per date. We need to aggregate.

```sql
-- First, let's see the services
SELECT PATIENTID, DATUM, LEISTUNG
FROM LEISTUNG
WHERE DATUM = '2022-01-18'
ORDER BY PATIENTID;
GO
```

**Result:**
```
PATIENTID  DATUM       LEISTUNG
---------  ----------  --------
1          2022-01-18  01
1          2022-01-18  1040
2          2022-01-18  13b
3          2022-01-18  Ä935
```

**Solution:** Use subquery with STRING_AGG()

```sql
SELECT
    k.DATUM AS date,
    k.PATIENTID AS patient_id,
    CASE ka.TYP
        WHEN 'G' THEN 'GKV'
        WHEN 'P' THEN 'PKV'
        ELSE 'Selbstzahler'
    END AS insurance_status,
    ka.NAME AS insurance_name,
    k.EINTRAG AS chart_entry,
    (
        SELECT STRING_AGG(l.LEISTUNG, ', ')
        FROM LEISTUNG l
        WHERE l.PATIENTID = k.PATIENTID
          AND l.DATUM = k.DATUM
    ) AS service_codes
FROM KARTEI k
JOIN PATIENT p ON k.PATIENTID = p.PATIENTID
LEFT JOIN KASSE ka ON p.KASSEID = ka.KASSEID
WHERE k.DATUM = '2022-01-18';
GO
```

**Result:**
```
date        patient_id  insurance_status  insurance_name          chart_entry                     service_codes
----------  ----------  ----------------  ----------------------  ----------------------------------  -------------
2022-01-18  1           GKV               AOK Bayern              Kontrolle, Befund unauffällig       01, 1040
2022-01-18  1           GKV               AOK Bayern              Zahnreinigung durchgeführt          01, 1040
2022-01-18  2           GKV               DAK Gesundheit          Füllungstherapie Zahn 36            13b
2022-01-18  3           GKV               Techniker Krankenkasse  Röntgenaufnahme OPG                 Ä935
2022-01-18  4           PKV               PRIVAT                  Beratung Zahnersatz                 NULL
2022-01-18  5           GKV               Barmer                  Professionelle Zahnreinigung        NULL
```

✅ All 5 required fields!

---

## Final Query with JSON Output

### Option 1: JSON rows (SQL Server 2016+)

```sql
SELECT
    k.DATUM AS date,
    k.PATIENTID AS patient_id,
    CASE ka.TYP
        WHEN 'G' THEN 'GKV'
        WHEN 'P' THEN 'PKV'
        ELSE 'Selbstzahler'
    END AS insurance_status,
    ISNULL(ka.NAME, 'Keine') AS insurance_name,
    k.EINTRAG AS chart_entry,
    ISNULL((
        SELECT STRING_AGG(l.LEISTUNG, ', ')
        FROM LEISTUNG l
        WHERE l.PATIENTID = k.PATIENTID
          AND l.DATUM = k.DATUM
    ), '') AS service_codes
FROM KARTEI k
JOIN PATIENT p ON k.PATIENTID = p.PATIENTID
LEFT JOIN KASSE ka ON p.KASSEID = ka.KASSEID
WHERE k.DATUM = '2022-01-18'
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
    "insurance_name": "AOK Bayern",
    "chart_entry": "Kontrolle, Befund unauffällig",
    "service_codes": "01, 1040"
  },
  {
    "date": "2022-01-18",
    "patient_id": 1,
    "insurance_status": "GKV",
    "insurance_name": "AOK Bayern",
    "chart_entry": "Zahnreinigung durchgeführt",
    "service_codes": "01, 1040"
  },
  ...
]
```

---

### Option 2: Service codes as JSON array

```sql
SELECT
    k.DATUM AS date,
    k.PATIENTID AS patient_id,
    CASE ka.TYP
        WHEN 'G' THEN 'GKV'
        WHEN 'P' THEN 'PKV'
        ELSE 'Selbstzahler'
    END AS insurance_status,
    ISNULL(ka.NAME, 'Keine') AS insurance_name,
    k.EINTRAG AS chart_entry,
    (
        SELECT l.LEISTUNG AS code
        FROM LEISTUNG l
        WHERE l.PATIENTID = k.PATIENTID
          AND l.DATUM = k.DATUM
        FOR JSON PATH
    ) AS service_codes
FROM KARTEI k
JOIN PATIENT p ON k.PATIENTID = p.PATIENTID
LEFT JOIN KASSE ka ON p.KASSEID = ka.KASSEID
WHERE k.DATUM = '2022-01-18'
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
    "insurance_name": "AOK Bayern",
    "chart_entry": "Kontrolle, Befund unauffällig",
    "service_codes": [{"code": "01"}, {"code": "1040"}]
  },
  ...
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

    query = """
    SELECT
        k.DATUM AS date,
        k.PATIENTID AS patient_id,
        CASE ka.TYP
            WHEN 'G' THEN 'GKV'
            WHEN 'P' THEN 'PKV'
            ELSE 'Selbstzahler'
        END AS insurance_status,
        ISNULL(ka.NAME, 'Keine') AS insurance_name,
        k.EINTRAG AS chart_entry,
        ISNULL((
            SELECT STRING_AGG(l.LEISTUNG, ', ')
            FROM LEISTUNG l
            WHERE l.PATIENTID = k.PATIENTID
              AND l.DATUM = k.DATUM
        ), '') AS service_codes
    FROM KARTEI k
    JOIN PATIENT p ON k.PATIENTID = p.PATIENTID
    LEFT JOIN KASSE ka ON p.KASSEID = ka.KASSEID
    WHERE k.DATUM = ?
    """

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute(query, target_date)

    entries = []
    for row in cursor.fetchall():
        entries.append({
            "date": row.date.isoformat() if row.date else None,
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

## Next Step

→ [05b-extraction-script.md](./05b-extraction-script.md) - Create Python script for CSV/JSON output
