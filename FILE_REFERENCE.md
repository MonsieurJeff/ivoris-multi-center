# File Reference

**Ivoris Extraction Pipeline** | Complete File Inventory

---

## Part 1: ivoris-pipeline (Main Challenge)

### Root Files

| File | Description | Keywords |
|------|-------------|----------|
| `README.md` | Project overview with setup instructions and usage examples | (documentation, setup, quickstart) |
| `CHALLENGE.md` | Original challenge requirements and solution architecture | (requirements, architecture, specification) |
| `ACCEPTANCE.md` | Gherkin acceptance criteria with 7 scenarios for validation | (testing, validation, gherkin, BDD) |
| `SESSION_LOG.md` | Development session history and decisions made | (history, decisions, log) |
| `requirements.txt` | Python dependencies (pyodbc, python-dotenv) | (dependencies, pip, setup) |
| `docker-compose.yml` | SQL Server container configuration on port 1433 | (docker, infrastructure, database, SQL Server) |

### Configuration

| File | Description | Keywords |
|------|-------------|----------|
| `config/settings.py` | Database connection settings and environment loading | (configuration, environment, connection) |
| `config/.env.example` | Template for environment variables (DB credentials) | (environment, secrets, template) |

### Source Code

| File | Description | Keywords |
|------|-------------|----------|
| `src/main.py` | CLI entry point with argument parsing for daily extraction | (entry-point, CLI, argparse) |
| `src/adapters/database.py` | Database connection management using pyodbc | (adapter, pyodbc, SQL Server, connection) |
| `src/models/chart_entry.py` | ChartEntry dataclass with 6 required fields | (model, dataclass, schema) |
| `src/services/daily_extract.py` | Core extraction logic with SQL joins and output formatting | (service, extraction, SQL, joins, CSV, JSON) |

### Data

| File | Description | Keywords |
|------|-------------|----------|
| `data/output/ivoris_chart_entries_*.json` | Extracted chart entries in JSON format | (output, JSON, export) |
| `data/input/README.md` | Placeholder for input data documentation | (documentation) |

---

## Part 2: ivoris-multi-center (Extension)

### Root Files

| File | Description | Keywords |
|------|-------------|----------|
| `README.md` | Project overview covering both challenges with commands | (documentation, setup, quickstart) |
| `CHALLENGE.md` | Unified challenge document for Part 1 and Part 2 | (requirements, architecture, specification) |
| `ACCEPTANCE.md` | 19 Gherkin scenarios (7 for Part 1, 12 for Part 2) | (testing, validation, gherkin, BDD) |
| `BRIEFING.md` | Technical briefing for interview context | (interview, briefing, context) |
| `PRESENTATION.md` | Presentation script and demo flow | (presentation, demo, script) |
| `QUICK_REFERENCE.md` | Cheat sheet with key commands and facts | (reference, commands, cheatsheet) |
| `CHANGELOG.md` | Version history and feature additions | (history, versions, changelog) |
| `SESSION_LOG.md` | Development session notes and decisions | (history, decisions, log) |
| `requirements.txt` | Python dependencies (pyodbc, fastapi, uvicorn, pyyaml) | (dependencies, pip, setup) |
| `docker-compose.yml` | SQL Server container with 30 databases on port 1434 | (docker, infrastructure, database, scale) |

### Configuration

| File | Description | Keywords |
|------|-------------|----------|
| `config/centers.yml` | 30 dental center definitions (id, name, city, database) | (configuration, centers, YAML, multi-tenant) |

### Source Code - Core

| File | Description | Keywords |
|------|-------------|----------|
| `src/__main__.py` | Package entry point for `python -m src.cli` | (entry-point, module) |
| `src/core/config.py` | Configuration loader for centers.yml | (configuration, YAML, loading) |
| `src/core/discovery.py` | Schema discovery using INFORMATION_SCHEMA queries | (discovery, introspection, INFORMATION_SCHEMA) |
| `src/core/introspector.py` | Database introspection for tables and columns | (introspection, metadata, schema) |
| `src/core/schema_mapping.py` | Pattern matching to map random names to canonical names | (pattern-matching, mapping, canonicalization) |

### Source Code - CLI

| File | Description | Keywords |
|------|-------------|----------|
| `src/cli/main.py` | CLI with 10 commands (list, extract, benchmark, web, etc.) | (CLI, commands, interface) |
| `src/cli/__main__.py` | CLI module entry point | (entry-point, module) |

### Source Code - Services

| File | Description | Keywords |
|------|-------------|----------|
| `src/services/extraction.py` | Parallel extraction with ThreadPoolExecutor | (extraction, parallel, ThreadPoolExecutor, performance) |
| `src/services/mapping_generator.py` | Generate and save schema mappings to JSON | (mapping, generation, JSON, persistence) |

### Source Code - Models

| File | Description | Keywords |
|------|-------------|----------|
| `src/models/chart_entry.py` | ChartEntry dataclass with center metadata | (model, dataclass, schema) |

### Source Code - Adapters

| File | Description | Keywords |
|------|-------------|----------|
| `src/adapters/center_adapter.py` | Per-center database adapter using mappings | (adapter, database, multi-tenant) |

### Source Code - Web UI

| File | Description | Keywords |
|------|-------------|----------|
| `src/web/app.py` | FastAPI application with REST endpoints | (FastAPI, REST, API, web) |
| `src/web/templates/base.html` | Base HTML template with Tailwind CSS styling | (template, HTML, Tailwind, dark-mode) |
| `src/web/templates/explore.html` | Interactive explorer with filters and export | (UI, explorer, filters, export, CSV, JSON) |
| `src/web/templates/metrics.html` | Performance metrics dashboard | (UI, metrics, dashboard) |
| `src/web/templates/schema_diff.html` | Schema comparison view | (UI, schema, diff, comparison) |

### Data - Mappings

| File | Description | Keywords |
|------|-------------|----------|
| `data/mappings/center_XX_mapping.json` | Canonical-to-actual name mappings per center (30 files) | (mapping, JSON, schema, canonicalization) |
| `data/mappings/center_XX_schema.json` | Raw schema discovery results per center (30 files) | (schema, discovery, raw, metadata) |

### Data - Ground Truth

| File | Description | Keywords |
|------|-------------|----------|
| `data/ground_truth/center_XX_ground_truth.json` | Expected extraction results for validation (30 files) | (testing, validation, ground-truth, expected) |

### Data - Output

| File | Description | Keywords |
|------|-------------|----------|
| `data/output/ivoris_multi_center_*.json` | Multi-center extraction output | (output, JSON, export, multi-center) |

### Scripts

| File | Description | Keywords |
|------|-------------|----------|
| `scripts/generate_test_dbs.py` | Generate 30 test databases with random schemas | (testing, setup, database, generation) |

### Documentation

| File | Description | Keywords |
|------|-------------|----------|
| `docs/README.md` | Documentation index and navigation | (documentation, index) |
| `docs/TECH_SPEC.md` | Technical specification and architecture details | (architecture, specification, technical) |
| `docs/METHODOLOGY.md` | Development methodology and approach | (methodology, approach, process) |
| `docs/OPERATIONS.md` | Operational runbook and maintenance guide | (operations, runbook, maintenance) |
| `docs/SECURITY.md` | Security considerations and best practices | (security, best-practices, credentials) |
| `docs/TESTING.md` | Testing strategy and validation approach | (testing, validation, strategy) |

### Presentation Materials

| File | Description | Keywords |
|------|-------------|----------|
| `docs/presentation/SCRIPT.md` | Full presentation script with timing | (presentation, script, demo) |
| `docs/presentation/STORY.md` | Narrative arc for the presentation | (presentation, narrative, story) |
| `docs/presentation/DEMO_CHECKLIST.md` | Pre-demo checklist to ensure everything works | (demo, checklist, preparation) |
| `docs/presentation/QUICK_CARD.md` | One-page quick reference card | (reference, cheatsheet, quick) |
| `docs/presentation/QUICK_REFERENCE.md` | Extended quick reference with examples | (reference, examples, commands) |
| `docs/presentation/TRANSITION.md` | Transition talking points between sections | (presentation, transitions, flow) |

---

## Keyword Index

### By Category

**Architecture**
- entry-point, CLI, adapter, service, model, core

**Technical**
- SQL Server, pyodbc, Docker, JSON, CSV, UTF-8, REST, FastAPI

**Domain**
- extraction, schema, mapping, discovery, chart-entry, insurance, dental

**Scale**
- multi-center, parallel, ThreadPoolExecutor, benchmark, performance

**Process**
- validation, testing, gherkin, BDD, ground-truth

**Output**
- export, CSV, JSON, output, report

**Documentation**
- specification, quickstart, cheatsheet, demo, presentation

### Most Important for Demo

| Concept | Keywords to Remember |
|---------|---------------------|
| **The Problem** | random-schema, canonicalization, pattern-matching |
| **The Solution** | INFORMATION_SCHEMA, discovery, mapping |
| **Performance** | parallel, ThreadPoolExecutor, <500ms |
| **Safety** | human-review, reviewed-flag, validation |
| **Output** | CSV, JSON, UTF-8, export |

---

## Quick Stats

| Metric | Part 1 | Part 2 |
|--------|--------|--------|
| Python files | 6 | 15 |
| Config files | 2 | 1 |
| Templates | 0 | 4 |
| Output files | 1 | 1 |
| Mapping files | 0 | 60 |
| Doc files | 4 | 14 |
| **Total** | ~13 | ~95 |
