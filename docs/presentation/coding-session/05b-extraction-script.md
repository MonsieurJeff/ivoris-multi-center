# Step 5b: Create Extraction Script

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

## Step 3: Data Model (models/chart_entry.py)

```python
"""Data models for chart entries."""
from dataclasses import dataclass, asdict
from datetime import date
from typing import List, Optional


@dataclass
class ChartEntry:
    """Represents a single chart entry extraction."""
    date: date
    patient_id: int
    insurance_status: str
    insurance_name: Optional[str]
    chart_entry: str
    service_codes: List[str]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "date": self.date.isoformat() if self.date else None,
            "patient_id": self.patient_id,
            "insurance_status": self.insurance_status,
            "insurance_name": self.insurance_name or "",
            "chart_entry": self.chart_entry,
            "service_codes": self.service_codes
        }
```

---

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

    EXTRACTION_QUERY = """
    SELECT
        k.DATUM AS date,
        k.PATIENTID AS patient_id,
        CASE ka.TYP
            WHEN 'G' THEN 'GKV'
            WHEN 'P' THEN 'PKV'
            ELSE 'Selbstzahler'
        END AS insurance_status,
        ISNULL(ka.NAME, '') AS insurance_name,
        k.EINTRAG AS chart_entry,
        ISNULL((
            SELECT STRING_AGG(l.LEISTUNG, ',')
            FROM LEISTUNG l
            WHERE l.PATIENTID = k.PATIENTID
              AND l.DATUM = k.DATUM
        ), '') AS service_codes
    FROM KARTEI k
    JOIN PATIENT p ON k.PATIENTID = p.PATIENTID
    LEFT JOIN KASSE ka ON p.KASSEID = ka.KASSEID
    WHERE k.DATUM = ?
    ORDER BY k.PATIENTID, k.KARTEIID
    """

    def __init__(self, db: DatabaseConnection = None):
        self.db = db or DatabaseConnection()
        self.output_dir = Path("data/output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract(self, target_date: date) -> List[ChartEntry]:
        """Extract chart entries for a specific date."""
        entries = []

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(self.EXTRACTION_QUERY, target_date)

            for row in cursor.fetchall():
                # Parse service codes from comma-separated string
                service_codes = []
                if row.service_codes:
                    service_codes = [s.strip() for s in row.service_codes.split(",")]

                entry = ChartEntry(
                    date=row.date,
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
                    entry.date.isoformat() if entry.date else "",
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
Saved 6 entries to data/output/ivoris_chart_entries_2022-01-18.json
Done! Output: data/output/ivoris_chart_entries_2022-01-18.json
```

### Extract to CSV

```bash
python src/main.py --daily-extract --date 2022-01-18 --format csv
```

**Expected output:**
```
Extracting chart entries for 2022-01-18...
Saved 6 entries to data/output/ivoris_chart_entries_2022-01-18.csv
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
  "record_count": 6,
  "entries": [
    {
      "date": "2022-01-18",
      "patient_id": 1,
      "insurance_status": "GKV",
      "insurance_name": "AOK Bayern",
      "chart_entry": "Kontrolle, Befund unauffällig",
      "service_codes": ["01", "1040"]
    },
    {
      "date": "2022-01-18",
      "patient_id": 1,
      "insurance_status": "GKV",
      "insurance_name": "AOK Bayern",
      "chart_entry": "Zahnreinigung durchgeführt",
      "service_codes": ["01", "1040"]
    }
  ]
}
```

### CSV output

```bash
cat data/output/ivoris_chart_entries_2022-01-18.csv
```

```csv
date,patient_id,insurance_status,insurance_name,chart_entry,service_codes
2022-01-18,1,GKV,AOK Bayern,Kontrolle, Befund unauffällig,"01, 1040"
2022-01-18,1,GKV,AOK Bayern,Zahnreinigung durchgeführt,"01, 1040"
2022-01-18,2,GKV,DAK Gesundheit,Füllungstherapie Zahn 36,13b
2022-01-18,3,GKV,Techniker Krankenkasse,Röntgenaufnahme OPG,Ä935
2022-01-18,4,PKV,PRIVAT,Beratung Zahnersatz,
2022-01-18,5,GKV,Barmer,Professionelle Zahnreinigung,
```

---

## Complete Script (Single File Version)

For quick demos, here's everything in one file:

```python
#!/usr/bin/env python3
"""
ivoris_extract.py - Complete extraction script in one file.

Usage:
    python ivoris_extract.py 2022-01-18
    python ivoris_extract.py 2022-01-18 --csv
"""
import csv
import json
import sys
from datetime import date, datetime

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
    """Extract chart entries for a date."""
    query = """
    SELECT
        k.DATUM, k.PATIENTID,
        CASE ka.TYP WHEN 'G' THEN 'GKV' WHEN 'P' THEN 'PKV' ELSE 'Selbstzahler' END,
        ISNULL(ka.NAME, ''),
        k.EINTRAG,
        ISNULL((SELECT STRING_AGG(l.LEISTUNG, ',') FROM LEISTUNG l
                WHERE l.PATIENTID = k.PATIENTID AND l.DATUM = k.DATUM), '')
    FROM KARTEI k
    JOIN PATIENT p ON k.PATIENTID = p.PATIENTID
    LEFT JOIN KASSE ka ON p.KASSEID = ka.KASSEID
    WHERE k.DATUM = ?
    """

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(query, target_date)

    entries = []
    for row in cursor.fetchall():
        entries.append({
            "date": row[0].isoformat(),
            "patient_id": row[1],
            "insurance_status": row[2],
            "insurance_name": row[3],
            "chart_entry": row[4],
            "service_codes": row[5].split(",") if row[5] else []
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

## Next Step

→ [06-cron-setup.md](./06-cron-setup.md) - Automate with cron job
