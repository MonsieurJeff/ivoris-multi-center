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
docker exec -it ivoris-sqlserver /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P 'YourStrong@Passw0rd' -d DentalDB
```

---

## List All Databases

```sql
SELECT name FROM sys.databases ORDER BY name;
GO
```

**Output:**
```
name
--------------------
DentalDB
master
model
msdb
tempdb
```

**Explanation:** `master`, `model`, `msdb`, `tempdb` are system databases. `DentalDB` is our target.

---

## Switch to Target Database

```sql
USE DentalDB;
GO
```

---

> **💬 Talking Points - INFORMATION_SCHEMA**
> - "INFORMATION_SCHEMA is a SQL standard - works in MySQL, PostgreSQL, SQL Server"
> - "It's the meta-database - data about your data"
> - "These queries work on ANY database, memorize them"

## List All Tables

### Simple list

```sql
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;
GO
```

**Output:**
```
TABLE_NAME
--------------------
KARTEI
KASSE
LEISTUNG
PATIENT
```

### With row counts

```sql
SELECT
    t.TABLE_NAME,
    p.rows AS ROW_COUNT
FROM INFORMATION_SCHEMA.TABLES t
JOIN sys.tables st ON t.TABLE_NAME = st.name
JOIN sys.partitions p ON st.object_id = p.object_id AND p.index_id IN (0, 1)
WHERE t.TABLE_TYPE = 'BASE TABLE'
ORDER BY t.TABLE_NAME;
GO
```

**Output:**
```
TABLE_NAME     ROW_COUNT
-------------- ---------
KARTEI         15
KASSE          5
LEISTUNG       20
PATIENT        10
```

---

## List All Columns (One Per Line)

### All tables, all columns

```sql
SELECT
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
ORDER BY TABLE_NAME, ORDINAL_POSITION;
GO
```

**Output:**
```
TABLE_NAME  COLUMN_NAME   DATA_TYPE   CHARACTER_MAXIMUM_LENGTH  IS_NULLABLE
----------  -----------   ---------   ------------------------  -----------
KARTEI      KARTEIID      int         NULL                      NO
KARTEI      PATIENTID     int         NULL                      YES
KARTEI      DATUM         date        NULL                      YES
KARTEI      EINTRAG       nvarchar    -1                        YES
KASSE       KASSEID       int         NULL                      NO
KASSE       NAME          nvarchar    100                       YES
KASSE       TYP           char        1                         YES
LEISTUNG    LEISTUNGID    int         NULL                      NO
LEISTUNG    PATIENTID     int         NULL                      YES
LEISTUNG    DATUM         date        NULL                      YES
LEISTUNG    LEISTUNG      nvarchar    20                        YES
PATIENT     PATIENTID     int         NULL                      NO
PATIENT     NAME          nvarchar    100                       YES
PATIENT     VORNAME       nvarchar    100                       YES
PATIENT     GEBDAT        date        NULL                      YES
PATIENT     KASSEID       int         NULL                      YES
```

### Formatted for readability

```sql
SELECT
    TABLE_NAME + '.' + COLUMN_NAME + ' (' + DATA_TYPE +
    CASE
        WHEN CHARACTER_MAXIMUM_LENGTH IS NOT NULL AND CHARACTER_MAXIMUM_LENGTH > 0
        THEN '(' + CAST(CHARACTER_MAXIMUM_LENGTH AS VARCHAR) + ')'
        WHEN CHARACTER_MAXIMUM_LENGTH = -1 THEN '(MAX)'
        ELSE ''
    END + ')' AS COLUMN_INFO
FROM INFORMATION_SCHEMA.COLUMNS
ORDER BY TABLE_NAME, ORDINAL_POSITION;
GO
```

**Output:**
```
COLUMN_INFO
-----------------------------------------
KARTEI.KARTEIID (int)
KARTEI.PATIENTID (int)
KARTEI.DATUM (date)
KARTEI.EINTRAG (nvarchar(MAX))
KASSE.KASSEID (int)
KASSE.NAME (nvarchar(100))
KASSE.TYP (char(1))
LEISTUNG.LEISTUNGID (int)
LEISTUNG.PATIENTID (int)
LEISTUNG.DATUM (date)
LEISTUNG.LEISTUNG (nvarchar(20))
PATIENT.PATIENTID (int)
PATIENT.NAME (nvarchar(100))
PATIENT.VORNAME (nvarchar(100))
PATIENT.GEBDAT (date)
PATIENT.KASSEID (int)
```

---

> **💬 Talking Points - Exploring Tables**
> - "Always use TOP or LIMIT when exploring - you don't want 10 million rows"
> - "Look at real data to understand what each column means"
> - "KARTEI is 'chart' in German - this is the main table we need"

## Explore Individual Tables

### Look at KARTEI (Chart entries)

```sql
SELECT TOP 5 * FROM KARTEI;
GO
```

**Output:**
```
KARTEIID  PATIENTID  DATUM       EINTRAG
--------  ---------  ----------  ----------------------------------
1         1          2022-01-18  Kontrolle, Befund unauffällig
2         1          2022-01-18  Zahnreinigung durchgeführt
3         2          2022-01-18  Füllungstherapie Zahn 36
...
```

### Look at PATIENT

```sql
SELECT TOP 5 * FROM PATIENT;
GO
```

**Output:**
```
PATIENTID  NAME      VORNAME   GEBDAT      KASSEID
---------  --------  --------  ----------  -------
1          Müller    Hans      1985-03-15  1
2          Schmidt   Anna      1990-07-22  2
3          Weber     Thomas    1978-11-30  3
...
```

### Look at KASSE (Insurance)

```sql
SELECT * FROM KASSE;
GO
```

**Output:**
```
KASSEID  NAME                   TYP
-------  ---------------------  ---
1        AOK Bayern             G
2        DAK Gesundheit         G
3        Techniker Krankenkasse G
4        PRIVAT                 P
5        Debeka                 P
```

**TYP meaning:**
- `G` = Gesetzliche Krankenversicherung (GKV) - Public insurance
- `P` = Private Krankenversicherung (PKV) - Private insurance

### Look at LEISTUNG (Services)

```sql
SELECT TOP 5 * FROM LEISTUNG;
GO
```

**Output:**
```
LEISTUNGID  PATIENTID  DATUM       LEISTUNG
----------  ---------  ----------  --------
1           1          2022-01-18  01
2           1          2022-01-18  1040
3           2          2022-01-18  13b
4           3          2022-01-18  Ä935
...
```

---

> **💬 Talking Points - Keys & Relationships**
> - "Primary keys tell us how tables are uniquely identified"
> - "Foreign keys tell us how tables connect to each other"
> - "This reveals the data model without any documentation"

## Find Primary Keys and Foreign Keys

```sql
-- Primary Keys
SELECT
    tc.TABLE_NAME,
    kcu.COLUMN_NAME AS PRIMARY_KEY
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
    ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
ORDER BY tc.TABLE_NAME;
GO
```

**Output:**
```
TABLE_NAME  PRIMARY_KEY
----------  -----------
KARTEI      KARTEIID
KASSE       KASSEID
LEISTUNG    LEISTUNGID
PATIENT     PATIENTID
```

```sql
-- Foreign Keys
SELECT
    fk.name AS FK_NAME,
    tp.name AS PARENT_TABLE,
    cp.name AS PARENT_COLUMN,
    tr.name AS REFERENCED_TABLE,
    cr.name AS REFERENCED_COLUMN
FROM sys.foreign_keys fk
JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
JOIN sys.tables tr ON fk.referenced_object_id = tr.object_id
JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
JOIN sys.columns cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id;
GO
```

**Output:**
```
FK_NAME              PARENT_TABLE  PARENT_COLUMN  REFERENCED_TABLE  REFERENCED_COLUMN
-------------------  ------------  -------------  ----------------  -----------------
FK_KARTEI_PATIENT    KARTEI        PATIENTID      PATIENT           PATIENTID
FK_LEISTUNG_PATIENT  LEISTUNG      PATIENTID      PATIENT           PATIENTID
FK_PATIENT_KASSE     PATIENT       KASSEID        KASSE             KASSEID
```

---

> **💬 Talking Points - ER Diagram**
> - "This is what we've discovered - PATIENT is the central table"
> - "Notice how KARTEI and LEISTUNG both link to PATIENT"
> - "This is how dental software works - everything relates to a patient"

## Entity Relationship Diagram (Mental Model)

```
┌─────────────┐       ┌─────────────┐
│   KASSE     │       │  LEISTUNG   │
│  (Insurance)│       │  (Services) │
├─────────────┤       ├─────────────┤
│ KASSEID (PK)│       │ LEISTUNGID  │
│ NAME        │       │ PATIENTID───┼──┐
│ TYP (G/P)   │       │ DATUM       │  │
└──────┬──────┘       │ LEISTUNG    │  │
       │              └─────────────┘  │
       │ 1:N                           │
       │                               │
┌──────┴──────┐                        │
│   PATIENT   │◄───────────────────────┘
├─────────────┤           N:1
│ PATIENTID(PK)│
│ NAME        │
│ VORNAME     │
│ GEBDAT      │
│ KASSEID (FK)│
└──────┬──────┘
       │ 1:N
       │
┌──────┴──────┐
│   KARTEI    │
│(Chart Entry)│
├─────────────┤
│ KARTEIID    │
│ PATIENTID(FK)│
│ DATUM       │
│ EINTRAG     │
└─────────────┘
```

---

## Summary

We discovered:
- **4 tables**: KARTEI, KASSE, LEISTUNG, PATIENT
- **Relationships**: PATIENT is central, linked to KASSE, KARTEI, LEISTUNG
- **Key columns**: PATIENTID, KASSEID, DATUM

---

## Next Step

→ [04-find-tables.md](./04-find-tables.md) - Map tables to our requirements
