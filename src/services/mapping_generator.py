"""
Mapping Generator - Creates mapping files from discovered schemas.

This generates PROPOSED mappings based on naming conventions.
In production, these would be manually reviewed and adjusted
through client discussion.

The generator:
1. Takes raw discovery results
2. Proposes mappings based on naming patterns
3. Saves as JSON files for manual review
"""

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from ..core.discovery import DiscoveredSchema, DiscoveredTable

logger = logging.getLogger(__name__)

# Canonical tables we're looking for
CANONICAL_TABLES = ["PATIENT", "KASSEN", "PATKASSE", "KARTEI", "LEISTUNG"]

# Expected columns per table
EXPECTED_COLUMNS = {
    "PATIENT": ["ID", "P_NAME", "P_VORNAME", "DELKZ"],
    "KASSEN": ["ID", "NAME", "ART", "DELKZ"],
    "PATKASSE": ["ID", "PATNR", "KASSENID", "DELKZ"],
    "KARTEI": ["ID", "PATNR", "DATUM", "BEMERKUNG", "DELKZ"],
    "LEISTUNG": ["ID", "PATIENTID", "DATUM", "LEISTUNG", "DELKZ"],
}


def extract_base_name(name: str) -> str:
    """
    Extract base name by removing suffix.

    Examples:
        KARTEI_MN -> KARTEI
        PATNR_NAN6 -> PATNR
        P_NAME_LXZ -> P_NAME
    """
    # Match pattern: BASE_SUFFIX where SUFFIX is 2-4 alphanumeric chars
    match = re.match(r"^(.+)_[A-Z0-9]{2,4}$", name)
    if match:
        return match.group(1)
    return name


def find_matching_table(
    actual_name: str, canonical_tables: list[str]
) -> str | None:
    """Find which canonical table this actual name matches."""
    base = extract_base_name(actual_name)
    for canonical in canonical_tables:
        if base == canonical:
            return canonical
    return None


def find_matching_column(
    actual_name: str, expected_columns: list[str]
) -> str | None:
    """Find which canonical column this actual name matches."""
    base = extract_base_name(actual_name)
    for expected in expected_columns:
        if base == expected:
            return expected
    return None


def generate_mapping(
    center_id: str,
    discovered: DiscoveredSchema,
) -> dict:
    """
    Generate a proposed mapping from discovered schema.

    Returns a mapping structure ready for manual review.
    """
    mapping = {
        "center_id": center_id,
        "database": discovered.database,
        "schema": "ck",
        "generated": True,  # Flag indicating this was auto-generated
        "reviewed": False,  # Flag for manual review status
        "tables": {},
        "unmapped_tables": [],
    }

    for table in discovered.tables:
        canonical_table = find_matching_table(table.name, CANONICAL_TABLES)

        if canonical_table:
            expected_cols = EXPECTED_COLUMNS[canonical_table]
            column_mapping = {}

            for col in table.columns:
                canonical_col = find_matching_column(col.name, expected_cols)
                if canonical_col:
                    column_mapping[canonical_col] = {
                        "actual_name": col.name,
                    }

            mapping["tables"][canonical_table] = {
                "actual_name": table.name,
                "columns": column_mapping,
            }
        else:
            mapping["unmapped_tables"].append(table.name)

    return mapping


def save_mapping(mapping: dict, output_dir: Path) -> Path:
    """Save mapping to JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"{mapping['center_id']}_mapping.json"

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    return filepath


def generate_all_mappings(
    config,
    output_dir: Path,
) -> list[Path]:
    """
    Generate mapping files for all centers.

    This discovers schemas from each database and generates
    proposed mappings based on naming conventions.
    """
    from ..core.discovery import discover_schema

    generated_files = []

    for center in config.centers:
        logger.info(f"Processing {center.name} ({center.id})...")

        try:
            # Discover raw schema from database
            conn_str = config.database.connection_string(center.database)
            discovered = discover_schema(conn_str)

            # Generate proposed mapping
            mapping = generate_mapping(center.id, discovered)

            # Save mapping file
            filepath = save_mapping(mapping, output_dir)
            generated_files.append(filepath)

            # Report
            table_count = len(mapping["tables"])
            unmapped = len(mapping["unmapped_tables"])
            logger.info(f"  -> {table_count} tables mapped, {unmapped} unmapped")

        except Exception as e:
            logger.error(f"  -> Error: {e}")

    return generated_files
