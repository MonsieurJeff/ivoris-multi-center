"""
Center Adapter.

Extracts data from a specific dental center using discovered schema.
"""

import logging
from datetime import date

import pyodbc

from ..core.config import CenterConfig, DatabaseConfig
from ..core.introspector import get_schema
from ..core.schema_mapping import SchemaMapping
from ..models.chart_entry import ChartEntry

logger = logging.getLogger(__name__)


class CenterAdapter:
    """Adapter for extracting data from a single dental center."""

    def __init__(
        self,
        center: CenterConfig,
        db_config: DatabaseConfig,
        schema: SchemaMapping,
    ):
        self.center = center
        self.db_config = db_config
        self.schema = schema
        self._connection: pyodbc.Connection | None = None

    @property
    def connection_string(self) -> str:
        return self.db_config.connection_string(self.center.database)

    def connect(self) -> None:
        """Establish database connection."""
        if self._connection is None:
            logger.debug(f"Connecting to {self.center.database}")
            self._connection = pyodbc.connect(self.connection_string)

    def disconnect(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def _query(self, sql: str, params: tuple = ()) -> list[dict]:
        """Execute query and return results."""
        self.connect()
        cursor = self._connection.cursor()
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        return [dict(zip(columns, row)) for row in rows]

    def extract_chart_entries(self, target_date: date) -> list[ChartEntry]:
        """Extract chart entries for a specific date."""
        ivoris_date = int(target_date.strftime("%Y%m%d"))

        # Build query using schema mapping
        s = self.schema

        # Get actual column names
        k_patnr = s.get_column("KARTEI", "PATNR")
        k_datum = s.get_column("KARTEI", "DATUM")
        k_bemerkung = s.get_column("KARTEI", "BEMERKUNG")
        k_delkz = s.get_column("KARTEI", "DELKZ")
        
        pk_patnr = s.get_column("PATKASSE", "PATNR")
        pk_kassenid = s.get_column("PATKASSE", "KASSENID")
        
        ka_id = s.get_column("KASSEN", "ID")
        ka_name = s.get_column("KASSEN", "NAME")
        ka_art = s.get_column("KASSEN", "ART")

        # Get actual table names
        t_kartei = s.get_table("KARTEI")
        t_patient = s.get_table("PATIENT")
        t_patkasse = s.get_table("PATKASSE")
        t_kassen = s.get_table("KASSEN")

        query = f"""
            SELECT
                k.ID as KARTEI_ID,
                k.{k_patnr} as PATNR,
                k.{k_datum} as DATUM,
                k.{k_bemerkung} as BEMERKUNG,
                ka.{ka_name} as KASSE_NAME,
                ka.{ka_art} as KASSE_ART
            FROM ck.{t_kartei} k
            LEFT JOIN ck.{t_patient} p ON k.{k_patnr} = p.ID
            LEFT JOIN ck.{t_patkasse} pk ON k.{k_patnr} = pk.{pk_patnr}
            LEFT JOIN ck.{t_kassen} ka ON pk.{pk_kassenid} = ka.{ka_id}
            WHERE k.{k_datum} = ?
            AND (k.{k_delkz} = 0 OR k.{k_delkz} IS NULL)
            ORDER BY k.{k_patnr}, k.ID
        """

        logger.debug(f"Extracting from {self.center.name} for {target_date}")
        rows = self._query(query, (ivoris_date,))
        logger.info(f"{self.center.name}: {len(rows)} entries")

        if not rows:
            return []

        # Get service codes
        services = self._get_services(target_date)

        # Build ChartEntry objects
        entries = []
        for row in rows:
            patient_id = row.get("PATNR")
            entry = ChartEntry(
                center_id=self.center.id,
                center_name=self.center.name,
                date=target_date,
                patient_id=patient_id,
                insurance_status=self._map_insurance(row.get("KASSE_ART")),
                insurance_name=row.get("KASSE_NAME"),
                chart_entry=row.get("BEMERKUNG") or "",
                service_codes=services.get(patient_id, []),
            )
            entries.append(entry)

        return entries

    def _get_services(self, target_date: date) -> dict[int, list[str]]:
        """Get service codes grouped by patient."""
        ivoris_date = int(target_date.strftime("%Y%m%d"))
        s = self.schema

        t_leistung = s.get_table("LEISTUNG")
        l_patientid = s.get_column("LEISTUNG", "PATIENTID")
        l_datum = s.get_column("LEISTUNG", "DATUM")
        l_leistung = s.get_column("LEISTUNG", "LEISTUNG")
        l_delkz = s.get_column("LEISTUNG", "DELKZ")

        query = f"""
            SELECT {l_patientid} as PATIENTID, {l_leistung} as LEISTUNG
            FROM ck.{t_leistung}
            WHERE {l_datum} = ?
            AND ({l_delkz} = 0 OR {l_delkz} IS NULL)
        """

        rows = self._query(query, (ivoris_date,))

        services: dict[int, list[str]] = {}
        for row in rows:
            pid = row.get("PATIENTID")
            code = row.get("LEISTUNG")
            if pid and code:
                if pid not in services:
                    services[pid] = []
                if code not in services[pid]:
                    services[pid].append(code)

        return services

    def _map_insurance(self, kasse_art: str | None) -> str:
        """Map KASSEN.ART to insurance status."""
        if not kasse_art:
            return "Selbstzahler"
        if str(kasse_art).upper() == "P":
            return "PKV"
        return "GKV"

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False


class AdapterFactory:
    """Factory for creating center adapters."""

    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config

    def create(self, center: CenterConfig) -> CenterAdapter:
        """Create an adapter for a center with auto-discovered schema."""
        connection_string = self.db_config.connection_string(center.database)
        schema = get_schema(center.id, connection_string)
        
        return CenterAdapter(
            center=center,
            db_config=self.db_config,
            schema=schema,
        )
