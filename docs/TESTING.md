# Testing Strategy

**Test Plan for Ivoris Multi-Center Pipeline**

This document outlines the testing approach, test types, and how to write and run tests for the extraction pipeline.

---

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Pyramid](#test-pyramid)
3. [Test Structure](#test-structure)
4. [Unit Tests](#unit-tests)
5. [Integration Tests](#integration-tests)
6. [End-to-End Tests](#end-to-end-tests)
7. [Performance Tests](#performance-tests)
8. [Running Tests](#running-tests)
9. [Writing New Tests](#writing-new-tests)
10. [CI/CD Integration](#cicd-integration)

---

## Testing Philosophy

### Core Principles

| Principle | Meaning |
|-----------|---------|
| **Test behavior, not implementation** | Test what functions DO, not how they do it |
| **Fast feedback** | Unit tests run in <10s total |
| **Reliable** | No flaky tests; fix or delete them |
| **Readable** | Tests document expected behavior |
| **Independent** | Tests don't depend on each other |

### What We Test

| Layer | What to Test | What NOT to Test |
|-------|--------------|------------------|
| Core | Business logic, algorithms | Framework code |
| Adapters | Query generation | Database engine |
| Services | Orchestration, error handling | Third-party libraries |
| CLI | Argument parsing, output format | argparse library |
| Web | API contracts, responses | FastAPI framework |

---

## Test Pyramid

```
                    ┌───────────┐
                   │   E2E     │  Few, slow, high confidence
                  │   Tests    │  (5-10 tests)
                 └─────────────┘
                ┌───────────────────┐
               │   Integration      │  Some, medium speed
              │      Tests          │  (20-50 tests)
             └─────────────────────┘
            ┌───────────────────────────┐
           │         Unit Tests         │  Many, fast, focused
          │                             │  (100+ tests)
         └─────────────────────────────┘
```

### Target Distribution

| Test Type | Count | Runtime | Coverage |
|-----------|-------|---------|----------|
| Unit | 100+ | <10s | Core logic |
| Integration | 20-50 | <60s | Component interaction |
| E2E | 5-10 | <5m | Critical paths |
| Performance | 3-5 | <2m | Benchmarks |

---

## Test Structure

### Directory Layout

```
tests/
├── __tests__/
│   ├── unit/
│   │   ├── test_discovery.py
│   │   ├── test_schema_mapping.py
│   │   ├── test_mapping_generator.py
│   │   ├── test_center_adapter.py
│   │   └── test_chart_entry.py
│   │
│   ├── integration/
│   │   ├── test_extraction_service.py
│   │   ├── test_database_connection.py
│   │   └── test_cli_commands.py
│   │
│   ├── e2e/
│   │   ├── test_full_extraction.py
│   │   └── test_web_ui.py
│   │
│   └── performance/
│       └── test_benchmark.py
│
├── fixtures/
│   ├── sample_schema.json
│   ├── sample_mapping.json
│   └── sample_entries.json
│
├── conftest.py              # Shared fixtures
└── pytest.ini               # Pytest configuration
```

### Naming Conventions

```python
# File: test_<module>.py
# Class: Test<Component>
# Method: test_<behavior>_<scenario>

# Examples:
test_discovery.py
class TestSchemaDiscovery:
    def test_discover_finds_all_tables(self):
    def test_discover_handles_empty_schema(self):
    def test_discover_filters_by_schema_name(self):
```

---

## Unit Tests

### What to Unit Test

| Component | Test Cases |
|-----------|------------|
| `discovery.py` | Table discovery, column discovery, empty schema |
| `schema_mapping.py` | Mapping creation, column lookup, table lookup |
| `mapping_generator.py` | Pattern matching, suffix extraction, mapping output |
| `center_adapter.py` | SQL generation, query building |
| `chart_entry.py` | Model creation, serialization |

### Example: Testing Discovery

```python
# tests/__tests__/unit/test_discovery.py

import pytest
from unittest.mock import Mock, patch
from src.core.discovery import SchemaDiscovery, DiscoveredTable, DiscoveredColumn


class TestSchemaDiscovery:
    """Tests for raw schema discovery."""

    def test_discover_finds_all_tables(self):
        """Discovery should return all tables in the schema."""
        # Arrange
        mock_cursor = Mock()
        mock_cursor.fetchall.side_effect = [
            [("KARTEI_MN",), ("PATIENT_XY",)],  # Tables
            [("ID", "int", "NO", 1), ("PATNR_AB", "int", "YES", 2)],  # KARTEI columns
            [("ID", "int", "NO", 1), ("P_NAME_CD", "nvarchar", "YES", 2)],  # PATIENT columns
        ]

        with patch.object(SchemaDiscovery, '_get_connection') as mock_conn:
            mock_conn.return_value.cursor.return_value = mock_cursor

            # Act
            discovery = SchemaDiscovery("fake_connection_string")
            result = discovery.discover(schema_filter="ck")

            # Assert
            assert len(result.tables) == 2
            assert result.tables[0].name == "KARTEI_MN"
            assert result.tables[1].name == "PATIENT_XY"

    def test_discover_handles_empty_schema(self):
        """Discovery should handle schemas with no tables."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []

        with patch.object(SchemaDiscovery, '_get_connection') as mock_conn:
            mock_conn.return_value.cursor.return_value = mock_cursor

            discovery = SchemaDiscovery("fake_connection_string")
            result = discovery.discover(schema_filter="empty")

            assert len(result.tables) == 0

    def test_discover_captures_column_types(self):
        """Discovery should capture column data types correctly."""
        mock_cursor = Mock()
        mock_cursor.fetchall.side_effect = [
            [("TEST_TABLE",)],
            [
                ("ID", "int", "NO", 1),
                ("NAME", "nvarchar", "YES", 2),
                ("DATE", "datetime", "YES", 3),
            ],
        ]

        with patch.object(SchemaDiscovery, '_get_connection') as mock_conn:
            mock_conn.return_value.cursor.return_value = mock_cursor

            discovery = SchemaDiscovery("fake_connection_string")
            result = discovery.discover()

            columns = result.tables[0].columns
            assert columns[0].data_type == "int"
            assert columns[1].data_type == "nvarchar"
            assert columns[2].data_type == "datetime"
```

### Example: Testing Mapping Generator

```python
# tests/__tests__/unit/test_mapping_generator.py

import pytest
from src.services.mapping_generator import extract_base_name, generate_mapping


class TestExtractBaseName:
    """Tests for pattern matching suffix extraction."""

    @pytest.mark.parametrize("input,expected", [
        ("KARTEI_MN", "KARTEI"),
        ("KARTEI_8Y", "KARTEI"),
        ("KARTEI_XQ4", "KARTEI"),
        ("PATIENT_A1", "PATIENT"),
        ("PATNR_NAN6", "PATNR"),
        ("DATUM_3A4", "DATUM"),
        ("ID", "ID"),           # No suffix
        ("DELKZ", "DELKZ"),     # No suffix
    ])
    def test_extract_base_name(self, input, expected):
        """Should extract canonical name from suffixed name."""
        assert extract_base_name(input) == expected

    def test_extract_base_name_unknown_returns_none(self):
        """Should return None for unrecognized patterns."""
        assert extract_base_name("RANDOM_TABLE") is None
        assert extract_base_name("XYZ_123") is None


class TestGenerateMapping:
    """Tests for mapping generation from discovered schema."""

    def test_generates_correct_table_mappings(self):
        """Should map discovered tables to canonical names."""
        discovered = DiscoveredSchema(
            database="TestDB",
            tables=[
                DiscoveredTable(schema="ck", name="KARTEI_MN", columns=[]),
                DiscoveredTable(schema="ck", name="PATIENT_XY", columns=[]),
            ]
        )

        mapping = generate_mapping(discovered)

        assert "KARTEI" in mapping["tables"]
        assert mapping["tables"]["KARTEI"]["actual_name"] == "KARTEI_MN"
        assert "PATIENT" in mapping["tables"]
        assert mapping["tables"]["PATIENT"]["actual_name"] == "PATIENT_XY"

    def test_includes_reviewed_flag(self):
        """Generated mappings should have reviewed: false."""
        discovered = DiscoveredSchema(database="TestDB", tables=[])
        mapping = generate_mapping(discovered)

        assert mapping["reviewed"] is False
```

### Example: Testing Center Adapter

```python
# tests/__tests__/unit/test_center_adapter.py

import pytest
from src.adapters.center_adapter import CenterAdapter
from src.core.schema_mapping import SchemaMapping, TableMapping


class TestCenterAdapter:
    """Tests for SQL query generation."""

    @pytest.fixture
    def sample_mapping(self):
        """Create a sample mapping for testing."""
        return SchemaMapping(
            center_id="center_01",
            database="DentalDB_01",
            tables={
                "KARTEI": TableMapping(
                    actual_name="KARTEI_MN",
                    columns={
                        "PATNR": "PATNR_AB",
                        "DATUM": "DATUM_CD",
                        "BEMERKUNG": "BEMERKUNG_EF",
                    }
                ),
                "PATIENT": TableMapping(
                    actual_name="PATIENT_XY",
                    columns={
                        "ID": "ID",
                        "P_NAME": "P_NAME_GH",
                    }
                ),
            }
        )

    def test_builds_query_with_correct_table_names(self, sample_mapping):
        """Generated SQL should use actual table names."""
        adapter = CenterAdapter(center=Mock(), mapping=sample_mapping)

        sql = adapter._build_chart_query(date=20220118)

        assert "KARTEI_MN" in sql
        assert "KARTEI" not in sql or "KARTEI_MN" in sql

    def test_builds_query_with_correct_column_names(self, sample_mapping):
        """Generated SQL should use actual column names."""
        adapter = CenterAdapter(center=Mock(), mapping=sample_mapping)

        sql = adapter._build_chart_query(date=20220118)

        assert "PATNR_AB" in sql
        assert "DATUM_CD" in sql

    def test_query_filters_by_date(self, sample_mapping):
        """Generated SQL should filter by the provided date."""
        adapter = CenterAdapter(center=Mock(), mapping=sample_mapping)

        sql = adapter._build_chart_query(date=20220118)

        assert "20220118" in sql or "?" in sql  # Parameterized
```

---

## Integration Tests

### What to Integration Test

| Scenario | Components Involved |
|----------|---------------------|
| Full extraction flow | Service → Adapter → Database |
| CLI command execution | CLI → Service → Output |
| Mapping file I/O | Generator → File system → Loader |
| Database connectivity | Adapter → pyodbc → SQL Server |

### Example: Testing Extraction Service

```python
# tests/__tests__/integration/test_extraction_service.py

import pytest
from datetime import date
from src.services.extraction import ExtractionService
from src.core.config import load_config


@pytest.mark.integration
class TestExtractionService:
    """Integration tests for extraction service."""

    @pytest.fixture
    def config(self):
        """Load test configuration."""
        return load_config("config/centers.yml")

    @pytest.fixture
    def service(self, config):
        """Create extraction service."""
        return ExtractionService(config)

    def test_extracts_from_single_center(self, service):
        """Should extract data from one center."""
        result = service.extract_all(
            target_date=date(2022, 1, 18),
            center_ids=["center_01"],
            max_workers=1
        )

        assert len(result.results) == 1
        assert result.results[0].center_id == "center_01"
        assert result.results[0].error is None
        assert len(result.results[0].entries) > 0

    def test_extracts_from_all_centers(self, service):
        """Should extract data from all configured centers."""
        result = service.extract_all(
            target_date=date(2022, 1, 18),
            max_workers=5
        )

        assert result.successful_centers == 30
        assert result.total_entries > 0
        assert result.total_duration_ms < 5000  # Under 5s

    def test_handles_invalid_center_gracefully(self, service):
        """Should report error for invalid center."""
        result = service.extract_all(
            target_date=date(2022, 1, 18),
            center_ids=["invalid_center"],
            max_workers=1
        )

        assert len(result.results) == 1
        assert result.results[0].error is not None
```

### Example: Testing CLI Commands

```python
# tests/__tests__/integration/test_cli_commands.py

import pytest
from click.testing import CliRunner
from src.cli.main import main


@pytest.mark.integration
class TestCLICommands:
    """Integration tests for CLI commands."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_list_command_shows_centers(self, runner):
        """List command should show all configured centers."""
        result = runner.invoke(main, ["list"])

        assert result.exit_code == 0
        assert "center_01" in result.output
        assert "30 centers" in result.output

    def test_discover_raw_shows_schema(self, runner):
        """Discover-raw should show database schema."""
        result = runner.invoke(main, ["discover-raw", "-c", "center_01"])

        assert result.exit_code == 0
        assert "KARTEI" in result.output
        assert "PATIENT" in result.output

    def test_extract_produces_output(self, runner, tmp_path):
        """Extract should produce JSON/CSV files."""
        result = runner.invoke(main, [
            "extract",
            "-c", "center_01",
            "--date", "2022-01-18",
            "--format", "json"
        ])

        assert result.exit_code == 0
        assert "Extraction Complete" in result.output

    def test_benchmark_meets_target(self, runner):
        """Benchmark should complete under target time."""
        result = runner.invoke(main, ["benchmark"])

        assert result.exit_code == 0
        assert "PASS" in result.output
```

---

## End-to-End Tests

### What to E2E Test

| Scenario | Full Path |
|----------|-----------|
| Complete extraction | Config → Discovery → Mapping → Extraction → Output |
| Web UI extraction | Browser → API → Service → Database → Response |
| New center onboarding | Add config → Generate mapping → Extract |

### Example: Full Extraction E2E

```python
# tests/__tests__/e2e/test_full_extraction.py

import pytest
import json
from pathlib import Path


@pytest.mark.e2e
class TestFullExtraction:
    """End-to-end tests for complete extraction workflow."""

    def test_full_workflow_from_discovery_to_output(self, tmp_path):
        """Complete workflow should produce valid output."""
        import subprocess

        # 1. Discover schema
        result = subprocess.run(
            ["python", "-m", "src.cli", "discover-raw", "-c", "center_01"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # 2. Generate mappings
        result = subprocess.run(
            ["python", "-m", "src.cli", "generate-mappings"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # 3. Extract data
        result = subprocess.run(
            ["python", "-m", "src.cli", "extract",
             "--date", "2022-01-18",
             "--format", "json"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # 4. Verify output file exists and is valid JSON
        output_file = Path("data/output/extraction_2022-01-18.json")
        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)

        assert "entries" in data
        assert len(data["entries"]) > 0
        assert all("center_id" in e for e in data["entries"])
```

### Example: Web UI E2E

```python
# tests/__tests__/e2e/test_web_ui.py

import pytest
from fastapi.testclient import TestClient
from src.web.app import app


@pytest.mark.e2e
class TestWebUI:
    """End-to-end tests for web interface."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_explore_page_loads(self, client):
        """Explore page should load successfully."""
        response = client.get("/explore")
        assert response.status_code == 200
        assert "Explore Centers" in response.text

    def test_api_centers_returns_all(self, client):
        """API should return all configured centers."""
        response = client.get("/api/centers")
        assert response.status_code == 200

        data = response.json()
        assert len(data["centers"]) == 30

    def test_api_extract_returns_data(self, client):
        """API extraction should return chart entries."""
        response = client.post(
            "/api/centers/center_01/extract",
            json={"date": "2022-01-18"}
        )
        assert response.status_code == 200

        data = response.json()
        assert "entries" in data
        assert len(data["entries"]) > 0

    def test_api_benchmark_completes(self, client):
        """API benchmark should complete successfully."""
        response = client.post(
            "/api/benchmark",
            json={"center_ids": ["center_01", "center_02"]}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["successful"] == 2
        assert data["duration_ms"] < 5000
```

---

## Performance Tests

### Benchmarks

```python
# tests/__tests__/performance/test_benchmark.py

import pytest
import time
from src.services.extraction import ExtractionService
from src.core.config import load_config


@pytest.mark.performance
class TestPerformance:
    """Performance benchmarks."""

    @pytest.fixture
    def service(self):
        config = load_config()
        return ExtractionService(config)

    def test_30_centers_under_5_seconds(self, service):
        """Extraction of 30 centers should complete in <5s."""
        start = time.time()

        result = service.extract_all(
            target_date=date(2022, 1, 18),
            max_workers=5
        )

        duration = time.time() - start

        assert duration < 5.0, f"Took {duration:.2f}s, expected <5s"
        assert result.successful_centers == 30

    def test_single_center_under_100ms(self, service):
        """Single center extraction should complete in <100ms."""
        start = time.time()

        result = service.extract_all(
            target_date=date(2022, 1, 18),
            center_ids=["center_01"],
            max_workers=1
        )

        duration = time.time() - start

        assert duration < 0.1, f"Took {duration*1000:.0f}ms, expected <100ms"

    def test_parallel_scaling(self, service):
        """More workers should improve performance."""
        # Baseline: 1 worker
        start = time.time()
        service.extract_all(target_date=date(2022, 1, 18), max_workers=1)
        time_1_worker = time.time() - start

        # Scaled: 5 workers
        start = time.time()
        service.extract_all(target_date=date(2022, 1, 18), max_workers=5)
        time_5_workers = time.time() - start

        # 5 workers should be at least 2x faster than 1
        assert time_5_workers < time_1_worker / 2
```

---

## Running Tests

### Quick Reference

```bash
# Run all tests
pytest

# Run only unit tests
pytest tests/__tests__/unit/

# Run only integration tests
pytest tests/__tests__/integration/ -m integration

# Run only E2E tests
pytest tests/__tests__/e2e/ -m e2e

# Run only performance tests
pytest tests/__tests__/performance/ -m performance

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/__tests__/unit/test_discovery.py

# Run specific test
pytest tests/__tests__/unit/test_discovery.py::TestSchemaDiscovery::test_discover_finds_all_tables

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x

# Run tests matching pattern
pytest -k "discovery"
```

### pytest.ini Configuration

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (requires database)
    e2e: End-to-end tests (full workflow)
    performance: Performance benchmarks

addopts = -v --tb=short

# Default: run unit tests only
# Use -m to select other markers
```

### conftest.py Shared Fixtures

```python
# tests/conftest.py

import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def test_data_dir():
    """Path to test fixtures."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sample_mapping(test_data_dir):
    """Load sample mapping fixture."""
    import json
    with open(test_data_dir / "sample_mapping.json") as f:
        return json.load(f)


@pytest.fixture
def temp_mapping_dir(tmp_path):
    """Temporary directory for mapping files."""
    mapping_dir = tmp_path / "mappings"
    mapping_dir.mkdir()
    return mapping_dir


# Skip integration tests if no database
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "requires_db: mark test as requiring database"
    )


def pytest_collection_modifyitems(config, items):
    if not database_available():
        skip_db = pytest.mark.skip(reason="Database not available")
        for item in items:
            if "requires_db" in item.keywords:
                item.add_marker(skip_db)
```

---

## Writing New Tests

### Test Template

```python
# tests/__tests__/unit/test_<module>.py

import pytest
from unittest.mock import Mock, patch

from src.<module> import <Class>


class Test<Class>:
    """Tests for <Class>."""

    @pytest.fixture
    def instance(self):
        """Create instance for testing."""
        return <Class>(...)

    def test_<method>_<scenario>(self, instance):
        """<Method> should <expected behavior>."""
        # Arrange
        input_data = ...

        # Act
        result = instance.<method>(input_data)

        # Assert
        assert result == expected
```

### Guidelines

1. **One assertion per test** (when possible)
2. **Use descriptive test names** that explain the scenario
3. **Arrange-Act-Assert** structure
4. **Mock external dependencies** in unit tests
5. **Use fixtures** for common setup
6. **Parametrize** for multiple input scenarios

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-test.txt

      - name: Run unit tests
        run: pytest tests/__tests__/unit/ -v --cov=src

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      sqlserver:
        image: mcr.microsoft.com/mssql/server:2019-latest
        env:
          ACCEPT_EULA: Y
          SA_PASSWORD: TestPassword123!
        ports:
          - 1433:1433

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-test.txt

      - name: Setup test database
        run: python scripts/generate_test_dbs.py

      - name: Run integration tests
        run: pytest tests/__tests__/integration/ -v -m integration
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest tests/__tests__/unit/ -x -q
        language: system
        pass_filenames: false
        always_run: true
```

---

## Summary

### Test Coverage Goals

| Layer | Coverage Target |
|-------|-----------------|
| Core logic | 90%+ |
| Services | 80%+ |
| Adapters | 70%+ |
| CLI | 60%+ |
| Web | 50%+ |

### Quick Commands

```bash
# Daily development
pytest tests/__tests__/unit/ -x     # Fast, stop on failure

# Before commit
pytest --cov=src                    # With coverage

# Before release
pytest -m "not performance"         # All except perf
pytest -m performance               # Perf separately
```
