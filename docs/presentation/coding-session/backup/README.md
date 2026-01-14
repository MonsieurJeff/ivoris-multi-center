# Backup Demo Files

**Use these if live demo fails**

---

## Contents

| File | Purpose |
|------|---------|
| `ivoris_chart_entries_2022-01-18.json` | Expected JSON output |
| `ivoris_chart_entries_2022-01-18.csv` | Expected CSV output |
| `expected-terminal-output.txt` | All expected terminal output |

---

## How to Use

### If extraction fails:

```bash
# Show pre-generated output
cat docs/presentation/coding-session/backup/ivoris_chart_entries_2022-01-18.json
```

### If SQL queries fail:

Open `expected-terminal-output.txt` and copy/paste the expected results.

### If everything fails:

1. Open the backup files in a text editor
2. Walk through what the output looks like
3. Explain the structure conceptually

---

## What to Say

> "Let me show you what the output looks like - I have a pre-generated example here..."

> "This is exactly what the extraction produces - 6 entries with all our required fields..."

> "Notice how the service codes are stored as an array in JSON..."
