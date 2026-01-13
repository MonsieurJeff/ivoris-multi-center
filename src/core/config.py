"""
Configuration loader.

Loads center configuration from YAML file.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


@dataclass
class CenterConfig:
    """Configuration for a single dental center."""
    
    id: str
    name: str
    suffix: str
    database: str
    city: str


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    
    host: str
    port: int
    user: str
    password: str
    driver: str

    def connection_string(self, database: str) -> str:
        """Build ODBC connection string for a specific database."""
        return (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.host},{self.port};"
            f"DATABASE={database};"
            f"UID={self.user};"
            f"PWD={self.password};"
            f"TrustServerCertificate=yes;"
        )


@dataclass 
class AppConfig:
    """Application configuration."""
    
    database: DatabaseConfig
    centers: list[CenterConfig]

    def get_center(self, center_id: str) -> CenterConfig | None:
        """Get center by ID."""
        for center in self.centers:
            if center.id == center_id:
                return center
        return None

    def get_center_ids(self) -> list[str]:
        """Get all center IDs."""
        return [c.id for c in self.centers]


def load_config(config_path: Path | None = None) -> AppConfig:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "centers.yml"

    logger.debug(f"Loading config from {config_path}")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    db_data = data["database"]
    database = DatabaseConfig(
        host=db_data["host"],
        port=db_data["port"],
        user=db_data["user"],
        password=db_data["password"],
        driver=db_data["driver"],
    )

    centers = [
        CenterConfig(
            id=c["id"],
            name=c["name"],
            suffix=c["suffix"],
            database=c["database"],
            city=c["city"],
        )
        for c in data["centers"]
    ]

    return AppConfig(database=database, centers=centers)
