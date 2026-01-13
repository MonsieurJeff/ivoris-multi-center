# Demo Checklist

**Pre-Recording Setup for Loom Video**

---

## 30 Minutes Before Recording

### Environment

- [ ] Close Slack, email, notifications
- [ ] Hide Dock / Taskbar
- [ ] Set Do Not Disturb mode
- [ ] Close browser tabs (except localhost)
- [ ] Quit unused applications

### Terminal Setup

```bash
# Navigate to project
cd ~/Projects/outre_base/sandbox/ivoris-multi-center

# Clear terminal
clear

# Set font size (iTerm2: Cmd+Plus or preferences)
# Target: 16pt minimum

# Set terminal theme to high contrast
```

### Browser Setup

- [ ] Zoom to 125% (Cmd +)
- [ ] Open http://localhost:8000 (will start later)
- [ ] Clear browser history (optional, cleaner URL bar)
- [ ] Hide bookmarks bar

---

## 10 Minutes Before Recording

### Docker Check

```bash
# Is SQL Server running?
docker ps | grep ivoris-multi-sqlserver

# If not running:
docker-compose up -d
sleep 30
```

**Expected output:**
```
ivoris-multi-sqlserver   running   0.0.0.0:1434->1433/tcp
```

### Database Check

```bash
# Do databases exist?
python -m src.cli list | head -10
```

**Expected:** Should show 30 centers with `[mapped]` status

### Mapping Files Check

```bash
# Do mapping files exist?
ls data/mappings/ | wc -l
```

**Expected:** `30` (one per center)

### Quick Smoke Test

```bash
# Run a fast extraction
python -m src.cli extract -c center_01 --date 2022-01-18

# Should complete in <100ms with entries
```

---

## 2 Minutes Before Recording

### Final Terminal State

```bash
# Clear and ready
clear

# Show you're in the right place
pwd
# Should show: .../sandbox/ivoris-multi-center
```

### Loom Setup

- [ ] Select screen area (or full screen)
- [ ] Enable microphone
- [ ] Disable webcam (optional - focus on demo)
- [ ] Check audio levels

### Mental Prep

- Take a breath
- Review the first line: *"I built a data extraction pipeline..."*
- Remember: you can always re-record

---

## Command Sequence (Copy-Paste Ready)

### Section 4: CLI Demo

```bash
# 4.1 List centers
python -m src.cli list

# 4.2 Raw discovery
python -m src.cli discover-raw -c center_01

# 4.3 Show mapping
python -m src.cli show-mapping center_01

# 4.4 Extract
python -m src.cli extract --date 2022-01-18 -c center_01

# 4.5 Benchmark
python -m src.cli benchmark
```

### Section 5: Web UI

```bash
# Start web server
python -m src.cli web
```

Then open: http://localhost:8000

---

## Emergency Recovery

### If Docker is down

```bash
docker-compose up -d
sleep 30
# Then continue
```

### If databases are missing

```bash
python scripts/generate_test_dbs.py
python -m src.cli generate-mappings
```

### If web server won't start

```bash
# Kill any existing uvicorn
pkill -f uvicorn

# Try again
python -m src.cli web
```

### If Python imports fail

```bash
# Make sure you're in the right directory
cd ~/Projects/outre_base/sandbox/ivoris-multi-center

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Post-Recording

- [ ] Watch playback (check audio levels)
- [ ] Note any retake sections
- [ ] Export/upload to Loom
- [ ] Copy share link

---

## Quick Reference Card

| What | Command |
|------|---------|
| Start Docker | `docker-compose up -d` |
| Check Docker | `docker ps \| grep ivoris` |
| List centers | `python -m src.cli list` |
| Discover | `python -m src.cli discover-raw -c center_01` |
| Show mapping | `python -m src.cli show-mapping center_01` |
| Extract | `python -m src.cli extract --date 2022-01-18` |
| Benchmark | `python -m src.cli benchmark` |
| Web UI | `python -m src.cli web` |
| Kill web | `pkill -f uvicorn` |
