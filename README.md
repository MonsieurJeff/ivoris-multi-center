# Ivoris Multi-Center Extraction Pipeline

**Supplemental Challenge** | Clinero Interview | Jean-Francois Desjardins

---

## Challenge

Extract daily chart entries from **30 dental centers** across Germany, Austria, and Switzerland, each with different database schema names, using **automatic schema discovery**.

```
30 Centers → Schema Auto-Discovery → Unified Extraction → Single Output
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

### Germany (20 Centers)

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
| center_11 | Zahnarzt am Dom | Aachen | A1 |
| center_12 | Praxis Dr. Weber | Nürnberg | N2 |
| center_13 | Dental Lounge | Essen | E3 |
| center_14 | Zahnklinik Riverside | Regensburg | R4 |
| center_15 | Praxis Lächeln | Potsdam | P5 |
| center_16 | Dental Wellness | Göttingen | G6 |
| center_17 | Zahnärzte Altstadt | Trier | T7 |
| center_18 | Smile Factory | Chemnitz | C8 |
| center_19 | Praxis Dr. Müller | Jena | J9 |
| center_20 | Dental Excellence | Wiesbaden | X0 |

### Austria (5 Centers)

| ID | Name | City | Suffix |
|----|------|------|--------|
| center_21 | Zahnarzt Stephansplatz | Wien | V1 |
| center_22 | Dental Studio Salzburg | Salzburg | Z2 |
| center_23 | Praxis Bergblick | Innsbruck | I3 |
| center_24 | Zahnklinik Graz | Graz | Q4 |
| center_25 | Smile Center Linz | Linz | Y5 |

### Switzerland (5 Centers)

| ID | Name | City | Suffix |
|----|------|------|--------|
| center_26 | Zahnarztpraxis Zürich | Zürich | ZH |
| center_27 | Dental Care Bern | Bern | BE |
| center_28 | Praxis Genève | Genève | GE |
| center_29 | Zahnzentrum Basel | Basel | BS |
| center_30 | Smile Clinic Lausanne | Lausanne | LA |

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
- **Performance Target**: <5 seconds for 30 centers (actual: ~1.2 seconds)

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
