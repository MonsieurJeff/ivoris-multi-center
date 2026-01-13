# Loom Presentation Plan

**Duration Target**: 5-7 minutes

---

## Part 1: Problem Statement (30 seconds)

**Show**: README.md or slide

> "The challenge: Extract daily chart entries from 30 dental centers across Germany, Austria, and Switzerland. Each center has randomly generated table and column names - no consistent pattern across centers."

**Key points**:
- 30 centers, unique schemas each
- Tables like `KARTEI_MN`, `KARTEI_8Y` (random suffixes)
- Columns like `PATNR_NAN6`, `DATUM_3A4` (each column has unique suffix)
- Need to discover schemas and map them to a canonical format

---

## Part 2: Architecture Overview (1 minute)

**Show**: Terminal or architecture diagram

> "Here's how I approached it..."

```
30 Centers → Schema Discovery → Mapping Files → Parallel Extraction → Unified Output
```

**Key architectural decisions**:
1. **Raw Schema Discovery** - Query INFORMATION_SCHEMA without interpretation
2. **Mapping Generator** - Proposes mappings based on naming patterns
3. **Manual Review Workflow** - `reviewed: false` flag for human approval
4. **Ground Truth Separation** - Generator saves actual schema, discovery works independently
5. **Parallel Extraction** - ThreadPoolExecutor for concurrent database access

---

## Part 3: Live Demo - CLI Workflow (2 minutes)

**Commands to run**:

```bash
# 1. Show the centers configuration
python -m src.cli list

# 2. Show raw schema discovery (pick one center)
python -m src.cli discover-raw -c center_01

# 3. Show the generated mapping
python -m src.cli show-mapping center_01

# 4. Run extraction
python -m src.cli extract --date 2022-01-18 -c center_01

# 5. Run the benchmark
python -m src.cli benchmark
```

**Talk through**:
- Random suffixes per table AND per column
- Pattern-based discovery: `KARTEI_XYZ` → `KARTEI`
- Mapping file structure with `reviewed: false`
- Performance: <500ms for 30 centers (target was <5s)

---

## Part 4: Live Demo - Web UI (2 minutes)

**Start the server**:
```bash
python -m src.cli web
```

**Show each page**:

### 4.1 Explore Centers
- Select a center from dropdown
- Show center details and schema mapping
- Load extracted data for a date
- Point out the canonical → actual table/column mapping

### 4.2 Metrics Dashboard
- Click "Select All" for all 30 centers
- Click "Benchmark" button
- Show:
  - Summary cards (30 centers, entries, duration, PASS)
  - Chart.js visualization (horizontal bar chart)
  - Per-center timing table
- Click "Export JSON" and "Export CSV" buttons

### 4.3 Schema Diff (Extra Feature)
- Select a center
- Click "Compare Schemas"
- Show:
  - Accuracy percentage
  - Table-by-table comparison
  - Ground truth vs discovered mapping
  - Green checkmarks for matches

### 4.4 Dark Mode
- Toggle dark mode in sidebar
- Show charts update correctly

---

## Part 5: Extra Challenge - Web UI (30 seconds)

> "For the supplemental challenge, I built a FastAPI-based web UI..."

**Highlight**:
- Side navigation like a production app
- Chart.js for data visualization
- Export functionality (JSON/CSV)
- Schema Diff for validation accuracy
- Dark mode support
- Animated progress during extraction

---

## Part 6: Wrap Up (30 seconds)

**Summary**:
- 30 dental centers with random schemas
- Pattern-based schema discovery
- Manual mapping review workflow
- Parallel extraction (<500ms for 30 centers)
- Web UI for exploration and metrics

**Tech stack**:
- Python, FastAPI, SQL Server
- Jinja2 templates, Tailwind CSS, Chart.js
- ThreadPoolExecutor for parallelism

> "Thanks for watching! Happy to answer any questions."

---

## Quick Reference - Commands

```bash
# Start everything
docker-compose up -d
sleep 30
pip install -r requirements.txt
python scripts/generate_test_dbs.py
python -m src.cli generate-mappings

# Run benchmark
python -m src.cli benchmark

# Start web UI
python -m src.cli web
# Open http://localhost:8000
```

---

## Tips for Recording

1. **Terminal**: Use a large font (16pt+)
2. **Browser**: Zoom to 125% for better visibility
3. **Pace**: Pause briefly after each major point
4. **Errors**: If something fails, explain and recover gracefully
5. **Focus**: Keep cursor movements slow and deliberate
