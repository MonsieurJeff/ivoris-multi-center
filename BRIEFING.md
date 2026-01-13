# Unified Presentation Briefing

**Your prep guide for the Loom recording - Both Projects**

---

## The Two Projects

| Project | Type | What It Shows |
|---------|------|---------------|
| **ivoris-pipeline** | Main Challenge | Daily extraction from ONE database |
| **ivoris-multi-center** | Extension | 30 databases with random schemas |

**Narrative:** "I built what was asked. Then I went further."

---

## Database Installation (From Scratch)

### Project 1: ivoris-pipeline

```bash
cd ~/Projects/outre_base/sandbox/ivoris-pipeline

# 1. Start SQL Server
docker-compose up -d && sleep 30

# 2. Restore the database from backup
./scripts/restore-database.sh

# 3. Install dependencies
pip install -r requirements.txt

# 4. Test extraction
python src/main.py --daily-extract --date 2022-01-18
```

**What this creates:** Single `DentalDB` with standard Ivoris schema

### Project 2: ivoris-multi-center

```bash
cd ~/Projects/outre_base/sandbox/ivoris-multi-center

# 1. Start SQL Server
docker-compose up -d && sleep 30

# 2. Generate 30 databases with RANDOM schemas
python scripts/generate_test_dbs.py

# 3. Install dependencies
pip install -r requirements.txt

# 4. Discover and map schemas
python -m src.cli discover-raw
python -m src.cli generate-mappings

# 5. Test extraction
python -m src.cli extract --date 2022-01-18
```

**What this creates:** 30 databases, each with randomly-suffixed table/column names

---

## Step 1: Prepare (30 min before)

Read these in order:
1. **[docs/presentation/STORY.md](docs/presentation/STORY.md)** - The 5-act unified narrative
2. **[docs/presentation/SCRIPT.md](docs/presentation/SCRIPT.md)** - Full talking points
3. **[docs/presentation/TRANSITION.md](docs/presentation/TRANSITION.md)** - The pivot between projects

---

## Step 2: Pre-Flight Check (10 min before)

Run **[docs/presentation/DEMO_CHECKLIST.md](docs/presentation/DEMO_CHECKLIST.md)** or use this quick check:

```bash
# Check ivoris-pipeline
cd ~/Projects/outre_base/sandbox/ivoris-pipeline
python src/main.py --test-connection           # ✓ Connected

# Check ivoris-multi-center
cd ~/Projects/outre_base/sandbox/ivoris-multi-center
docker ps | grep ivoris                        # ✓ SQL Server running
python -m src.cli list | head -5               # ✓ Centers configured
ls data/mappings/ | wc -l                      # ✓ Should show 30
python -m src.cli benchmark                    # ✓ Should pass
```

Setup:
- [ ] Terminal font 16pt+
- [ ] Browser zoom 125%
- [ ] Close Slack/email/notifications
- [ ] Have QUICK_CARD.md open on second monitor

---

## Step 3: Record

**Have open:** [docs/presentation/QUICK_CARD.md](docs/presentation/QUICK_CARD.md)

### Unified Timing Guide

| Time | Act | Project | What to Show |
|------|-----|---------|--------------|
| 0:00 | Opening | - | "I was asked to build an extraction pipeline..." |
| 0:30 | Act 1: The Ask | pipeline | Show original German requirement |
| 1:00 | Act 2: The Solution | pipeline | `--daily-extract`, show CSV/JSON |
| 2:30 | Act 3: The Question | - | "But what about 30 centers with random schemas?" |
| 3:00 | Act 4: The Chaos | multi-center | `discover-raw` showing random names |
| 4:00 | Act 4: The Solution | multi-center | Pattern matching, mappings |
| 5:00 | Act 4: The Proof | multi-center | Benchmark (466ms) |
| 6:00 | Act 5: Wrap-up | - | Summary, thanks |

**Total: ~7 minutes**

### Commands - ivoris-pipeline

```bash
cd ~/Projects/outre_base/sandbox/ivoris-pipeline

# Test connection
python src/main.py --test-connection

# Extract (main demo)
python src/main.py --daily-extract --date 2022-01-18

# Show output
cat data/output/daily_extract_2022-01-18.json
```

### Commands - ivoris-multi-center

```bash
cd ~/Projects/outre_base/sandbox/ivoris-multi-center

# List centers
python -m src.cli list

# Show the chaos
python -m src.cli discover-raw -c center_01

# Show the order
python -m src.cli show-mapping center_01

# Extract
python -m src.cli extract --date 2022-01-18 -c center_01

# Benchmark (the wow moment)
python -m src.cli benchmark

# Web UI (optional)
python -m src.cli web
```

---

## Key Messages (Say These!)

### For ivoris-pipeline:
1. **"Here's the original requirement"** - Show German text
2. **"5 required fields"** - Date, Patient ID, Insurance, Chart Entry, Services
3. **"Clean extraction in ~3 hours"** - Production-ready

### For ivoris-multi-center:
1. **"But what if there were 30 centers?"** - The pivot
2. **"Random schemas per center"** - This is the hard problem
3. **"Pattern-based discovery"** - How we solve it
4. **"Human review before extraction"** - Production safety
5. **"466ms for 30 centers"** - 10x faster than target

---

## The Pivot (Memorize This!)

> "So the main challenge is complete. But in production, Clinero doesn't manage one dental practice - they manage many. And here's the thing about Ivoris: each installation can have randomly generated table and column names. KARTEI_MN in Munich, KARTEI_8Y in Berlin. How do you build a pipeline that handles that? Let me show you."

---

## Recovery Commands

```bash
# If Docker down
docker-compose up -d && sleep 30

# If pipeline database missing
cd ~/Projects/outre_base/sandbox/ivoris-pipeline
./scripts/restore-database.sh

# If multi-center databases missing
cd ~/Projects/outre_base/sandbox/ivoris-multi-center
python scripts/generate_test_dbs.py
python -m src.cli generate-mappings

# If web stuck
pkill -f uvicorn && python -m src.cli web
```

---

## Opening Line

> "I was asked to build a daily extraction pipeline for Ivoris dental software. I built that. Then I asked myself: what happens at scale? What if there are 30 centers, each with completely different schema names? Let me show you both solutions."

## Closing Line

> "That's both challenges complete. The daily extraction pipeline you asked for - working, tested, production-ready. Plus a scalable multi-center solution that handles schema chaos across 30 databases in 466 milliseconds. Thank you for watching."

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [QUICK_CARD.md](docs/presentation/QUICK_CARD.md) | Commands during recording |
| [SCRIPT.md](docs/presentation/SCRIPT.md) | Full talking points |
| [STORY.md](docs/presentation/STORY.md) | 5-act narrative |
| [TRANSITION.md](docs/presentation/TRANSITION.md) | The pivot script |
| [DEMO_CHECKLIST.md](docs/presentation/DEMO_CHECKLIST.md) | Pre-flight checks |

---

## Don't Forget

- **The pivot is the key moment** - Practice the transition
- **Pause after benchmark results** - Let numbers sink in
- **Slow cursor movements** - Easier to follow
- **If something fails**, stay calm and explain
