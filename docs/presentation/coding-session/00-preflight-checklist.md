# Pre-Flight Checklist

**Run 30 minutes before the coding session**

---

## Quick Verification (2 minutes)

```bash
cd ~/Projects/outre_base/sandbox/ivoris-pipeline

# Run all checks
./preflight.sh  # If you create this script
```

Or manually:

---

## 1. Docker Environment

### □ Docker Desktop Running?

```bash
docker info > /dev/null 2>&1 && echo "✓ Docker running" || echo "✗ Start Docker Desktop"
```

### □ SQL Server Container Up?

```bash
docker ps | grep ivoris-sqlserver && echo "✓ Container running" || echo "✗ Run: docker-compose up -d"
```

**If not running:**
```bash
docker-compose up -d
sleep 10  # Wait for SQL Server to start
```

### □ Container Healthy?

```bash
docker logs ivoris-sqlserver 2>&1 | tail -5
# Should see: "SQL Server is now ready for client connections"
```

---

## 2. Database Connection

### □ Can Connect?

```bash
docker exec ivoris-sqlserver /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P 'YourStrong@Passw0rd' \
  -Q "SELECT 'Connection OK'" -h -1
```

**Expected:** `Connection OK`

### □ Database Exists?

```bash
docker exec ivoris-sqlserver /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P 'YourStrong@Passw0rd' \
  -Q "SELECT name FROM sys.databases WHERE name = 'DentalDB'" -h -1
```

**Expected:** `DentalDB`

### □ Tables Have Data?

```bash
docker exec ivoris-sqlserver /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P 'YourStrong@Passw0rd' -d DentalDB \
  -Q "SELECT 'KARTEI=' + CAST(COUNT(*) AS VARCHAR) FROM KARTEI" -h -1
```

**Expected:** `KARTEI=6` (or more)

---

## 3. Python Environment

### □ Virtual Environment?

```bash
cd ~/Projects/outre_base/sandbox/ivoris-pipeline
source .venv/bin/activate
python --version
```

**Expected:** `Python 3.10+`

### □ Dependencies Installed?

```bash
python -c "import pyodbc; print('✓ pyodbc installed')"
```

### □ Script Runs?

```bash
python src/main.py --test-connection
```

**Expected:** `✓ Database connection successful`

---

## 4. Test Extraction

### □ Extraction Works?

```bash
python src/main.py --daily-extract --date 2022-01-18 --format json
```

**Expected:** `Saved 6 entries to data/output/ivoris_chart_entries_2022-01-18.json`

### □ Output File Valid?

```bash
cat data/output/ivoris_chart_entries_2022-01-18.json | head -20
```

**Expected:** Valid JSON with entries

---

## 5. Screen Setup

### □ Terminal Font Size

```bash
# Increase font size for readability
# macOS Terminal: Cmd + to increase
# iTerm2: Cmd + to increase
# VS Code: Ctrl/Cmd + to increase

# Recommended: 16-18pt for screen sharing
```

### □ Terminal Window Size

- **Width:** At least 120 characters
- **Height:** At least 40 lines
- **Tip:** Use split pane (left: commands, right: file viewer)

### □ Clear Terminal History

```bash
clear
history -c  # Optional: clear history for clean start
```

---

## 6. Files Ready

### □ Documentation Open?

Open in browser or second screen:
- `docs/presentation/coding-session/README.md`
- `docs/presentation/coding-session/CHEATSHEET.md`

### □ Output Folder Clean?

```bash
# Optional: remove old outputs for clean demo
rm -f data/output/*.json data/output/*.csv
```

---

## 7. Screen Sharing (if remote)

### □ Correct Screen Selected?

- Share the terminal window, not entire desktop
- Or share specific application window

### □ Notifications Disabled?

```bash
# macOS: Enable Do Not Disturb
# Windows: Enable Focus Assist
```

### □ Sensitive Info Hidden?

- Close email, Slack, personal browser tabs
- Check terminal history for passwords

---

## Quick Reset (If Something Fails)

```bash
# Nuclear option: restart everything
cd ~/Projects/outre_base/sandbox/ivoris-pipeline
docker-compose down
docker-compose up -d
sleep 15
python src/main.py --test-connection
```

---

## Checklist Summary

```
□ Docker Desktop running
□ SQL Server container up
□ Database connection works
□ Test data present (KARTEI has rows)
□ Python venv activated
□ pyodbc installed
□ Test extraction succeeds
□ Terminal font size increased
□ Screen sharing ready
□ Notifications disabled
```

**All green? You're ready!** 🚀
