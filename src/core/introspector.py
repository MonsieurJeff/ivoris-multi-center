"""
Schema Introspector.

Auto-discovers table and column names from the database
by querying INFORMATION_SCHEMA and pattern matching.
"""

import logging
import re
from functools import lru_cache

import pyodbc

from .schema_mapping import SchemaMapping, TableMapping

logger = logging.getLogger(__name__)

# Canonical table names we're looking for
CANONICAL_TABLES = {
    "KARTEI": ["KARTEI"],
    "PATIENT": ["PATIENT"],
    "PATKASSE": ["PATKASSE"],
    "KASSEN": ["KASSEN"],
    "LEISTUNG": ["LEISTUNG"],
}

# Canonical column names per table
CANONICAL_COLUMNS = {
    "KARTEI": ["ID", "PATNR", "DATUM", "BEMERKUNG", "DELKZ"],
    "PATIENT": ["ID", "P_NAME", "P_VORNAME"],
    "PATKASSE": ["PATNR", "KASSENID"],
    "KASSEN": ["ID", "NAME", "ART"],
    "LEISTUNG": ["PATIENTID", "DATUM", "LEISTUNG", "DELKZ"],
}


class SchemaIntrospector:
    """Discovers schema by introspecting the database."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._connection: pyodbc.Connection | None = None

    def connect(self) -> None:
        """Establish database connection."""
        if self._connection is None:
            self._connection = pyodbc.connect(self.connection_string)

    def disconnect(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def _query(self, sql: str) -> list[dict]:
        """Execute query and return results as dicts."""
        self.connect()
        cursor = self._connection.cursor()
        cursor.execute(sql)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        return [dict(zip(columns, row)) for row in rows]

    def discover_tables(self) -> dict[str, str]:
        """
        Discover actual table names by pattern matching.
        
        Returns: {canonical_name: actual_name}
        """
        sql = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'ck'
            ORDER BY TABLE_NAME
        """
        rows = self._query(sql)
        table_names = [r["TABLE_NAME"] for r in rows]

        discovered = {}
        for canonical, patterns in CANONICAL_TABLES.items():
            for table in table_names:
                base = self._extract_base_name(table)
                if base in patterns:
                    discovered[canonical] = table
                    logger.debug(f"Discovered: {canonical} -> {table}")
                    break

        return discovered

    def discover_columns(self, table_name: str) -> dict[str, str]:
        """
        Discover actual column names for a table.
        
        Returns: {canonical_name: actual_name}
        """
        sql = f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'ck' AND TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
        """
        rows = self._query(sql)
        column_names = [r["COLUMN_NAME"] for r in rows]

        discovered = {}
        for col in column_names:
            base = self._extract_base_name(col)
            discovered[base] = col

        return discovered

    def _extract_base_name(self, name: str) -> str:
        """
        Extract base name by removing suffix.
        
        KARTEI_M1 -> KARTEI
        PATNR_M1 -> PATNR
        """
        # Pattern: ends with _XX where XX is 2 alphanumeric chars
        match = re.match(r"^(.+)_[A-Z0-9]{2}$", name)
        if match:
            return match.group(1)
        return name

    def _detect_suffix(self, tables: dict[str, str]) -> str:
        """Detect the suffix used in this database."""
        for actual in tables.values():
            match = re.search(r"_([A-Z0-9]{2})$", actual)
            if match:
                return match.group(1)
        return ""

    def introspect(self, center_id: str) -> SchemaMapping:
        """
        Fully introspect the database and build a SchemaMapping.
        """
        logger.info(f"Introspecting schema for {center_id}")

        # Discover tables
        tables = self.discover_tables()
        suffix = self._detect_suffix(tables)

        logger.info(f"Detected suffix: {suffix}")
        logger.info(f"Discovered {len(tables)} tables")

        # Build mapping
        mapping = SchemaMapping(center_id=center_id, suffix=suffix)

        for canonical, actual in tables.items():
            columns = self.discover_columns(actual)
            
            table_mapping = TableMapping(
                canonical_name=canonical,
                actual_name=actual,
                columns=columns,
            )
            mapping.tables[canonical] = table_mapping

            logger.debug(f"  {canonical}: {len(columns)} columns")

        return mapping


# Cache for discovered schemas
_schema_cache: dict[str, SchemaMapping] = {}


def get_schema(center_id: str, connection_string: str, use_cache: bool = True) -> SchemaMapping:
    """
    Get schema mapping for a center, with caching.
    """
    if use_cache and center_id in _schema_cache:
        logger.debug(f"Using cached schema for {center_id}")
        return _schema_cache[center_id]

    introspector = SchemaIntrospector(connection_string)
    try:
        schema = introspector.introspect(center_id)
        _schema_cache[center_id] = schema
        return schema
    finally:
        introspector.disconnect()


def clear_cache() -> None:
    """Clear the schema cache."""
    _schema_cache.clear()
