# Presentation Briefing

**Your 5-minute prep guide for the Loom recording**

---

## Database Installation (From Scratch)

If you need to explain or demo the full setup from zero:

### Why SQL Server?

- **Industry standard** for dental software in DACH region (Germany, Austria, Switzerland)
- **Ivoris uses SQL Server** - this matches the real-world production environment
- **Docker** makes it portable - runs identically on Mac, Linux, Windows

### Infrastructure Setup

```bash
# 1. Start SQL Server 2019 in Docker
docker-compose up -d

# What this creates:
#   - Container: ivoris-multi-sqlserver
#   - Port: 1434 (mapped to internal 1433)
#   - Credentials: sa / MultiCenter@2024
#   - Volume: sqlserver_data (persistent)

# 2. Wait for SQL Server to be ready (~30 seconds)
sleep 30

# 3. Verify it's running
docker ps | grep ivoris
```

### Database Generation (The Magic)

```bash
# Generate 30 test databases with RANDOM schemas
python scripts/generate_test_dbs.py
```

**What this does:**

1. **Creates 30 databases**: `DentalDB_01` through `DentalDB_30`
2. **Randomizes EVERY name**:
   - Tables: `KARTEI_MN`, `KARTEI_8Y`, `KARTEI_XQ4` (random 2-4 char suffix)
   - Columns: `PATNR_NAN6`, `DATUM_3A4`, `BEMERKUNG_QW2` (each column gets its own suffix)
3. **Populates sample data**: 5 patients, 5 insurers, 8 chart entries per center
4. **Saves ground truth**: `data/ground_truth/<center_id>_ground_truth.json`

### Schema Randomization Example

```
Center 01:  KARTEI_MN   → PATNR_NAN6,  DATUM_3A4,  BEMERKUNG_QW2
Center 02:  KARTEI_8Y   → PATNR_DZ,    DATUM_QW2,  BEMERKUNG_X7K
Center 03:  KARTEI_XQ4  → PATNR_R2Z5,  DATUM_7M,   BEMERKUNG_P3
...
Center 30:  KARTEI_LA   → PATNR_BE,    DATUM_ZH,   BEMERKUNG_Y5
```

**No two centers have the same schema** - this is the challenge.

### Complete From-Scratch Flow

```bash
# 1. Infrastructure
docker-compose up -d && sleep 30

# 2. Dependencies
pip install -r requirements.txt

# 3. Generate databases (with random schemas)
python scripts/generate_test_dbs.py

# 4. Discover schemas from databases
python -m src.cli discover-raw

# 5. Generate mapping proposals
python -m src.cli generate-mappings

# 6. Extract data
python -m src.cli extract --date 2022-01-18

# 7. Benchmark
python -m src.cli benchmark
```

**Total time from zero to extraction: ~2 minutes**

---

## Step 1: Prepare (30 min before)

Read these in order:
1. **[docs/presentation/STORY.md](docs/presentation/STORY.md)** - Understand the narrative arc
2. **[docs/presentation/SCRIPT.md](docs/presentation/SCRIPT.md)** - Know your talking points

---

## Step 2: Setup (10 min before)

Run through **[docs/presentation/DEMO_CHECKLIST.md](docs/presentation/DEMO_CHECKLIST.md)**:

```bash
# Quick check
docker ps | grep ivoris                    # ✓ SQL Server running
python -m src.cli list | head -5           # ✓ Centers configured
ls data/mappings/ | wc -l                  # ✓ Should show 30
```

Setup:
- [ ] Terminal font 16pt+
- [ ] Browser zoom 125%
- [ ] Close Slack/email/notifications
- [ ] Print or open QUICK_CARD.md on second monitor

---

## Step 3: Record

**Have open:** [docs/presentation/QUICK_CARD.md](docs/presentation/QUICK_CARD.md)

### Commands (copy-paste)

```bash
python -m src.cli list
python -m src.cli discover-raw -c center_01
python -m src.cli show-mapping center_01
python -m src.cli extract --date 2022-01-18 -c center_01
python -m src.cli benchmark
python -m src.cli web
```

### Timing

| Time | Section | Key Point |
|------|---------|-----------|
| 0:00 | Hook | "30 databases, random schemas" |
| 0:15 | Problem | Show `discover-raw` chaos |
| 0:45 | Architecture | "Discovery → Mapping → Extraction" |
| 1:45 | CLI Demo | Run the 5 commands |
| 3:45 | Web Demo | Explore, Metrics, Export |
| 5:45 | Results | "<500ms, all passing" |
| 6:15 | Wrap | "Thanks for watching" |

### Key Messages (say these!)

1. **"Random schemas per center"** - This is the hard problem
2. **"Pattern-based discovery"** - How we solve it
3. **"Human review before extraction"** - Production safety (`reviewed: false`)
4. **"400ms for 30 centers"** - 10x faster than target

---

## Step 4: Recovery (if needed)

```bash
# If Docker down
docker-compose up -d && sleep 30

# If mappings missing
python -m src.cli generate-mappings

# If web stuck
pkill -f uvicorn && python -m src.cli web
```

---

## Opening Line

> "I built a data extraction pipeline that handles 30 dental databases - each with completely random table and column names. Let me show you how it works."

## Closing Line

> "That's the Ivoris Multi-Center Pipeline - 30 databases, random schemas, unified through pattern-based discovery. 400 milliseconds, 10 times faster than target. Thanks for watching."

---

## Don't Forget

- **Pause** after showing the benchmark results (let numbers sink in)
- **Slow cursor movements** (easier to follow)
- **If something fails**, stay calm and explain

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [QUICK_CARD.md](docs/presentation/QUICK_CARD.md) | Commands during recording |
| [SCRIPT.md](docs/presentation/SCRIPT.md) | Full talking points |
| [DEMO_CHECKLIST.md](docs/presentation/DEMO_CHECKLIST.md) | Pre-flight checks |
