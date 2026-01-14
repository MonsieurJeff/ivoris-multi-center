# Timing & Pacing Guide

**Total Session: ~55 minutes**

---

## Timeline Overview

```
00:00 ─────────────────────────────────────────────── 55:00
  │     │         │         │              │        │
  │     │         │         │              │        └─ Q&A
  │     │         │         │              └─ Cron (5m)
  │     │         │         └─ Script (10m)
  │     │         └─ Query Building (15m)
  │     └─ Explore + Find Tables (15m)
  └─ Setup (10m)
```

---

## Detailed Timing

| Time | Section | Duration | Document |
|------|---------|----------|----------|
| 0:00 | **Intro & Setup** | 10 min | 01 + 02 |
| 0:10 | **Database Exploration** | 10 min | 03 |
| 0:20 | **Find Tables** | 5 min | 04 |
| 0:25 | **Build Query** | 15 min | 05 |
| 0:40 | **Python Script** | 10 min | 05b |
| 0:50 | **Cron Setup** | 5 min | 06 |
| 0:55 | **Q&A / Buffer** | 5 min | - |

---

## Checkpoints

### Checkpoint 1: 10 minutes
**Should be at:** Docker running, connected to SQL Server

**If behind:** Skip Option A/B in database setup, use pre-configured docker-compose

**Say:** "Let me use the pre-configured setup to save time"

---

### Checkpoint 2: 20 minutes
**Should be at:** Finished exploring tables, understand the schema

**If behind:** Show the ER diagram directly, skip some exploration queries

**Say:** "I've already explored this - here's what the schema looks like"

---

### Checkpoint 3: 25 minutes
**Should be at:** Identified all 4 tables and their relationships

**If behind:** Show the mapping table directly

**Say:** "The key insight is: KARTEI → PATIENT → KASSE for insurance"

---

### Checkpoint 4: 40 minutes
**Should be at:** Complete extraction query working

**If behind:** Copy the final query from cheatsheet, explain it

**Say:** "Let me paste the complete query and walk through it"

---

### Checkpoint 5: 50 minutes
**Should be at:** Python script running, output generated

**If behind:** Use single-file version, skip modular structure

**Say:** "Here's the compact version - same result, less boilerplate"

---

### Checkpoint 6: 55 minutes
**Should be at:** Cron explained, session complete

**If behind:** Show cron command, skip systemd/launchd options

**Say:** "The key line is: 0 6 * * * /path/to/script.sh"

---

## Fallback Paths

### If Docker Fails
1. Show pre-recorded terminal output
2. Use backup JSON/CSV files
3. Focus on explaining the concepts

### If Query Fails
1. Use CHEATSHEET.md - copy final query
2. Show expected output from backup files
3. Explain what the query does conceptually

### If Python Fails
1. Use single-file version (simpler)
2. Show pre-generated output files
3. Walk through code without running

### If Everything Fails
1. Switch to conceptual walkthrough
2. Use slides for structure
3. Show backup output files
4. "Let me show you what the output looks like..."

---

## Pacing Tips

### Too Fast?
- Add more exploration queries
- Ask audience questions
- Show Azure Data Studio GUI
- Explain German terms in more detail

### Too Slow?
- Skip to checkpoints
- Use cheatsheet for commands
- Show final results, explain backwards
- "Here's what we're building toward..."

---

## Natural Break Points

| Time | Good Moment to Pause |
|------|---------------------|
| 10m | After Docker is running |
| 25m | After finding all tables |
| 40m | After query works |
| 50m | After seeing output |

---

## Time Signals

- **5 min warning:** "We have about 5 minutes left"
- **Wrap up:** "Let me show you the final result"
- **Overtime:** "Happy to answer questions offline"

---

## Emergency Shortcuts

| Situation | Shortcut |
|-----------|----------|
| Docker won't start | Use `./scripts/reset-demo.sh` |
| Query has error | Copy from CHEATSHEET.md |
| No time for Python | Show backup output files |
| No time for cron | "Here's the one-liner for your crontab" |
