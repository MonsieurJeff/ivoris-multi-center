# Changelog

All notable changes to the Ivoris Multi-Center Pipeline are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Async extraction with `asyncio` + `aioodbc`
- Connection pooling for improved performance
- Prometheus metrics endpoint
- Kubernetes deployment manifests

---

## [1.0.0] - 2026-01-13

### Added

#### Core Features
- **Schema Discovery** - Raw introspection of database schemas via `INFORMATION_SCHEMA`
- **Pattern-Based Mapping** - Automatic detection of canonical table/column names from suffixed variants
- **Mapping Generator** - Creates JSON mapping files with `reviewed: false` flag for human verification
- **Parallel Extraction** - `ThreadPoolExecutor`-based concurrent extraction from multiple centers
- **Unified Output** - Canonical `ChartEntry` model regardless of source schema

#### CLI Commands
- `list` - Display all configured centers with mapping status
- `discover-raw` - Show raw database schema for a center
- `generate-mappings` - Create mapping files from discovered schemas
- `show-mapping` - Display a center's schema mapping
- `extract` - Extract chart entries for a date (JSON/CSV output)
- `benchmark` - Performance test across all centers

#### Web UI
- **Explore Page** - Browse centers, view mappings, extract data
- **Metrics Dashboard** - Multi-select benchmark with Chart.js visualization
- **Schema Diff** - Compare discovered mapping vs ground truth
- **Dark Mode** - Toggle between light and dark themes
- **Export** - Download benchmark results as JSON or CSV

#### Infrastructure
- Docker Compose setup for SQL Server 2019
- 30 dental center configurations (Germany, Austria, Switzerland)
- Test database generator with random schema suffixes

#### Documentation
- `README.md` - Project overview and quick start
- `CHALLENGE.md` - Original challenge requirements
- `ACCEPTANCE.md` - Gherkin acceptance criteria
- `docs/METHODOLOGY.md` - How the project was built
- `docs/TECH_SPEC.md` - Technical specifications and scalability
- `docs/SECURITY.md` - Security and GDPR considerations
- `docs/OPERATIONS.md` - Production runbook
- `docs/TESTING.md` - Test strategy and examples
- `docs/presentation/` - Loom video materials

### Performance
- **Target**: <5 seconds for 30 centers
- **Achieved**: ~400ms with 5 workers
- **Per-center average**: ~15ms

### Technical Decisions
- JSON mapping files for human-readable, version-controlled mappings
- `reviewed` flag for production safety checkpoint
- Ground truth separation for discovery validation
- FastAPI + Jinja2 for web UI
- Tailwind CSS for styling
- Chart.js for data visualization

---

## [0.3.0] - 2026-01-13

### Added
- Web UI with FastAPI
- Metrics dashboard with benchmark visualization
- Schema diff comparison page
- Dark mode support
- Export functionality (JSON/CSV)

### Changed
- Moved from 10 to 30 dental centers
- Updated benchmark target from 5s to maintain with more centers

---

## [0.2.0] - 2026-01-13

### Added
- Parallel extraction with `ThreadPoolExecutor`
- Benchmark command for performance testing
- Ground truth files for validation
- Per-center timing in benchmark output

### Changed
- Refactored extraction to use service layer
- Moved mapping files to `data/mappings/`

### Fixed
- Column suffix detection for multi-character suffixes

---

## [0.1.0] - 2026-01-13

### Added
- Initial project structure from OutrePilot sandbox template
- Basic schema discovery via `INFORMATION_SCHEMA`
- Pattern-based mapping generation
- Single-center extraction
- CLI with argparse

### Infrastructure
- Docker Compose for SQL Server
- Test database generator script
- Basic configuration in YAML

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 1.0.0 | 2026-01-13 | Full release: Web UI, 30 centers, documentation |
| 0.3.0 | 2026-01-13 | Web UI, metrics dashboard |
| 0.2.0 | 2026-01-13 | Parallel extraction, benchmarking |
| 0.1.0 | 2026-01-13 | Initial implementation |

---

## Migration Guide

### From 0.x to 1.0.0

No breaking changes. Upgrade by pulling latest code:

```bash
git pull origin main
pip install -r requirements.txt
```

---

## Deprecation Notices

None currently.

---

## Security Fixes

None currently. See `docs/SECURITY.md` for security considerations.

---

## Contributors

- **Jean-Francois Desjardins** - Initial development

---

## Links

- [README](README.md)
- [Challenge Requirements](CHALLENGE.md)
- [Acceptance Criteria](ACCEPTANCE.md)
- [Technical Specification](docs/TECH_SPEC.md)
