# Quick Reference Card

**Print this or keep on second monitor during recording**

---

## Unified Presentation Flow

| Time | Act | Project | Command/Action |
|------|-----|---------|----------------|
| 0:00 | Opening | - | Hook line |
| 0:30 | The Ask | pipeline | Show requirement |
| 1:00 | Solution | pipeline | `--daily-extract` |
| 2:30 | **PIVOT** | - | "But what about 30 centers?" |
| 3:00 | Chaos | multi-center | `discover-raw` |
| 4:00 | Extension | multi-center | `show-mapping` |
| 5:00 | Proof | multi-center | `benchmark` |
| 6:00 | Wrap Up | - | Summary |

---

## Commands: ivoris-pipeline

```bash
cd ~/Projects/outre_base/sandbox/ivoris-pipeline

# Extract
python src/main.py --daily-extract --date 2022-01-18

# Show output
cat data/output/ivoris_chart_entries_2022-01-18.json
```

---

## Commands: ivoris-multi-center

```bash
cd ~/Projects/outre_base/sandbox/ivoris-multi-center

# List centers
python -m src.cli list

# Show chaos
python -m src.cli discover-raw -c center_01

# Show mapping
python -m src.cli show-mapping center_01

# Extract
python -m src.cli extract --date 2022-01-18 -c center_01

# Benchmark (THE WOW MOMENT)
python -m src.cli benchmark

# Web UI (optional)
python -m src.cli web
```

**Web URL:** http://localhost:8000

---

## Key Numbers

| Metric | Pipeline | Multi-Center |
|--------|----------|--------------|
| Centers | 1 | 30 |
| Fields | 5 | 5 |
| Target time | - | <5000ms |
| Actual time | ~50ms | ~466ms |

---

## The Pivot Line (MEMORIZE!)

> "So the main challenge is done. But then I started thinking... Clinero doesn't manage one dental practice. They manage many. And here's the thing about Ivoris: each installation can have **randomly generated** table and column names. Let me show you."

---

## Key Messages

### Pipeline (Act 2):
1. "5 required fields" - Date, Patient ID, Insurance, Entry, Services
2. "Clean extraction" - One command, CSV/JSON output

### Multi-Center (Act 4-5):
1. "Random schemas per center" - The hard problem
2. "Pattern-based discovery" - The solution
3. "Human review" - The `reviewed: false` flag
4. "466ms for 30 centers" - 10x faster than target

---

## Recovery Commands

```bash
# Docker down
docker-compose up -d && sleep 30

# Pipeline DB missing
cd ~/Projects/outre_base/sandbox/ivoris-pipeline
./scripts/restore-database.sh

# Multi-center DBs missing
cd ~/Projects/outre_base/sandbox/ivoris-multi-center
python scripts/generate_test_dbs.py
python -m src.cli generate-mappings

# Web stuck
pkill -f uvicorn
```

---

## Opening Line

> "I was asked to build a daily extraction pipeline for Ivoris dental software. I built that. Then I asked myself: what happens at scale? Let me show you both solutions."

## Closing Line

> "That's both challenges complete. The extraction pipeline you asked for, plus a scalable solution that handles schema chaos across 30 databases in 466 milliseconds. Thank you for watching."
