# Step 3: Explore Database Manually

> **💬 Talking Points**
> - "This is the detective work - we have a database, no documentation"
> - "Every customer database will be different, so you need these exploration skills"
> - "The goal: understand the schema before writing any extraction code"

---

## Goal

Discover the database structure without any documentation. This is the real-world scenario when you receive a customer's database.

---

## Connect to the Database

```bash
# Enter SQL Server container
docker exec -it ivoris-sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'YourStrong@Passw0rd' -C -d DentalDB
```

---

## List All Schemas

> **💬 Talking Points**
> - "First surprise: tables might not be in the default 'dbo' schema"
> - "Ivoris uses a custom 'ck' schema"
> - "Always check schemas first!"

```sql
SELECT DISTINCT TABLE_SCHEMA
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_SCHEMA;
GO
```

**Output:**
```
TABLE_SCHEMA
------------
ck
ckexternpu
dbo
```

**Key finding:** Most tables are in `ck` schema!

---

> **💬 Talking Points - INFORMATION_SCHEMA**
> - "INFORMATION_SCHEMA is a SQL standard - works in MySQL, PostgreSQL, SQL Server"
> - "It's the meta-database - data about your data"
> - "These queries work on ANY database, memorize them"

## Count Tables

```sql
SELECT TABLE_SCHEMA, COUNT(*) AS table_count
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
GROUP BY TABLE_SCHEMA
ORDER BY table_count DESC;
GO
```

**Output:**
```
TABLE_SCHEMA  table_count
------------  -----------
ck            487
dbo           4
ckexternpu    1
```

**487 tables!** We need to find the right ones.

---

## Search for Relevant Tables

```sql
-- Find tables with promising names
SELECT TABLE_SCHEMA, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
  AND (TABLE_NAME LIKE '%KARTEI%'
    OR TABLE_NAME LIKE '%PATIENT%'
    OR TABLE_NAME LIKE '%KASSE%'
    OR TABLE_NAME LIKE '%LEISTUNG%')
ORDER BY TABLE_NAME;
GO
```

**Output (truncated):**
```
TABLE_SCHEMA  TABLE_NAME
------------  ----------
ck            KARTEI
ck            KARTEIABRECHNUNG
ck            KARTEIABTEILUNG
...
ck            KASSEN
ck            KASSENABSCHLAG
...
ck            LEISTUNG
ck            LEISTUNGVALID
...
ck            PATIENT
ck            PATIENTABTEILUNG
...
ck            PATKASSE
```

**Found our candidates:** `ck.KARTEI`, `ck.PATIENT`, `ck.KASSEN`, `ck.LEISTUNG`, `ck.PATKASSE`

---

## Explore Key Tables

> **💬 Talking Points - Exploring Tables**
> - "Always use TOP or LIMIT when exploring - you don't want 10 million rows"
> - "Look at real data to understand what each column means"
> - "KARTEI is 'chart' in German - this is the main table we need"

### Look at KARTEI (Chart entries)

```sql
-- List columns
SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ck' AND TABLE_NAME = 'KARTEI'
ORDER BY ORDINAL_POSITION;
GO
```

**Key columns found:**
```
COLUMN_NAME    DATA_TYPE  LENGTH
-----------    ---------  ------
ID             int        NULL
PATNR          int        NULL      ← Patient reference (not PATIENTID!)
DATUM          varchar    8         ← Date as YYYYMMDD string!
BEMERKUNG      varchar    -1        ← Chart entry text (not EINTRAG!)
DELKZ          bit        NULL      ← Soft delete flag
```

```sql
-- Sample data
SELECT TOP 5 ID, PATNR, DATUM, LEFT(BEMERKUNG, 50) AS bemerkung
FROM ck.KARTEI
WHERE DELKZ = 0 OR DELKZ IS NULL
ORDER BY DATUM DESC;
GO
```

**Output:**
```
ID  PATNR  DATUM     bemerkung
--  -----  --------  --------------------------------------------------
1   1      20241029
2   1      20230519  Behandlungsmitteilung (19.05.2023)
3   1      20220118  Kontrolle,
```

---

### Look at PATIENT

```sql
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ck' AND TABLE_NAME = 'PATIENT'
  AND COLUMN_NAME IN ('ID', 'P_NAME', 'P_VORNAME', 'P_GEBOREN', 'DELKZ')
ORDER BY ORDINAL_POSITION;
GO
```

**Key columns:**
```
COLUMN_NAME  DATA_TYPE
-----------  ---------
ID           int         ← Primary key
P_NAME       varchar     ← Last name
P_VORNAME    varchar     ← First name
P_GEBOREN    varchar     ← Birth date (also VARCHAR!)
DELKZ        bit         ← Soft delete
```

---

### Look at KASSEN (Insurance)

```sql
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ck' AND TABLE_NAME = 'KASSEN'
  AND COLUMN_NAME IN ('ID', 'NAME', 'ART', 'DELKZ')
ORDER BY ORDINAL_POSITION;
GO
```

**Key columns:**
```
COLUMN_NAME  DATA_TYPE
-----------  ---------
ID           int         ← Primary key
NAME         varchar     ← Insurance company name
ART          char(1)     ← Type code (not TYP!)
DELKZ        bit         ← Soft delete
```

```sql
-- What are the ART values?
SELECT ART, COUNT(*) as cnt, MIN(NAME) as example
FROM ck.KASSEN
GROUP BY ART
ORDER BY cnt DESC;
GO
```

**Output:**
```
ART  cnt    example
---  -----  -------
6    20707  abc BKK
4    2549   AOK Albstadt
9    1418   ...
8    849    BARMER
P    54     Albingia        ← P = Private insurance!
...
```

**Key insight:** `ART = 'P'` means private insurance, numbers (1-9) are public insurance types.

---

### Look at PATKASSE (Patient-Insurance Link)

> **💬 Talking Points - Junction Table**
> - "This is a surprise - insurance isn't directly on PATIENT"
> - "PATKASSE is a junction table linking patients to insurance"
> - "This allows a patient to have multiple insurance records"

```sql
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ck' AND TABLE_NAME = 'PATKASSE'
  AND COLUMN_NAME IN ('ID', 'PATNR', 'KASSENID', 'DELKZ')
ORDER BY ORDINAL_POSITION;
GO
```

**Key columns:**
```
COLUMN_NAME  DATA_TYPE
-----------  ---------
ID           int         ← Primary key
PATNR        int         ← → PATIENT.ID
KASSENID     int         ← → KASSEN.ID
DELKZ        bit         ← Soft delete
```

---

### Look at LEISTUNG (Services)

```sql
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ck' AND TABLE_NAME = 'LEISTUNG'
  AND COLUMN_NAME IN ('ID', 'PATIENTID', 'DATUM', 'LEISTUNG', 'DELKZ')
ORDER BY ORDINAL_POSITION;
GO
```

**Key columns:**
```
COLUMN_NAME  DATA_TYPE
-----------  ---------
ID           int         ← Primary key
PATIENTID    int         ← Patient reference (different from KARTEI!)
DATUM        varchar     ← Date as YYYYMMDD
LEISTUNG     varchar     ← Service code
DELKZ        bit         ← Soft delete
```

---

> **💬 Talking Points - ER Diagram**
> - "This is what we've discovered - PATIENT is the central table"
> - "Notice PATKASSE as a junction table - not a direct link"
> - "LEISTUNG uses PATIENTID but KARTEI uses PATNR - inconsistent naming!"

## Entity Relationship Diagram (Discovered)

```
┌─────────────┐       ┌─────────────┐
│ ck.KASSEN   │       │ck.LEISTUNG  │
│ (Insurance) │       │ (Services)  │
├─────────────┤       ├─────────────┤
│ ID (PK)     │       │ ID          │
│ NAME        │       │ PATIENTID───┼──┐
│ ART (P=PKV) │       │ DATUM       │  │
└──────┬──────┘       │ LEISTUNG    │  │
       │              └─────────────┘  │
       │ ID                            │
       │                               │
┌──────┴──────┐                        │
│ck.PATKASSE  │                        │
│ (Junction)  │                        │
├─────────────┤                        │
│ PATNR ──────┼───┐                    │
│ KASSENID    │   │                    │
└─────────────┘   │                    │
                  │                    │
┌─────────────────┴────────────────────┘
│
│  ┌─────────────┐
└─►│ ck.PATIENT  │
   ├─────────────┤
   │ ID (PK)     │
   │ P_NAME      │
   │ P_VORNAME   │
   └──────┬──────┘
          │ ID = PATNR
          │
   ┌──────┴──────┐
   │ ck.KARTEI   │
   │(Chart Entry)│
   ├─────────────┤
   │ ID          │
   │ PATNR (FK)  │
   │ DATUM       │
   │ BEMERKUNG   │
   └─────────────┘
```

---

## Key Discoveries Summary

| What we expected | What we found | Difference |
|------------------|---------------|------------|
| `dbo` schema | `ck` schema | Different schema! |
| `PATIENTID` | `PATNR` | Different column name |
| `EINTRAG` | `BEMERKUNG` | Different column name |
| `KASSE.TYP` | `KASSEN.ART` | Different table & column |
| `DATE` type | `VARCHAR(8)` | YYYYMMDD strings |
| Direct insurance link | `PATKASSE` junction | Extra table! |
| No soft delete | `DELKZ` flag | Must filter! |

---

## Next Step

→ [04-find-tables.md](./04-find-tables.md) - Map tables to our requirements
