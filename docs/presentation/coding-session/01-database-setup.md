# Step 1: Database Setup from Backup

> **💬 Talking Points**
> - "In reality, customers send us their database backup files - usually `.bak` files from SQL Server"
> - "For security reasons, we always work on a copy, never the production database"
> - "The real challenge: we don't know the schema until we explore it"

---

## Context

Ivoris dental software uses Microsoft SQL Server. In a real scenario, you would:
1. Get a database backup (.bak file) from the customer
2. Restore it to your local SQL Server for development
3. **Discover** the schema - every customer's database may be different!

---

## Option A: Restore from .bak Backup File

> **💬 Talking Points**
> - "This is the real-world scenario - customer gives you their backup"
> - "The `WITH MOVE` is crucial - it remaps the file paths to our container"
> - "Always use `REPLACE` to overwrite if you're doing multiple restores"

### 1. Copy backup to Docker container

```bash
# Assuming you have a backup file: DentalDB.bak
docker cp /path/to/DentalDB.bak ivoris-sqlserver:/var/opt/mssql/backup/
```

### 2. Connect to SQL Server

```bash
# Using sqlcmd inside container
docker exec -it ivoris-sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'YourStrong@Passw0rd' -C
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

## Option B: Use Existing Docker Setup

> **💬 Talking Points**
> - "We already have a restored database in our Docker container"
> - "This is the real Ivoris schema - 400+ tables!"
> - "The challenge is discovering which tables we need"

Our project already has a docker-compose with the database:

```bash
cd ~/Projects/outre_base/sandbox/ivoris-multi-center
docker-compose up -d

# Wait for SQL Server to start (~10 seconds)
sleep 10

# Verify database exists
docker exec ivoris-sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'YourStrong@Passw0rd' -C \
  -Q "SELECT name FROM sys.databases WHERE name = 'DentalDB'"
```

---

## What We're Working With

The real DentalDB has:
- **400+ tables** - not just 4!
- **Custom schema** - tables are in `ck` schema, not `dbo`
- **Soft deletes** - `DELKZ` column on every table
- **German column names** - need to discover what they mean
- **Different data types** - dates stored as `VARCHAR(8)` in YYYYMMDD format

**This is the real challenge** - discovering the right tables and columns.

---

## Verification Commands

```bash
# Check container is running
docker ps | grep ivoris

# Check database exists
docker exec ivoris-sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'YourStrong@Passw0rd' -C \
  -Q "SELECT name FROM sys.databases"

# Count tables (expect 400+)
docker exec ivoris-sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'YourStrong@Passw0rd' -C -d DentalDB \
  -Q "SELECT COUNT(*) AS table_count FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
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
