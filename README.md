# Ivoris Multi-Center Extraction Pipeline

**Supplemental Challenge** | Clinero Interview | Jean-Francois Desjardins

---

## Challenge

Extract daily chart entries from **10 dental centers**, each with different database schema names, using **automatic schema discovery**.

```
10 Centers → Schema Auto-Discovery → Unified Extraction → Single Output
```

---

## Quick Start

```bash
# 1. Start SQL Server
docker-compose up -d

# 2. Wait for SQL Server to be ready (30 seconds)
sleep 30

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate test databases
python scripts/generate_test_dbs.py

# 5. List centers
python -m src.cli list

# 6. Discover schemas
python -m src.cli discover

# 7. Extract data
python -m src.cli extract --date 2022-01-18

# 8. Run benchmark
python -m src.cli benchmark
```

---

## Commands

```bash
# List configured centers
python -m src.cli list

# Discover schemas (auto-introspection)
python -m src.cli discover

# Extract from all centers
python -m src.cli extract --date 2022-01-18

# Extract from specific center
python -m src.cli extract --center center_01 --date 2022-01-18

# Export format
python -m src.cli extract --format json
python -m src.cli extract --format csv
python -m src.cli extract --format both

# Parallel workers
python -m src.cli extract --workers 10

# Benchmark performance
python -m src.cli benchmark
```

---

## Centers

| ID | Name | City | Suffix |
|----|------|------|--------|
| center_01 | Zahnarztpraxis München | München | M1 |
| center_02 | Dental Klinik Berlin | Berlin | B2 |
| center_03 | Praxis Dr. Schmidt | Hamburg | H3 |
| center_04 | Zahnzentrum Frankfurt | Frankfurt | F4 |
| center_05 | Dental Care Köln | Köln | K5 |
| center_06 | Praxis Sonnenschein | Dresden | D6 |
| center_07 | Zahnärzte am Markt | Stuttgart | S7 |
| center_08 | Smile Center Leipzig | Leipzig | L8 |
| center_09 | Dental Plus | Düsseldorf | U9 |
| center_10 | Praxis Alpenblick | Wien | W0 |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Multi-Center Pipeline                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    CLI / API                            │ │
│  │   list | discover | extract | benchmark                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                 │
│                            ▼                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                 Extraction Service                      │ │
│  │          ThreadPoolExecutor (parallel)                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                 │
│         ┌──────────────────┼──────────────────┐             │
│         ▼                  ▼                  ▼             │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐        │
│  │  Center 1  │    │  Center 2  │    │  Center N  │        │
│  │  Adapter   │    │  Adapter   │    │  Adapter   │        │
│  └────────────┘    └────────────┘    └────────────┘        │
│         │                  │                  │             │
│         ▼                  ▼                  ▼             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Schema Introspector                        │ │
│  │   INFORMATION_SCHEMA → Pattern Match → SchemaMapping    │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                 │
│                            ▼                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                  Canonical Output                       │ │
│  │   center_id | date | patient_id | insurance | entry     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Features

- **Schema Auto-Discovery**: No manual mapping files - introspects INFORMATION_SCHEMA
- **Parallel Extraction**: ThreadPoolExecutor for concurrent database access
- **Schema Caching**: Discovered schemas cached for performance
- **Unified Output**: All centers output to same canonical format
- **Performance Target**: <5 seconds for 10 centers

---

## Project Structure

```
ivoris-multi-center/
├── src/
│   ├── cli/              # CLI commands
│   │   └── main.py
│   ├── core/             # Core components
│   │   ├── config.py     # Configuration loader
│   │   ├── introspector.py  # Schema discovery
│   │   └── schema_mapping.py
│   ├── adapters/         # Database adapters
│   │   └── center_adapter.py
│   ├── services/         # Business logic
│   │   └── extraction.py # Parallel extraction
│   └── models/           # Data models
│       └── chart_entry.py
├── config/
│   └── centers.yml       # Center configuration
├── scripts/
│   └── generate_test_dbs.py  # Test data generator
├── docker-compose.yml    # SQL Server container
└── requirements.txt
```

---

## Documentation

- [CHALLENGE.md](./CHALLENGE.md) - Full challenge requirements
- [ACCEPTANCE.md](./ACCEPTANCE.md) - Acceptance criteria (Gherkin)

---

## Author

Jean-Francois Desjardins  
Clinero Coding Challenge - January 2026
