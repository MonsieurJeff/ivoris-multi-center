#!/usr/bin/env python3
"""
Generate test databases for multi-center extraction.

Creates 10 databases with different table/column suffixes,
each populated with identical sample data.
"""

import logging
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
        cursor.execute(f"ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
        cursor.execute(f"DROP DATABASE [{db_name}]")
    
    logger.info(f"  Creating database {db_name}...")
    cursor.execute(f"CREATE DATABASE [{db_name}]")
    cursor.close()


def create_schema_and_tables(db_config, database, suffix):
    """Create schema and tables with suffixed names."""
    conn = get_db_connection(db_config, database)
    cursor = conn.cursor()

    # Create ck schema
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'ck')
        EXEC('CREATE SCHEMA ck')
    """)

    # Create PATIENT table
    cursor.execute(f"""
        CREATE TABLE ck.PATIENT_{suffix} (
            ID INT PRIMARY KEY,
            P_NAME_{suffix} NVARCHAR(100),
            P_VORNAME_{suffix} NVARCHAR(100),
            DELKZ INT DEFAULT 0
        )
    """)

    # Create KASSEN table
    cursor.execute(f"""
        CREATE TABLE ck.KASSEN_{suffix} (
            ID INT PRIMARY KEY,
            NAME_{suffix} NVARCHAR(100),
            ART_{suffix} VARCHAR(10),
            DELKZ INT DEFAULT 0
        )
    """)

    # Create PATKASSE table
    cursor.execute(f"""
        CREATE TABLE ck.PATKASSE_{suffix} (
            ID INT IDENTITY PRIMARY KEY,
            PATNR_{suffix} INT,
            KASSENID_{suffix} INT,
            DELKZ INT DEFAULT 0
        )
    """)

    # Create KARTEI table
    cursor.execute(f"""
        CREATE TABLE ck.KARTEI_{suffix} (
            ID INT IDENTITY PRIMARY KEY,
            PATNR_{suffix} INT,
            DATUM_{suffix} INT,
            BEMERKUNG_{suffix} NVARCHAR(500),
            DELKZ INT DEFAULT 0
        )
    """)

    # Create LEISTUNG table
    cursor.execute(f"""
        CREATE TABLE ck.LEISTUNG_{suffix} (
            ID INT IDENTITY PRIMARY KEY,
            PATIENTID_{suffix} INT,
            DATUM_{suffix} INT,
            LEISTUNG_{suffix} VARCHAR(20),
            DELKZ INT DEFAULT 0
        )
    """)

    cursor.close()
    conn.close()


def populate_data(db_config, database, suffix):
    """Populate tables with sample data."""
    conn = get_db_connection(db_config, database)
    cursor = conn.cursor()

    # Insert patients
    for id, name, vorname in SAMPLE_PATIENTS:
        cursor.execute(
            f"INSERT INTO ck.PATIENT_{suffix} (ID, P_NAME_{suffix}, P_VORNAME_{suffix}) VALUES (?, ?, ?)",
            (id, name, vorname)
        )

    # Insert insurance providers
    for id, name, art in SAMPLE_INSURANCE:
        cursor.execute(
            f"INSERT INTO ck.KASSEN_{suffix} (ID, NAME_{suffix}, ART_{suffix}) VALUES (?, ?, ?)",
            (id, name, art)
        )

    # Link patients to insurance (patient ID = insurance ID for simplicity)
    for id, _, _ in SAMPLE_PATIENTS:
        cursor.execute(
            f"INSERT INTO ck.PATKASSE_{suffix} (PATNR_{suffix}, KASSENID_{suffix}) VALUES (?, ?)",
            (id, id)
        )

    # Insert chart entries
    for patient_id, datum, entry in SAMPLE_CHART_ENTRIES:
        cursor.execute(
            f"INSERT INTO ck.KARTEI_{suffix} (PATNR_{suffix}, DATUM_{suffix}, BEMERKUNG_{suffix}) VALUES (?, ?, ?)",
            (patient_id, datum, entry)
        )

    # Insert services
    for patient_id, datum, code in SAMPLE_SERVICES:
        cursor.execute(
            f"INSERT INTO ck.LEISTUNG_{suffix} (PATIENTID_{suffix}, DATUM_{suffix}, LEISTUNG_{suffix}) VALUES (?, ?, ?)",
            (patient_id, datum, code)
        )

    cursor.close()
    conn.close()


def main():
    logger.info("=" * 60)
    logger.info("Multi-Center Test Database Generator")
    logger.info("=" * 60)

    db_config, centers = load_centers()
    
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
        logger.info(f"Creating {center['name']} ({center['database']})...")
        
        try:
            # Create database
            create_database(master_conn, center["database"])
            
            # Create schema and tables
            create_schema_and_tables(db_config, center["database"], center["suffix"])
            
            # Populate data
            populate_data(db_config, center["database"], center["suffix"])
            
            logger.info(f"  ✓ Done\n")
        except Exception as e:
            logger.error(f"  ✗ Error: {e}\n")
            return 1

    master_conn.close()

    logger.info("=" * 60)
    logger.info(f"Created {len(centers)} test databases")
    logger.info("=" * 60)
    
    logger.info("\nSample data per database:")
    logger.info(f"  - {len(SAMPLE_PATIENTS)} patients")
    logger.info(f"  - {len(SAMPLE_INSURANCE)} insurance providers")
    logger.info(f"  - {len(SAMPLE_CHART_ENTRIES)} chart entries")
    logger.info(f"  - {len(SAMPLE_SERVICES)} service codes")

    logger.info("\nTest with:")
    logger.info("  python -m src.cli list")
    logger.info("  python -m src.cli discover")
    logger.info("  python -m src.cli extract --date 2022-01-18")

    return 0


if __name__ == "__main__":
    sys.exit(main())
