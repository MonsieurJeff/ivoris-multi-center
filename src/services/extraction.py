"""
Multi-Center Extraction Service.

Extracts data from multiple dental centers in parallel.
"""

import csv
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..adapters.center_adapter import AdapterFactory, CenterAdapter
from ..core.config import AppConfig, CenterConfig
from ..models.chart_entry import ChartEntry

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result from extracting a single center."""
    
    center_id: str
    center_name: str
    entries: list[ChartEntry]
    duration_ms: float
    error: str | None = None


@dataclass
class MultiExtractionResult:
    """Result from extracting all centers."""
    
    target_date: date
    results: list[ExtractionResult]
    total_entries: int
    total_duration_ms: float

    @property
    def all_entries(self) -> list[ChartEntry]:
        """Get all entries from all centers."""
        entries = []
        for result in self.results:
            entries.extend(result.entries)
        return entries

    @property
    def successful_centers(self) -> int:
        """Count of centers that extracted successfully."""
        return sum(1 for r in self.results if r.error is None)


class ExtractionService:
    """Service for extracting data from dental centers."""

    def __init__(self, config: AppConfig, output_dir: Path | None = None):
        self.config = config
        self.output_dir = output_dir or Path("data/output")
        self.factory = AdapterFactory(config.database)

    def extract_center(self, center: CenterConfig, target_date: date) -> ExtractionResult:
        """Extract data from a single center."""
        start = time.perf_counter()
        
        try:
            adapter = self.factory.create(center)
            with adapter:
                entries = adapter.extract_chart_entries(target_date)
            
            duration = (time.perf_counter() - start) * 1000
            return ExtractionResult(
                center_id=center.id,
                center_name=center.name,
                entries=entries,
                duration_ms=duration,
            )
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            logger.error(f"Error extracting {center.name}: {e}")
            return ExtractionResult(
                center_id=center.id,
                center_name=center.name,
                entries=[],
                duration_ms=duration,
                error=str(e),
            )

    def extract_all(
        self,
        target_date: date,
        center_ids: list[str] | None = None,
        max_workers: int = 5,
    ) -> MultiExtractionResult:
        """
        Extract data from multiple centers in parallel.
        
        Args:
            target_date: Date to extract
            center_ids: Specific centers to extract (None = all)
            max_workers: Max parallel connections
        """
        start = time.perf_counter()

        # Determine which centers to extract
        if center_ids:
            centers = [c for c in self.config.centers if c.id in center_ids]
        else:
            centers = self.config.centers

        logger.info(f"Extracting from {len(centers)} centers for {target_date}")

        # Extract in parallel
        results: list[ExtractionResult] = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.extract_center, center, target_date): center
                for center in centers
            }

            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                
                status = "✓" if result.error is None else "✗"
                logger.info(
                    f"  {status} {result.center_name}: "
                    f"{len(result.entries)} entries in {result.duration_ms:.0f}ms"
                )

        # Sort by center_id for consistent output
        results.sort(key=lambda r: r.center_id)

        total_duration = (time.perf_counter() - start) * 1000
        total_entries = sum(len(r.entries) for r in results)

        return MultiExtractionResult(
            target_date=target_date,
            results=results,
            total_entries=total_entries,
            total_duration_ms=total_duration,
        )

    def export_json(self, result: MultiExtractionResult) -> Path:
        """Export extraction result to JSON."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"ivoris_multi_center_{result.target_date.isoformat()}.json"
        path = self.output_dir / filename

        data = {
            "target_date": result.target_date.isoformat(),
            "total_entries": result.total_entries,
            "total_duration_ms": round(result.total_duration_ms, 2),
            "centers": [
                {
                    "center_id": r.center_id,
                    "center_name": r.center_name,
                    "entry_count": len(r.entries),
                    "duration_ms": round(r.duration_ms, 2),
                    "error": r.error,
                }
                for r in result.results
            ],
            "entries": [e.to_dict() for e in result.all_entries],
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported to {path}")
        return path

    def export_csv(self, result: MultiExtractionResult) -> Path:
        """Export extraction result to CSV."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"ivoris_multi_center_{result.target_date.isoformat()}.csv"
        path = self.output_dir / filename

        entries = result.all_entries
        if not entries:
            path.write_text("")
            return path

        fieldnames = list(entries[0].to_csv_row().keys())
        
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for entry in entries:
                writer.writerow(entry.to_csv_row())

        logger.info(f"Exported to {path}")
        return path
