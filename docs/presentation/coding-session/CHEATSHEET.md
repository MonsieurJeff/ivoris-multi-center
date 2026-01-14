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
docker exec -it ivoris-sqlserver /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P 'YourStrong@Passw0rd' -d DentalDB
```

---

## SQL Exploration Commands

```sql
-- List all tables
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';
GO

-- List all columns (one per line)
SELECT TABLE_NAME + '.' + COLUMN_NAME + ' (' + DATA_TYPE + ')'
FROM INFORMATION_SCHEMA.COLUMNS ORDER BY TABLE_NAME, ORDINAL_POSITION;
GO

-- Preview table
SELECT TOP 5 * FROM KARTEI;
GO

-- Count rows
SELECT 'KARTEI=' + CAST(COUNT(*) AS VARCHAR) FROM KARTEI;
GO
```

---

## The Extraction Query

```sql
SELECT
    k.DATUM AS date,
    k.PATIENTID AS patient_id,
    CASE ka.TYP
        WHEN 'G' THEN 'GKV'
        WHEN 'P' THEN 'PKV'
        ELSE 'Selbstzahler'
    END AS insurance_status,
    ISNULL(ka.NAME, '') AS insurance_name,
    k.EINTRAG AS chart_entry,
    ISNULL((
        SELECT STRING_AGG(l.LEISTUNG, ', ')
        FROM LEISTUNG l
        WHERE l.PATIENTID = k.PATIENTID AND l.DATUM = k.DATUM
    ), '') AS service_codes
FROM KARTEI k
JOIN PATIENT p ON k.PATIENTID = p.PATIENTID
LEFT JOIN KASSE ka ON p.KASSEID = ka.KASSEID
WHERE k.DATUM = '2022-01-18';
GO
```

---

## Python Quick Script

```python
#!/usr/bin/env python3
import json, pyodbc

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost,1433;DATABASE=DentalDB;"
    "UID=sa;PWD=YourStrong@Passw0rd;TrustServerCertificate=yes"
)

query = """
SELECT k.DATUM, k.PATIENTID,
    CASE ka.TYP WHEN 'G' THEN 'GKV' WHEN 'P' THEN 'PKV' ELSE 'Selbstzahler' END,
    ISNULL(ka.NAME,''), k.EINTRAG,
    ISNULL((SELECT STRING_AGG(l.LEISTUNG,',') FROM LEISTUNG l
            WHERE l.PATIENTID=k.PATIENTID AND l.DATUM=k.DATUM),'')
FROM KARTEI k
JOIN PATIENT p ON k.PATIENTID = p.PATIENTID
LEFT JOIN KASSE ka ON p.KASSEID = ka.KASSEID
WHERE k.DATUM = ?
"""

cursor = conn.cursor()
cursor.execute(query, '2022-01-18')

entries = [{"date": str(r[0]), "patient_id": r[1], "insurance_status": r[2],
            "insurance_name": r[3], "chart_entry": r[4],
            "service_codes": r[5].split(',') if r[5] else []} for r in cursor]

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

## Table Relationships

```
KASSE (Insurance)     LEISTUNG (Services)
    │                      │
    │ KASSEID              │ PATIENTID + DATUM
    ▼                      ▼
PATIENT ◄──────────── KARTEI (Chart)
    PATIENTID              PATIENTID
```

---

## Key Fields Mapping

| Requirement | Source |
|-------------|--------|
| Datum | `KARTEI.DATUM` |
| Pat-ID | `KARTEI.PATIENTID` |
| Versicherungsstatus | `KASSE.TYP` → GKV/PKV/Selbstzahler |
| Karteikarteneintrag | `KARTEI.EINTRAG` |
| Leistungen | `LEISTUNG.LEISTUNG` (aggregated) |

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
```
