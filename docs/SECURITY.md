# Security Specification

**Authentication, Secrets Management, and Compliance**

This document covers security considerations for the Ivoris Multi-Center Pipeline, including GDPR compliance for handling dental patient data across Germany, Austria, and Switzerland.

---

## Table of Contents

1. [Security Overview](#security-overview)
2. [Data Classification](#data-classification)
3. [Authentication & Authorization](#authentication--authorization)
4. [Secrets Management](#secrets-management)
5. [Network Security](#network-security)
6. [GDPR Compliance](#gdpr-compliance)
7. [Audit Logging](#audit-logging)
8. [Security Checklist](#security-checklist)
9. [Incident Response](#incident-response)

---

## Security Overview

### Current State (Development)

| Aspect | Status | Risk Level |
|--------|--------|------------|
| Database credentials | Hardcoded in config | HIGH |
| SSL/TLS | Disabled | HIGH |
| Authentication | None | MEDIUM |
| Audit logging | Basic console | MEDIUM |
| Data encryption at rest | SQL Server default | LOW |

### Production Requirements

| Aspect | Required | Implementation |
|--------|----------|----------------|
| Database credentials | Secrets manager | HashiCorp Vault / AWS Secrets |
| SSL/TLS | Mandatory | Valid certificates |
| Authentication | OAuth2/OIDC | Keycloak / Auth0 |
| Audit logging | Comprehensive | Structured logs to SIEM |
| Data encryption | AES-256 | SQL Server TDE |

---

## Data Classification

### Data Types Handled

| Data Type | Classification | Sensitivity | Retention |
|-----------|---------------|-------------|-----------|
| Patient ID | PII | HIGH | Per center policy |
| Patient Name | PII | HIGH | Not extracted |
| Insurance Status | PII | MEDIUM | Per center policy |
| Chart Entries | PHI | HIGH | Per center policy |
| Service Codes | PHI | MEDIUM | Per center policy |
| Schema Mappings | Technical | LOW | Indefinite |
| Extraction Logs | Operational | LOW | 90 days |

### What We Extract vs. What We Don't

```
EXTRACTED (minimized):          NOT EXTRACTED (by design):
─────────────────────           ─────────────────────────
✓ Patient ID (numeric)          ✗ Patient full name
✓ Insurance type code           ✗ Address
✓ Chart entry text              ✗ Phone number
✓ Service codes                 ✗ Email
✓ Date of service               ✗ Date of birth
                                ✗ Full insurance details
```

### Data Minimization Principle

```python
# We only extract what's needed for the business case
SELECT
    k.PATNR,           # Patient ID only, not name
    k.DATUM,           # Date of service
    kas.ART,           # Insurance type code only
    k.BEMERKUNG        # Chart entry
FROM ...

# NOT this:
SELECT * FROM PATIENT  # Never extract full patient records
```

---

## Authentication & Authorization

### Current State (Development)

```python
# No authentication - development only
@app.get("/api/centers")
async def list_centers():
    return {"centers": [...]}
```

### Production Implementation

#### API Authentication (OAuth2 + JWT)

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "read:centers": "View center list",
        "read:data": "Extract patient data",
        "admin:mappings": "Modify schema mappings",
    }
)

async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme)
):
    # Validate JWT token
    # Check scopes
    # Return user
    ...

@app.get("/api/centers/{center_id}/extract")
async def extract_data(
    center_id: str,
    user: User = Security(get_current_user, scopes=["read:data"])
):
    # Only users with read:data scope can extract
    ...
```

#### Role-Based Access Control (RBAC)

| Role | Permissions | Use Case |
|------|-------------|----------|
| `viewer` | `read:centers` | View center list only |
| `extractor` | `read:centers`, `read:data` | Run extractions |
| `admin` | All scopes | Manage mappings, full access |

#### Center-Level Authorization

```python
# Users can only access their assigned centers
@dataclass
class User:
    id: str
    roles: list[str]
    allowed_centers: list[str]  # ["center_01", "center_02"]

async def authorize_center_access(user: User, center_id: str):
    if center_id not in user.allowed_centers:
        raise HTTPException(403, "Access to this center denied")
```

### Database Authentication

#### Development (Current)

```python
# SA account - NOT for production
conn_str = "UID=sa;PWD=Clinero2026;"
```

#### Production

```python
# Dedicated service account per center region
conn_str = (
    f"UID={get_secret('db_user_germany')};"
    f"PWD={get_secret('db_password_germany')};"
)
```

| Account | Access | Purpose |
|---------|--------|---------|
| `svc_extract_de` | Read-only on German centers | Extraction |
| `svc_extract_at` | Read-only on Austrian centers | Extraction |
| `svc_extract_ch` | Read-only on Swiss centers | Extraction |
| `svc_admin` | Schema discovery only | Mapping generation |

---

## Secrets Management

### Current State (Development)

```yaml
# config/centers.yml - INSECURE for production
database:
  password: Clinero2026  # Hardcoded!
```

### Production Implementation

#### Option 1: HashiCorp Vault

```python
import hvac

client = hvac.Client(url='https://vault.example.com')
client.auth.approle.login(
    role_id=os.environ['VAULT_ROLE_ID'],
    secret_id=os.environ['VAULT_SECRET_ID']
)

# Read secrets at runtime
secrets = client.secrets.kv.v2.read_secret_version(
    path='ivoris/database/germany'
)
db_password = secrets['data']['data']['password']
```

#### Option 2: AWS Secrets Manager

```python
import boto3

client = boto3.client('secretsmanager')

def get_secret(secret_name: str) -> str:
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

db_password = get_secret('ivoris/db/germany')
```

#### Option 3: Environment Variables (Kubernetes)

```yaml
# kubernetes/deployment.yaml
env:
  - name: DB_PASSWORD_GERMANY
    valueFrom:
      secretKeyRef:
        name: ivoris-secrets
        key: db-password-germany
```

### Secret Rotation

| Secret | Rotation Frequency | Method |
|--------|-------------------|--------|
| Database passwords | 90 days | Vault auto-rotation |
| API keys | 30 days | Manual + notification |
| JWT signing key | 365 days | Blue-green deployment |

### What Should Never Be in Code

```python
# NEVER commit these:
password = "Clinero2026"      # ❌ Hardcoded password
api_key = "sk-abc123..."           # ❌ API key
private_key = "-----BEGIN RSA..."  # ❌ Private key

# ALWAYS use environment or secrets manager:
password = os.environ['DB_PASSWORD']           # ✓
password = get_secret('db/password')           # ✓
password = vault.read('secret/db')['password'] # ✓
```

---

## Network Security

### Current State (Development)

```yaml
# docker-compose.yml - exposes to all interfaces
ports:
  - "1434:1433"  # Accessible from anywhere
```

### Production Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERNET                                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTPS only (443)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WAF / API Gateway                             │
│                  (Rate limiting, DDoS protection)                │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────┼─────────────────────────────────┐
│                         DMZ                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Load Balancer                          │    │
│  │              (TLS termination)                           │    │
│  └─────────────────────────────────────────────────────────┘    │
└───────────────────────────────┬─────────────────────────────────┘
                                │ Internal only
┌───────────────────────────────┼─────────────────────────────────┐
│                    PRIVATE SUBNET                                │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Extractor   │  │  Extractor   │  │  Extractor   │          │
│  │   Pod 1      │  │   Pod 2      │  │   Pod N      │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                    │
│         └─────────────────┼─────────────────┘                    │
│                           │ Private network only                 │
│  ┌────────────────────────┼────────────────────────────────┐    │
│  │                   DATABASE SUBNET                        │    │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐            │    │
│  │  │ SQL (DE)  │  │ SQL (AT)  │  │ SQL (CH)  │            │    │
│  │  └───────────┘  └───────────┘  └───────────┘            │    │
│  └──────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### TLS Configuration

```python
# Production connection string
conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=sqlserver-germany.internal:1433;"
    "DATABASE={database};"
    "UID={user};"
    "PWD={password};"
    "Encrypt=yes;"                    # Force encryption
    "TrustServerCertificate=no;"      # Verify certificate
    "HostNameInCertificate=*.internal;"
)
```

### Firewall Rules

| Source | Destination | Port | Allow |
|--------|-------------|------|-------|
| Internet | WAF | 443 | Yes |
| WAF | Load Balancer | 443 | Yes |
| Load Balancer | Extractor Pods | 8000 | Yes |
| Extractor Pods | SQL Servers | 1433 | Yes |
| Everything else | * | * | No |

---

## GDPR Compliance

### Applicability

| Country | Regulation | Applies? |
|---------|------------|----------|
| Germany | GDPR + BDSG | Yes |
| Austria | GDPR + DSG | Yes |
| Switzerland | FADP (revDSG) | Yes |

### Data Subject Rights

| Right | Implementation |
|-------|----------------|
| **Access** | Export API with patient ID filter |
| **Rectification** | Not applicable (read-only extraction) |
| **Erasure** | Delete from output files, log retention policy |
| **Portability** | JSON/CSV export in standard format |
| **Objection** | Center-level opt-out in config |

### Legal Basis for Processing

```yaml
# config/centers.yml - document legal basis
centers:
  - id: center_01
    name: Zahnarztpraxis München
    legal_basis: legitimate_interest  # or contract, consent
    dpa_signed: true                  # Data Processing Agreement
    dpa_date: "2024-01-15"
```

### Data Processing Agreement (DPA) Requirements

| Clause | Requirement |
|--------|-------------|
| Purpose | Daily extraction for operational reporting |
| Data types | Patient ID, insurance type, chart entries |
| Retention | 30 days in extraction output |
| Subprocessors | List of cloud providers |
| Security measures | This document |
| Breach notification | 72 hours |

### Cross-Border Data Transfer

```
Germany ──────────────────► Germany (Processing)     ✓ No transfer
Austria ──────────────────► Austria (Processing)     ✓ No transfer
Switzerland ──────────────► Switzerland (Processing) ✓ No transfer

Germany ──────────────────► Switzerland              ⚠ Adequacy decision
Austria ──────────────────► Germany                  ✓ Within EU
```

**Recommendation:** Process data in the same country/region as the source.

### Privacy by Design

| Principle | Implementation |
|-----------|----------------|
| Data minimization | Only extract needed fields |
| Purpose limitation | Extraction for reporting only |
| Storage limitation | 30-day retention on outputs |
| Pseudonymization | Patient ID only, not name |
| Encryption | TLS in transit, TDE at rest |

### Audit Requirements

```python
# Every extraction must be logged
@dataclass
class ExtractionAuditLog:
    timestamp: datetime
    user_id: str
    center_id: str
    date_extracted: date
    record_count: int
    legal_basis: str
    purpose: str
    ip_address: str
```

---

## Audit Logging

### What Must Be Logged

| Event | Fields | Retention |
|-------|--------|-----------|
| Authentication | user, timestamp, IP, success/fail | 1 year |
| Authorization | user, resource, action, allowed/denied | 1 year |
| Data access | user, center, date range, record count | 2 years |
| Configuration change | user, what changed, old/new value | 5 years |
| Error | timestamp, error type, stack trace | 90 days |

### Log Format (Structured JSON)

```json
{
  "timestamp": "2026-01-13T14:30:00Z",
  "level": "INFO",
  "event": "data_extraction",
  "user_id": "user_123",
  "center_id": "center_01",
  "action": "extract_chart_entries",
  "date_range": "2022-01-18",
  "record_count": 6,
  "duration_ms": 23,
  "ip_address": "10.0.1.50",
  "user_agent": "IvorisExtractor/1.0",
  "legal_basis": "legitimate_interest",
  "correlation_id": "req_abc123"
}
```

### Log Shipping

```yaml
# Production: ship to SIEM
logging:
  handlers:
    - type: stdout
      format: json
    - type: elasticsearch
      host: https://logs.example.com
      index: ivoris-audit
    - type: s3
      bucket: ivoris-audit-logs
      retention_days: 730  # 2 years
```

### Sensitive Data in Logs

```python
# NEVER log patient data
logger.info(f"Extracted {count} records")  # ✓ OK
logger.info(f"Patient {patient_id} data: {data}")  # ❌ NEVER

# Mask sensitive values
logger.info(f"Connected with user {mask(username)}")  # ✓ OK
```

---

## Security Checklist

### Before Development

- [ ] Data classification completed
- [ ] Legal basis documented
- [ ] DPA signed with each center

### Before Production

- [ ] Secrets moved to secrets manager
- [ ] SSL/TLS enabled and verified
- [ ] Authentication implemented
- [ ] Authorization rules defined
- [ ] Audit logging enabled
- [ ] Network segmentation configured
- [ ] Firewall rules reviewed
- [ ] Penetration test completed

### Ongoing

- [ ] Secret rotation on schedule
- [ ] Access reviews quarterly
- [ ] Log monitoring active
- [ ] Vulnerability scanning
- [ ] Security training for team

---

## Incident Response

### Classification

| Severity | Definition | Response Time |
|----------|------------|---------------|
| P1 - Critical | Data breach, system compromise | 15 minutes |
| P2 - High | Authentication bypass, privilege escalation | 1 hour |
| P3 - Medium | Suspicious activity, failed attacks | 4 hours |
| P4 - Low | Policy violation, configuration issue | 24 hours |

### Response Steps

1. **Detect** - Monitoring alert or report
2. **Contain** - Isolate affected systems
3. **Investigate** - Determine scope and cause
4. **Remediate** - Fix vulnerability
5. **Recover** - Restore normal operations
6. **Report** - Notify stakeholders, regulators if required

### Breach Notification

| Stakeholder | Timeframe | Method |
|-------------|-----------|--------|
| Internal security team | Immediately | Pager/Slack |
| Management | 4 hours | Email + call |
| Affected centers | 24 hours | Formal notice |
| Regulators (if required) | 72 hours | Official filing |
| Data subjects (if required) | Without undue delay | Written notice |

### Contact Information

```yaml
# Incident contacts (example)
security_team:
  email: security@example.com
  phone: +49-xxx-xxx-xxxx
  slack: #security-incidents

dpo:  # Data Protection Officer
  name: "[Name]"
  email: dpo@example.com
  phone: +49-xxx-xxx-xxxx
```

---

## Summary

### Security Priorities

| Priority | Item | Status |
|----------|------|--------|
| P0 | Move secrets out of code | Required for production |
| P0 | Enable TLS | Required for production |
| P0 | Implement authentication | Required for production |
| P1 | Add audit logging | Required for compliance |
| P1 | Document legal basis | Required for GDPR |
| P2 | Network segmentation | Recommended |
| P2 | Penetration testing | Recommended |

### Key Message

> **Security is not optional for healthcare data.** This pipeline handles PHI/PII from dental patients across three countries. GDPR compliance, proper authentication, and audit logging are non-negotiable for production deployment.
