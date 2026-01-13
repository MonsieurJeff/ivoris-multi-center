"""
Raw Schema Discovery - No interpretation, just facts.

This module queries the database and returns raw table/column information
without any pattern matching or interpretation. The interpretation is done
by the agentic mapping process.
"""

import logging
from dataclasses import dataclass

import pyodbc

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredColumn:
    """A column found in the database."""
    name: str
    data_type: str
    is_nullable: bool
    ordinal_position: int


@dataclass
class DiscoveredTable:
    """A table found in the database."""
    schema: str
    name: str
    columns: list[DiscoveredColumn]


@dataclass
class DiscoveredSchema:
    """Complete schema discovery result."""
    database: str
    tables: list[DiscoveredTable]


class SchemaDiscovery:
    """Discovers database schema without interpretation."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def _get_connection(self) -> pyodbc.Connection:
        return pyodbc.connect(self.connection_string)

    def discover(self, schema_filter: str = "ck") -> DiscoveredSchema:
        """
        Discover all tables and columns in a schema.

        Returns raw discovery - no interpretation of what things mean.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get database name
        cursor.execute("SELECT DB_NAME()")
        database = cursor.fetchone()[0]

        # Get all tables in schema
        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = ? AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """, (schema_filter,))

        table_names = [row[0] for row in cursor.fetchall()]

        # Get columns for each table
        tables = []
        for table_name in table_names:
            cursor.execute("""
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    ORDINAL_POSITION
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """, (schema_filter, table_name))

            columns = [
                DiscoveredColumn(
                    name=row[0],
                    data_type=row[1],
                    is_nullable=(row[2] == "YES"),
                    ordinal_position=row[3],
                )
                for row in cursor.fetchall()
            ]

            tables.append(DiscoveredTable(
                schema=schema_filter,
                name=table_name,
                columns=columns,
            ))

        cursor.close()
        conn.close()

        return DiscoveredSchema(database=database, tables=tables)

    def to_text(self, discovered: DiscoveredSchema) -> str:
        """Convert discovery to human-readable text for agentic processing."""
        lines = [
            f"Database: {discovered.database}",
            f"Tables found: {len(discovered.tables)}",
            "",
        ]

        for table in discovered.tables:
            lines.append(f"TABLE: {table.schema}.{table.name}")
            lines.append("  Columns:")
            for col in table.columns:
                nullable = "NULL" if col.is_nullable else "NOT NULL"
                lines.append(f"    - {col.name} ({col.data_type}, {nullable})")
            lines.append("")

        return "\n".join(lines)


def discover_schema(connection_string: str, schema_filter: str = "ck") -> DiscoveredSchema:
    """Convenience function to discover schema."""
    discovery = SchemaDiscovery(connection_string)
    return discovery.discover(schema_filter)
