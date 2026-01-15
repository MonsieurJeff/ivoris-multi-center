# Coding Session Cheat Sheet

**One-page quick reference - Copy & paste when needed**

---

## Docker Commands

```bash
# Start database
docker-compose up -d

# Check status
docker ps | grep ivoris

# View logs
docker logs ivoris-sqlserver

# Stop
docker-compose down
```

---

## Connect to SQL Server

```bash
# Enter SQL shell
docker exec -it ivoris-sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'YourStrong@Passw0rd' -C -d DentalDB
```

---

## SQL Exploration Commands

```sql
-- List schemas
SELECT DISTINCT TABLE_SCHEMA FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_SCHEMA;
GO

-- Count tables per schema (expect ~487 in 'ck')
SELECT TABLE_SCHEMA, COUNT(*) FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE' GROUP BY TABLE_SCHEMA;
GO

-- Find tables by name (in ck schema)
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'ck' AND TABLE_NAME LIKE '%KARTEI%';
GO

-- List columns for a table
SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ck' AND TABLE_NAME = 'KARTEI';
GO

-- Preview table (remember DELKZ filter!)
SELECT TOP 5 * FROM ck.KARTEI WHERE DELKZ = 0 OR DELKZ IS NULL;
GO
```

---

## Real Schema Key Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `ck.KARTEI` | Chart entries | PATNR, DATUM, BEMERKUNG, DELKZ |
| `ck.PATIENT` | Patient info | ID, P_NAME, P_VORNAME |
| `ck.PATKASSE` | Patient↔Insurance link | PATNR, KASSENID |
| `ck.KASSEN` | Insurance companies | ID, NAME, ART |
| `ck.LEISTUNG` | Service codes | PATIENTID, DATUM, LEISTUNG |

---

## The Extraction Query (Real Schema)

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
        WHERE l.PATIENTID = k.PATNR
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

---

## Python Quick Script (Real Schema)

```python
#!/usr/bin/env python3
import json, pyodbc

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost,1433;DATABASE=DentalDB;"
    "UID=sa;PWD=YourStrong@Passw0rd;TrustServerCertificate=yes"
)

query = """
SELECT
    SUBSTRING(k.DATUM, 1, 4) + '-' + SUBSTRING(k.DATUM, 5, 2) + '-' + SUBSTRING(k.DATUM, 7, 2),
    k.PATNR,
    CASE WHEN ka.ART = 'P' THEN 'PKV'
         WHEN ka.ART IN ('1','2','3','4','5','6','7','8','9') THEN 'GKV'
         ELSE 'Selbstzahler' END,
    ISNULL(ka.NAME,''),
    LEFT(ISNULL(k.BEMERKUNG,''),100),
    ISNULL((SELECT STRING_AGG(l.LEISTUNG,', ') FROM ck.LEISTUNG l
            WHERE l.PATIENTID=k.PATNR AND l.DATUM=k.DATUM
            AND (l.DELKZ=0 OR l.DELKZ IS NULL)),'')
FROM ck.KARTEI k
JOIN ck.PATKASSE pk ON k.PATNR = pk.PATNR AND (pk.DELKZ=0 OR pk.DELKZ IS NULL)
LEFT JOIN ck.KASSEN ka ON pk.KASSENID = ka.ID
WHERE (k.DELKZ=0 OR k.DELKZ IS NULL) AND k.DATUM = ?
"""

cursor = conn.cursor()
cursor.execute(query, '20220118')  # YYYYMMDD format!

entries = [{"date": r[0], "patient_id": r[1], "insurance_status": r[2],
            "insurance_name": r[3], "chart_entry": r[4],
            "service_codes": r[5].split(', ') if r[5] else []} for r in cursor]

print(json.dumps(entries, indent=2, ensure_ascii=False))
```

---

## Run Extraction

```bash
# Activate environment
source .venv/bin/activate

# Test connection
python src/main.py --test-connection

# Extract JSON
python src/main.py --daily-extract --date 2022-01-18

# Extract CSV
python src/main.py --daily-extract --date 2022-01-18 --format csv

# View output
cat data/output/ivoris_chart_entries_2022-01-18.json
```

---

## Cron Job (Quick Setup)

```bash
# Edit crontab
crontab -e

# Add line (runs at 6 AM daily)
0 6 * * * cd ~/Projects/outre_base/sandbox/ivoris-pipeline && .venv/bin/python src/main.py --daily-extract

# Verify
crontab -l
```

---

## Table Relationships (Real Schema)

```
ck.KASSEN (Insurance)        ck.LEISTUNG (Services)
     │                            │
     │ ID                         │ PATIENTID + DATUM
     ▼                            ▼
ck.PATKASSE ◄──────────────► ck.KARTEI (Chart)
     │   KASSENID                 │ PATNR
     │                            │
     │ PATNR                      │ PATNR
     ▼                            │
ck.PATIENT ◄──────────────────────┘
     ID
```

---

## Key Schema Differences

| What You Might Expect | Real Ivoris |
|----------------------|-------------|
| `dbo` schema | `ck` schema |
| `PATIENTID` | `PATNR` |
| `EINTRAG` | `BEMERKUNG` |
| `KASSE.TYP` | `KASSEN.ART` |
| `TYP = 'G'/'P'` | `ART = '1'-'9'/'P'` |
| Direct PATIENT→KASSE | PATKASSE junction |
| DATE type | VARCHAR(8) YYYYMMDD |
| No soft delete | `DELKZ` flag |

---

## Key Fields Mapping

| Requirement | Source |
|-------------|--------|
| Datum | `ck.KARTEI.DATUM` (VARCHAR YYYYMMDD) |
| Pat-ID | `ck.KARTEI.PATNR` |
| Versicherungsstatus | `ck.KASSEN.ART` via PATKASSE |
| Karteikarteneintrag | `ck.KARTEI.BEMERKUNG` |
| Leistungen | `ck.LEISTUNG.LEISTUNG` (aggregated) |

---

## Emergency Fixes

```bash
# Container won't start
docker-compose down && docker-compose up -d && sleep 15

# Permission denied
chmod +x src/main.py

# Module not found
pip install pyodbc python-dotenv

# Connection refused
# Wait 15 seconds after docker-compose up, SQL Server needs time

# "Invalid object name 'KARTEI'"
# Tables are in 'ck' schema! Use ck.KARTEI

# No data returned
# Check DELKZ filter and date format (YYYYMMDD not YYYY-MM-DD)
```
