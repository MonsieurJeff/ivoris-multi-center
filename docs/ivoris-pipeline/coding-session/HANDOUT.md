# Ivoris Daily Extraction Pipeline

**Coding Session Handout** | Quick Reference

---

## What We Built

A pipeline that extracts daily dental chart entries from Ivoris database:

- **Input:** SQL Server database with 487+ tables (real Ivoris schema)
- **Output:** JSON/CSV files with chart entries
- **Schedule:** Runs automatically every day via cron

---

## The 5 Required Fields

| Field | German | Source (Real Schema) |
|-------|--------|----------------------|
| Date | Datum | `ck.KARTEI.DATUM` (VARCHAR YYYYMMDD) |
| Patient ID | Pat-ID | `ck.KARTEI.PATNR` |
| Insurance Status | Versicherungsstatus | `ck.KASSEN.ART` via PATKASSE |
| Chart Entry | Karteikarteneintrag | `ck.KARTEI.BEMERKUNG` |
| Service Codes | Leistungen | `ck.LEISTUNG.LEISTUNG` |

---

## Key Schema Discoveries

| Expected | Real Ivoris |
|----------|-------------|
| `dbo` schema | `ck` schema |
| `PATIENTID` | `PATNR` |
| `EINTRAG` | `BEMERKUNG` |
| `KASSE.TYP = 'G'/'P'` | `KASSEN.ART = '1'-'9'/'P'` |
| Direct PATIENT→KASSE | PATKASSE junction table |
| DATE type | VARCHAR(8) YYYYMMDD |
| No soft delete | `DELKZ` flag on all tables |

---

## Key Commands

### Start Database
```bash
docker-compose up -d
```

### Connect to SQL Server
```bash
docker exec -it ivoris-sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'YourStrong@Passw0rd' -C -d DentalDB
```

### Run Extraction
```bash
python src/main.py --daily-extract --date 2022-01-18
python src/main.py --daily-extract --format csv
```

### Schedule (cron)
```bash
0 6 * * * /path/to/ivoris-extract.sh
```

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
  AND k.DATUM = ?   -- Use YYYYMMDD format: '20220118'
```

---

## Database Schema (Real)

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

**Key insight:** PATKASSE is a junction table - patients don't link directly to insurance!

---

## Output Example

```json
{
  "date": "2022-01-18",
  "patient_id": 1,
  "insurance_status": "GKV",
  "insurance_name": "DAK Gesundheit",
  "chart_entry": "Ausführliche Aufklärung über Mundhygiene und Putztechnik, Röntgenauswertung OPG",
  "service_codes": []
}
```

**Note:** `service_codes` is empty because all LEISTUNG records in this database are soft-deleted.

---

## Important Filters

Always include soft delete filter on every table:
```sql
WHERE (DELKZ = 0 OR DELKZ IS NULL)
```

Date format in database is YYYYMMDD (no dashes):
```sql
WHERE k.DATUM = '20220118'  -- NOT '2022-01-18'
```

---

## Resources

- **Repository:** [Link to your repo]
- **Documentation:** `docs/presentation/coding-session/`
- **Cheatsheet:** `CHEATSHEET.md`

---

## German Terms

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

---

## Contact

**Questions?** Reach out to: [Your contact info]

---

*Generated from Ivoris Daily Extraction Pipeline coding session*
