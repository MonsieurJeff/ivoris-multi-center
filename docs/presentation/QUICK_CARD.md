# Quick Reference Card

**Print this or keep on second monitor during recording**

---

## Commands (Copy-Paste Ready)

```bash
# List centers
python -m src.cli list

# Discover schema
python -m src.cli discover-raw -c center_01

# Show mapping
python -m src.cli show-mapping center_01

# Extract data
python -m src.cli extract --date 2022-01-18 -c center_01

# Benchmark
python -m src.cli benchmark

# Web UI
python -m src.cli web
```

**Web URL:** http://localhost:8000

---

## Timing Guide

| Section | Time | Key Point |
|---------|------|-----------|
| Hook | 0:00-0:15 | "30 databases, random schemas" |
| Problem | 0:15-0:45 | Show `discover-raw` chaos |
| Architecture | 0:45-1:45 | Discovery → Mapping → Extraction |
| CLI Demo | 1:45-3:45 | Run 5 commands |
| Web Demo | 3:45-5:45 | Explore, Metrics, Diff |
| Results | 5:45-6:15 | <500ms, all pass |
| Wrap Up | 6:15-6:30 | "Thanks for watching" |

---

## Key Numbers

| Metric | Value |
|--------|-------|
| Centers | 30 |
| Target time | <5000ms |
| Actual time | ~400ms |
| Tables per center | 5 |
| Test entries | 6 per center |

---

## Key Messages

1. **Problem is real** - Random schemas happen
2. **Solution is systematic** - Pattern-based discovery
3. **Safety built-in** - Human review before extraction

---

## Recovery Commands

```bash
# If Docker down
docker-compose up -d && sleep 30

# If mappings missing
python -m src.cli generate-mappings

# If web stuck
pkill -f uvicorn
```

---

## Opening Line

> "I built a data extraction pipeline that handles 30 dental databases - each with completely random table and column names. Let me show you how it works."

## Closing Line

> "That's the Ivoris Multi-Center Pipeline - 30 databases with random schemas, unified through pattern-based discovery and parallel extraction. Thanks for watching."
