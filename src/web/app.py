"""
FastAPI Web Application for Ivoris Multi-Center Pipeline.

Simple UI for exploring dental center databases and viewing metrics.
"""

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..core.config import load_config
from ..core.introspector import list_available_mappings
from ..services.extraction import ExtractionService

logger = logging.getLogger(__name__)

# Directories
WEB_DIR = Path(__file__).parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"
DATA_DIR = Path(__file__).parent.parent.parent / "data"
MAPPINGS_DIR = DATA_DIR / "mappings"

# Create FastAPI app
app = FastAPI(
    title="Ivoris Multi-Center Explorer",
    description="Explore dental center databases and view extraction metrics",
    version="1.0.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Load config once
_config = None


def get_config():
    """Get or load configuration."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


# =============================================================================
# HTML PAGES
# =============================================================================


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Redirect to explore page."""
    return templates.TemplateResponse(
        "explore.html",
        {
            "request": request,
            "page": "explore",
            "title": "Explore Centers",
        },
    )


@app.get("/explore", response_class=HTMLResponse)
async def explore_page(request: Request):
    """Explore dental center databases."""
    return templates.TemplateResponse(
        "explore.html",
        {
            "request": request,
            "page": "explore",
            "title": "Explore Centers",
        },
    )


@app.get("/metrics", response_class=HTMLResponse)
async def metrics_page(request: Request):
    """View extraction metrics."""
    return templates.TemplateResponse(
        "metrics.html",
        {
            "request": request,
            "page": "metrics",
            "title": "Metrics Dashboard",
        },
    )


# =============================================================================
# API ENDPOINTS
# =============================================================================


@app.get("/api/centers")
async def list_centers():
    """List all configured centers with mapping status."""
    config = get_config()
    available_mappings = set(list_available_mappings(MAPPINGS_DIR))

    centers = []
    for center in config.centers:
        centers.append(
            {
                "id": center.id,
                "name": center.name,
                "city": center.city,
                "database": center.database,
                "has_mapping": center.id in available_mappings,
            }
        )

    return {"centers": centers, "total": len(centers)}


@app.get("/api/centers/{center_id}")
async def get_center(center_id: str):
    """Get center details and schema mapping."""
    config = get_config()
    center = config.get_center(center_id)

    if not center:
        raise HTTPException(status_code=404, detail=f"Center not found: {center_id}")

    # Load mapping if available
    mapping = None
    mapping_file = MAPPINGS_DIR / f"{center_id}_mapping.json"
    if mapping_file.exists():
        with open(mapping_file) as f:
            mapping = json.load(f)

    return {
        "id": center.id,
        "name": center.name,
        "city": center.city,
        "database": center.database,
        "mapping": mapping,
    }


@app.get("/api/extract")
async def extract_data(
    date_str: str = Query(default="2022-01-18", alias="date"),
    center_ids: Optional[str] = Query(default=None, alias="centers"),
):
    """Extract chart entries from centers."""
    config = get_config()

    # Check for mappings
    available = list_available_mappings(MAPPINGS_DIR)
    if not available:
        raise HTTPException(
            status_code=400,
            detail="No mapping files found. Run 'generate-mappings' first.",
        )

    # Parse date
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date: {date_str}")

    # Parse center IDs
    selected_centers = None
    if center_ids:
        selected_centers = [c.strip() for c in center_ids.split(",")]
        # Validate centers exist
        for cid in selected_centers:
            if not config.get_center(cid):
                raise HTTPException(status_code=404, detail=f"Unknown center: {cid}")

    # Run extraction
    service = ExtractionService(config)
    result = service.extract_all(
        target_date=target_date,
        center_ids=selected_centers,
        max_workers=5,
    )

    # Format results
    centers_data = []
    for r in result.results:
        centers_data.append(
            {
                "center_id": r.center_id,
                "center_name": r.center_name,
                "entries_count": len(r.entries),
                "duration_ms": round(r.duration_ms, 1),
                "success": r.error is None,
                "error": r.error,
                "entries": [
                    {
                        "center_id": e.center_id,
                        "date": e.date.isoformat() if e.date else None,
                        "patient_id": e.patient_id,
                        "insurance_type": e.insurance_type,
                        "entry": e.entry,
                    }
                    for e in r.entries
                ],
            }
        )

    return {
        "date": result.target_date.isoformat(),
        "total_entries": result.total_entries,
        "total_duration_ms": round(result.total_duration_ms, 1),
        "successful_centers": result.successful_centers,
        "total_centers": len(result.results),
        "centers": centers_data,
    }


@app.get("/api/benchmark")
async def run_benchmark():
    """Run performance benchmark."""
    config = get_config()

    # Check for mappings
    available = list_available_mappings(MAPPINGS_DIR)
    if not available:
        raise HTTPException(
            status_code=400,
            detail="No mapping files found. Run 'generate-mappings' first.",
        )

    # Run extraction on test date
    service = ExtractionService(config)
    result = service.extract_all(
        target_date=date(2022, 1, 18),
        max_workers=5,
    )

    # Per-center timing
    timing = []
    for r in sorted(result.results, key=lambda x: x.duration_ms, reverse=True):
        timing.append(
            {
                "center_id": r.center_id,
                "center_name": r.center_name,
                "duration_ms": round(r.duration_ms, 1),
                "entries_count": len(r.entries),
                "success": r.error is None,
            }
        )

    target_ms = 5000
    passed = result.total_duration_ms < target_ms

    return {
        "total_centers": len(result.results),
        "total_entries": result.total_entries,
        "total_duration_ms": round(result.total_duration_ms, 1),
        "target_ms": target_ms,
        "passed": passed,
        "timing": timing,
    }


# =============================================================================
# STARTUP
# =============================================================================


def create_app():
    """Create and configure the FastAPI application."""
    # Ensure directories exist
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.web.app:app", host="0.0.0.0", port=8000, reload=True)
