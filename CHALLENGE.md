# Ivoris Multi-Center Extraction Pipeline

**Supplemental Challenge** | Clinero Interview | Jean-Francois Desjardins

---

## Challenge

> **Multi-Center Schema Mapping & Extraction**
>
> A dental group operates 10 centers, each with their own Ivoris database.
> While the data structure is logically identical, each center's database
> has different table and column names due to legacy migrations.
>
> Build a unified extraction pipeline that:
> 1. Maps each center's unique schema to a canonical model
> 2. Extracts daily chart entries from all 10 centers
> 3. Outputs unified data regardless of source schema

---

## The Problem

Each dental center has tables like:

| Center | Patient Table | Chart Table | Patient ID Column | Date Column |
|--------|--------------|-------------|-------------------|-------------|
| Center 1 | PATIENT_A1 | KARTEI_A1 | PATNR_A1 | DATUM_A1 |
| Center 2 | PATIENT_B2 | KARTEI_B2 | PATNR_B2 | DATUM_B2 |
| Center 3 | PATIENT_C3 | KARTEI_C3 | PATNR_C3 | DATUM_C3 |
| ... | ... | ... | ... | ... |
| Center 10 | PATIENT_J0 | KARTEI_J0 | PATNR_J0 | DATUM_J0 |

**Same logical data, different physical names.**

---

## Requirements

### Functional

1. **Schema Auto-Discovery**
   - Introspect database using `INFORMATION_SCHEMA`
   - Detect tables by pattern matching (e.g., contains "KARTEI", "PATIENT")
   - Map columns by base name (strip suffix to find canonical name)
   - No manual YAML mapping files - fully automatic

2. **Canonical Model**
   - Define a standard schema that all centers map to
   - Same ChartEntry model as original challenge

3. **Unified Extraction**
   - Extract from all 10 centers with a single command
   - Output combined results or per-center files

4. **Performance**
   - Parallel extraction across centers
   - Connection pooling per database
   - Cache discovered schemas (don't introspect every run)
   - Target: <5 seconds for 10 centers with 1000 records each

### Technical

- Python 3.11+
- SQL Server 2019 (Docker)
- Dynamic adapter generation from introspected schema
- Factory pattern with schema caching

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Multi-Center Pipeline                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      ┌──────────┐    │
│  │ Center 1 │  │ Center 2 │  │ Center 3 │ ...  │ Center 10│    │
│  │ _A1      │  │ _B2      │  │ _C3      │      │ _J0      │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘      └────┬─────┘    │
│       │             │             │                  │          │
│       ▼             ▼             ▼                  ▼          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Schema Introspector (Auto-Discovery)         │   │
│  │                                                           │   │
│  │   1. Query INFORMATION_SCHEMA.TABLES                      │   │
│  │   2. Pattern match: *KARTEI*, *PATIENT*, *KASSEN*         │   │
│  │   3. Query INFORMATION_SCHEMA.COLUMNS                     │   │
│  │   4. Strip suffix to find canonical column name           │   │
│  │   5. Build SchemaMapping object                           │   │
│  │   6. Cache for performance                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Adapter Factory                         │   │
│  │   get_adapter("center_01")                                │   │
│  │     → introspect schema                                   │   │
│  │     → build CenterAdapter with discovered mapping         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  Canonical ChartEntry                     │   │
│  │   date | patient_id | insurance_status | chart_entry      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  Unified Output                           │   │
│  │            JSON / CSV with center_id field                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Schema Auto-Discovery Algorithm

```python
# Pseudo-code for schema introspection

def discover_schema(connection) -> SchemaMapping:
    # 1. Find tables by pattern
    tables = query("""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'ck'
    """)

    # 2. Match canonical tables
    mapping = {}
    for table in tables:
        base_name = extract_base_name(table)  # KARTEI_A1 → KARTEI
        if base_name in CANONICAL_TABLES:
            mapping[base_name] = table

    # 3. For each table, discover columns
    for canonical, actual in mapping.items():
        columns = query(f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{actual}'
        """)

        for col in columns:
            base_col = extract_base_name(col)  # PATNR_A1 → PATNR
            mapping[f"{canonical}.{base_col}"] = col

    return SchemaMapping(mapping)
```

**Pattern Matching Rules:**
- Table: `KARTEI_XX` → canonical `KARTEI`
- Column: `PATNR_XX` → canonical `PATNR`
- Suffix detected by: last `_` + 2 alphanumeric chars

---

## Schema Mapping Format

```yaml
# config/mappings/center_01.yml
center_id: "center_01"
suffix: "A1"
database: "DentalDB_A1"

tables:
  patient: "PATIENT_A1"
  chart: "KARTEI_A1"
  insurance: "PATKASSE_A1"
  insurance_provider: "KASSEN_A1"
  service: "LEISTUNG_A1"

columns:
  patient:
    id: "ID"
    name: "P_NAME_A1"
  chart:
    id: "ID"
    patient_ref: "PATNR_A1"
    date: "DATUM_A1"
    entry: "BEMERKUNG_A1"
    deleted: "DELKZ"
  insurance:
    patient_ref: "PATNR_A1"
    provider_ref: "KASSENID_A1"
  insurance_provider:
    id: "ID"
    name: "NAME_A1"
    type: "ART_A1"
  service:
    patient_ref: "PATIENTID_A1"
    date: "DATUM_A1"
    code: "LEISTUNG_A1"
    deleted: "DELKZ"
```

---

## Deliverables

1. **Database Generator** (`scripts/generate_test_dbs.py`)
   - Creates 10 test databases with randomized schema names
   - Populates with identical test data
   - Generates random 2-char suffixes per center

2. **Schema Introspector** (`src/core/introspector.py`)
   - Queries INFORMATION_SCHEMA to discover tables/columns
   - Pattern matching to identify canonical entities
   - Caches discovered schemas for performance

3. **Schema Mapping** (`src/core/schema_mapping.py`)
   - Dataclass representing discovered schema
   - Methods to translate canonical → actual names
   - Generates SQL with correct table/column names

4. **Center Adapter** (`src/adapters/center_adapter.py`)
   - Single adapter class that uses SchemaMapping
   - Factory method that introspects and builds adapter
   - Connection pooling per center

5. **Parallel Extractor** (`src/services/multi_extract.py`)
   - ThreadPoolExecutor for parallel extraction
   - Aggregates results from all centers
   - Reports timing per center

6. **CLI** (`src/main.py`)
   - `--discover` - Show discovered schemas
   - `--extract-all` - Extract from all centers
   - `--center CENTER_ID` - Extract from specific center
   - `--benchmark` - Performance test with timing

---

## Success Criteria

| Metric | Target |
|--------|--------|
| All 10 centers extracted | ✅ |
| Unified output format | ✅ |
| Schema mapping works | ✅ |
| Parallel extraction | <5s for 10 centers |
| Clean adapter pattern | ✅ |
| OutrePilot quality standards | ✅ |

---

## Bonus Points

- [ ] Auto-discovery of schema (introspect database)
- [ ] Hot-reload of mappings without restart
- [ ] Async extraction with `asyncio` + `aioodbc`
- [ ] REST API endpoint for extraction
- [ ] Monitoring/metrics per center

---

## Getting Started

```bash
# 1. Generate test databases
python scripts/generate-test-dbs.py

# 2. Run extraction
python src/main.py --extract-all --date 2022-01-18

# 3. Run benchmark
python src/main.py --benchmark
```
