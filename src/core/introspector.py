"""
Schema Introspector - Auto-discovers database schema via pattern matching.

This module handles the complex task of discovering table and column names
when each element has a random suffix. It uses INFORMATION_SCHEMA to query
the actual database structure and pattern matching to identify canonical elements.

Strategy:
1. Query all tables in the 'ck' schema
2. Match tables to canonical names (PATIENT, KARTEI, KASSEN, PATKASSE, LEISTUNG)
3. For each matched table, query its columns
4. Match columns to expected canonical column names
5. Build a complete SchemaMapping that can be used for queries
"""

import logging
import re
from functools import lru_cache

import pyodbc

from .schema_mapping import ColumnMapping, SchemaMapping, TableMapping

logger = logging.getLogger(__name__)

# Canonical table definitions with expected columns
# Each table has a base name and expected column base names
CANONICAL_TABLES = {
    "PATIENT": {
        "pattern": r"^PATIENT[_A-Z0-9]*$",
        "columns": {
            "ID": r"^ID$",
            "P_NAME": r"^P_NAME[_A-Z0-9]*$",
            "P_VORNAME": r"^P_VORNAME[_A-Z0-9]*$",
            "DELKZ": r"^DELKZ$",
        },
    },
    "KASSEN": {
        "pattern": r"^KASSEN[_A-Z0-9]*$",
        "columns": {
            "ID": r"^ID$",
            "NAME": r"^NAME[_A-Z0-9]*$",
            "ART": r"^ART[_A-Z0-9]*$",
            "DELKZ": r"^DELKZ$",
        },
    },
    "PATKASSE": {
        "pattern": r"^PATKASSE[_A-Z0-9]*$",
        "columns": {
            "ID": r"^ID$",
            "PATNR": r"^PATNR[_A-Z0-9]*$",
            "KASSENID": r"^KASSENID[_A-Z0-9]*$",
            "DELKZ": r"^DELKZ$",
        },
    },
    "KARTEI": {
        "pattern": r"^KARTEI[_A-Z0-9]*$",
        "columns": {
            "ID": r"^ID$",
            "PATNR": r"^PATNR[_A-Z0-9]*$",
            "DATUM": r"^DATUM[_A-Z0-9]*$",
            "BEMERKUNG": r"^BEMERKUNG[_A-Z0-9]*$",
            "DELKZ": r"^DELKZ$",
        },
    },
    "LEISTUNG": {
        "pattern": r"^LEISTUNG[_A-Z0-9]*$",
        "columns": {
            "ID": r"^ID$",
            "PATIENTID": r"^PATIENTID[_A-Z0-9]*$",
            "DATUM": r"^DATUM[_A-Z0-9]*$",
            "LEISTUNG": r"^LEISTUNG[_A-Z0-9]*$",
            "DELKZ": r"^DELKZ$",
        },
    },
}


class SchemaIntrospector:
    """Discovers database schema through pattern matching on INFORMATION_SCHEMA."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def _get_connection(self) -> pyodbc.Connection:
        return pyodbc.connect(self.connection_string)

    def discover_tables(self) -> dict[str, str]:
        """
        Query all tables in 'ck' schema and match to canonical names.

        Returns:
            dict mapping canonical name -> actual table name
            e.g., {"PATIENT": "PATIENT_X7K", "KARTEI": "KARTEI_QW2", ...}
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'ck' AND TABLE_TYPE = 'BASE TABLE'
        """)

        actual_tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        # Match each actual table to a canonical name
        table_mapping = {}
        for canonical_name, table_def in CANONICAL_TABLES.items():
            pattern = re.compile(table_def["pattern"])
            for actual_name in actual_tables:
                if pattern.match(actual_name):
                    table_mapping[canonical_name] = actual_name
                    break

        return table_mapping

    def discover_columns(self, actual_table_name: str, canonical_table: str) -> dict[str, str]:
        """
        Query all columns for a table and match to canonical column names.

        Args:
            actual_table_name: The actual table name in the database
            canonical_table: The canonical table name (e.g., "KARTEI")

        Returns:
            dict mapping canonical column name -> actual column name
            e.g., {"PATNR": "PATNR_QW2", "DATUM": "DATUM_8MK", ...}
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ck' AND TABLE_NAME = ?
        """, (actual_table_name,))

        actual_columns = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        # Get expected columns for this canonical table
        expected_columns = CANONICAL_TABLES[canonical_table]["columns"]

        # Match each actual column to a canonical name
        column_mapping = {}
        for canonical_col, pattern_str in expected_columns.items():
            pattern = re.compile(pattern_str)
            for actual_col in actual_columns:
                if pattern.match(actual_col):
                    column_mapping[canonical_col] = actual_col
                    break

        return column_mapping

    def introspect(self) -> SchemaMapping:
        """
        Full schema introspection - discovers all tables and their columns.

        Returns:
            SchemaMapping with complete table and column mappings
        """
        # Discover tables
        table_name_mapping = self.discover_tables()
        logger.info(f"Discovered {len(table_name_mapping)} tables")

        # Build table mappings with columns
        tables = {}
        for canonical_table, actual_table in table_name_mapping.items():
            column_mapping = self.discover_columns(actual_table, canonical_table)

            # Convert to ColumnMapping objects
            columns = {
                canonical: ColumnMapping(canonical_name=canonical, actual_name=actual)
                for canonical, actual in column_mapping.items()
            }

            tables[canonical_table] = TableMapping(
                canonical_name=canonical_table,
                actual_name=actual_table,
                columns=columns,
            )

        return SchemaMapping(
            schema="ck",
            suffix="RANDOM",  # No single suffix anymore
            tables=tables,
        )


# Cache for schema mappings per center
_schema_cache: dict[str, SchemaMapping] = {}


def get_schema(center_id: str, connection_string: str) -> SchemaMapping:
    """
    Get schema mapping for a center, using cache if available.

    Args:
        center_id: The center identifier
        connection_string: Database connection string

    Returns:
        SchemaMapping for the center
    """
    if center_id not in _schema_cache:
        logger.info(f"Introspecting schema for {center_id}")
        introspector = SchemaIntrospector(connection_string)
        _schema_cache[center_id] = introspector.introspect()

    return _schema_cache[center_id]


def clear_cache():
    """Clear the schema cache (useful for testing)."""
    _schema_cache.clear()
