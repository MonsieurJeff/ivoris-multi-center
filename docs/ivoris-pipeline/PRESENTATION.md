# Loom Recording Guide
## Ivoris Extraction Pipeline — Main + Extension

**Duration:** 6-7 min | **Format:** Loom screen recording

**All files shown are from `ivoris-multi-center/`**

---

## THE HOOK (10 sec)

**SAY:**
> "I was asked to build a daily extraction pipeline for dental software. I built that. Then I asked: what happens at scale? I built that too."

---

# DIRECT STEPS OVERVIEW

```
Step 0: Understand the requirement     → 5 fields → CSV/JSON
Step 1: Explore the database           → Identify tables & columns
Step 2: Write the 4-table JOIN         → KARTEI + PATIENT + PATKASSE + KASSEN
Step 3: Query service codes            → LEISTUNG table
Step 4: Map insurance status           → GKV / PKV / Selbstzahler
Step 5: Export to CSV + JSON           → Done
```

---

# PART 1: MAIN CHALLENGE (3 min)

## 1.1 The Requirement (20 sec)

**SHOW:** Terminal or state verbally

**SAY:**
- "Daily extraction from Ivoris dental software"
- "5 required fields: Date, Patient ID, Insurance Status, Chart Entry, Service Codes"
- "Output: CSV and JSON"

---

## 1.2 Database Setup (Context - 15 sec)

**SAY:**
- "The challenge provided a SQL Server backup file: `DentalDB.bak`"
- "I restored it to a Docker container for local development"
- "This gives me the exact schema and sample data from the challenge"

**Setup steps (don't show in video, just explain if asked):**
```bash
# 1. Start SQL Server in Docker
docker-compose up -d

# 2. Copy backup file into container
docker cp DentalDB.bak ivoris-sqlserver:/var/opt/mssql/backup/

# 3. Restore database
docker exec ivoris-sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'Clinero2026' -C \
  -Q "RESTORE DATABASE DentalDB FROM DISK = '/var/opt/mssql/backup/DentalDB.bak' ..."
```

---

## 1.3 Explore the Database (Optional - 30 sec)

**1.3.1 Start Docker (SQL Server + 30 databases):**
```bash
docker-compose up -d
```

**1.3.2 List all databases:**
```bash
docker exec ivoris-multi-sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'Clinero2026' -C \
  -Q "SELECT name FROM sys.databases WHERE name LIKE 'DentalDB%'"
```

**1.3.3 List tables in a database:**
```bash
docker exec ivoris-multi-sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'Clinero2026' -C -d DentalDB_01 \
  -Q "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='ck'"
```

**1.3.4 Preview data from KARTEI:**
```bash
docker exec ivoris-multi-sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'Clinero2026' -C -d DentalDB_01 \
  -Q "SELECT TOP 3 * FROM ck.KARTEI"
```

**SAY:**
- "30 databases — one per dental center"
- "5 tables in each: KARTEI, PATIENT, PATKASSE, KASSEN, LEISTUNG"
- "KARTEI is the main table — contains chart entries"
- "Need to JOIN to get insurance info"

---

## 1.4 The Database Query (45 sec)

**SHOW:** `src/adapters/center_adapter.py` (lines 86-101)

```python
query = f"""
    SELECT
        k.ID as KARTEI_ID,
        k.{k_patnr} as PATNR,
        k.{k_datum} as DATUM,
        k.{k_bemerkung} as BEMERKUNG,
        ka.{ka_name} as KASSE_NAME,
        ka.{ka_art} as KASSE_ART
    FROM ck.{t_kartei} k
    LEFT JOIN ck.{t_patient} p ON k.{k_patnr} = p.ID
    LEFT JOIN ck.{t_patkasse} pk ON k.{k_patnr} = pk.{pk_patnr}
    LEFT JOIN ck.{t_kassen} ka ON pk.{pk_kassenid} = ka.{ka_id}
    WHERE k.{k_datum} = ?
    AND (k.{k_delkz} = 0 OR k.{k_delkz} IS NULL)
    ORDER BY k.{k_patnr}, k.ID
"""
```

**SAY:**
- "4-table JOIN: KARTEI, PATIENT, PATKASSE, KASSEN"
- "KARTEI is the chart entry table — the core data"
- "JOINs bring in patient info and insurance details"
- "Filtered by date and soft-delete flag"

---

## 1.5 Service Codes Aggregation (30 sec)

**SHOW:** `src/adapters/center_adapter.py` (lines 131-161)

**SAY:**
- "Second query: LEISTUNG table for service codes"
- "Grouped by patient ID"
- "Multiple services per patient, deduplicated"

---

## 1.6 Insurance Status Mapping (20 sec)

**SHOW:** `src/adapters/center_adapter.py` (lines 163-169)

```python
def _map_insurance(self, kasse_art: str | None) -> str:
    if not kasse_art:
        return "Selbstzahler"
    if str(kasse_art).upper() == "P":
        return "PKV"
    return "GKV"
```

**SAY:**
- "Maps KASSE.ART to readable status"
- "GKV for public, PKV for private, Selbstzahler for self-pay"

---

## 1.7 Export: CSV + JSON (30 sec)

**SHOW:** `src/services/extraction.py` (lines 148-199)

**SAY:**
- "Dual export: CSV for spreadsheets, JSON for APIs"
- "Proper encoding, headers, timestamps"

**DO:**
```bash
cd sandbox/ivoris-multi-center
python -m src.cli extract --date 2022-01-18 -c center_01
cat data/output/ivoris_multi_center_2022-01-18.json | head -30
```

**SAY:**
- "All 5 required fields + center info"
- "Main challenge complete"

**TRANSITION:** *pause* "But Clinero manages 30 centers, not one..."

---

# PART 2: EXTENSION CHALLENGE (3 min)

## 2.1 The Problem (30 sec)

**OPTION A: Compare via SQL (Terminal)**

```bash
# List tables in center_01 (clean names)
docker exec ivoris-multi-sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'Clinero2026' -C -d DentalDB_01 \
  -Q "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='ck' AND TABLE_NAME LIKE 'KARTEI%' OR TABLE_NAME LIKE 'PATIENT%'"

# List tables in center_02 (random suffixes)
docker exec ivoris-multi-sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'Clinero2026' -C -d DentalDB_02 \
  -Q "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='ck' AND TABLE_NAME LIKE 'KARTEI%' OR TABLE_NAME LIKE 'PATIENT%'"
```

**OPTION B: Compare columns (more dramatic)**

```bash
# Columns in center_01 KARTEI (clean)
docker exec ivoris-multi-sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'Clinero2026' -C -d DentalDB_01 \
  -Q "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='ck' AND TABLE_NAME='KARTEI' ORDER BY ORDINAL_POSITION"

# Columns in center_02 KARTEI (with suffixes)
docker exec ivoris-multi-sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'Clinero2026' -C -d DentalDB_02 \
  -Q "SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='ck' AND TABLE_NAME LIKE 'KARTEI%' ORDER BY ORDINAL_POSITION"
```

**OPTION C: Show mapping files side-by-side (Editor)**
- `data/mappings/center_01_mapping.json` (clean)
- `data/mappings/center_02_mapping.json` (suffixes)

**SAY:**
- "Center 01 has the clean schema — like the Main Challenge"
- "But center 02 has random suffixes: `KARTEI_XYZ`, `PATNR_ABC`"
- "Every other center is different too"
- "One SQL query won't work everywhere"

---

## 2.2 The Solution (45 sec)

**SHOW:** `src/adapters/center_adapter.py` (lines 64-85)

**SAY:**
- "Schema mapping layer"
- "Translates canonical names to actual names"
- "One query template, built dynamically per center"

**SHOW:** `src/services/extraction.py` (lines 148-175)

**SAY:**
- "Extraction service handles the full workflow"
- "Dual export: CSV for spreadsheets, JSON for APIs"

---

## 2.3 Demo — CLI Benchmark (45 sec)

**DO:**
```bash
python -m src.cli benchmark
```

**SAY:**
- "30 centers extracted"
- "Under 500 milliseconds total"
- "Target was 5 seconds — beat it by 10x"

---

## 2.4 Demo — Web UI (45 sec)

**DO:** Browser already open at `http://localhost:8000/metrics`

**CLICK:** Select All → Benchmark

**SAY:**
- "Visual dashboard for operations team"
- "Per-center timing breakdown"
- "Export to JSON/CSV"

*Optional: quick dark mode toggle*

---

# CLOSING (15 sec)

**SAY:**
> "Part 1: SQL extraction, 4-table join, dual export.
> Part 2: 30 centers, schema mapping layer, unified extraction.
> Production-ready patterns throughout.
> Thanks for watching."

*End recording*

---

# TIMING GUIDE

| Section | Duration | Cumulative |
|---------|----------|------------|
| Hook | 10 sec | 0:10 |
| **PART 1** | | |
| 1.1 Requirement | 20 sec | 0:30 |
| 1.2 Database Query | 45 sec | 1:15 |
| 1.3 Service Codes | 30 sec | 1:45 |
| 1.4 Insurance Mapping | 20 sec | 2:05 |
| 1.5 Export + Demo | 30 sec | 2:35 |
| Transition | 10 sec | 2:45 |
| **PART 2** | | |
| 2.1 Problem | 30 sec | 3:15 |
| 2.2 Solution | 45 sec | 4:00 |
| 2.3 CLI Benchmark | 45 sec | 4:45 |
| 2.4 Web UI | 45 sec | 5:30 |
| Closing | 15 sec | **5:45** |

---

# KEY FILES TO SHOW (all from ivoris-multi-center/)

| What | File | Lines |
|------|------|-------|
| SQL Query (4-table join) | `src/adapters/center_adapter.py` | 86-101 |
| Service codes query | `src/adapters/center_adapter.py` | 131-161 |
| Insurance mapping | `src/adapters/center_adapter.py` | 163-169 |
| CSV/JSON export | `src/services/extraction.py` | 148-199 |
| Schema comparison | `data/mappings/center_01_mapping.json` vs `center_02_mapping.json` | all |
| Schema mapping layer | `src/adapters/center_adapter.py` | 64-85 |
| Extraction + export | `src/services/extraction.py` | 148-175 |
| Web UI | Browser `http://localhost:8000/metrics` | — |

---

# TIMELINE (quick reference)

| Time | Section | Show | Do |
|------|---------|------|-----|
| 0:00 | **HOOK** | — | SAY: "I built a pipeline... what happens at scale?" |
| 0:10 | 1.1 Requirement | — | SAY: "5 fields → CSV/JSON" |
| 0:30 | 1.2 Explore DB | Terminal (sqlcmd) | OPTIONAL: Show tables/columns |
| 1:00 | 1.3 SQL Query | `center_adapter.py:86-101` | Highlight 4-table JOIN |
| 1:45 | 1.4 Services | `center_adapter.py:131-161` | Highlight LEISTUNG query |
| 2:15 | 1.5 Insurance | `center_adapter.py:163-169` | Highlight GKV/PKV mapping |
| 2:35 | 1.6 Export | Terminal | RUN: `extract` + `cat json` |
| 3:05 | — | — | TRANSITION: "But 30 centers..." |
| 3:15 | 2.1 Problem | `center_01_mapping.json` + `center_02_mapping.json` | Show side-by-side |
| 3:45 | 2.2 Solution | `center_adapter.py:64-85` | Highlight schema mapping |
| 4:30 | 2.3 Benchmark | Terminal | RUN: `benchmark` |
| 5:15 | 2.4 Web UI | Browser `:8000/metrics` | Click Select All → Benchmark |
| 6:00 | **CLOSING** | — | SAY: "4-table join, schema mapping, production-ready" |

---

# ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────┐
│                    30 Dental Centers                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐     ┌─────────┐   │
│  │ (clean) │ │ _DLI    │ │ _XQ4    │ ... │ _LA     │   │
│  │ Munich  │ │ Berlin  │ │ Hamburg │     │Lausanne │   │
│  │ center1 │ │ center2 │ │ center3 │     │center30 │   │
│  └────┬────┘ └────┬────┘ └────┬────┘     └────┬────┘   │
│       │          │          │               │          │
│       ▼          ▼          ▼               ▼          │
│  ┌─────────────────────────────────────────────────┐   │
│  │           Schema Mapping Layer                  │   │
│  │      canonical names → actual names             │   │
│  │   KARTEI → KARTEI | KARTEI_DLI | KARTEI_XQ4    │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                              │
│                         ▼                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Extraction Service                 │   │
│  │   4-table JOIN • Service codes • Insurance map  │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                              │
│                         ▼                              │
│                 CSV / JSON Output                      │
│         (per center, daily extraction)                 │
└─────────────────────────────────────────────────────────┘
```

---

# KEY NUMBERS TO EMPHASIZE

| Number | What | When to Say |
|--------|------|-------------|
| **30** | Dental centers | "30 centers across Germany, Austria, Switzerland" |
| **5** | Required fields | "5 fields: Date, Patient ID, Insurance, Entry, Services" |
| **4** | Table JOIN | "4-table JOIN: KARTEI, PATIENT, PATKASSE, KASSEN" |
| **< 500ms** | Extraction time | "Under 500 milliseconds" |
| **~25x** | Faster than target | "Target was 5 seconds — beat it by 25x" |

---

# SCREEN LAYOUT

```
┌────────────────────────────────┬─────────────────┐
│                                │                 │
│     VS Code / Editor           │    Terminal     │
│     (70% width)                │    (30%)        │
│                                │                 │
│  Tabs open:                    │  Ready for      │
│  1. center_adapter.py          │  commands       │
│  2. extraction.py              │                 │
│  3. center_01_mapping.json     │  $ _            │
│  4. center_02_mapping.json     │                 │
│                                │                 │
└────────────────────────────────┴─────────────────┘

Browser: Hidden until Part 2.4 (Web UI), then fullscreen
```

**Font sizes:**
- Terminal: 16pt+
- Editor: 14pt+
- Browser: 125% zoom

---

# COMMANDS TO RUN DURING RECORDING

**Copy these in order. Have terminal ready in `sandbox/ivoris-multi-center/`**

## Database Exploration (Optional - to show architecture)

```bash
# List all 30 centers
python -m src.cli list
```

```bash
# Discover raw schema for a center (shows actual table/column names)
python -m src.cli discover-raw -c center_01
```

```bash
# Show canonical → actual mapping
python -m src.cli show-mapping center_01
```

## Part 1: Export Demo (1.5)

```bash
python -m src.cli extract --date 2022-01-18 -c center_01
```

```bash
cat data/output/ivoris_multi_center_2022-01-18.json | head -30
```

## Part 2: Benchmark Demo (2.3)

```bash
python -m src.cli benchmark
```

## Part 2: Web UI (2.4) — run before recording

```bash
python -m src.cli web
```

Then open browser: `http://localhost:8000/metrics`

---

# BONUS: Direct SQL Commands (if needed)

```bash
# Connect to SQL Server (requires sqlcmd or mssql-cli)
docker exec -it ivoris-multi-sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'Clinero2026' -C
```

```sql
-- List all databases
SELECT name FROM sys.databases WHERE name LIKE 'DentalDB%';

-- Use a specific center database
USE DentalDB_01;

-- List all tables in ck schema
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'ck';

-- Show columns for a table (note: actual name has random suffix)
SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ck' AND TABLE_NAME LIKE 'KARTEI%';

-- Query chart entries (use actual table name from discover-raw)
SELECT TOP 5 * FROM ck.KARTEI_MN;  -- Replace with actual table name
```

---

# PRE-RECORDING CHECKLIST

```bash
# 0. Start/restart Docker (SQL Server + 30 databases, port 1434)
docker-compose up -d                              # Start
docker-compose restart                            # Restart if issues
docker-compose down && docker-compose up -d       # Full reset

# 1. Verify container is running
docker ps | grep 1434

# 2. Test extraction works
cd sandbox/ivoris-multi-center
python -m src.cli extract --date 2022-01-18 -c center_01

# 3. Test benchmark works
python -m src.cli benchmark

# 4. Web UI running
python -m src.cli web
# Browser open at http://localhost:8000/metrics

# 5. Editor tabs ready (in order of appearance):
#    - src/adapters/center_adapter.py
#    - src/services/extraction.py
#    - data/mappings/center_01_mapping.json (clean)
#    - data/mappings/center_02_mapping.json (suffixes)
```

---

# RECORDING TIPS

| Do | Don't |
|----|-------|
| Large terminal font (16pt+) | Tiny unreadable text |
| Browser at 125% zoom | Default zoom |
| Slow, deliberate cursor | Frantic mouse movements |
| Pause after key points | Rush through everything |
| Pre-run all commands once | Debug live on camera |
| Have output files ready | Wait for extraction to run |

---

# WHY DOCKER?

| Reason | Explanation |
|--------|-------------|
| **Cross-platform** | SQL Server runs on macOS/Linux via container |
| **Isolation** | Doesn't touch host system, no install conflicts |
| **Reproducible** | Same setup every time, easy to share |
| **Easy reset** | `docker-compose down && up` = fresh start |
| **30 databases** | One SQL Server instance, 30 separate databases inside |

---

# KEY POINTS FOR STAKEHOLDERS

## For Business Stakeholders

| Concern | Key Point | What to Say |
|---------|-----------|-------------|
| **Maintenance** | Schema mapping layer | "Add a new center in minutes — just a JSON config file, no code changes" |
| **Scalability** | 30 centers, <500ms | "Built for growth — 30 centers today, 300 tomorrow, same architecture" |
| **ROI** | Automation | "Daily extraction runs unattended — no manual export, no human error" |

## For IT Experts

| Concern | Key Point | What to Say |
|---------|-----------|-------------|
| **Maintenance** | Single query template | "One SQL template for all centers — fix once, deploy everywhere" |
| **Security** | Parameterized queries | "SQL injection protection built-in — no string concatenation" |
| **Scalability** | Connection pooling ready | "Architecture supports connection pooling, async if needed" |
| **Adaptability** | Schema discovery | "Auto-discovers schema variations — handles legacy naming conventions" |

## For Both (UX Prosumer)

| Concern | Key Point | What to Say |
|---------|-----------|-------------|
| **UX** | Web dashboard | "Ops team sees all 30 centers at a glance — no SQL knowledge needed" |
| **Dual export** | CSV + JSON | "CSV for Excel users, JSON for API integration — same extraction" |
| **Self-service** | CLI + Web | "Power users get CLI, operations get dashboard — same data" |

## Quick Phrases to Drop In

- "Zero-touch onboarding for new centers"
- "Configuration over code"
- "Single source of truth"
- "Fail-fast with clear error messages"
- "Audit trail via JSON timestamps"

## What NOT to Mention (keep it simple)

- Docker internals (they don't care how, just that it works)
- SQL Server specifics (unless asked)
- Python implementation details

**Focus on outcomes, not implementation.**

---

# IF SOMETHING FAILS

Since it's Loom — just stop and re-record that section. No stress.

**Backup:** If database won't connect, show the code and pre-generated output files in `data/output/`.
