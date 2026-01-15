# Step 5b: Create Extraction Script

> **💬 Talking Points**
> - "Now we wrap our SQL query in Python for automation"
> - "I'll show two approaches: modular (for production) and single-file (for quick demos)"
> - "The goal is a CLI tool we can run from cron"

---

## Goal

Create a Python script that:
1. Connects to the database
2. Runs the extraction query
3. Outputs to CSV or JSON file

---

## Project Structure

```
ivoris-pipeline/
├── src/
│   ├── main.py              # CLI entry point
│   ├── services/
│   │   └── daily_extract.py # Extraction logic
│   ├── adapters/
│   │   └── database.py      # Database connection
│   └── models/
│       └── chart_entry.py   # Data model
├── data/
│   └── output/              # Output files go here
├── config/
│   └── settings.py          # Configuration
└── requirements.txt
```

---

## Step 1: Install Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install packages
pip install pyodbc python-dotenv
```

**requirements.txt:**
```
pyodbc>=4.0.39
python-dotenv>=1.0.0
```

---

> **💬 Talking Points - Database Adapter**
> - "Context manager pattern ensures connections are always closed"
> - "TrustServerCertificate=yes is needed for local Docker SSL"
> - "This class is reusable across all our extraction services"

## Step 2: Database Connection (adapters/database.py)

```python
"""Database connection adapter."""
import pyodbc
from contextlib import contextmanager


class DatabaseConnection:
    """Manages SQL Server database connections."""

    def __init__(
        self,
        server: str = "localhost,1433",
        database: str = "DentalDB",
        username: str = "sa",
        password: str = "YourStrong@Passw0rd"
    ):
        self.conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"TrustServerCertificate=yes"
        )

    @contextmanager
    def connect(self):
        """Context manager for database connection."""
        conn = None
        try:
            conn = pyodbc.connect(self.conn_str, timeout=30)
            yield conn
        finally:
            if conn:
                conn.close()

    def test_connection(self) -> bool:
        """Test if database is reachable."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
```

**Test it:**
```bash
python -c "
from src.adapters.database import DatabaseConnection
db = DatabaseConnection()
print('Connected!' if db.test_connection() else 'Failed!')
"
```

---

> **💬 Talking Points - Data Model**
> - "Dataclass gives us type safety and auto-generated __init__"
> - "to_dict() converts for JSON serialization"
> - "This is our contract - what the output looks like"

## Step 3: Data Model (models/chart_entry.py)

```python
"""Data models for chart entries."""
from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class ChartEntry:
    """Represents a single chart entry extraction."""
    date: str  # Already formatted as YYYY-MM-DD
    patient_id: int
    insurance_status: str
    insurance_name: Optional[str]
    chart_entry: str
    service_codes: List[str]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "date": self.date,
            "patient_id": self.patient_id,
            "insurance_status": self.insurance_status,
            "insurance_name": self.insurance_name or "",
            "chart_entry": self.chart_entry,
            "service_codes": self.service_codes
        }
```

---

> **💬 Talking Points - Extraction Service**
> - "The SQL query uses the REAL Ivoris schema we discovered"
> - "Tables are in the `ck` schema - not `dbo`!"
> - "We must filter soft-deleted rows with DELKZ everywhere"
> - "Date conversion from YYYYMMDD to YYYY-MM-DD happens in SQL"

## Step 4: Extraction Service (services/daily_extract.py)

```python
"""Daily extraction service."""
import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import List

from ..adapters.database import DatabaseConnection
from ..models.chart_entry import ChartEntry


class DailyExtractService:
    """Extracts daily chart entries from Ivoris database."""

    # Real Ivoris schema query:
    # - Tables in 'ck' schema
    # - PATNR (not PATIENTID) in KARTEI
    # - BEMERKUNG (not EINTRAG) for chart entry
    # - PATKASSE junction table for insurance link
    # - ART values: 'P'=PKV, '1'-'9'=GKV
    # - DELKZ soft delete flag
    # - Date stored as VARCHAR(8) YYYYMMDD

    EXTRACTION_QUERY = """
    SELECT
        SUBSTRING(k.DATUM, 1, 4) + '-' +
        SUBSTRING(k.DATUM, 5, 2) + '-' +
        SUBSTRING(k.DATUM, 7, 2) AS date,
        k.PATNR AS patient_id,
        CASE
            WHEN ka.ART = 'P' THEN 'PKV'
            WHEN ka.ART IN ('1','2','3','4','5','6','7','8','9') THEN 'GKV'
            ELSE 'Selbstzahler'
        END AS insurance_status,
        ISNULL(ka.NAME, '') AS insurance_name,
        LEFT(ISNULL(k.BEMERKUNG, ''), 500) AS chart_entry,
        ISNULL((
            SELECT STRING_AGG(l.LEISTUNG, ', ')
            FROM ck.LEISTUNG l
            WHERE l.PATIENTID = k.PATNR
              AND l.DATUM = k.DATUM
              AND (l.DELKZ = 0 OR l.DELKZ IS NULL)
        ), '') AS service_codes
    FROM ck.KARTEI k
    JOIN ck.PATKASSE pk ON k.PATNR = pk.PATNR
        AND (pk.DELKZ = 0 OR pk.DELKZ IS NULL)
    LEFT JOIN ck.KASSEN ka ON pk.KASSENID = ka.ID
    WHERE (k.DELKZ = 0 OR k.DELKZ IS NULL)
      AND k.DATUM = ?
    ORDER BY k.PATNR
    """

    def __init__(self, db: DatabaseConnection = None):
        self.db = db or DatabaseConnection()
        self.output_dir = Path("data/output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract(self, target_date: date) -> List[ChartEntry]:
        """Extract chart entries for a specific date."""
        entries = []

        # Convert date to YYYYMMDD format for the query
        date_str = target_date.strftime('%Y%m%d')

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(self.EXTRACTION_QUERY, date_str)

            for row in cursor.fetchall():
                # Parse service codes from comma-separated string
                service_codes = []
                if row.service_codes:
                    service_codes = [s.strip() for s in row.service_codes.split(", ")]

                entry = ChartEntry(
                    date=row.date,  # Already formatted YYYY-MM-DD from SQL
                    patient_id=row.patient_id,
                    insurance_status=row.insurance_status,
                    insurance_name=row.insurance_name,
                    chart_entry=row.chart_entry,
                    service_codes=service_codes
                )
                entries.append(entry)

        return entries

    def save_json(self, entries: List[ChartEntry], target_date: date) -> Path:
        """Save entries to JSON file."""
        filename = self.output_dir / f"ivoris_chart_entries_{target_date.isoformat()}.json"

        output = {
            "extraction_timestamp": datetime.now().isoformat(),
            "target_date": target_date.isoformat(),
            "record_count": len(entries),
            "entries": [e.to_dict() for e in entries]
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(entries)} entries to {filename}")
        return filename

    def save_csv(self, entries: List[ChartEntry], target_date: date) -> Path:
        """Save entries to CSV file."""
        filename = self.output_dir / f"ivoris_chart_entries_{target_date.isoformat()}.csv"

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Header row
            writer.writerow([
                "date",
                "patient_id",
                "insurance_status",
                "insurance_name",
                "chart_entry",
                "service_codes"
            ])

            # Data rows
            for entry in entries:
                writer.writerow([
                    entry.date,
                    entry.patient_id,
                    entry.insurance_status,
                    entry.insurance_name,
                    entry.chart_entry,
                    ", ".join(entry.service_codes)
                ])

        print(f"Saved {len(entries)} entries to {filename}")
        return filename

    def extract_and_save(
        self,
        target_date: date,
        format: str = "json"
    ) -> Path:
        """Extract and save in one call."""
        entries = self.extract(target_date)

        if format == "csv":
            return self.save_csv(entries, target_date)
        else:
            return self.save_json(entries, target_date)
```

---

> **💬 Talking Points - CLI**
> - "argparse gives us professional command-line argument handling"
> - "Default to yesterday's date - that's what cron will use"
> - "--test-connection is useful for debugging"

## Step 5: CLI Entry Point (main.py)

```python
#!/usr/bin/env python3
"""
Ivoris Daily Extraction Pipeline

Usage:
    python src/main.py --daily-extract --date 2022-01-18
    python src/main.py --daily-extract --date 2022-01-18 --format csv
    python src/main.py --daily-extract  # defaults to yesterday
    python src/main.py --test-connection
"""
import argparse
from datetime import date, timedelta

from services.daily_extract import DailyExtractService
from adapters.database import DatabaseConnection


def main():
    parser = argparse.ArgumentParser(
        description="Ivoris Daily Data Extraction Pipeline"
    )

    parser.add_argument(
        "--daily-extract",
        action="store_true",
        help="Run daily extraction"
    )

    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Target date (YYYY-MM-DD). Defaults to yesterday."
    )

    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Output format (default: json)"
    )

    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Test database connection"
    )

    args = parser.parse_args()

    # Test connection
    if args.test_connection:
        db = DatabaseConnection()
        if db.test_connection():
            print("✓ Database connection successful")
            return 0
        else:
            print("✗ Database connection failed")
            return 1

    # Daily extraction
    if args.daily_extract:
        # Parse date or default to yesterday
        if args.date:
            target_date = date.fromisoformat(args.date)
        else:
            target_date = date.today() - timedelta(days=1)

        print(f"Extracting chart entries for {target_date}...")

        service = DailyExtractService()
        output_file = service.extract_and_save(target_date, args.format)

        print(f"Done! Output: {output_file}")
        return 0

    # No action specified
    parser.print_help()
    return 1


if __name__ == "__main__":
    exit(main())
```

---

## Step 6: Run the Script

### Test connection first

```bash
python src/main.py --test-connection
```

**Expected output:**
```
✓ Database connection successful
```

### Extract to JSON (default)

```bash
python src/main.py --daily-extract --date 2022-01-18
```

**Expected output:**
```
Extracting chart entries for 2022-01-18...
Saved 4 entries to data/output/ivoris_chart_entries_2022-01-18.json
Done! Output: data/output/ivoris_chart_entries_2022-01-18.json
```

### Extract to CSV

```bash
python src/main.py --daily-extract --date 2022-01-18 --format csv
```

**Expected output:**
```
Extracting chart entries for 2022-01-18...
Saved 4 entries to data/output/ivoris_chart_entries_2022-01-18.csv
Done! Output: data/output/ivoris_chart_entries_2022-01-18.csv
```

### Extract yesterday (default for cron)

```bash
python src/main.py --daily-extract
```

---

## Step 7: Verify Output

### JSON output

```bash
cat data/output/ivoris_chart_entries_2022-01-18.json
```

```json
{
  "extraction_timestamp": "2026-01-14T15:30:00.123456",
  "target_date": "2022-01-18",
  "record_count": 4,
  "entries": [
    {
      "date": "2022-01-18",
      "patient_id": 1,
      "insurance_status": "GKV",
      "insurance_name": "DAK Gesundheit",
      "chart_entry": "Ausführliche Aufklärung über Mundhygiene und Putztechnik, Röntgenauswertung OPG",
      "service_codes": []
    },
    {
      "date": "2022-01-18",
      "patient_id": 1,
      "insurance_status": "GKV",
      "insurance_name": "DAK Gesundheit",
      "chart_entry": "Kontrolle,",
      "service_codes": []
    }
  ]
}
```

**Note:** `service_codes` is empty because all LEISTUNG records in this database are soft-deleted.

### CSV output

```bash
cat data/output/ivoris_chart_entries_2022-01-18.csv
```

```csv
date,patient_id,insurance_status,insurance_name,chart_entry,service_codes
2022-01-18,1,GKV,DAK Gesundheit,"Ausführliche Aufklärung über Mundhygiene und Putztechnik, Röntgenauswertung OPG",
2022-01-18,1,GKV,DAK Gesundheit,"Kontrolle,",
```

---

> **💬 Talking Points - Single File Version**
> - "For demos or one-off scripts, you don't need all that structure"
> - "This is the same logic in under 100 lines"
> - "Good for prototyping, then refactor when it works"

## Complete Script (Single File Version)

For quick demos, here's everything in one file:

```python
#!/usr/bin/env python3
"""
ivoris_extract.py - Complete extraction script in one file.

Uses REAL Ivoris schema:
- Tables in 'ck' schema
- PATNR for patient ID, BEMERKUNG for chart entry
- PATKASSE junction table for insurance
- ART: 'P'=PKV, '1'-'9'=GKV
- DELKZ soft delete flag
- Date as VARCHAR(8) YYYYMMDD

Usage:
    python ivoris_extract.py 2022-01-18
    python ivoris_extract.py 2022-01-18 --csv
"""
import csv
import json
import sys
from datetime import datetime

import pyodbc


def connect_db():
    """Connect to SQL Server."""
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=DentalDB;"
        "UID=sa;PWD=YourStrong@Passw0rd;"
        "TrustServerCertificate=yes"
    )
    return pyodbc.connect(conn_str)


def extract(target_date: str) -> list:
    """Extract chart entries for a date (YYYY-MM-DD format)."""
    # Convert YYYY-MM-DD to YYYYMMDD for the query
    date_str = target_date.replace("-", "")

    query = """
    SELECT
        SUBSTRING(k.DATUM, 1, 4) + '-' +
        SUBSTRING(k.DATUM, 5, 2) + '-' +
        SUBSTRING(k.DATUM, 7, 2) AS date,
        k.PATNR AS patient_id,
        CASE
            WHEN ka.ART = 'P' THEN 'PKV'
            WHEN ka.ART IN ('1','2','3','4','5','6','7','8','9') THEN 'GKV'
            ELSE 'Selbstzahler'
        END AS insurance_status,
        ISNULL(ka.NAME, '') AS insurance_name,
        LEFT(ISNULL(k.BEMERKUNG, ''), 500) AS chart_entry,
        ISNULL((
            SELECT STRING_AGG(l.LEISTUNG, ', ')
            FROM ck.LEISTUNG l
            WHERE l.PATIENTID = k.PATNR
              AND l.DATUM = k.DATUM
              AND (l.DELKZ = 0 OR l.DELKZ IS NULL)
        ), '') AS service_codes
    FROM ck.KARTEI k
    JOIN ck.PATKASSE pk ON k.PATNR = pk.PATNR
        AND (pk.DELKZ = 0 OR pk.DELKZ IS NULL)
    LEFT JOIN ck.KASSEN ka ON pk.KASSENID = ka.ID
    WHERE (k.DELKZ = 0 OR k.DELKZ IS NULL)
      AND k.DATUM = ?
    ORDER BY k.PATNR
    """

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(query, date_str)

    entries = []
    for row in cursor.fetchall():
        entries.append({
            "date": row[0],
            "patient_id": row[1],
            "insurance_status": row[2],
            "insurance_name": row[3],
            "chart_entry": row[4],
            "service_codes": [s.strip() for s in row[5].split(", ")] if row[5] else []
        })

    conn.close()
    return entries


def save_json(entries: list, target_date: str):
    """Save to JSON."""
    filename = f"ivoris_chart_entries_{target_date}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({
            "extraction_timestamp": datetime.now().isoformat(),
            "target_date": target_date,
            "record_count": len(entries),
            "entries": entries
        }, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(entries)} entries to {filename}")


def save_csv(entries: list, target_date: str):
    """Save to CSV."""
    filename = f"ivoris_chart_entries_{target_date}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "patient_id", "insurance_status", "insurance_name", "chart_entry", "service_codes"])
        for e in entries:
            w.writerow([e["date"], e["patient_id"], e["insurance_status"],
                       e["insurance_name"], e["chart_entry"], ", ".join(e["service_codes"])])
    print(f"Saved {len(entries)} entries to {filename}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ivoris_extract.py YYYY-MM-DD [--csv]")
        sys.exit(1)

    target = sys.argv[1]
    use_csv = "--csv" in sys.argv

    print(f"Extracting for {target}...")
    data = extract(target)

    if use_csv:
        save_csv(data, target)
    else:
        save_json(data, target)
```

**Run it:**
```bash
python ivoris_extract.py 2022-01-18          # JSON
python ivoris_extract.py 2022-01-18 --csv    # CSV
```

---

## Key Schema Points (Real Ivoris)

| What You Might Expect | Real Ivoris Schema |
|-----------------------|-------------------|
| `dbo` schema | `ck` schema |
| `PATIENTID` | `PATNR` (in KARTEI, PATKASSE) |
| `EINTRAG` | `BEMERKUNG` |
| `KASSE` table | `KASSEN` table |
| `KASSE.TYP` = 'G'/'P' | `KASSEN.ART` = '1'-'9' (GKV) / 'P' (PKV) |
| Direct PATIENT→KASSE FK | PATKASSE junction table |
| DATE type | VARCHAR(8) as YYYYMMDD |
| No soft delete | `DELKZ` flag on ALL tables |

---

## Next Step

→ [06-cron-setup.md](./06-cron-setup.md) - Automate with cron job
