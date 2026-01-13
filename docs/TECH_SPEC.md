# Technical Specification

**Requirements, Architecture Decisions, and Scalability**

This document explains WHAT we chose and WHY, with an eye toward scaling to hundreds of dental centers.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Infrastructure Requirements](#infrastructure-requirements)
3. [Database Choice](#database-choice)
4. [Containerization Strategy](#containerization-strategy)
5. [Adapter Architecture](#adapter-architecture)
6. [Scalability Analysis](#scalability-analysis)
7. [Performance Characteristics](#performance-characteristics)
8. [Adding New Centers](#adding-new-centers)
9. [Production Considerations](#production-considerations)
10. [Technology Alternatives](#technology-alternatives)

---

## Executive Summary

### Current State

| Metric | Value |
|--------|-------|
| Centers supported | 30 |
| Extraction time | ~400ms |
| Parallel workers | 5 (configurable) |
| Code changes to add center | 0 (config only) |

### Scalability Target

| Metric | Target |
|--------|--------|
| Centers supported | 500+ |
| Extraction time | <30 seconds |
| Parallel workers | 50-100 |
| Code changes to add center | Still 0 |

### Key Design Principles

1. **Configuration over code** - Add centers via YAML, not Python
2. **Adapter pattern** - Each center is isolated, same interface
3. **Horizontal scaling** - More workers = more throughput
4. **Stateless extraction** - No shared state between centers

---

## Infrastructure Requirements

### Minimum Requirements (Development)

| Component | Specification | Why |
|-----------|---------------|-----|
| **Docker** | 20.10+ | Container isolation, reproducible environments |
| **Python** | 3.11+ | Modern async, type hints, performance |
| **Memory** | 4GB | SQL Server minimum + Python overhead |
| **CPU** | 2 cores | Parallel extraction benefits from cores |
| **Disk** | 10GB | SQL Server data + mapping files |

### Production Requirements (500 Centers)

| Component | Specification | Why |
|-----------|---------------|-----|
| **Docker/K8s** | Kubernetes cluster | Orchestration, auto-scaling |
| **Python** | 3.11+ | Same, but multiple instances |
| **Memory** | 16GB+ per node | Connection pools, concurrent extractions |
| **CPU** | 8+ cores per node | Maximize parallelism |
| **Disk** | SSD, 100GB+ | Fast I/O for mapping files |
| **Network** | Low latency to DBs | Database RTT is the bottleneck |

---

## Database Choice

### Why SQL Server?

| Reason | Explanation |
|--------|-------------|
| **Client requirement** | Ivoris dental software runs on SQL Server |
| **INFORMATION_SCHEMA** | Standard interface for schema discovery |
| **Mature ODBC drivers** | pyodbc is stable, well-documented |
| **Enterprise features** | Connection pooling, query optimization |

### Why NOT Other Databases?

| Database | Why Not |
|----------|---------|
| PostgreSQL | Client uses SQL Server |
| MySQL | Client uses SQL Server |
| SQLite | Can't handle concurrent connections at scale |
| NoSQL | Relational data, need joins |

### SQL Server Version

```yaml
# docker-compose.yml
image: mcr.microsoft.com/mssql/server:2019-latest
```

**Why 2019?**
- LTS (Long Term Support)
- Stable, well-tested
- Works on Apple Silicon via emulation
- Same version client likely runs

### Connection Configuration

```python
# Why these settings?
conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"  # Latest stable driver
    "SERVER=localhost,1434;"                    # Non-default port (avoid conflicts)
    "DATABASE={database};"                      # Per-center database
    "UID=sa;"                                   # Admin access for schema discovery
    "PWD={password};"                           # From config, not hardcoded
    "TrustServerCertificate=yes;"               # Dev only - skip SSL verification
)
```

**Production changes:**
- Use dedicated service account (not `sa`)
- Enable SSL verification
- Use connection pooling
- Add retry logic

---

## Containerization Strategy

### Why Docker?

| Benefit | Explanation |
|---------|-------------|
| **Reproducibility** | Same environment everywhere |
| **Isolation** | SQL Server doesn't pollute host |
| **Easy reset** | `docker-compose down -v` starts fresh |
| **Version control** | `docker-compose.yml` in git |
| **CI/CD ready** | Same container in dev/test/prod |

### Current Setup (Development)

```yaml
# Single SQL Server with 30 databases
services:
  sqlserver:
    image: mcr.microsoft.com/mssql/server:2019-latest
    ports:
      - "1434:1433"
    volumes:
      - sqlserver_data:/var/opt/mssql/data
```

**Why single container with multiple databases?**
- Simpler for development
- Lower resource usage
- Mimics some production scenarios (shared server)

### Production Setup (500 Centers)

```yaml
# Each region gets its own SQL Server
services:
  sqlserver-germany:
    image: mcr.microsoft.com/mssql/server:2019-latest
    # 200 German center databases

  sqlserver-austria:
    image: mcr.microsoft.com/mssql/server:2019-latest
    # 50 Austrian center databases

  sqlserver-switzerland:
    image: mcr.microsoft.com/mssql/server:2019-latest
    # 50 Swiss center databases

  extractor:
    image: ivoris-extractor:latest
    deploy:
      replicas: 10  # Scale horizontally
```

**Why separate servers by region?**
- Data sovereignty (GDPR)
- Lower latency (closer to data)
- Failure isolation
- Independent scaling

### Why NOT Kubernetes Yet?

| Current (Docker Compose) | When to Switch to K8s |
|--------------------------|----------------------|
| 30 centers | 100+ centers |
| Single developer | Team of operators |
| Demo/POC | Production SLA |
| Manual deployment | CI/CD required |

---

## Adapter Architecture

### The Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                     ExtractionService                        │
│                   (Orchestration Layer)                      │
└─────────────────────────────┬───────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  CenterAdapter  │ │  CenterAdapter  │ │  CenterAdapter  │
│   (center_01)   │ │   (center_02)   │ │   (center_N)    │
│                 │ │                 │ │                 │
│ + SchemaMapping │ │ + SchemaMapping │ │ + SchemaMapping │
│ + Connection    │ │ + Connection    │ │ + Connection    │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   DentalDB_01   │ │   DentalDB_02   │ │   DentalDB_N    │
│   (SQL Server)  │ │   (SQL Server)  │ │   (SQL Server)  │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Why Adapters?

| Benefit | Explanation |
|---------|-------------|
| **Isolation** | One center's failure doesn't affect others |
| **Testability** | Can mock adapter for unit tests |
| **Flexibility** | Different adapters for different DB types |
| **Scalability** | Each adapter runs independently |

### Adapter Interface

```python
class CenterAdapter:
    """Every center adapter implements the same interface."""

    def __init__(self, center: CenterConfig, mapping: SchemaMapping):
        self.center = center
        self.mapping = mapping
        self.conn = self._connect()

    def extract_chart_entries(self, date: int) -> list[ChartEntry]:
        """Extract entries for a date. Same interface for all centers."""
        sql = self._build_query(date)  # Uses mapping for actual names
        return self._execute(sql)

    def health_check(self) -> bool:
        """Check if center is reachable."""
        ...
```

### Why Same Interface Matters

```python
# ExtractionService doesn't care which center
for center in centers:
    adapter = get_adapter(center.id)  # Factory returns CenterAdapter
    entries = adapter.extract_chart_entries(date)  # Same method signature
    results.append(entries)
```

**Adding a new center type (e.g., different dental software)?**
1. Create `NewSoftwareAdapter` implementing same interface
2. Factory returns correct adapter based on config
3. ExtractionService unchanged

---

## Scalability Analysis

### Current Performance (30 Centers)

| Metric | Value | Bottleneck |
|--------|-------|------------|
| Total time | ~400ms | Network RTT |
| Per-center | ~15ms average | Query execution |
| Workers | 5 | Conservative default |
| Memory | ~200MB | Python + connections |

### Projected Performance (500 Centers)

| Scenario | Workers | Estimated Time | Notes |
|----------|---------|----------------|-------|
| Sequential | 1 | 500 × 15ms = 7.5s | Baseline |
| Current | 5 | 500 / 5 × 15ms = 1.5s | Limited by workers |
| Moderate | 50 | 500 / 50 × 15ms = 150ms | Need more memory |
| Aggressive | 100 | 500 / 100 × 15ms = 75ms | Diminishing returns |

### Scaling Strategies

#### Strategy 1: Increase Workers (Easy)

```python
# Current
service.extract_all(max_workers=5)

# Scaled
service.extract_all(max_workers=50)
```

**Pros:** Simple, no code changes
**Cons:** Memory grows linearly, connection limits

#### Strategy 2: Sharding by Region (Medium)

```python
# Run separate extractors per region
# Germany extractor: centers 1-200
# Austria extractor: centers 201-250
# Switzerland extractor: centers 251-300
```

**Pros:** Parallel at process level, failure isolation
**Cons:** Need orchestration layer

#### Strategy 3: Async I/O (Advanced)

```python
# Current: ThreadPoolExecutor (threads)
# Upgraded: asyncio + aioodbc (event loop)

async def extract_center(center):
    async with aioodbc.connect(dsn=...) as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql)
            return await cursor.fetchall()

# Run all 500 concurrently
results = await asyncio.gather(*[
    extract_center(c) for c in centers
])
```

**Pros:** Maximum concurrency, lower memory
**Cons:** More complex code, different driver

### Scaling Limits

| Limit | Value | Mitigation |
|-------|-------|------------|
| SQL Server connections | 32,767 max | Connection pooling |
| Python threads | ~1000 practical | Async I/O |
| Memory per connection | ~5MB | Connection pooling |
| Network bandwidth | Varies | Regional deployment |

---

## Performance Characteristics

### Time Breakdown (Per Center)

| Phase | Time | % of Total |
|-------|------|------------|
| Connection setup | 5ms | 33% |
| Query execution | 8ms | 53% |
| Result processing | 2ms | 14% |
| **Total** | **15ms** | 100% |

### Optimization Opportunities

| Optimization | Effort | Impact |
|--------------|--------|--------|
| Connection pooling | Low | -30% connection time |
| Prepared statements | Low | -20% query time |
| Batch queries | Medium | -50% for multiple dates |
| Async I/O | High | -60% total time |
| Caching mappings | Done | Already implemented |

### Memory Profile

| Component | Memory | At 500 Centers |
|-----------|--------|----------------|
| Python base | 50MB | 50MB |
| Per connection | 5MB | 250MB (50 workers) |
| Mapping cache | 1MB | 15MB (500 mappings) |
| Result buffer | 10MB | 100MB |
| **Total** | | ~400MB |

---

## Adding New Centers

### Zero Code Changes Required

Adding a new center requires ONLY configuration:

#### Step 1: Add to centers.yml

```yaml
# config/centers.yml
centers:
  # ... existing centers ...

  - id: center_31
    name: Neue Zahnarztpraxis Berlin
    database: DentalDB_31
    city: Berlin
```

#### Step 2: Generate Mapping

```bash
# Discovers schema automatically
python -m src.cli discover-raw -c center_31

# Generates mapping file
python -m src.cli generate-mappings
```

#### Step 3: Review Mapping

```bash
# Check the generated mapping
python -m src.cli show-mapping center_31

# Edit data/mappings/center_31_mapping.json if needed
# Set "reviewed": true when verified
```

#### Step 4: Extract

```bash
# Works immediately
python -m src.cli extract -c center_31 --date 2022-01-18
```

### Why Zero Code Changes?

| Design Choice | Enables |
|---------------|---------|
| YAML configuration | Add centers without touching Python |
| Pattern-based discovery | Handles any suffix automatically |
| JSON mapping files | Per-center customization without code |
| Factory pattern | Adapter created from config |

### Adding 100 Centers at Once

```yaml
# Generate centers.yml programmatically
centers:
  {% for i in range(1, 101) %}
  - id: center_{{ '%02d' | format(i) }}
    name: Dental Center {{ i }}
    database: DentalDB_{{ '%02d' | format(i) }}
    city: Berlin
  {% endfor %}
```

```bash
# Batch discovery and mapping
python -m src.cli generate-mappings  # Processes all at once
```

---

## Production Considerations

### What Would Change for Production

| Aspect | Development | Production |
|--------|-------------|------------|
| **Database credentials** | Hardcoded SA | Secrets manager (Vault, AWS Secrets) |
| **Connection pooling** | None | SQLAlchemy pool or similar |
| **SSL/TLS** | Disabled | Required, verified |
| **Error handling** | Log and continue | Retry, alert, circuit breaker |
| **Monitoring** | Console logs | Prometheus metrics, Grafana |
| **Deployment** | Docker Compose | Kubernetes, Helm charts |
| **Mapping storage** | Local JSON files | S3/GCS with versioning |
| **Authentication** | None | OAuth2/OIDC |

### Security Hardening

```python
# Development (current)
conn_str = f"UID=sa;PWD=MultiCenter@2024;TrustServerCertificate=yes;"

# Production
conn_str = (
    f"UID={os.environ['DB_USER']};"           # From secrets manager
    f"PWD={os.environ['DB_PASSWORD']};"        # From secrets manager
    f"Encrypt=yes;"                            # Force encryption
    f"TrustServerCertificate=no;"              # Verify certificates
)
```

### Monitoring & Alerting

```python
# Add Prometheus metrics
from prometheus_client import Counter, Histogram

extraction_duration = Histogram(
    'extraction_duration_seconds',
    'Time to extract from a center',
    ['center_id']
)

extraction_errors = Counter(
    'extraction_errors_total',
    'Number of extraction failures',
    ['center_id', 'error_type']
)
```

### High Availability

| Component | HA Strategy |
|-----------|-------------|
| Extractor service | Multiple replicas behind load balancer |
| Mapping files | Stored in S3 with versioning |
| SQL Server | Read replicas for extraction |
| Config | GitOps with ArgoCD |

---

## Technology Alternatives

### Database Drivers

| Option | Pros | Cons | When to Use |
|--------|------|------|-------------|
| **pyodbc** (current) | Stable, synchronous | No async | Default choice |
| aioodbc | Async support | Less mature | High concurrency |
| pymssql | Pure Python | Fewer features | No ODBC available |
| SQLAlchemy | ORM, pooling | Overhead | Complex queries |

### Parallelism

| Option | Pros | Cons | When to Use |
|--------|------|------|-------------|
| **ThreadPoolExecutor** (current) | Simple, works | Limited scale | <100 workers |
| asyncio + aioodbc | Maximum concurrency | Complex | 100+ workers |
| multiprocessing | True parallelism | Memory overhead | CPU-bound work |
| Celery | Distributed, robust | Infrastructure | Multi-node |

### Configuration

| Option | Pros | Cons | When to Use |
|--------|------|------|-------------|
| **YAML files** (current) | Human-readable | No validation | Simple configs |
| Pydantic Settings | Validation, typing | More code | Complex configs |
| Environment variables | 12-factor app | Hard to manage many | Secrets only |
| etcd/Consul | Dynamic, distributed | Infrastructure | Microservices |

### Web Framework

| Option | Pros | Cons | When to Use |
|--------|------|------|-------------|
| **FastAPI** (current) | Modern, async, docs | Newer | API-first |
| Flask | Simple, mature | Sync by default | Quick prototype |
| Django | Full-featured | Heavy | Full web app |
| Streamlit | Instant UI | Limited control | Data exploration |

---

## Summary

### Why These Choices Scale

| Choice | Scales Because |
|--------|----------------|
| **Docker** | Same container runs anywhere, K8s ready |
| **SQL Server** | Client requirement, enterprise-grade |
| **Adapter pattern** | Add centers without code changes |
| **JSON mappings** | Per-center config, version controlled |
| **ThreadPool** | Easily increase workers |
| **YAML config** | Batch add centers programmatically |

### What Stays the Same at 500 Centers

- Adapter interface
- Mapping file format
- CLI commands
- Extraction logic

### What Changes at 500 Centers

- Worker count (5 → 50+)
- Deployment (Docker Compose → K8s)
- Monitoring (logs → Prometheus)
- Credentials (hardcoded → secrets manager)

### The Core Insight

> **The architecture is designed so that scaling is a configuration change, not a code change.**

Adding center 31 or center 500 uses the same process:
1. Add entry to `centers.yml`
2. Run `generate-mappings`
3. Review and approve
4. Extract

No Python code touched. No deployment required. Just configuration.
