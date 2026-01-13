# Operations Runbook

**Production Operations Guide for Ivoris Multi-Center Pipeline**

This runbook provides step-by-step procedures for operating, monitoring, and troubleshooting the extraction pipeline in production.

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Daily Operations](#daily-operations)
3. [Monitoring](#monitoring)
4. [Alerting](#alerting)
5. [Troubleshooting](#troubleshooting)
6. [Maintenance Procedures](#maintenance-procedures)
7. [Disaster Recovery](#disaster-recovery)
8. [Runbook Procedures](#runbook-procedures)

---

## Quick Reference

### Key URLs

| Environment | URL | Purpose |
|-------------|-----|---------|
| Production | https://ivoris.example.com | Main application |
| Staging | https://ivoris-staging.example.com | Testing |
| Monitoring | https://grafana.example.com/d/ivoris | Dashboards |
| Logs | https://kibana.example.com/ivoris | Log search |
| Alerts | https://pagerduty.example.com | On-call |

### Key Commands

```bash
# Check service status
kubectl get pods -n ivoris

# View logs
kubectl logs -n ivoris -l app=extractor --tail=100

# Run manual extraction
kubectl exec -n ivoris deploy/extractor -- \
  python -m src.cli extract --date $(date -d yesterday +%Y-%m-%d)

# Scale extractors
kubectl scale -n ivoris deploy/extractor --replicas=10
```

### Emergency Contacts

| Role | Contact | When |
|------|---------|------|
| On-call engineer | PagerDuty | Service down |
| Database admin | dba@example.com | DB issues |
| Security team | security@example.com | Security incident |
| Management | manager@example.com | Major outage >1hr |

---

## Daily Operations

### Scheduled Jobs

| Job | Schedule | Duration | Owner |
|-----|----------|----------|-------|
| Daily extraction | 02:00 UTC | ~5 min | Cron |
| Mapping validation | 06:00 UTC | ~2 min | Cron |
| Log rotation | 00:00 UTC | ~1 min | System |
| Backup | 04:00 UTC | ~30 min | DBA |

### Morning Checklist

```markdown
- [ ] Check overnight extraction completed
      → Grafana: ivoris_extraction_success == 30
- [ ] Review any alerts from overnight
      → PagerDuty: no unresolved incidents
- [ ] Verify data freshness
      → Query: SELECT MAX(extraction_date) FROM extractions
- [ ] Check error rate
      → Grafana: ivoris_errors_total < 5
```

### Daily Extraction Verification

```bash
# Check yesterday's extraction
python -m src.cli verify --date $(date -d yesterday +%Y-%m-%d)

# Expected output:
# ✓ 30/30 centers extracted
# ✓ 180 total records
# ✓ Duration: 423ms
# ✓ No errors
```

---

## Monitoring

### Key Metrics

| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| `extraction_duration_seconds` | <5s | >10s | >30s |
| `extraction_success_total` | 30/30 | <28/30 | <25/30 |
| `extraction_errors_total` | 0 | >3 | >10 |
| `database_connection_pool_used` | <80% | >80% | >95% |
| `cpu_usage_percent` | <60% | >80% | >95% |
| `memory_usage_percent` | <70% | >85% | >95% |

### Prometheus Metrics

```python
# Exposed at /metrics
ivoris_extraction_duration_seconds{center="center_01"}
ivoris_extraction_success_total
ivoris_extraction_errors_total{center="center_01", error="connection"}
ivoris_centers_configured
ivoris_centers_mapped
ivoris_database_connections_active{region="germany"}
```

### Grafana Dashboards

#### Dashboard: Ivoris Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  EXTRACTION STATUS                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ 30/30    │ │ 180      │ │ 423ms    │ │ 0        │           │
│  │ Centers  │ │ Records  │ │ Duration │ │ Errors   │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
├─────────────────────────────────────────────────────────────────┤
│  EXTRACTION DURATION BY CENTER (Last 24h)                        │
│  ████████████████████ center_01 (23ms)                          │
│  ███████████████████  center_02 (21ms)                          │
│  █████████████████    center_03 (19ms)                          │
│  ...                                                             │
├─────────────────────────────────────────────────────────────────┤
│  ERROR RATE (Last 7 days)                                        │
│  [Line chart showing errors over time]                           │
└─────────────────────────────────────────────────────────────────┘
```

### Health Checks

```python
# GET /health
{
  "status": "healthy",
  "version": "1.0.0",
  "checks": {
    "database_germany": "ok",
    "database_austria": "ok",
    "database_switzerland": "ok",
    "mapping_files": "ok",
    "disk_space": "ok"
  },
  "timestamp": "2026-01-13T14:30:00Z"
}

# GET /health/live (Kubernetes liveness)
{"status": "ok"}

# GET /health/ready (Kubernetes readiness)
{"status": "ok", "databases": 30, "mappings": 30}
```

---

## Alerting

### Alert Definitions

#### Critical (P1) - Page immediately

```yaml
- alert: ExtractionCompleteFailure
  expr: ivoris_extraction_success_total < 25
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Less than 25 centers extracted successfully"
    runbook: "See OPERATIONS.md#extraction-failure"

- alert: ServiceDown
  expr: up{job="ivoris"} == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Ivoris service is down"
    runbook: "See OPERATIONS.md#service-down"
```

#### Warning (P2) - Notify during business hours

```yaml
- alert: ExtractionPartialFailure
  expr: ivoris_extraction_success_total < 28
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Some centers failed to extract"
    runbook: "See OPERATIONS.md#partial-failure"

- alert: ExtractionSlow
  expr: ivoris_extraction_duration_seconds > 10
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Extraction taking longer than normal"
    runbook: "See OPERATIONS.md#slow-extraction"
```

### PagerDuty Integration

```yaml
# alertmanager.yml
receivers:
  - name: 'ivoris-critical'
    pagerduty_configs:
      - service_key: '<pagerduty-key>'
        severity: critical

  - name: 'ivoris-warning'
    slack_configs:
      - channel: '#ivoris-alerts'
        send_resolved: true
```

---

## Troubleshooting

### Decision Tree

```
Extraction Failed?
├── All centers failed?
│   ├── Yes → Check service health
│   │         → See: Service Down
│   └── No → Check specific centers
│            → See: Partial Failure
│
Extraction Slow?
├── All centers slow?
│   ├── Yes → Check database load
│   │         → See: Slow Extraction
│   └── No → Check specific center
│            → See: Single Center Slow
│
Mapping Issues?
├── Discovery failed?
│   └── See: Schema Discovery Issues
├── Mapping incorrect?
│   └── See: Mapping Mismatch
```

### Common Issues

#### Issue: Service Down

**Symptoms:**
- Health check returns 503
- No metrics being reported
- Alerts firing

**Diagnosis:**
```bash
# Check pod status
kubectl get pods -n ivoris
# Look for: CrashLoopBackOff, Error, Pending

# Check pod logs
kubectl logs -n ivoris -l app=extractor --tail=200

# Check events
kubectl get events -n ivoris --sort-by='.lastTimestamp'
```

**Resolution:**
```bash
# Restart deployment
kubectl rollout restart -n ivoris deploy/extractor

# If still failing, check config
kubectl describe configmap -n ivoris ivoris-config

# Check secrets
kubectl get secret -n ivoris ivoris-secrets -o yaml
```

#### Issue: Partial Failure (Some Centers)

**Symptoms:**
- 25-29 centers succeed
- Specific centers consistently fail

**Diagnosis:**
```bash
# Check which centers failed
kubectl logs -n ivoris -l app=extractor | grep "Error"

# Test specific center
kubectl exec -n ivoris deploy/extractor -- \
  python -m src.cli discover-raw -c center_XX
```

**Resolution:**
```bash
# If database unreachable
ping sqlserver-germany.internal

# If mapping issue
python -m src.cli show-mapping center_XX
# Regenerate if needed
python -m src.cli generate-mappings
```

#### Issue: Slow Extraction

**Symptoms:**
- Duration >10s (normally <1s)
- CPU/memory normal
- Database connection slow

**Diagnosis:**
```bash
# Check database latency
kubectl exec -n ivoris deploy/extractor -- \
  python -c "import time; t=time.time(); __import__('pyodbc').connect('...'); print(f'{time.time()-t:.2f}s')"

# Check query execution time
# In SQL Server:
SELECT TOP 10
    total_elapsed_time/execution_count AS avg_time,
    execution_count,
    SUBSTRING(st.text, 1, 100) AS query
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
ORDER BY avg_time DESC;
```

**Resolution:**
```bash
# If network latency
# Check if in same region/VPC

# If query slow
# Add missing indexes (DBA task)
CREATE INDEX IX_KARTEI_DATUM ON ck.KARTEI_XX(DATUM_XX);

# If connection pool exhausted
# Increase pool size in config
```

#### Issue: Schema Discovery Failed

**Symptoms:**
- `discover-raw` returns no tables
- New center can't be mapped

**Diagnosis:**
```bash
# Test database connection
python -m src.cli discover-raw -c center_XX 2>&1

# Check if ck schema exists
# In SQL Server:
SELECT * FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'ck';

# Check user permissions
SELECT * FROM fn_my_permissions('ck.KARTEI_XX', 'OBJECT');
```

**Resolution:**
```bash
# If schema doesn't exist
# Contact center IT - database not set up correctly

# If permission denied
# Grant SELECT on ck schema to service account
GRANT SELECT ON SCHEMA::ck TO svc_extract;
```

#### Issue: Mapping Mismatch

**Symptoms:**
- Extraction returns wrong data
- Column values swapped

**Diagnosis:**
```bash
# Compare mapping to actual schema
python -m src.cli show-mapping center_XX
python -m src.cli discover-raw -c center_XX

# Check ground truth
cat data/ground_truth/center_XX_ground_truth.json
```

**Resolution:**
```bash
# Regenerate mapping
rm data/mappings/center_XX_mapping.json
python -m src.cli generate-mappings

# Manually fix if pattern matching failed
vi data/mappings/center_XX_mapping.json
# Set "reviewed": true after fixing
```

---

## Maintenance Procedures

### Adding a New Center

```bash
# 1. Add to configuration
vi config/centers.yml
# Add new center entry

# 2. Discover schema
python -m src.cli discover-raw -c center_NEW

# 3. Generate mapping
python -m src.cli generate-mappings

# 4. Review mapping
python -m src.cli show-mapping center_NEW
# Edit if needed, set reviewed: true

# 5. Test extraction
python -m src.cli extract -c center_NEW --date 2022-01-18

# 6. Deploy config change
kubectl apply -f kubernetes/configmap.yaml
kubectl rollout restart -n ivoris deploy/extractor
```

### Removing a Center

```bash
# 1. Remove from configuration
vi config/centers.yml
# Remove center entry

# 2. Archive mapping (don't delete)
mv data/mappings/center_OLD_mapping.json data/mappings/archive/

# 3. Deploy config change
kubectl apply -f kubernetes/configmap.yaml
kubectl rollout restart -n ivoris deploy/extractor

# 4. Update monitoring
# Remove center from dashboards/alerts
```

### Updating Mappings

```bash
# 1. Backup current mapping
cp data/mappings/center_XX_mapping.json data/mappings/center_XX_mapping.json.bak

# 2. Regenerate
python -m src.cli generate-mappings

# 3. Diff and review
diff data/mappings/center_XX_mapping.json.bak data/mappings/center_XX_mapping.json

# 4. Test
python -m src.cli extract -c center_XX --date 2022-01-18

# 5. Deploy
# Commit and push, CI/CD deploys
```

### Scaling Up

```bash
# Increase replicas
kubectl scale -n ivoris deploy/extractor --replicas=10

# Increase worker count per pod
kubectl set env -n ivoris deploy/extractor MAX_WORKERS=50

# Verify
kubectl get pods -n ivoris
kubectl top pods -n ivoris
```

### Scaling Down

```bash
# Decrease replicas (during off-hours)
kubectl scale -n ivoris deploy/extractor --replicas=2

# Verify no extraction in progress first!
kubectl logs -n ivoris -l app=extractor | grep "Extracting"
```

---

## Disaster Recovery

### Backup Strategy

| Component | Backup Method | Frequency | Retention |
|-----------|---------------|-----------|-----------|
| Mapping files | Git + S3 | On change | Forever |
| Configuration | Git + S3 | On change | Forever |
| Extraction output | S3 | Daily | 90 days |
| Audit logs | S3 | Daily | 2 years |
| Database | DBA managed | Daily | 30 days |

### Recovery Procedures

#### Recover Mapping Files

```bash
# From Git
git checkout HEAD~1 -- data/mappings/

# From S3
aws s3 cp s3://ivoris-backups/mappings/2026-01-12/ data/mappings/ --recursive
```

#### Recover from Complete Failure

```bash
# 1. Verify infrastructure
kubectl get nodes
kubectl get pods -n ivoris

# 2. Restore config from Git
git pull origin main

# 3. Deploy
kubectl apply -f kubernetes/

# 4. Verify
kubectl get pods -n ivoris
python -m src.cli list

# 5. Run manual extraction for missed period
python -m src.cli extract --date 2026-01-12
python -m src.cli extract --date 2026-01-13
```

### RTO/RPO Targets

| Scenario | RTO | RPO |
|----------|-----|-----|
| Pod failure | 2 minutes | 0 (retry) |
| Node failure | 5 minutes | 0 (replica) |
| Region failure | 1 hour | 24 hours |
| Complete failure | 4 hours | 24 hours |

---

## Runbook Procedures

### RB-001: Daily Extraction Verification

```
TRIGGER: Daily at 06:00 UTC
OWNER: On-call engineer
TIME: 5 minutes

STEPS:
1. Open Grafana dashboard
2. Verify extraction_success_total == 30
3. Verify extraction_errors_total == 0
4. Check extraction_duration_seconds < 5s
5. If any issues, escalate per alerting rules

EXPECTED OUTCOME:
- All 30 centers extracted
- No errors
- Duration under 5 seconds
```

### RB-002: New Center Onboarding

```
TRIGGER: New center request
OWNER: DevOps engineer
TIME: 30 minutes

PREREQUISITES:
- Database credentials from center IT
- Network connectivity confirmed
- DPA signed

STEPS:
1. Add center to config/centers.yml
2. Run: python -m src.cli discover-raw -c center_NEW
3. Run: python -m src.cli generate-mappings
4. Review: python -m src.cli show-mapping center_NEW
5. Test: python -m src.cli extract -c center_NEW --date YYYY-MM-DD
6. Commit and push changes
7. Verify in staging environment
8. Deploy to production
9. Verify in production
10. Update documentation

EXPECTED OUTCOME:
- Center extracts successfully
- Mapping reviewed and approved
- Monitoring shows new center
```

### RB-003: Emergency Rollback

```
TRIGGER: Critical failure after deployment
OWNER: On-call engineer
TIME: 10 minutes

STEPS:
1. Identify last known good version
   kubectl rollout history -n ivoris deploy/extractor

2. Rollback deployment
   kubectl rollout undo -n ivoris deploy/extractor

3. Verify pods healthy
   kubectl get pods -n ivoris

4. Test extraction
   python -m src.cli extract -c center_01 --date YYYY-MM-DD

5. Create incident ticket
6. Notify team

EXPECTED OUTCOME:
- Service restored to last known good state
- Extraction working
- Incident documented
```

---

## Summary

### Key Contacts

| Role | Contact |
|------|---------|
| On-call | PagerDuty rotation |
| DevOps | devops@example.com |
| DBA | dba@example.com |
| Security | security@example.com |

### Key Commands

```bash
# Health check
curl https://ivoris.example.com/health

# Manual extraction
python -m src.cli extract --date YYYY-MM-DD

# View logs
kubectl logs -n ivoris -l app=extractor -f

# Restart service
kubectl rollout restart -n ivoris deploy/extractor
```

### Escalation Path

```
Alert fires
    ↓
On-call engineer (15 min)
    ↓
DevOps team lead (30 min)
    ↓
Engineering manager (1 hour)
    ↓
CTO (critical only)
```
