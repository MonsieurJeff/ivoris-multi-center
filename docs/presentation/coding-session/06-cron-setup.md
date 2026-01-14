# Step 6: Cron Job Setup

> **💬 Talking Points**
> - "Now we make it run automatically every day - no human intervention"
> - "Cron is Unix's built-in scheduler - been around since the 70s"
> - "I'll show you 5 different approaches - pick what fits your environment"

---

## Goal

Automate the extraction to run daily without manual intervention.

---

> **💬 Talking Points - Cron Format**
> - "Five stars, five positions - minute, hour, day, month, weekday"
> - "The asterisk means 'any' - so * * * * * runs every minute"
> - "This format is universal - works the same on Linux, Mac, Docker"

## What is Cron?

Cron is a Unix/Linux job scheduler. It runs commands at specified times.

**Cron format:**
```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6, Sunday=0)
│ │ │ │ │
* * * * * command
```

**Examples:**
| Expression | Meaning |
|------------|---------|
| `0 6 * * *` | Every day at 6:00 AM |
| `30 23 * * *` | Every day at 11:30 PM |
| `0 */2 * * *` | Every 2 hours |
| `0 6 * * 1-5` | Monday-Friday at 6:00 AM |

---

> **💬 Talking Points - Option 1**
> - "This is the classic approach - a bash wrapper script"
> - "Important: activate the venv inside the script"
> - "Redirect output to a log file so you can debug later"

## Option 1: Simple Cron Job (Linux/macOS)

### Create the extraction script

```bash
# Create script
cat > ~/ivoris-extract.sh << 'EOF'
#!/bin/bash

# Configuration
PROJECT_DIR="$HOME/Projects/outre_base/sandbox/ivoris-pipeline"
VENV="$PROJECT_DIR/.venv"
LOG_FILE="$PROJECT_DIR/logs/extraction.log"

# Activate virtual environment
source "$VENV/bin/activate"

# Navigate to project
cd "$PROJECT_DIR"

# Run extraction for yesterday
python src/main.py --daily-extract >> "$LOG_FILE" 2>&1

# Log completion
echo "[$(date)] Extraction completed" >> "$LOG_FILE"
EOF

# Make executable
chmod +x ~/ivoris-extract.sh
```

### Add to crontab

```bash
# Edit crontab
crontab -e

# Add this line (runs at 6:00 AM daily)
0 6 * * * /bin/bash ~/ivoris-extract.sh
```

### Verify crontab

```bash
# List current cron jobs
crontab -l
```

---

## Option 2: Cron with Docker

If running in Docker environment:

```bash
cat > ~/ivoris-extract-docker.sh << 'EOF'
#!/bin/bash

PROJECT_DIR="$HOME/Projects/outre_base/sandbox/ivoris-pipeline"
LOG_FILE="$PROJECT_DIR/logs/extraction.log"

# Ensure Docker container is running
cd "$PROJECT_DIR"
docker-compose up -d

# Wait for SQL Server to be ready
sleep 5

# Run extraction
source .venv/bin/activate
python src/main.py --daily-extract >> "$LOG_FILE" 2>&1

echo "[$(date)] Docker extraction completed" >> "$LOG_FILE"
EOF

chmod +x ~/ivoris-extract-docker.sh
```

---

> **💬 Talking Points - Systemd**
> - "Systemd is the modern replacement for cron on Linux"
> - "Better logging, dependency management, and reliability"
> - "Use this if you're deploying to a production Linux server"

## Option 3: Systemd Timer (Modern Linux)

More robust than cron, with better logging.

### Create service file

```bash
sudo cat > /etc/systemd/system/ivoris-extract.service << 'EOF'
[Unit]
Description=Ivoris Daily Data Extraction
After=docker.service

[Service]
Type=oneshot
User=your-username
WorkingDirectory=/home/your-username/Projects/outre_base/sandbox/ivoris-pipeline
ExecStart=/home/your-username/ivoris-extract.sh
StandardOutput=journal
StandardError=journal
EOF
```

### Create timer file

```bash
sudo cat > /etc/systemd/system/ivoris-extract.timer << 'EOF'
[Unit]
Description=Run Ivoris extraction daily at 6 AM

[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF
```

### Enable timer

```bash
sudo systemctl daemon-reload
sudo systemctl enable ivoris-extract.timer
sudo systemctl start ivoris-extract.timer

# Check status
systemctl list-timers | grep ivoris
```

---

> **💬 Talking Points - launchd**
> - "On macOS, launchd is preferred over cron"
> - "It handles sleep/wake correctly - cron can miss jobs on laptops"
> - "XML format is verbose but it's the Apple way"

## Option 4: macOS launchd

For macOS, use launchd instead of cron.

### Create plist file

```bash
cat > ~/Library/LaunchAgents/com.ivoris.extract.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ivoris.extract</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/YOUR_USERNAME/ivoris-extract.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/ivoris-extract.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/ivoris-extract.error.log</string>
</dict>
</plist>
EOF
```

### Load the job

```bash
# Replace YOUR_USERNAME
sed -i '' "s/YOUR_USERNAME/$(whoami)/g" ~/Library/LaunchAgents/com.ivoris.extract.plist

# Load
launchctl load ~/Library/LaunchAgents/com.ivoris.extract.plist

# Check status
launchctl list | grep ivoris
```

---

## Option 5: Python Schedule (In-Process)

For simpler setups, use Python's `schedule` library:

```python
# scheduler.py
import schedule
import time
from datetime import date, timedelta
from src.services.daily_extract import extract_and_save

def job():
    """Run daily extraction for yesterday."""
    yesterday = date.today() - timedelta(days=1)
    print(f"[{date.today()}] Running extraction for {yesterday}")
    extract_and_save(yesterday)
    print(f"[{date.today()}] Extraction completed")

# Schedule for 6:00 AM
schedule.every().day.at("06:00").do(job)

print("Scheduler started. Press Ctrl+C to exit.")
while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute
```

Run with:
```bash
# Keep running in background
nohup python scheduler.py > scheduler.log 2>&1 &
```

---

> **💬 Talking Points - Logging**
> - "Logging is crucial for production - you need to know when things fail"
> - "Rotate logs to prevent filling up disk space"
> - "Consider sending alerts when extraction fails"

## Logging Best Practices

### Log rotation

```bash
# Add to script
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

# Rotate logs (keep 7 days)
find "$LOG_DIR" -name "*.log" -mtime +7 -delete
```

### Structured logging

```python
import logging
from datetime import datetime

logging.basicConfig(
    filename=f"logs/extraction_{datetime.now():%Y%m%d}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Starting extraction")
# ... extraction code ...
logging.info(f"Extracted {count} entries")
```

---

## Monitoring & Alerts

### Email on failure

```bash
# In extraction script
if ! python src/main.py --daily-extract; then
    echo "Extraction failed on $(date)" | mail -s "Ivoris Extraction Failed" admin@example.com
fi
```

### Health check endpoint

```python
# In web app
@app.get("/health")
def health_check():
    # Check last extraction time
    last_file = max(Path("data/output").glob("*.json"), key=os.path.getctime)
    last_time = datetime.fromtimestamp(os.path.getctime(last_file))

    hours_ago = (datetime.now() - last_time).total_seconds() / 3600

    return {
        "status": "healthy" if hours_ago < 25 else "stale",
        "last_extraction": last_time.isoformat(),
        "hours_ago": round(hours_ago, 1)
    }
```

---

## Production Recommendations

| Aspect | Recommendation |
|--------|----------------|
| **Timing** | Run after business hours (e.g., 6 AM) |
| **Retry** | Add retry logic (3 attempts) |
| **Logging** | Keep 30 days of logs |
| **Monitoring** | Set up alerts for failures |
| **Backup** | Store outputs in cloud storage |
| **Idempotency** | Safe to run multiple times |

---

## Quick Test

```bash
# Test the script manually first
./ivoris-extract.sh

# Check output
ls -la data/output/

# View log
cat logs/extraction.log
```

---

## Summary

| Platform | Method | File |
|----------|--------|------|
| Linux | cron | `crontab -e` |
| Linux (modern) | systemd timer | `/etc/systemd/system/*.timer` |
| macOS | launchd | `~/Library/LaunchAgents/*.plist` |
| Any | Python schedule | `scheduler.py` |
| Container | Docker cron | `Dockerfile` with cron |

---

> **💬 Talking Points - Wrap Up**
> - "And that's it! From database to automated daily extraction"
> - "This same pattern works for any data extraction project"
> - "Questions?"

## Complete!

You now have:
1. ✅ Database setup from backup
2. ✅ Docker environment
3. ✅ Database exploration skills
4. ✅ Table identification
5. ✅ Working extraction query
6. ✅ Automated daily job

**The Daily Extraction Pipeline is complete!**
