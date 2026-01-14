# Troubleshooting Guide

**Common problems and solutions during the coding session**

---

## Docker Issues

### Docker Desktop Not Running

**Symptom:**
```
Cannot connect to the Docker daemon
```

**Solution:**
```bash
# macOS
open -a Docker

# Wait 30 seconds for Docker to start
# Then retry
```

---

### Container Won't Start

**Symptom:**
```
Error response from daemon: Conflict. The container name is already in use
```

**Solution:**
```bash
# Remove existing container
docker rm -f ivoris-sqlserver

# Start fresh
docker-compose up -d
```

---

### Port Already in Use

**Symptom:**
```
Bind for 0.0.0.0:1433 failed: port is already allocated
```

**Solution:**
```bash
# Find what's using port 1433
lsof -i :1433

# Option 1: Kill the process
kill -9 <PID>

# Option 2: Use different port in docker-compose.yml
# Change "1433:1433" to "1434:1433"
# Then connect with: localhost,1434
```

---

### SQL Server Not Ready

**Symptom:**
```
Login failed for user 'sa'
```

**Solution:**
```bash
# SQL Server needs ~15 seconds to initialize
# Check logs for "ready for client connections"
docker logs ivoris-sqlserver | tail -10

# Wait and retry
sleep 15
```

---

## Database Connection Issues

### ODBC Driver Not Found

**Symptom:**
```
[IM002] [Microsoft][ODBC Driver Manager] Data source name not found
```

**Solution:**
```bash
# macOS - Install ODBC driver
brew install unixodbc
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew install msodbcsql18

# Linux
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
apt-get update && apt-get install -y msodbcsql18
```

---

### Connection Refused

**Symptom:**
```
[08001] [Microsoft][ODBC Driver 18] TCP Provider: Error code 0x2749
```

**Solution:**
```bash
# Container might not be running
docker ps | grep ivoris

# If not running, start it
docker-compose up -d
sleep 15

# Verify SQL Server is ready
docker logs ivoris-sqlserver | grep "ready for client"
```

---

### Wrong Password

**Symptom:**
```
Login failed for user 'sa'. Reason: Password did not match
```

**Solution:**
```bash
# Check password in docker-compose.yml
grep SA_PASSWORD docker-compose.yml

# Use that exact password
# Note: Special characters may need escaping in shell
```

---

### Certificate Error

**Symptom:**
```
SSL Provider: The certificate chain was issued by an authority that is not trusted
```

**Solution:**
```python
# Add TrustServerCertificate=yes to connection string
conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=DentalDB;"
    "UID=sa;PWD=YourStrong@Passw0rd;"
    "TrustServerCertificate=yes"  # Add this line
)
```

---

## Python Issues

### Module Not Found

**Symptom:**
```
ModuleNotFoundError: No module named 'pyodbc'
```

**Solution:**
```bash
# Activate virtual environment first
source .venv/bin/activate

# Install dependencies
pip install pyodbc python-dotenv
```

---

### Virtual Environment Not Activated

**Symptom:**
```
Command 'python' not found
# or
Using system Python instead of project Python
```

**Solution:**
```bash
# Activate the virtual environment
source .venv/bin/activate

# Verify
which python
# Should show: /path/to/project/.venv/bin/python
```

---

### Import Error in Script

**Symptom:**
```
ModuleNotFoundError: No module named 'src'
```

**Solution:**
```bash
# Run from project root directory
cd ~/Projects/outre_base/sandbox/ivoris-pipeline

# Or run as module
python -m src.main --daily-extract
```

---

## SQL Query Issues

### STRING_AGG Not Found

**Symptom:**
```
'STRING_AGG' is not a recognized built-in function name
```

**Cause:** SQL Server version < 2017

**Solution:**
```sql
-- Use FOR XML PATH instead (works on older versions)
SELECT
    STUFF((
        SELECT ', ' + l.LEISTUNG
        FROM LEISTUNG l
        WHERE l.PATIENTID = k.PATIENTID AND l.DATUM = k.DATUM
        FOR XML PATH('')
    ), 1, 2, '') AS service_codes
FROM KARTEI k
```

---

### No Data Returned

**Symptom:**
```
Query runs but returns 0 rows
```

**Solution:**
```sql
-- Check if data exists for that date
SELECT COUNT(*) FROM KARTEI WHERE DATUM = '2022-01-18';

-- List available dates
SELECT DISTINCT DATUM FROM KARTEI ORDER BY DATUM;

-- Use a date that has data
```

---

### German Characters (Umlauts) Broken

**Symptom:**
```
M??ller instead of Müller
```

**Solution:**
```python
# Use UTF-8 encoding when writing files
with open(filename, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)  # ensure_ascii=False is key
```

---

## File/Permission Issues

### Permission Denied

**Symptom:**
```
PermissionError: [Errno 13] Permission denied
```

**Solution:**
```bash
# Create output directory
mkdir -p data/output

# Fix permissions
chmod 755 data/output

# Make script executable
chmod +x src/main.py
```

---

### Output Directory Not Found

**Symptom:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/output/...'
```

**Solution:**
```bash
mkdir -p data/output
```

---

## Quick Recovery Commands

### Full Reset

```bash
# Stop everything
docker-compose down

# Clean up
rm -rf data/output/*.json data/output/*.csv

# Fresh start
docker-compose up -d
sleep 15

# Verify
python src/main.py --test-connection
```

### Skip Docker (Use Existing Server)

If Docker keeps failing, connect to an existing SQL Server:

```python
# Change connection string to point to existing server
conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=existing-server.example.com,1433;"  # Remote server
    "DATABASE=DentalDB;"
    "UID=your_user;PWD=your_password;"
    "TrustServerCertificate=yes"
)
```

---

## When All Else Fails

### Show Pre-recorded Demo

If live coding isn't working:
1. Show the output files you prepared earlier
2. Walk through the code without running it
3. Explain what each part does

### Have Backup Files Ready

```bash
# Pre-generate output before the session
python src/main.py --daily-extract --date 2022-01-18

# Keep these files as backup
cp data/output/ivoris_chart_entries_2022-01-18.json data/backup/
```

### Use the Web UI

If CLI fails, fall back to the web UI:
```bash
cd ~/Projects/outre_base/sandbox/ivoris-multi-center
python -m src.cli web
# Open http://localhost:8000/explore
```
