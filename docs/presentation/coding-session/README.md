# Coding Session: Ivoris Daily Extraction Pipeline

**Friday Coding Session** | Step-by-Step Manual Walkthrough

---

## Overview

This session walks through building the Daily Extraction Pipeline from scratch, manually, to understand every step.

## Documents

| Step | Document | Duration | Description |
|------|----------|----------|-------------|
| 1 | [01-database-setup.md](./01-database-setup.md) | ~5 min | Restore database from backup |
| 2 | [02-docker-setup.md](./02-docker-setup.md) | ~5 min | Start SQL Server in Docker |
| 3 | [03-explore-database.md](./03-explore-database.md) | ~10 min | Explore tables and columns manually |
| 4 | [04-find-tables.md](./04-find-tables.md) | ~5 min | Identify the 4 key tables |
| 5 | [05-build-extraction-query.md](./05-build-extraction-query.md) | ~15 min | Build the JOIN query step by step |
| 5b | [05b-extraction-script.md](./05b-extraction-script.md) | ~10 min | Create Python script for CSV/JSON output |
| 6 | [06-cron-setup.md](./06-cron-setup.md) | ~5 min | Automate with cron job |

**Total estimated time:** ~55 minutes

---

## The Challenge

> **Original requirement (German):**
> Extraction-Pipeline für Ivoris bauen. Wenn User einen Karteikarteneintrag machen, soll täglich ein Update/Datenübertrag vorgenommen werden.
>
> **Datenbedarf:** Datum, Pat-ID, Versicherungsstatus, Karteikarteneintrag, Leistungen (Ziffern)
>
> **Output:** CSV/JSON

**Translation:** Build a pipeline that extracts daily chart entries with: Date, Patient ID, Insurance Status, Chart Entry, Service Codes.

---

## Prerequisites

- Docker Desktop installed
- Terminal access
- SQL client (sqlcmd or Azure Data Studio)
- Python 3.10+

---

## Quick Start (If short on time)

```bash
# 1. Start Docker
cd ~/Projects/outre_base/sandbox/ivoris-pipeline
docker-compose up -d

# 2. Run extraction
python src/main.py --daily-extract --date 2022-01-18

# 3. View output
cat data/output/ivoris_chart_entries_2022-01-18.json
```

But for the coding session, we go step by step...
