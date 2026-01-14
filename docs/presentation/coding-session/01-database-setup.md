# Step 1: Database Setup from Backup

> **💬 Talking Points**
> - "In reality, customers send us their database backup files - usually `.bak` files from SQL Server"
> - "For security reasons, we always work on a copy, never the production database"
> - "Today I'll show you three ways to set this up - choose based on your situation"

---

## Context

Ivoris dental software uses Microsoft SQL Server. In a real scenario, you would:
1. Get a database backup (.bak file) from the customer
2. Restore it to your local SQL Server for development

---

> **💬 Talking Points - Option A**
> - "This is the real-world scenario - customer gives you their backup"
> - "The `WITH MOVE` is crucial - it remaps the file paths to our container"
> - "Always use `REPLACE` to overwrite if you're doing multiple restores"

## Option A: Restore from .bak Backup File

### 1. Copy backup to Docker container

```bash
# Assuming you have a backup file: DentalDB.bak
docker cp /path/to/DentalDB.bak ivoris-sqlserver:/var/opt/mssql/backup/
```

### 2. Connect to SQL Server

```bash
# Using sqlcmd inside container
docker exec -it ivoris-sqlserver /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P 'YourStrong@Passw0rd'
```

### 3. List available backups

```sql
RESTORE FILELISTONLY FROM DISK = '/var/opt/mssql/backup/DentalDB.bak';
GO
```

**Output shows:** Logical names of data and log files

### 4. Restore the database

```sql
RESTORE DATABASE DentalDB
FROM DISK = '/var/opt/mssql/backup/DentalDB.bak'
WITH MOVE 'DentalDB' TO '/var/opt/mssql/data/DentalDB.mdf',
     MOVE 'DentalDB_log' TO '/var/opt/mssql/data/DentalDB_log.ldf',
     REPLACE;
GO
```

**Explanation:**
- `RESTORE DATABASE` - Command to restore
- `FROM DISK` - Path to backup file inside container
- `WITH MOVE` - Relocate files to container paths
- `REPLACE` - Overwrite if database exists

### 5. Verify restoration

```sql
SELECT name, state_desc FROM sys.databases WHERE name = 'DentalDB';
GO
```

**Expected:** `DentalDB | ONLINE`

---

> **💬 Talking Points - Option B**
> - "For demos or when you don't have customer data yet"
> - "Notice the German column names - this is authentic to the Ivoris software"
> - "TYP with 'G' and 'P' represents the German insurance system"

## Option B: Create Test Database (For Demo)

If no backup available, create a test database with sample data:

```bash
# Run the test database generator
cd ~/Projects/outre_base/sandbox/ivoris-pipeline
python scripts/create_test_db.py
```

Or manually:

```sql
-- Create database
CREATE DATABASE DentalDB;
GO

USE DentalDB;
GO

-- Create PATIENT table
CREATE TABLE PATIENT (
    PATIENTID INT PRIMARY KEY,
    NAME NVARCHAR(100),
    VORNAME NVARCHAR(100),
    GEBDAT DATE,
    KASSEID INT
);

-- Create KASSE table (Insurance)
CREATE TABLE KASSE (
    KASSEID INT PRIMARY KEY,
    NAME NVARCHAR(100),
    TYP CHAR(1)  -- 'G' = GKV, 'P' = PKV
);

-- Create KARTEI table (Chart entries)
CREATE TABLE KARTEI (
    KARTEIID INT PRIMARY KEY,
    PATIENTID INT,
    DATUM DATE,
    EINTRAG NVARCHAR(MAX),
    FOREIGN KEY (PATIENTID) REFERENCES PATIENT(PATIENTID)
);

-- Create LEISTUNG table (Services)
CREATE TABLE LEISTUNG (
    LEISTUNGID INT PRIMARY KEY,
    PATIENTID INT,
    DATUM DATE,
    LEISTUNG NVARCHAR(20),  -- Service code like '01', 'Ä1', '2060'
    FOREIGN KEY (PATIENTID) REFERENCES PATIENT(PATIENTID)
);
GO
```

---

> **💬 Talking Points - Option C**
> - "This is the fastest way - everything is pre-configured"
> - "The docker-compose handles all the setup automatically"
> - "We'll use this for today's session to save time"

## Option C: Use Existing Docker Setup

Our project already has a docker-compose that creates the database:

```bash
cd ~/Projects/outre_base/sandbox/ivoris-pipeline
docker-compose up -d

# Wait for SQL Server to start (~10 seconds)
sleep 10

# Database is auto-created with test data
```

---

## Verification Commands

```bash
# Check container is running
docker ps | grep ivoris

# Check database exists
docker exec ivoris-sqlserver /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P 'YourStrong@Passw0rd' \
  -Q "SELECT name FROM sys.databases"
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Container won't start | Check Docker Desktop is running |
| "Login failed" | Verify password matches docker-compose.yml |
| Backup restore fails | Check file paths inside container |
| Database not found | Wait longer for SQL Server startup |

---

## Next Step

→ [02-docker-setup.md](./02-docker-setup.md) - Configure Docker environment
