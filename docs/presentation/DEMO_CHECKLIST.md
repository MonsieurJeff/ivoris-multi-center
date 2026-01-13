# Demo Checklist

**Pre-Recording Setup for Unified Presentation**

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
# Open TWO terminal tabs

# Tab 1: ivoris-pipeline
cd ~/Projects/outre_base/sandbox/ivoris-pipeline

# Tab 2: ivoris-multi-center
cd ~/Projects/outre_base/sandbox/ivoris-multi-center

# Set font size to 16pt+ in each
# Clear both terminals
clear
```

### Browser Setup

- [ ] Zoom to 125% (Cmd +)
- [ ] Have http://localhost:8000 ready (will start later)
- [ ] Clear browser history (optional)
- [ ] Hide bookmarks bar

---

## 10 Minutes Before Recording

### Docker Check

```bash
# Is SQL Server running?
docker ps | grep ivoris

# If not running:
docker-compose up -d
sleep 30
```

**Expected output:**
```
ivoris-multi-sqlserver   running   0.0.0.0:1434->1433/tcp
```

---

### Check Project 1: ivoris-pipeline

```bash
cd ~/Projects/outre_base/sandbox/ivoris-pipeline

# Test connection
python src/main.py --test-connection

# Test extraction
python src/main.py --daily-extract --date 2022-01-18

# Verify output exists
ls data/output/
```

**Expected:**
- Connection successful
- Extraction with entries
- Output files exist

---

### Check Project 2: ivoris-multi-center

```bash
cd ~/Projects/outre_base/sandbox/ivoris-multi-center

# Check centers
python -m src.cli list | head -5

# Check mappings
ls data/mappings/ | wc -l
# Expected: 30

# Quick smoke test
python -m src.cli extract -c center_01 --date 2022-01-18
# Should complete in <100ms

# Run benchmark
python -m src.cli benchmark
# Should show PASS
```

**Expected:**
- 30 centers with `[mapped]` status
- 30 mapping files
- Benchmark passes (<500ms)

---

## 2 Minutes Before Recording

### Final Terminal State

**Tab 1 (pipeline):**
```bash
cd ~/Projects/outre_base/sandbox/ivoris-pipeline
clear
pwd
```

**Tab 2 (multi-center):**
```bash
cd ~/Projects/outre_base/sandbox/ivoris-multi-center
clear
pwd
```

### Loom Setup

- [ ] Select screen area (or full screen)
- [ ] Enable microphone
- [ ] Disable webcam (optional)
- [ ] Check audio levels

### Mental Prep

- Take a breath
- Review the pivot line: *"So the main challenge is done. But then I started thinking..."*
- Remember: you can always re-record

---

## Command Sequence (Copy-Paste Ready)

### Act 2: Pipeline Solution

```bash
cd ~/Projects/outre_base/sandbox/ivoris-pipeline

python src/main.py --daily-extract --date 2022-01-18

cat data/output/daily_extract_2022-01-18.json
```

### Acts 4-5: Multi-Center

```bash
cd ~/Projects/outre_base/sandbox/ivoris-multi-center

python -m src.cli list

python -m src.cli discover-raw -c center_01

python -m src.cli show-mapping center_01

python -m src.cli extract --date 2022-01-18 -c center_01

python -m src.cli benchmark
```

### Optional: Web UI

```bash
python -m src.cli web
```

Then open: http://localhost:8000

---

## Emergency Recovery

### If Pipeline Database Missing

```bash
cd ~/Projects/outre_base/sandbox/ivoris-pipeline
./scripts/restore-database.sh
```

### If Multi-Center Databases Missing

```bash
cd ~/Projects/outre_base/sandbox/ivoris-multi-center
python scripts/generate_test_dbs.py
python -m src.cli generate-mappings
```

### If Docker is Down

```bash
docker-compose up -d
sleep 30
```

### If Web Server Won't Start

```bash
pkill -f uvicorn
python -m src.cli web
```

### If Python Imports Fail

```bash
# Make sure you're in the right directory
# Then reinstall dependencies
pip install -r requirements.txt
```

---

## Quick Verification Checklist

Run this complete check before recording:

```bash
# 1. Docker
docker ps | grep ivoris && echo "✓ Docker OK"

# 2. Pipeline
cd ~/Projects/outre_base/sandbox/ivoris-pipeline
python src/main.py --test-connection && echo "✓ Pipeline OK"

# 3. Multi-center
cd ~/Projects/outre_base/sandbox/ivoris-multi-center
python -m src.cli list | head -3 && echo "✓ Multi-center OK"

# 4. Benchmark
python -m src.cli benchmark | tail -3
```

**All should show OK/PASS**

---

## Post-Recording

- [ ] Watch playback (check audio levels)
- [ ] Verify the pivot moment is clear
- [ ] Note any retake sections
- [ ] Export/upload to Loom
- [ ] Copy share link
