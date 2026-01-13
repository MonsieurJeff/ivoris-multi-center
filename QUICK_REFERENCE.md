# Quick Reference

**Developer Reference for Both Ivoris Projects**

> **Unified Presentation:** This reference covers both `ivoris-pipeline` (main challenge) and `ivoris-multi-center` (extension).

---

## The Two Projects

| Project | Type | Location | Purpose |
|---------|------|----------|---------|
| **ivoris-pipeline** | Main Challenge | `sandbox/ivoris-pipeline` | Daily extraction from ONE database |
| **ivoris-multi-center** | Extension | `sandbox/ivoris-multi-center` | 30 databases with random schemas |

---

## Database Architecture

### Docker Containers

| Container | Port | Project | Databases |
|-----------|------|---------|-----------|
| `ivoris-sqlserver` | 1433 | ivoris-pipeline | 1 (`DentalDB`) |
| `ivoris-multi-sqlserver` | 1434 | ivoris-multi-center | 30 (`DentalDB_01`-`DentalDB_30`) |

### Why 30 Databases?

The multi-center extension demonstrates **real-world scale**:

- **30 dental centers** across Germany (20), Austria (5), Switzerland (5)
- **Each center = separate database** (production isolation)
- **Each database has RANDOM schema names** (the hard problem)
- **Same logical tables, different physical names**

```
DentalDB_01: KARTEI_MN   → columns: PATNR_NAN6, DATUM_3A4
DentalDB_02: KARTEI_8Y   → columns: PATNR_DZ,   DATUM_QW2
DentalDB_30: KARTEI_LA   → columns: PATNR_BE,   DATUM_ZH
```

> "You can't write one SQL query that works everywhere. Each center needs its own mapping."

---

## ivoris-pipeline Commands

**Location:** `~/Projects/outre_base/sandbox/ivoris-pipeline`

```bash
cd ~/Projects/outre_base/sandbox/ivoris-pipeline

# Setup (from scratch)
docker-compose up -d && sleep 30    # Start SQL Server
./scripts/restore-database.sh       # Restore DentalDB from backup
pip install -r requirements.txt     # Install dependencies

# Daily usage
python src/main.py --test-connection           # Test DB connection
python src/main.py --daily-extract             # Extract yesterday's data
python src/main.py --daily-extract --date 2022-01-18  # Specific date
python src/main.py --daily-extract --format csv       # CSV output
python src/main.py --daily-extract --format json      # JSON output

# View output
cat data/output/daily_extract_2022-01-18.json
cat data/output/daily_extract_2022-01-18.csv
```

### ivoris-pipeline Output Format

```json
{
  "extraction_timestamp": "2026-01-13T06:00:00",
  "target_date": "2022-01-18",
  "record_count": 4,
  "entries": [
    {
      "date": "2022-01-18",
      "patient_id": 1,
      "insurance_status": "GKV",
      "insurance_name": "DAK Gesundheit",
      "chart_entry": "Kontrolle, Befund unauffällig",
      "service_codes": ["01", "Ä1"]
    }
  ]
}
```

### Required Fields (Main Challenge)

| Field | German | Source |
|-------|--------|--------|
| date | Datum | KARTEI.DATUM |
| patient_id | Pat-ID | KARTEI.PATNR |
| insurance_status | Versicherungsstatus | KASSEN.ART |
| chart_entry | Karteikarteneintrag | KARTEI.BEMERKUNG |
| service_codes | Leistungen | LEISTUNG.LEISTUNG |

---

## ivoris-multi-center Commands

**Location:** `~/Projects/outre_base/sandbox/ivoris-multi-center`

```bash
cd ~/Projects/outre_base/sandbox/ivoris-multi-center

# Setup (from scratch)
docker-compose up -d && sleep 30         # Start SQL Server
python scripts/generate_test_dbs.py      # Generate 30 random-schema databases
pip install -r requirements.txt          # Install dependencies
python -m src.cli generate-mappings      # Create mapping files

# Daily usage
python -m src.cli list                   # Show all 30 centers
python -m src.cli benchmark              # Performance test (target: <5s)
python -m src.cli web                    # Start web UI
```

> **Full multi-center reference continues below...**

---

## Table of Contents

1. [Quick Start Commands](#quick-start-commands)
2. [Docker & Database](#docker--database)
3. [CLI Commands](#cli-commands)
4. [Database Exploration](#database-exploration)
5. [Web UI](#web-ui)
6. [Project Structure](#project-structure)
7. [Key Files Reference](#key-files-reference)
8. [The Story (For Presentation)](#the-story-for-presentation)

---

## Quick Start Commands

```bash
# Navigate to project
cd sandbox/ivoris-multi-center

# Full setup (from scratch)
docker-compose up -d          # 1. Start SQL Server
sleep 30                       # 2. Wait for SQL Server
pip install -r requirements.txt  # 3. Install dependencies
python scripts/generate_test_dbs.py  # 4. Generate 30 databases with random schemas
python -m src.cli generate-mappings  # 5. Create mapping files

# Daily workflow
python -m src.cli benchmark    # Run performance test
python -m src.cli web          # Start web UI at http://localhost:8000
```

---

## Docker & Database

### Start/Stop SQL Server

```bash
# Start SQL Server container
docker-compose up -d

# Check if running
docker ps | grep ivoris-multi-sqlserver

# View logs
docker logs ivoris-multi-sqlserver

# Stop SQL Server
docker-compose down

# Stop and remove volumes (full reset)
docker-compose down -v
```

### Connection Details

| Setting | Value |
|---------|-------|
| **Host** | localhost |
| **Port** | 1434 |
| **User** | sa |
| **Password** | MultiCenter@2024 |
| **Driver** | ODBC Driver 18 for SQL Server |

### Connect with sqlcmd (inside container)

```bash
# Enter container
docker exec -it ivoris-multi-sqlserver /bin/bash

# Connect with sqlcmd
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "MultiCenter@2024" -C

# List databases
SELECT name FROM sys.databases;
GO

# Use a specific database
USE DentalDB_01;
GO

# Show tables
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'ck';
GO

# Show columns for a table
SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'KARTEI_XYZ';
GO
```

### Connect with Python (quick test)

```python
import pyodbc

conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost,1434;"
    "DATABASE=DentalDB_01;"
    "UID=sa;"
    "PWD=MultiCenter@2024;"
    "TrustServerCertificate=yes;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# List tables in ck schema
cursor.execute("""
    SELECT TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'ck'
""")

for row in cursor.fetchall():
    print(row[0])
```

---

## CLI Commands

All commands use: `python -m src.cli <command>`

### List Centers

```bash
# Show all 30 configured centers with mapping status
python -m src.cli list
```

### Discover Raw Schema

```bash
# Discover schema for ALL centers
python -m src.cli discover-raw

# Discover schema for ONE center
python -m src.cli discover-raw -c center_01
python -m src.cli discover-raw --center center_15
```

Output shows actual table/column names like:
```
TABLE: ck.KARTEI_MN
  - ID (int, NOT NULL)
  - PATNR_NAN6 (int, NULL)
  - DATUM_3A4 (int, NULL)
  - BEMERKUNG_X7K (nvarchar, NULL)
  - DELKZ (int, NULL)
```

### Generate Mappings

```bash
# Generate mapping files for all centers
python -m src.cli generate-mappings
```

Creates JSON files in `data/mappings/`:
- `center_01_mapping.json`
- `center_02_mapping.json`
- ... (30 files)

### Show Mapping

```bash
# List available mappings
python -m src.cli show-mapping

# Show specific center mapping
python -m src.cli show-mapping center_01
```

### Extract Data

```bash
# Extract from ALL centers for specific date
python -m src.cli extract --date 2022-01-18

# Extract from ONE center
python -m src.cli extract -c center_01 --date 2022-01-18

# Output formats
python -m src.cli extract --format json
python -m src.cli extract --format csv
python -m src.cli extract --format both   # default

# Control parallelism
python -m src.cli extract --workers 10
```

### Benchmark Performance

```bash
# Run benchmark (clears cache, measures full time)
python -m src.cli benchmark

# With more workers
python -m src.cli benchmark --workers 10
```

Target: <5 seconds for 30 centers
Typical: ~380ms with pre-loaded mappings

### Web UI

```bash
# Start web server (default port 8000)
python -m src.cli web

# Custom port
python -m src.cli web --port 8080

# Development mode (auto-reload)
python -m src.cli web --reload
```

Open: http://localhost:8000

---

## Database Exploration

### Understanding the Random Schema

Each center has:
- **5 tables**: PATIENT, KASSEN, PATKASSE, KARTEI, LEISTUNG
- **Random suffixes per table**: KARTEI_MN, KARTEI_8Y, KARTEI_XQ4...
- **Random suffixes per column**: PATNR_NAN6, PATNR_DZ, PATNR_R2Z5...

### Canonical Schema (What we expect)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| **PATIENT** | Patients | ID, P_NAME, P_VORNAME |
| **KASSEN** | Insurance providers | ID, NAME, ART |
| **PATKASSE** | Patient-insurance link | PATNR, KASSENID |
| **KARTEI** | Chart entries | PATNR, DATUM, BEMERKUNG |
| **LEISTUNG** | Services | PATIENTID, DATUM, LEISTUNG |

### Example: Raw vs Mapped

**In database (raw):**
```sql
SELECT PATNR_NAN6, DATUM_3A4, BEMERKUNG_X7K
FROM ck.KARTEI_MN
WHERE DATUM_3A4 = 20220118
```

**What we discover:**
```
KARTEI_MN → canonical KARTEI
PATNR_NAN6 → canonical PATNR
DATUM_3A4 → canonical DATUM
BEMERKUNG_X7K → canonical BEMERKUNG
```

### Query to See All Tables Across Centers

```sql
-- Connect to master, then:
EXEC sp_MSforeachdb 'USE [?];
SELECT DB_NAME() as db, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = ''ck'''
```

---

## Web UI

### Pages

| Page | URL | Purpose |
|------|-----|---------|
| **Explore** | http://localhost:8000/explore | Browse centers, view mappings, extract data |
| **Metrics** | http://localhost:8000/metrics | Multi-select, benchmark, export results |
| **Schema Diff** | http://localhost:8000/schema-diff | Compare discovered vs ground truth |

### Explore Page Features

1. Select center from dropdown
2. View center details (name, city, database)
3. See schema mapping (canonical → actual)
4. Extract data for a specific date
5. View results in table format

### Metrics Dashboard Features

1. **Select Centers**: Click individual or "Select All"
2. **Run Benchmark**: Parallel extraction with timing
3. **View Results**:
   - Summary cards (centers, entries, duration, pass/fail)
   - Bar chart visualization
   - Per-center timing table
4. **Export**: JSON or CSV download

### Schema Diff Features

1. Compare discovered mapping vs ground truth
2. See accuracy percentage
3. Table-by-table comparison
4. Visual indicators (checkmarks for matches)

---

## Project Structure

```
ivoris-multi-center/
├── src/
│   ├── cli/                    # CLI commands
│   │   └── main.py             # All CLI logic (list, discover, extract...)
│   │
│   ├── core/                   # Core components
│   │   ├── config.py           # Load centers.yml configuration
│   │   ├── discovery.py        # Raw schema discovery (INFORMATION_SCHEMA)
│   │   ├── introspector.py     # Load/cache mapping files
│   │   └── schema_mapping.py   # SchemaMapping dataclass
│   │
│   ├── adapters/               # Database adapters
│   │   └── center_adapter.py   # SQL query generation using mappings
│   │
│   ├── services/               # Business logic
│   │   ├── extraction.py       # Parallel extraction (ThreadPoolExecutor)
│   │   └── mapping_generator.py # Generate mapping files from discovery
│   │
│   ├── models/                 # Data models
│   │   └── chart_entry.py      # ChartEntry dataclass
│   │
│   └── web/                    # Web UI
│       ├── app.py              # FastAPI application
│       ├── templates/          # Jinja2 HTML templates
│       │   ├── base.html       # Base layout with sidebar
│       │   ├── explore.html    # Center exploration page
│       │   ├── metrics.html    # Benchmark dashboard
│       │   └── schema_diff.html # Schema comparison
│       └── static/             # CSS/JS assets
│
├── config/
│   └── centers.yml             # 30 dental centers configuration
│
├── data/
│   ├── mappings/               # Per-center mapping JSON files
│   │   ├── center_01_mapping.json
│   │   └── ...
│   ├── ground_truth/           # Generator's actual schema (for validation)
│   │   ├── center_01_ground_truth.json
│   │   └── ...
│   └── output/                 # Extraction output (JSON/CSV)
│
├── scripts/
│   └── generate_test_dbs.py    # Creates 30 databases with random schemas
│
├── docker-compose.yml          # SQL Server container
├── requirements.txt            # Python dependencies
├── README.md                   # Project overview
├── CHALLENGE.md                # Challenge requirements
├── ACCEPTANCE.md               # Gherkin acceptance criteria
└── PRESENTATION.md             # Loom video script
```

---

## Key Files Reference

### Configuration

| File | Path | Purpose |
|------|------|---------|
| Centers config | `config/centers.yml` | All 30 dental centers (id, name, database) |
| Docker | `docker-compose.yml` | SQL Server container on port 1434 |
| Dependencies | `requirements.txt` | Python packages |

### Core Logic

| File | Path | Purpose |
|------|------|---------|
| CLI | `src/cli/main.py` | All CLI commands |
| Config loader | `src/core/config.py` | Parse centers.yml |
| Discovery | `src/core/discovery.py` | Query INFORMATION_SCHEMA |
| Mapping loader | `src/core/introspector.py` | Load/cache JSON mappings |
| Schema model | `src/core/schema_mapping.py` | SchemaMapping dataclass |

### Services

| File | Path | Purpose |
|------|------|---------|
| Extraction | `src/services/extraction.py` | ThreadPoolExecutor parallel extraction |
| Mapping gen | `src/services/mapping_generator.py` | Generate mapping files from raw discovery |

### Adapters

| File | Path | Purpose |
|------|------|---------|
| Center adapter | `src/adapters/center_adapter.py` | Generate SQL with actual table/column names |

### Data

| File | Path | Purpose |
|------|------|---------|
| Mapping files | `data/mappings/<center_id>_mapping.json` | Discovered schema → canonical mapping |
| Ground truth | `data/ground_truth/<center_id>_ground_truth.json` | What generator actually created |
| Output | `data/output/` | Extraction results (JSON/CSV) |

---

## The Story (For Presentation)

> **See Also:** [docs/presentation/STORY.md](docs/presentation/STORY.md) for the full 5-act unified narrative.

### The Unified Narrative

| Act | Project | Key Message |
|-----|---------|-------------|
| **Act 1: The Ask** | pipeline | Original German requirement, 5 fields |
| **Act 2: The Solution** | pipeline | Clean extraction, CSV/JSON output |
| **Act 3: The Pivot** | - | "But what about 30 centers with random schemas?" |
| **Act 4: The Extension** | multi-center | Pattern-based discovery, parallel extraction |
| **Act 5: The Proof** | multi-center | 466ms for 30 centers, 10x faster than target |

### The Pivot Line (Memorize This!)

> "So the main challenge is done. But then I started thinking... Clinero doesn't manage one dental practice. They manage many. And here's the thing about Ivoris: each installation can have **randomly generated** table and column names. Let me show you."

### Act 4 Detail: The Multi-Center Problem

> "30 dental centers across Germany, Austria, and Switzerland. Same software, but each has a **randomly generated schema**. Tables like `KARTEI_MN`, `KARTEI_8Y` - every center different. Columns too: `PATNR_NAN6`, `PATNR_DZ`. No pattern across centers."

**Key point**: Can't write static SQL. Need dynamic schema discovery.

### Act 4 Detail: The Solution Architecture

```
Raw Discovery → Mapping Files → Parallel Extraction → Unified Output
```

1. **Raw Discovery** (`src/core/discovery.py`)
   - Query `INFORMATION_SCHEMA.TABLES` and `INFORMATION_SCHEMA.COLUMNS`
   - No interpretation, just facts

2. **Mapping Generator** (`src/services/mapping_generator.py`)
   - Pattern matching: `KARTEI_XYZ` → `KARTEI`
   - Creates JSON mapping files with `reviewed: false`

3. **Manual Review Workflow**
   - Human reviews mapping files
   - Sets `reviewed: true` when verified

4. **Parallel Extraction** (`src/services/extraction.py`)
   - ThreadPoolExecutor for concurrent database access
   - Each center uses its own mapping

5. **Unified Output**
   - Same canonical format regardless of source schema
   - JSON and CSV exports

### Act 3: Live Demo Flow

1. **Show the centers**: `python -m src.cli list`
2. **Raw discovery**: `python -m src.cli discover-raw -c center_01`
3. **View mapping**: `python -m src.cli show-mapping center_01`
4. **Extract data**: `python -m src.cli extract --date 2022-01-18 -c center_01`
5. **Benchmark**: `python -m src.cli benchmark`
6. **Web UI**: `python -m src.cli web` → http://localhost:8000

### Act 4: The Results

- **30 centers** with random schemas
- **Pattern-based discovery** works for all
- **Manual review workflow** for production safety
- **<500ms** for 30 centers (target was <5s)
- **Web UI** for exploration and metrics

### Key Technical Decisions

| Decision | Why |
|----------|-----|
| JSON mapping files | Human-readable, version-controllable |
| `reviewed: false` flag | Production safety, human approval |
| Ground truth separation | Validate discovery accuracy |
| ThreadPoolExecutor | Simple parallelism, good enough for 30 |
| FastAPI + Jinja2 | Quick to build, familiar patterns |

---

## Troubleshooting

### SQL Server won't start

```bash
# Check if port 1434 is in use
lsof -i :1434

# Check Docker logs
docker logs ivoris-multi-sqlserver

# Full reset
docker-compose down -v
docker-compose up -d
```

### No mapping files found

```bash
# Generate them
python -m src.cli generate-mappings
```

### ODBC Driver not found

```bash
# macOS (Homebrew)
brew install microsoft/mssql-release/msodbcsql18

# Or check installed drivers
odbcinst -q -d
```

### Python import errors

```bash
# Make sure you're in the right directory
cd sandbox/ivoris-multi-center

# Install dependencies
pip install -r requirements.txt

# Run as module
python -m src.cli <command>
```
