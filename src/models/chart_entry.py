"""
Canonical ChartEntry model.

This is the unified data model that all centers map to,
regardless of their underlying schema names.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class ChartEntry:
    """Canonical chart entry from any dental center."""
    
    center_id: str
    center_name: str
    date: date
    patient_id: int
    insurance_status: str
    insurance_name: str | None
    chart_entry: str
    service_codes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "center_id": self.center_id,
            "center_name": self.center_name,
            "date": self.date.isoformat(),
            "patient_id": self.patient_id,
            "insurance_status": self.insurance_status,
            "insurance_name": self.insurance_name,
            "chart_entry": self.chart_entry,
            "service_codes": self.service_codes,
        }

    def to_csv_row(self) -> dict[str, str]:
        """Convert to flat dictionary for CSV output."""
        return {
            "center_id": self.center_id,
            "center_name": self.center_name,
            "date": self.date.isoformat(),
            "patient_id": str(self.patient_id),
            "insurance_status": self.insurance_status,
            "insurance_name": self.insurance_name or "",
            "chart_entry": self.chart_entry,
            "service_codes": ",".join(self.service_codes),
        }
