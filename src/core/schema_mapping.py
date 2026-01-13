"""
Schema mapping for a dental center.

Maps canonical table/column names to actual database names.
"""

from dataclasses import dataclass, field


@dataclass
class TableMapping:
    """Mapping for a single table."""
    
    canonical_name: str
    actual_name: str
    columns: dict[str, str] = field(default_factory=dict)

    def get_column(self, canonical: str) -> str:
        """Get actual column name from canonical name."""
        return self.columns.get(canonical, canonical)


@dataclass
class SchemaMapping:
    """Complete schema mapping for a dental center."""
    
    center_id: str
    suffix: str
    tables: dict[str, TableMapping] = field(default_factory=dict)

    def get_table(self, canonical: str) -> str:
        """Get actual table name from canonical name."""
        if canonical in self.tables:
            return self.tables[canonical].actual_name
        return canonical

    def get_column(self, table: str, column: str) -> str:
        """Get actual column name from canonical table and column."""
        if table in self.tables:
            return self.tables[table].get_column(column)
        return column

    def build_select(self, table: str, columns: list[str], alias: str = "") -> str:
        """Build SELECT clause with actual column names."""
        actual_table = self.get_table(table)
        prefix = f"{alias}." if alias else ""
        
        parts = []
        for col in columns:
            actual_col = self.get_column(table, col)
            if actual_col != col:
                parts.append(f"{prefix}{actual_col} as {col}")
            else:
                parts.append(f"{prefix}{actual_col}")
        
        return ", ".join(parts)

    def build_from(self, table: str, alias: str = "") -> str:
        """Build FROM clause with actual table name."""
        actual = self.get_table(table)
        if alias:
            return f"ck.{actual} {alias}"
        return f"ck.{actual}"

    def build_join(self, table: str, alias: str, on_left: str, on_right: str, 
                   left_table: str, left_alias: str) -> str:
        """Build JOIN clause with actual names."""
        actual_table = self.get_table(table)
        actual_left_col = self.get_column(left_table, on_left)
        actual_right_col = self.get_column(table, on_right)
        
        return (
            f"LEFT JOIN ck.{actual_table} {alias} "
            f"ON {left_alias}.{actual_left_col} = {alias}.{actual_right_col}"
        )
