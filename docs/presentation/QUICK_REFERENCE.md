# Quick Reference

**Complete Developer Reference for Ivoris Multi-Center Pipeline**

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Docker & SQL Server](#docker--sql-server)
3. [Database Deep Dive](#database-deep-dive)
4. [CLI Commands Reference](#cli-commands-reference)
5. [Python Code Examples](#python-code-examples)
6. [Project Architecture](#project-architecture)
7. [File-by-File Reference](#file-by-file-reference)
8. [Data Flow](#data-flow)
9. [Web UI API](#web-ui-api)
10. [Troubleshooting](#troubleshooting)

---

## Quick Start

### From Zero to Demo (5 minutes)

```bash
# 1. Navigate
cd sandbox/ivoris-multi-center

# 2. Start SQL Server
docker-compose up -d

# 3. Wait for it
sleep 30

# 4. Install Python deps
pip install -r requirements.txt

# 5. Generate 30 databases with random schemas
python scripts/generate_test_dbs.py

# 6. Generate mapping files
python -m src.cli generate-mappings

# 7. Verify
python -m src.cli list
python -m src.cli benchmark
```

### Daily Development

```bash
# Start Docker (if not running)
docker-compose up -d

# Run benchmark
python -m src.cli benchmark

# Start web UI
python -m src.cli web
# Open http://localhost:8000
```

---

## Docker & SQL Server

### Container Management

```bash
# Start container
docker-compose up -d

# Check status
docker ps | grep ivoris-multi-sqlserver

# View logs
docker logs ivoris-multi-sqlserver
docker logs -f ivoris-multi-sqlserver  # Follow

# Stop container
docker-compose down

# Full reset (delete data)
docker-compose down -v
```

### Connection Details

| Property | Value |
|----------|-------|
| **Host** | `localhost` |
| **Port** | `1434` (mapped from 1433) |
| **User** | `sa` |
| **Password** | `MultiCenter@2024` |
| **Driver** | `ODBC Driver 18 for SQL Server` |
| **Container Name** | `ivoris-multi-sqlserver` |

### Connection String (Python)

```python
conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost,1434;"
    "DATABASE=DentalDB_01;"
    "UID=sa;"
    "PWD=MultiCenter@2024;"
    "TrustServerCertificate=yes;"
)
```

### docker-compose.yml Explained

```yaml
# File: docker-compose.yml
services:
  sqlserver:
    image: mcr.microsoft.com/mssql/server:2019-latest
    platform: linux/amd64                    # Required for Apple Silicon
    container_name: ivoris-multi-sqlserver
    user: root                               # Required for volume permissions
    environment:
      - ACCEPT_EULA=Y                        # Required license acceptance
      - SA_PASSWORD=MultiCenter@2024         # SA password
      - MSSQL_PID=Developer                  # Free developer edition
    ports:
      - "1434:1433"                           # Host:Container
    volumes:
      - sqlserver_data:/var/opt/mssql/data   # Persistent storage
```

---

## Database Deep Dive

### Database Structure

Each center has its own database:

| Center ID | Database Name | Sample Table |
|-----------|---------------|--------------|
| center_01 | DentalDB_01 | KARTEI_MN |
| center_02 | DentalDB_02 | KARTEI_8Y |
| ... | ... | ... |
| center_30 | DentalDB_30 | KARTEI_XQ4 |

### Schema: `ck`

All tables are in the `ck` schema (Clinero Kartei):

```sql
ck.PATIENT_XYZ     -- Patients
ck.KASSEN_ABC      -- Insurance providers
ck.PATKASSE_DEF    -- Patient-insurance links
ck.KARTEI_GHI      -- Chart entries (main table)
ck.LEISTUNG_JKL    -- Services/procedures
```

### Canonical vs Actual Names

**Canonical** (what we want):
```
PATIENT.ID, PATIENT.P_NAME, PATIENT.P_VORNAME
KARTEI.PATNR, KARTEI.DATUM, KARTEI.BEMERKUNG
```

**Actual** (what's in the database - random per center):
```
PATIENT_X7K.ID, PATIENT_X7K.P_NAME_QW2, PATIENT_X7K.P_VORNAME_8M
KARTEI_MN.PATNR_NAN6, KARTEI_MN.DATUM_3A4, KARTEI_MN.BEMERKUNG_R5
```

### SQL: Connect via Container

```bash
# Enter container
docker exec -it ivoris-multi-sqlserver /bin/bash

# Run sqlcmd
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "MultiCenter@2024" -C
```

### SQL: Useful Queries

```sql
-- List all databases
SELECT name FROM sys.databases WHERE database_id > 4;
GO

-- Use specific database
USE DentalDB_01;
GO

-- List tables in ck schema
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'ck';
GO

-- Show columns for a table
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ck' AND TABLE_NAME = 'KARTEI_MN';
GO

-- Sample data from chart table
SELECT TOP 5 * FROM ck.KARTEI_MN;
GO

-- Count entries per date
SELECT DATUM_3A4 as datum, COUNT(*) as entries
FROM ck.KARTEI_MN
GROUP BY DATUM_3A4;
GO

-- Join patient with chart (using actual column names)
SELECT
    p.P_NAME_QW2 as patient_name,
    k.DATUM_3A4 as date,
    k.BEMERKUNG_R5 as entry
FROM ck.PATIENT_X7K p
JOIN ck.KARTEI_MN k ON p.ID = k.PATNR_NAN6
WHERE k.DATUM_3A4 = 20220118;
GO
```

### SQL: Cross-Database Query

```sql
-- Query across all databases (from master)
USE master;
GO

-- Dynamic query to count tables per database
DECLARE @sql NVARCHAR(MAX) = '';
SELECT @sql = @sql +
    'SELECT ''' + name + ''' as db, COUNT(*) as tables FROM ' +
    QUOTENAME(name) + '.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = ''ck'' UNION ALL '
FROM sys.databases
WHERE name LIKE 'DentalDB_%';
SET @sql = LEFT(@sql, LEN(@sql) - 10);  -- Remove last UNION ALL
EXEC sp_executesql @sql;
GO
```

---

## CLI Commands Reference

### Overview

All commands: `python -m src.cli <command> [options]`

| Command | Purpose |
|---------|---------|
| `list` | Show all 30 centers with mapping status |
| `discover-raw` | Query INFORMATION_SCHEMA, show raw tables/columns |
| `generate-mappings` | Create JSON mapping files from discovery |
| `show-mapping` | Display a center's mapping file |
| `extract` | Extract chart entries using mappings |
| `benchmark` | Performance test all centers |
| `web` | Start FastAPI web UI |

### `list` - Show Centers

```bash
python -m src.cli list
```

**Output:**
```
============================================================
Configured Dental Centers
============================================================

  center_01 [mapped]
    Name: Zahnarztpraxis München
    City: München
    Database: DentalDB_01

  center_02 [mapped]
    ...

============================================================
Total: 30 centers
Mapped: 30 centers
============================================================
```

### `discover-raw` - Raw Schema Discovery

```bash
# All centers
python -m src.cli discover-raw

# Specific center
python -m src.cli discover-raw -c center_01
python -m src.cli discover-raw --center center_01
```

**Output:**
```
============================================================
Center: Zahnarztpraxis München (center_01)
Database: DentalDB_01
============================================================

TABLE: ck.KARTEI_MN
  - ID (int, NOT NULL)
  - PATNR_NAN6 (int, NULL)
  - DATUM_3A4 (int, NULL)
  - BEMERKUNG_X7K (nvarchar, NULL)
  - DELKZ (int, NULL)

TABLE: ck.PATIENT_R2Z
  ...
```

### `generate-mappings` - Create Mapping Files

```bash
python -m src.cli generate-mappings
```

**Output:**
```
============================================================
Generated 30 mapping files
============================================================

Files saved to: data/mappings
IMPORTANT: Review and adjust mappings as needed before extraction.
Each file has 'reviewed: false' flag - set to true after review.
```

**Creates:** `data/mappings/center_XX_mapping.json`

### `show-mapping` - View Mapping

```bash
# List available mappings
python -m src.cli show-mapping

# Show specific center
python -m src.cli show-mapping center_01
```

**Output:**
```
============================================================
Mapping: center_01
Database: DentalDB_01
Reviewed: False
============================================================

KARTEI -> KARTEI_MN
  PATNR -> PATNR_NAN6
  DATUM -> DATUM_3A4
  BEMERKUNG -> BEMERKUNG_X7K
  ID -> ID
  DELKZ -> DELKZ

PATIENT -> PATIENT_R2Z
  P_NAME -> P_NAME_QW2
  ...
```

### `extract` - Extract Data

```bash
# All centers, yesterday
python -m src.cli extract

# Specific date
python -m src.cli extract --date 2022-01-18
python -m src.cli extract -d 2022-01-18

# Specific center
python -m src.cli extract -c center_01 --date 2022-01-18

# Output format
python -m src.cli extract --format json
python -m src.cli extract --format csv
python -m src.cli extract --format both  # default

# Parallelism
python -m src.cli extract --workers 10  # default: 5
```

**Output:**
```
============================================================
Extraction Complete
============================================================
Date: 2022-01-18
Centers: 30/30
Total Entries: 180
Total Time: 387ms
============================================================
JSON: data/output/extraction_2022-01-18.json
CSV: data/output/extraction_2022-01-18.csv
```

### `benchmark` - Performance Test

```bash
python -m src.cli benchmark
python -m src.cli benchmark --workers 10
```

**Output:**
```
============================================================
BENCHMARK RESULTS
============================================================
Centers: 30
Total Entries: 180
Total Time: 423ms
============================================================

Per-Center Timing:
  [ok] Zahnarztpraxis München           23ms  (6 entries)
  [ok] Dental Klinik Berlin             21ms  (6 entries)
  ...

============================================================
PASS: Under 5000ms target
============================================================
```

### `web` - Start Web UI

```bash
# Default (port 8000)
python -m src.cli web

# Custom port
python -m src.cli web --port 8080

# Development mode (auto-reload)
python -m src.cli web --reload

# Specific host
python -m src.cli web --host 127.0.0.1
```

**URLs:**
- Home: http://localhost:8000
- Explore: http://localhost:8000/explore
- Metrics: http://localhost:8000/metrics
- Schema Diff: http://localhost:8000/schema-diff

---

## Python Code Examples

### Connect to Database

```python
# File: src/core/config.py (simplified)

import pyodbc

def get_connection(database: str) -> pyodbc.Connection:
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=localhost,1434;"
        f"DATABASE={database};"
        "UID=sa;"
        "PWD=MultiCenter@2024;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)
```

### Discover Schema

```python
# File: src/core/discovery.py (key method)

def discover(self, schema_filter: str = "ck") -> DiscoveredSchema:
    conn = self._get_connection()
    cursor = conn.cursor()

    # Get tables
    cursor.execute("""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = ? AND TABLE_TYPE = 'BASE TABLE'
    """, (schema_filter,))

    tables = []
    for (table_name,) in cursor.fetchall():
        # Get columns for each table
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        """, (schema_filter, table_name))

        columns = [
            DiscoveredColumn(name=row[0], data_type=row[1], ...)
            for row in cursor.fetchall()
        ]
        tables.append(DiscoveredTable(name=table_name, columns=columns))

    return DiscoveredSchema(database=..., tables=tables)
```

### Pattern Matching for Mapping

```python
# File: src/services/mapping_generator.py (simplified)

CANONICAL_TABLES = ["PATIENT", "KARTEI", "KASSEN", "PATKASSE", "LEISTUNG"]
CANONICAL_COLUMNS = {
    "KARTEI": ["PATNR", "DATUM", "BEMERKUNG", "ID", "DELKZ"],
    "PATIENT": ["P_NAME", "P_VORNAME", "ID", "DELKZ"],
    ...
}

def extract_base_name(actual_name: str) -> str:
    """KARTEI_MN -> KARTEI, PATNR_NAN6 -> PATNR"""
    # Try to match against canonical names
    for canonical in CANONICAL_TABLES + flatten(CANONICAL_COLUMNS.values()):
        if actual_name.startswith(canonical + "_") or actual_name == canonical:
            return canonical
    return None

def generate_mapping(discovered: DiscoveredSchema) -> dict:
    mapping = {"tables": {}}

    for table in discovered.tables:
        canonical = extract_base_name(table.name)
        if canonical:
            mapping["tables"][canonical] = {
                "actual_name": table.name,
                "columns": {}
            }
            for col in table.columns:
                col_canonical = extract_base_name(col.name)
                if col_canonical:
                    mapping["tables"][canonical]["columns"][col_canonical] = {
                        "actual_name": col.name
                    }

    return mapping
```

### Build Dynamic SQL

```python
# File: src/adapters/center_adapter.py (key method)

def extract_chart_entries(self, date: int) -> list[ChartEntry]:
    """Generate SQL using mapping, execute, return canonical model."""

    # Get actual table/column names from mapping
    kartei = self.mapping.tables["KARTEI"]
    patient = self.mapping.tables["PATIENT"]
    patkasse = self.mapping.tables["PATKASSE"]
    kassen = self.mapping.tables["KASSEN"]

    sql = f"""
        SELECT
            k.{kartei.columns["DATUM"]} as datum,
            k.{kartei.columns["PATNR"]} as patient_id,
            kas.{kassen.columns["ART"]} as insurance_status,
            k.{kartei.columns["BEMERKUNG"]} as entry
        FROM ck.{kartei.actual_name} k
        JOIN ck.{patkasse.actual_name} pk ON k.{kartei.columns["PATNR"]} = pk.{patkasse.columns["PATNR"]}
        JOIN ck.{kassen.actual_name} kas ON pk.{patkasse.columns["KASSENID"]} = kas.ID
        WHERE k.{kartei.columns["DATUM"]} = ?
          AND k.DELKZ = 0
    """

    cursor = self.conn.cursor()
    cursor.execute(sql, (date,))

    return [
        ChartEntry(
            date=row.datum,
            patient_id=row.patient_id,
            insurance_status=row.insurance_status,
            chart_entry=row.entry
        )
        for row in cursor.fetchall()
    ]
```

### Parallel Extraction

```python
# File: src/services/extraction.py (key method)

from concurrent.futures import ThreadPoolExecutor, as_completed

def extract_all(self, target_date: date, max_workers: int = 5) -> ExtractionResult:
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(self._extract_center, center, target_date): center
            for center in self.config.centers
        }

        for future in as_completed(futures):
            center = futures[future]
            try:
                entries = future.result()
                results.append(CenterResult(
                    center_id=center.id,
                    entries=entries,
                    duration_ms=...
                ))
            except Exception as e:
                results.append(CenterResult(
                    center_id=center.id,
                    entries=[],
                    error=str(e)
                ))

    return ExtractionResult(results=results, ...)
```

---

## Project Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLI / Web UI                            │
│  python -m src.cli <cmd>  |  http://localhost:8000              │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       ExtractionService                          │
│  src/services/extraction.py                                      │
│  - Parallel execution (ThreadPoolExecutor)                       │
│  - Aggregates results from all centers                           │
│  - Exports to JSON/CSV                                           │
└───────────────────────────────┬─────────────────────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            ▼                   ▼                   ▼
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│   CenterAdapter   │ │   CenterAdapter   │ │   CenterAdapter   │
│   center_01       │ │   center_02       │ │   center_N        │
│ adapters/center_  │ │                   │ │                   │
│   adapter.py      │ │                   │ │                   │
└─────────┬─────────┘ └─────────┬─────────┘ └─────────┬─────────┘
          │                     │                     │
          ▼                     ▼                     ▼
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│  SchemaMapping    │ │  SchemaMapping    │ │  SchemaMapping    │
│  (from JSON)      │ │  (from JSON)      │ │  (from JSON)      │
│ core/introspector │ │                   │ │                   │
└─────────┬─────────┘ └─────────┬─────────┘ └─────────┬─────────┘
          │                     │                     │
          ▼                     ▼                     ▼
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│   DentalDB_01     │ │   DentalDB_02     │ │   DentalDB_N      │
│   (SQL Server)    │ │   (SQL Server)    │ │   (SQL Server)    │
└───────────────────┘ └───────────────────┘ └───────────────────┘
```

### Data Flow: Discovery → Mapping → Extraction

```
1. DISCOVERY (discover-raw)
   Database INFORMATION_SCHEMA
        │
        ▼
   DiscoveredSchema (dataclass)
   - database: "DentalDB_01"
   - tables: [DiscoveredTable, ...]
   - columns: [DiscoveredColumn, ...]

2. MAPPING GENERATION (generate-mappings)
   DiscoveredSchema
        │
        ▼
   Pattern Matching
   "KARTEI_MN" → "KARTEI"
   "PATNR_NAN6" → "PATNR"
        │
        ▼
   JSON Mapping File
   data/mappings/center_01_mapping.json

3. EXTRACTION (extract)
   JSON Mapping File
        │
        ▼
   SchemaMapping (dataclass)
        │
        ▼
   CenterAdapter (generates SQL)
        │
        ▼
   ChartEntry[] (canonical model)
        │
        ▼
   JSON/CSV Output
```

---

## File-by-File Reference

### Configuration Layer

| File | Purpose | Key Contents |
|------|---------|--------------|
| `config/centers.yml` | Center definitions | 30 centers with id, name, database, city |
| `docker-compose.yml` | SQL Server container | Port 1434, SA password |
| `requirements.txt` | Python dependencies | pyodbc, fastapi, uvicorn, pyyaml, jinja2 |

### Core Layer (`src/core/`)

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `config.py` | Load centers.yml | `load_config() -> Config` |
| `discovery.py` | Raw INFORMATION_SCHEMA queries | `SchemaDiscovery.discover() -> DiscoveredSchema` |
| `introspector.py` | Load/cache mapping files | `load_mapping(center_id) -> SchemaMapping` |
| `schema_mapping.py` | Mapping dataclass | `SchemaMapping`, `TableMapping`, `ColumnMapping` |

### Service Layer (`src/services/`)

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `extraction.py` | Parallel extraction | `ExtractionService.extract_all() -> ExtractionResult` |
| `mapping_generator.py` | Generate mapping JSON | `generate_all_mappings(config, output_dir)` |

### Adapter Layer (`src/adapters/`)

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `center_adapter.py` | SQL generation per center | `CenterAdapter.extract_chart_entries(date) -> list[ChartEntry]` |

### Model Layer (`src/models/`)

| File | Purpose | Key Classes |
|------|---------|-------------|
| `chart_entry.py` | Canonical output model | `ChartEntry(date, patient_id, insurance_status, chart_entry)` |

### CLI Layer (`src/cli/`)

| File | Purpose | Key Functions |
|------|---------|---------------|
| `main.py` | All CLI commands | `cmd_list`, `cmd_discover_raw`, `cmd_extract`, `cmd_benchmark`, `cmd_web` |

### Web Layer (`src/web/`)

| File | Purpose |
|------|---------|
| `app.py` | FastAPI app with routes |
| `templates/base.html` | Base layout with sidebar |
| `templates/explore.html` | Center exploration page |
| `templates/metrics.html` | Benchmark dashboard |
| `templates/schema_diff.html` | Schema comparison |

### Data Layer (`data/`)

| Directory | Purpose | File Pattern |
|-----------|---------|--------------|
| `mappings/` | Discovered → canonical mapping | `center_XX_mapping.json` |
| `ground_truth/` | What generator actually created | `center_XX_ground_truth.json` |
| `output/` | Extraction results | `extraction_YYYY-MM-DD.json/csv` |

### Scripts (`scripts/`)

| File | Purpose |
|------|---------|
| `generate_test_dbs.py` | Create 30 databases with random schemas |

---

## Web UI API

### Pages

| Route | Template | Purpose |
|-------|----------|---------|
| `GET /` | redirect | Redirects to /explore |
| `GET /explore` | explore.html | Browse centers, view mappings |
| `GET /metrics` | metrics.html | Benchmark dashboard |
| `GET /schema-diff` | schema_diff.html | Compare discovered vs ground truth |

### API Endpoints

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/centers` | GET | List all centers |
| `/api/centers/{id}` | GET | Get center details |
| `/api/centers/{id}/mapping` | GET | Get center's mapping |
| `/api/centers/{id}/extract` | POST | Extract data for date |
| `/api/benchmark` | POST | Run benchmark for selected centers |
| `/api/schema-diff/{id}` | GET | Compare discovered vs ground truth |

### Example API Calls

```bash
# List centers
curl http://localhost:8000/api/centers

# Get specific center
curl http://localhost:8000/api/centers/center_01

# Get mapping
curl http://localhost:8000/api/centers/center_01/mapping

# Extract data
curl -X POST http://localhost:8000/api/centers/center_01/extract \
  -H "Content-Type: application/json" \
  -d '{"date": "2022-01-18"}'

# Benchmark
curl -X POST http://localhost:8000/api/benchmark \
  -H "Content-Type: application/json" \
  -d '{"center_ids": ["center_01", "center_02"]}'
```

---

## Troubleshooting

### Docker Issues

```bash
# Container won't start
docker logs ivoris-multi-sqlserver

# Port already in use
lsof -i :1434
# Kill process or change port in docker-compose.yml

# Full reset
docker-compose down -v
docker-compose up -d
sleep 30
```

### Database Issues

```bash
# Connection refused
# 1. Check Docker is running
docker ps | grep ivoris

# 2. Check port
nc -zv localhost 1434

# 3. Check credentials
python -c "
import pyodbc
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=localhost,1434;DATABASE=master;'
    'UID=sa;PWD=MultiCenter@2024;TrustServerCertificate=yes;'
)
print('Connected!')
"
```

### ODBC Driver Issues

```bash
# Check installed drivers
odbcinst -q -d

# Install on macOS
brew install microsoft/mssql-release/msodbcsql18

# Install on Ubuntu
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

### Python Issues

```bash
# Import errors
cd sandbox/ivoris-multi-center  # Must be in project root
pip install -r requirements.txt

# Module not found
python -m src.cli list  # Use -m, not direct path
```

### Mapping Issues

```bash
# No mapping files
python -m src.cli generate-mappings

# Mapping accuracy issues
python -m src.cli show-mapping center_01
# Compare with ground truth in data/ground_truth/
```

### Web UI Issues

```bash
# Port in use
pkill -f uvicorn
python -m src.cli web

# Template errors
# Check src/web/templates/ for syntax errors

# Static files not loading
# Check src/web/static/ exists
```
