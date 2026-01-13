# Ivoris Extraction Pipeline Challenge

**Clinero Interview** | Jean-Francois Desjardins | January 2026

---

## Overview

This challenge has two parts:

| Part | Challenge | Scope | Status |
|------|-----------|-------|--------|
| **Part 1** | Daily Extraction Pipeline | 1 database, standard schema | ✅ Complete |
| **Part 2** | Multi-Center Scale | 30 databases, random schemas | ✅ Complete |

**Projects:**
- Part 1: [ivoris-pipeline](../ivoris-pipeline)
- Part 2: ivoris-multi-center (this project)

---

## Part 1: Daily Extraction Pipeline (Main Challenge)

### Original Requirement

> **Extraction-Pipeline für Ivoris bauen**
>
> Anforderung: Wenn User einen Karteikarteneintrag machen, soll täglich ein Update/Datenübertrag vorgenommen werden.
>
> Datenbedarf: Datum, Pat-ID, Versicherungsstatus, Karteikarteneintrag, Leistungen (Ziffern)
>
> Output: csv/json

### Translation

Build a data extraction pipeline that runs daily to transfer patient chart entries from Ivoris to external systems.

### Required Fields

| # | German | English | Source Table | Description |
|---|--------|---------|--------------|-------------|
| 1 | Datum | Date | KARTEI.DATUM | Date of chart entry |
| 2 | Pat-ID | Patient ID | KARTEI.PATIENTID | Patient identifier |
| 3 | Versicherungsstatus | Insurance Status | KASSE.TYP | GKV/PKV/Selbstzahler |
| 4 | Karteikarteneintrag | Chart Entry | KARTEI.EINTRAG | Medical record text |
| 5 | Leistungen (Ziffern) | Services | LEISTUNG.LEISTUNG | Treatment codes |

### Solution Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Ivoris    │────▶│  Extraction  │────▶│  CSV / JSON     │
│   DentalDB  │     │   Service    │     │  Output Files   │
└─────────────┘     └──────────────┘     └─────────────────┘
      │                    │
      ▼                    ▼
┌─────────────┐     ┌──────────────┐
│  Tables:    │     │  Combines:   │
│  • KARTEI   │     │  • Date      │
│  • PATIENT  │     │  • Patient   │
│  • KASSE    │     │  • Insurance │
│  • LEISTUNG │     │  • Entry     │
└─────────────┘     │  • Services  │
                    └──────────────┘
```

### Part 1 Commands

```bash
cd ~/Projects/outre_base/sandbox/ivoris-pipeline

# Extract
python src/main.py --daily-extract --date 2022-01-18

# Output
cat data/output/ivoris_chart_entries_2022-01-18.json
```

### Part 1 Success Criteria

- [x] All 5 required fields extracted
- [x] Insurance status correctly mapped (GKV/PKV/Selbstzahler)
- [x] Service codes linked to chart entries
- [x] CSV output with proper headers
- [x] JSON output with structured format

---

## Part 2: Multi-Center Scale (Extension)

### The Question

> *"The main challenge is complete. But Clinero doesn't manage one dental practice - they manage many. What happens when you need to extract from 30 centers, each with randomly generated table and column names?"*

### The Problem

Each Ivoris installation can have **randomly generated schema names**:

| Center | Table Name | Column Names |
|--------|------------|--------------|
| Munich | `KARTEI_MN` | `PATNR_NAN6`, `DATUM_3A4` |
| Berlin | `KARTEI_8Y` | `PATNR_DZ`, `DATUM_QW2` |
| Hamburg | `KARTEI_XQ4` | `PATNR_R2Z5`, `DATUM_7M` |
| ... | ... | ... |

**Same logical data, different physical names. You can't write one SQL query that works everywhere.**

### Extension Requirements

1. **Schema Auto-Discovery**
   - Query `INFORMATION_SCHEMA` to discover actual table/column names
   - Pattern matching to identify canonical entities
   - No hardcoded mappings

2. **Human Review Workflow**
   - Generate proposed mappings with `reviewed: false` flag
   - Production safety: human verifies before extraction

3. **Parallel Extraction**
   - ThreadPoolExecutor for concurrent database access
   - Target: <5 seconds for 30 centers

4. **Unified Output**
   - Same 5 fields as Part 1 + center_id, center_name
   - CSV and JSON formats

### Solution Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Multi-Center Pipeline                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      ┌──────────┐│
│  │ Center 1 │  │ Center 2 │  │ Center 3 │ ...  │Center 30 ││
│  │ _MN      │  │ _8Y      │  │ _XQ4     │      │ _LA      ││
│  └────┬─────┘  └────┬─────┘  └────┬─────┘      └────┬─────┘│
│       │             │             │                  │      │
│       ▼             ▼             ▼                  ▼      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Schema Discovery (INFORMATION_SCHEMA)       │  │
│  │              ↓                                        │  │
│  │           Pattern Matching (KARTEI_XX → KARTEI)       │  │
│  │              ↓                                        │  │
│  │           Mapping Files (reviewed: false)             │  │
│  │              ↓                                        │  │
│  │           Human Review (reviewed: true)               │  │
│  └──────────────────────────────────────────────────────┘  │
│                              │                              │
│                              ▼                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Parallel Extraction                      │  │
│  │              ThreadPoolExecutor                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                              │                              │
│                              ▼                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Unified Output                           │  │
│  │   center_id | date | patient_id | insurance | entry   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Part 2 Commands

```bash
cd ~/Projects/outre_base/sandbox/ivoris-multi-center

# Discover schema chaos
python -m src.cli discover-raw -c center_01

# View mapping
python -m src.cli show-mapping center_01

# Extract
python -m src.cli extract --date 2022-01-18

# Benchmark (the proof)
python -m src.cli benchmark
```

### Part 2 Success Criteria

- [x] 30 centers with random schemas
- [x] Pattern-based discovery works for all
- [x] Human review workflow (`reviewed` flag)
- [x] <500ms for 30 centers (target was <5s)
- [x] Web UI for exploration

---

## Database Architecture

| Container | Port | Project | Databases |
|-----------|------|---------|-----------|
| `ivoris-sqlserver` | 1433 | ivoris-pipeline | 1 (`DentalDB`) |
| `ivoris-multi-sqlserver` | 1434 | ivoris-multi-center | 30 (`DentalDB_01`-`DentalDB_30`) |

---

## Results Summary

| Metric | Part 1 | Part 2 |
|--------|--------|--------|
| **Databases** | 1 | 30 |
| **Schema Type** | Standard | Random per center |
| **Output Fields** | 5 | 5 + center info |
| **Extraction Time** | ~50ms | ~466ms |
| **Status** | ✅ Complete | ✅ Complete |

---

## The Narrative

> "I was asked to build a daily extraction pipeline for Ivoris dental software. I built that.
>
> Then I asked myself: what happens at scale? What if there are 30 centers, each with randomly generated schema names?
>
> I built that too."
