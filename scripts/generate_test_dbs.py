#!/usr/bin/env python3
"""
Generate test databases for multi-center extraction.

Creates 30 databases with RANDOM table/column suffixes per element,
simulating real-world schema variations across dental centers.
Each center gets a mapping file recording the actual schema.
"""

import json
import logging
import random
import string
import sys
from pathlib import Path

import pyodbc
import yaml

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Sample data for testing
SAMPLE_PATIENTS = [
    (1, "Müller", "Anna"),
    (2, "Schmidt", "Hans"),
    (3, "Weber", "Maria"),
    (4, "Fischer", "Klaus"),
    (5, "Meyer", "Petra"),
]

SAMPLE_INSURANCE = [
    (1, "AOK Bayern", "4"),
    (2, "DAK Gesundheit", "8"),
    (3, "Techniker Krankenkasse", "8"),
    (4, "PRIVAT", "P"),
    (5, "Barmer", "8"),
]

SAMPLE_CHART_ENTRIES = [
    # (patient_id, date, entry)
    (1, 20220118, "Kontrolle, Befund unauffällig"),
    (1, 20220118, "Zahnreinigung durchgeführt"),
    (2, 20220118, "Füllungstherapie Zahn 36"),
    (3, 20220118, "Röntgenaufnahme OPG"),
    (4, 20220118, "Beratung Zahnersatz"),
    (5, 20220118, "Professionelle Zahnreinigung"),
    (1, 20220119, "Nachkontrolle"),
    (2, 20220119, "Wurzelbehandlung Zahn 36"),
]

SAMPLE_SERVICES = [
    # (patient_id, date, code)
    (1, 20220118, "01"),
    (1, 20220118, "1040"),
    (2, 20220118, "13b"),
    (3, 20220118, "Ä935"),
]

# Canonical schema definition
# This defines what tables and columns we expect in each center
CANONICAL_SCHEMA = {
    "PATIENT": {
        "columns": ["ID", "P_NAME", "P_VORNAME", "DELKZ"],
        "id_column": "ID",
    },
    "KASSEN": {
        "columns": ["ID", "NAME", "ART", "DELKZ"],
        "id_column": "ID",
    },
    "PATKASSE": {
        "columns": ["ID", "PATNR", "KASSENID", "DELKZ"],
        "id_column": "ID",
        "identity": True,
    },
    "KARTEI": {
        "columns": ["ID", "PATNR", "DATUM", "BEMERKUNG", "DELKZ"],
        "id_column": "ID",
        "identity": True,
    },
    "LEISTUNG": {
        "columns": ["ID", "PATIENTID", "DATUM", "LEISTUNG", "DELKZ"],
        "id_column": "ID",
        "identity": True,
    },
}


def generate_suffix() -> str:
    """Generate a random 2-4 character suffix."""
    length = random.choice([2, 3, 4])
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def generate_schema_mapping(center_id: str) -> dict:
    """
    Generate random suffixes for each table and column.

    NOTE: center_01 uses clean names (no suffixes) to match the
    original Main Challenge schema. All other centers have random suffixes.

    Returns a mapping structure like:
    {
        "center_id": "center_01",
        "tables": {
            "PATIENT": {
                "actual_name": "PATIENT_X7K",
                "columns": {
                    "ID": "ID",  # ID columns keep their name
                    "P_NAME": "P_NAME_QW2",
                    "P_VORNAME": "P_VORNAME_8M",
                    "DELKZ": "DELKZ"  # DELKZ keeps its name (standard flag)
                }
            },
            ...
        }
    }
    """
    # center_01 uses clean schema (no suffixes) - matches Main Challenge
    use_clean_schema = (center_id == "center_01")

    mapping = {
        "center_id": center_id,
        "schema": "ck",
        "tables": {},
    }

    for table_name, table_def in CANONICAL_SCHEMA.items():
        if use_clean_schema:
            actual_table_name = table_name
        else:
            table_suffix = generate_suffix()
            actual_table_name = f"{table_name}_{table_suffix}"

        column_mapping = {}
        for col in table_def["columns"]:
            # Keep ID and DELKZ columns unchanged (they're standard)
            if col in ("ID", "DELKZ"):
                column_mapping[col] = col
            elif use_clean_schema:
                column_mapping[col] = col
            else:
                col_suffix = generate_suffix()
                column_mapping[col] = f"{col}_{col_suffix}"

        mapping["tables"][table_name] = {
            "actual_name": actual_table_name,
            "columns": column_mapping,
        }

    return mapping


def save_ground_truth(mapping: dict, output_dir: Path) -> None:
    """Save ground truth mapping (what was actually generated)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"{mapping['center_id']}_ground_truth.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)
    logger.info(f"  Saved ground truth to {filepath.name}")


def load_centers():
    """Load center configuration."""
    config_path = Path(__file__).parent.parent / "config" / "centers.yml"
    with open(config_path) as f:
        data = yaml.safe_load(f)
    return data["database"], data["centers"]


def get_master_connection(db_config):
    """Get connection to master database."""
    conn_str = (
        f"DRIVER={{{db_config['driver']}}};"
        f"SERVER={db_config['host']},{db_config['port']};"
        f"DATABASE=master;"
        f"UID={db_config['user']};"
        f"PWD={db_config['password']};"
        f"TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str, autocommit=True)


def get_db_connection(db_config, database):
    """Get connection to specific database."""
    conn_str = (
        f"DRIVER={{{db_config['driver']}}};"
        f"SERVER={db_config['host']},{db_config['port']};"
        f"DATABASE={database};"
        f"UID={db_config['user']};"
        f"PWD={db_config['password']};"
        f"TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str, autocommit=True)


def create_database(conn, db_name):
    """Create a database if it doesn't exist."""
    cursor = conn.cursor()

    # Check if exists
    cursor.execute(f"SELECT DB_ID('{db_name}')")
    if cursor.fetchone()[0] is not None:
        logger.info(f"  Database {db_name} already exists, dropping...")
        cursor.execute(
            f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE"
        )
        cursor.execute(f"DROP DATABASE [{db_name}]")

    logger.info(f"  Creating database {db_name}...")
    cursor.execute(f"CREATE DATABASE [{db_name}]")
    cursor.close()


def create_schema_and_tables(db_config, database, mapping: dict):
    """Create schema and tables with randomized names from mapping."""
    conn = get_db_connection(db_config, database)
    cursor = conn.cursor()

    # Create ck schema
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'ck')
        EXEC('CREATE SCHEMA ck')
    """)

    tables = mapping["tables"]

    # Create PATIENT table
    t = tables["PATIENT"]
    cursor.execute(f"""
        CREATE TABLE ck.{t['actual_name']} (
            {t['columns']['ID']} INT PRIMARY KEY,
            {t['columns']['P_NAME']} NVARCHAR(100),
            {t['columns']['P_VORNAME']} NVARCHAR(100),
            {t['columns']['DELKZ']} INT DEFAULT 0
        )
    """)

    # Create KASSEN table
    t = tables["KASSEN"]
    cursor.execute(f"""
        CREATE TABLE ck.{t['actual_name']} (
            {t['columns']['ID']} INT PRIMARY KEY,
            {t['columns']['NAME']} NVARCHAR(100),
            {t['columns']['ART']} VARCHAR(10),
            {t['columns']['DELKZ']} INT DEFAULT 0
        )
    """)

    # Create PATKASSE table
    t = tables["PATKASSE"]
    cursor.execute(f"""
        CREATE TABLE ck.{t['actual_name']} (
            {t['columns']['ID']} INT IDENTITY PRIMARY KEY,
            {t['columns']['PATNR']} INT,
            {t['columns']['KASSENID']} INT,
            {t['columns']['DELKZ']} INT DEFAULT 0
        )
    """)

    # Create KARTEI table
    t = tables["KARTEI"]
    cursor.execute(f"""
        CREATE TABLE ck.{t['actual_name']} (
            {t['columns']['ID']} INT IDENTITY PRIMARY KEY,
            {t['columns']['PATNR']} INT,
            {t['columns']['DATUM']} INT,
            {t['columns']['BEMERKUNG']} NVARCHAR(500),
            {t['columns']['DELKZ']} INT DEFAULT 0
        )
    """)

    # Create LEISTUNG table
    t = tables["LEISTUNG"]
    cursor.execute(f"""
        CREATE TABLE ck.{t['actual_name']} (
            {t['columns']['ID']} INT IDENTITY PRIMARY KEY,
            {t['columns']['PATIENTID']} INT,
            {t['columns']['DATUM']} INT,
            {t['columns']['LEISTUNG']} VARCHAR(20),
            {t['columns']['DELKZ']} INT DEFAULT 0
        )
    """)

    cursor.close()
    conn.close()


def populate_data(db_config, database, mapping: dict):
    """Populate tables with sample data using mapping."""
    conn = get_db_connection(db_config, database)
    cursor = conn.cursor()

    tables = mapping["tables"]

    # Insert patients
    t = tables["PATIENT"]
    for id, name, vorname in SAMPLE_PATIENTS:
        cursor.execute(
            f"INSERT INTO ck.{t['actual_name']} "
            f"({t['columns']['ID']}, {t['columns']['P_NAME']}, {t['columns']['P_VORNAME']}) "
            f"VALUES (?, ?, ?)",
            (id, name, vorname),
        )

    # Insert insurance providers
    t = tables["KASSEN"]
    for id, name, art in SAMPLE_INSURANCE:
        cursor.execute(
            f"INSERT INTO ck.{t['actual_name']} "
            f"({t['columns']['ID']}, {t['columns']['NAME']}, {t['columns']['ART']}) "
            f"VALUES (?, ?, ?)",
            (id, name, art),
        )

    # Link patients to insurance (patient ID = insurance ID for simplicity)
    t = tables["PATKASSE"]
    for id, _, _ in SAMPLE_PATIENTS:
        cursor.execute(
            f"INSERT INTO ck.{t['actual_name']} "
            f"({t['columns']['PATNR']}, {t['columns']['KASSENID']}) "
            f"VALUES (?, ?)",
            (id, id),
        )

    # Insert chart entries
    t = tables["KARTEI"]
    for patient_id, datum, entry in SAMPLE_CHART_ENTRIES:
        cursor.execute(
            f"INSERT INTO ck.{t['actual_name']} "
            f"({t['columns']['PATNR']}, {t['columns']['DATUM']}, {t['columns']['BEMERKUNG']}) "
            f"VALUES (?, ?, ?)",
            (patient_id, datum, entry),
        )

    # Insert services
    t = tables["LEISTUNG"]
    for patient_id, datum, code in SAMPLE_SERVICES:
        cursor.execute(
            f"INSERT INTO ck.{t['actual_name']} "
            f"({t['columns']['PATIENTID']}, {t['columns']['DATUM']}, {t['columns']['LEISTUNG']}) "
            f"VALUES (?, ?, ?)",
            (patient_id, datum, code),
        )

    cursor.close()
    conn.close()


def main():
    logger.info("=" * 60)
    logger.info("Multi-Center Test Database Generator")
    logger.info("With RANDOM Schema Variations")
    logger.info("=" * 60)

    db_config, centers = load_centers()
    ground_truth_dir = Path(__file__).parent.parent / "data" / "ground_truth"

    logger.info(f"\nConnecting to SQL Server at {db_config['host']}:{db_config['port']}...")

    try:
        master_conn = get_master_connection(db_config)
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        logger.info("\nMake sure SQL Server is running:")
        logger.info("  docker-compose up -d")
        return 1

    logger.info("Connected!\n")

    for center in centers:
        # Skip center_01 - it has the real challenge database
        if center["id"] == "center_01":
            logger.info(f"Skipping {center['name']} ({center['database']}) - using real challenge database")
            continue

        logger.info(f"Creating {center['name']} ({center['database']})...")

        try:
            # Generate random schema mapping for this center
            mapping = generate_schema_mapping(center["id"])

            # Create database
            create_database(master_conn, center["database"])

            # Create schema and tables with random names
            create_schema_and_tables(db_config, center["database"], mapping)

            # Populate data
            populate_data(db_config, center["database"], mapping)

            # Save ground truth (what was actually generated)
            save_ground_truth(mapping, ground_truth_dir)

            logger.info(f"  Done\n")
        except Exception as e:
            logger.error(f"  Error: {e}\n")
            return 1

    master_conn.close()

    logger.info("=" * 60)
    logger.info(f"Created {len(centers)} test databases")
    logger.info(f"Ground truth saved to: {ground_truth_dir}")
    logger.info("=" * 60)

    logger.info("\nSample data per database:")
    logger.info(f"  - {len(SAMPLE_PATIENTS)} patients")
    logger.info(f"  - {len(SAMPLE_INSURANCE)} insurance providers")
    logger.info(f"  - {len(SAMPLE_CHART_ENTRIES)} chart entries")
    logger.info(f"  - {len(SAMPLE_SERVICES)} service codes")

    logger.info("\nSchema variations:")
    logger.info("  - Each table has a RANDOM suffix (e.g., KARTEI_X7K)")
    logger.info("  - Each column has a RANDOM suffix (e.g., PATNR_QW2)")
    logger.info("  - Ground truth in data/ground_truth/<center_id>_ground_truth.json")

    logger.info("\nNext steps:")
    logger.info("  1. python -m src.cli discover-raw   # See raw schema")
    logger.info("  2. python -m src.cli map-schema     # Agentic mapping")
    logger.info("  3. python -m src.cli extract        # Extract data")

    return 0


if __name__ == "__main__":
    sys.exit(main())
