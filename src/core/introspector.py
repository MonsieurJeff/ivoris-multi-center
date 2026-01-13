"""
Schema Introspector - Loads schema mappings for extraction.

This module loads pre-computed schema mappings (created by the agentic
mapping process) and provides them to the extraction service.

The mappings are created through:
1. Raw discovery (discovery.py) - finds tables/columns
2. Agentic mapping (agentic_mapper.py) - identifies canonical names
3. Saved to data/mappings/<center_id>_mapping.json
"""

import json
import logging
from pathlib import Path

from .schema_mapping import ColumnMapping, SchemaMapping, TableMapping

logger = logging.getLogger(__name__)

# Default mappings directory
MAPPINGS_DIR = Path(__file__).parent.parent.parent / "data" / "mappings"


def load_mapping_file(center_id: str, mappings_dir: Path | None = None) -> dict:
    """Load a mapping file for a center."""
    if mappings_dir is None:
        mappings_dir = MAPPINGS_DIR

    filepath = mappings_dir / f"{center_id}_mapping.json"

    if not filepath.exists():
        raise FileNotFoundError(
            f"No mapping file for {center_id}. "
            f"Run 'python -m src.cli map-schema' first."
        )

    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def mapping_to_schema(mapping_data: dict) -> SchemaMapping:
    """Convert mapping file data to SchemaMapping object."""
    tables = {}

    for canonical_table, table_data in mapping_data.get("tables", {}).items():
        columns = {}

        for canonical_col, col_data in table_data.get("columns", {}).items():
            columns[canonical_col] = ColumnMapping(
                canonical_name=canonical_col,
                actual_name=col_data["actual_name"],
            )

        tables[canonical_table] = TableMapping(
            canonical_name=canonical_table,
            actual_name=table_data["actual_name"],
            columns=columns,
        )

    return SchemaMapping(
        schema=mapping_data.get("schema", "ck"),
        suffix="AGENTIC",  # Indicates mapping came from agentic process
        tables=tables,
    )


# Cache for schema mappings per center
_schema_cache: dict[str, SchemaMapping] = {}


def get_schema(center_id: str, connection_string: str = None) -> SchemaMapping:
    """
    Get schema mapping for a center.

    Loads from pre-computed mapping file (created by agentic mapper).
    Connection string is ignored - kept for API compatibility.

    Args:
        center_id: The center identifier
        connection_string: Ignored (kept for compatibility)

    Returns:
        SchemaMapping for the center
    """
    if center_id not in _schema_cache:
        logger.info(f"Loading mapping for {center_id}")
        mapping_data = load_mapping_file(center_id)
        _schema_cache[center_id] = mapping_to_schema(mapping_data)
        logger.info(f"Loaded {len(_schema_cache[center_id].tables)} tables")

    return _schema_cache[center_id]


def clear_cache():
    """Clear the schema cache."""
    _schema_cache.clear()


def list_available_mappings(mappings_dir: Path | None = None) -> list[str]:
    """List all available mapping files."""
    if mappings_dir is None:
        mappings_dir = MAPPINGS_DIR

    if not mappings_dir.exists():
        return []

    return [
        f.stem.replace("_mapping", "")
        for f in mappings_dir.glob("*_mapping.json")
    ]
