# Ivoris Daily Extraction Pipeline

**Coding Session Handout** | Quick Reference

---

## What We Built

A pipeline that extracts daily dental chart entries from Ivoris database:

- **Input:** SQL Server database with patient records
- **Output:** JSON/CSV files with chart entries
- **Schedule:** Runs automatically every day via cron

---

## The 5 Required Fields

| Field | German | Source |
|-------|--------|--------|
| Date | Datum | `KARTEI.DATUM` |
| Patient ID | Pat-ID | `KARTEI.PATIENTID` |
| Insurance Status | Versicherungsstatus | `KASSE.TYP` → GKV/PKV |
| Chart Entry | Karteikarteneintrag | `KARTEI.EINTRAG` |
| Service Codes | Leistungen | `LEISTUNG.LEISTUNG` |

---

## Key Commands

### Start Database
```bash
docker-compose up -d
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
        WHERE l.PATIENTID = k.PATIENTID
          AND l.DATUM = k.DATUM
    ), '') AS service_codes
FROM KARTEI k
JOIN PATIENT p ON k.PATIENTID = p.PATIENTID
LEFT JOIN KASSE ka ON p.KASSEID = ka.KASSEID
WHERE k.DATUM = ?
```

---

## Database Schema

```
KASSE (Insurance)     LEISTUNG (Services)
    │                      │
    │ KASSEID              │ PATIENTID + DATUM
    ▼                      ▼
PATIENT ◄──────────── KARTEI (Chart)
    PATIENTID              PATIENTID
```

---

## Output Example

```json
{
  "date": "2022-01-18",
  "patient_id": 1,
  "insurance_status": "GKV",
  "insurance_name": "AOK Bayern",
  "chart_entry": "Kontrolle, Befund unauffällig",
  "service_codes": ["01", "1040"]
}
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
| KASSE | Insurance fund |
| LEISTUNG | Service / Procedure |
| GKV | Public health insurance |
| PKV | Private health insurance |
| Selbstzahler | Self-pay patient |

---

## Contact

**Questions?** Reach out to: [Your contact info]

---

*Generated from Ivoris Daily Extraction Pipeline coding session*
