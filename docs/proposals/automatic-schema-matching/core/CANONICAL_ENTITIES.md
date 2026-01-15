# Canonical Entities: Target Schema Definition

**Purpose:** Define the standard entities we map source columns to
**Domain:** Dental Practice Management (Ivoris-based)

---

## Overview

Canonical entities are the **target** of schema matching. Source database columns (PATNR, PAT_NR, PATIENTENNUMMER) map to canonical entities (patient_id).

```
Source Columns          Canonical Entity
─────────────────       ─────────────────
PATNR            ─┐
PAT_NR           ─┼────▶  patient_id
PATIENTENNUMMER  ─┘
```

---

## Entity Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **Patient** | Patient identification and demographics | patient_id, birth_date, gender |
| **Insurance** | Insurance and billing | insurance_id, insurance_type |
| **Clinical** | Medical/dental records | chart_note, diagnosis_code |
| **Appointment** | Scheduling | appointment_date, provider_id |
| **Financial** | Billing and payments | invoice_amount, payment_date |
| **System** | Technical/metadata | created_at, modified_by |

---

## Patient Entities

### patient_id

| Attribute | Value |
|-----------|-------|
| **Category** | Patient |
| **Data Type** | INTEGER or VARCHAR |
| **Is Critical** | Yes - always requires review in conservative mode |
| **Description** | Unique identifier for a patient |

**Known Variants:**
| Variant | Occurrence | Source |
|---------|------------|--------|
| PATNR | High | German Ivoris |
| PAT_NR | Medium | Modified Ivoris |
| PATIENTENNUMMER | Low | Full German |
| PAT_ID | Medium | English |
| PATIENT_ID | Medium | English |
| PATIENTNR | Low | German variant |

**Value Patterns:**
- Sequential integers (1001, 1002, 1003...)
- Prefixed IDs (P-1001, PAT-1002)
- UUIDs (rare)

---

### birth_date

| Attribute | Value |
|-----------|-------|
| **Category** | Patient |
| **Data Type** | DATE, VARCHAR(8), VARCHAR(10) |
| **Is Critical** | Yes |
| **Description** | Patient's date of birth |

**Known Variants:**
| Variant | Occurrence | Source |
|---------|------------|--------|
| GEBDAT | High | German abbreviation |
| GEBURTSDATUM | Medium | Full German |
| GEB_DATUM | Low | German with underscore |
| DOB | Medium | English |
| BIRTH_DATE | Medium | English |
| DATE_OF_BIRTH | Low | Full English |
| GEBURTSTAG | Low | German (birthday) |

**Value Patterns:**
- YYYYMMDD (19850315)
- YYYY-MM-DD (1985-03-15)
- DD.MM.YYYY (15.03.1985) - German format
- Native DATE type

---

### patient_name

| Attribute | Value |
|-----------|-------|
| **Category** | Patient |
| **Data Type** | VARCHAR |
| **Is Critical** | Yes (PII) |
| **Description** | Patient's name (may be split or combined) |

**Known Variants:**
| Variant | Occurrence | Source |
|---------|------------|--------|
| NAME | High | Generic |
| PATNAME | Medium | Combined |
| NACHNAME | Medium | German (last name) |
| VORNAME | Medium | German (first name) |
| LASTNAME | Medium | English |
| FIRSTNAME | Medium | English |
| FULLNAME | Low | Combined |

**Sub-entities:**
- patient_first_name
- patient_last_name
- patient_full_name

---

### gender

| Attribute | Value |
|-----------|-------|
| **Category** | Patient |
| **Data Type** | VARCHAR(1), VARCHAR(10), INTEGER |
| **Is Critical** | No |
| **Description** | Patient's gender |

**Known Variants:**
| Variant | Occurrence | Source |
|---------|------------|--------|
| GESCHLECHT | High | German |
| SEX | Medium | English |
| GENDER | Medium | English |
| ANREDE | Low | German (salutation) |

**Value Patterns:**
- M/F/D (Male/Female/Diverse)
- 1/2/3 (coded)
- männlich/weiblich (German)
- Herr/Frau (Mr/Mrs)

---

## Insurance Entities

### insurance_id

| Attribute | Value |
|-----------|-------|
| **Category** | Insurance |
| **Data Type** | INTEGER, VARCHAR |
| **Is Critical** | Yes |
| **Description** | Reference to insurance company |

**Known Variants:**
| Variant | Occurrence | Source |
|---------|------------|--------|
| KASSENR | High | German |
| KASSE_ID | Medium | German |
| INSURANCE_ID | Medium | English |
| VERSICHERUNG_ID | Low | Full German |
| PAYER_ID | Low | US terminology |

---

### insurance_name

| Attribute | Value |
|-----------|-------|
| **Category** | Insurance |
| **Data Type** | VARCHAR |
| **Is Critical** | No |
| **Description** | Name of insurance company |

**Known Variants:**
| Variant | Occurrence | Source |
|---------|------------|--------|
| KASSE | High | German |
| KASSENNAME | Medium | German |
| VERSICHERUNG | Medium | Full German |
| INSURANCE | Medium | English |
| INSURANCE_NAME | Low | English |
| PAYER | Low | US terminology |

**Value Patterns:**
- German insurers: AOK, DAK, BARMER, TK, IKK
- Private: Debeka, DKV, Allianz
- Foreign: CSS, Sanitas (Swiss)

---

### insurance_type

| Attribute | Value |
|-----------|-------|
| **Category** | Insurance |
| **Data Type** | VARCHAR, INTEGER |
| **Is Critical** | No |
| **Description** | Type/class of insurance |

**Known Variants:**
| Variant | Occurrence | Source |
|---------|------------|--------|
| KASSENART | High | German |
| KASSE_TYP | Medium | German |
| ART | Low | Generic German |
| TYPE | Medium | English |
| INSURANCE_TYPE | Low | English |

**Value Patterns:**
- GKV/PKV (German public/private)
- 1/2/3 (coded)
- gesetzlich/privat (German text)

---

## Clinical Entities

### chart_note

| Attribute | Value |
|-----------|-------|
| **Category** | Clinical |
| **Data Type** | TEXT, VARCHAR(MAX) |
| **Is Critical** | No |
| **Description** | Clinical notes, observations |

**Known Variants:**
| Variant | Occurrence | Source |
|---------|------------|--------|
| BEMERKUNG | High | German |
| NOTIZ | Medium | German |
| ANMERKUNG | Medium | German |
| NOTE | Medium | English |
| NOTES | Medium | English |
| CHART_NOTE | Low | English |
| BEFUND | Low | German (finding) |
| KOMMENTAR | Low | German (comment) |

---

### diagnosis_code

| Attribute | Value |
|-----------|-------|
| **Category** | Clinical |
| **Data Type** | VARCHAR |
| **Is Critical** | No |
| **Description** | ICD or dental diagnosis code |

**Known Variants:**
| Variant | Occurrence | Source |
|---------|------------|--------|
| DIAGNOSE | High | German |
| ICD | Medium | International |
| ICD_CODE | Medium | English |
| DIAGNOSIS | Medium | English |
| BEFUNDNR | Low | German |

---

### procedure_code

| Attribute | Value |
|-----------|-------|
| **Category** | Clinical |
| **Data Type** | VARCHAR |
| **Is Critical** | No |
| **Description** | Procedure/treatment code (BEMA, GOZ) |

**Known Variants:**
| Variant | Occurrence | Source |
|---------|------------|--------|
| LEISTUNG | High | German |
| BEMA | Medium | German dental code |
| GOZ | Medium | German private dental |
| PROCEDURE | Medium | English |
| CPT | Low | US coding |

---

## Appointment Entities

### appointment_date

| Attribute | Value |
|-----------|-------|
| **Category** | Appointment |
| **Data Type** | DATE, DATETIME |
| **Is Critical** | No |
| **Description** | Date/time of appointment |

**Known Variants:**
| Variant | Occurrence | Source |
|---------|------------|--------|
| TERMIN | High | German |
| TERMINDATUM | Medium | German |
| DATUM | Medium | Generic German |
| APPOINTMENT | Medium | English |
| APPT_DATE | Low | English abbreviation |

---

### provider_id

| Attribute | Value |
|-----------|-------|
| **Category** | Appointment |
| **Data Type** | INTEGER, VARCHAR |
| **Is Critical** | No |
| **Description** | Reference to treating provider |

**Known Variants:**
| Variant | Occurrence | Source |
|---------|------------|--------|
| BEHANDLER | High | German |
| ARZT | Medium | German (doctor) |
| ZAHNARZT | Medium | German (dentist) |
| PROVIDER | Medium | English |
| DOCTOR_ID | Low | English |

---

## System Entities

### created_at

| Attribute | Value |
|-----------|-------|
| **Category** | System |
| **Data Type** | DATETIME, TIMESTAMP |
| **Is Critical** | No |
| **Description** | Record creation timestamp |

**Known Variants:**
| Variant | Occurrence | Source |
|---------|------------|--------|
| ERSTELLT | High | German |
| ANGELEGT | Medium | German |
| CREATED | Medium | English |
| CREATED_AT | Medium | English |
| ERSTELLDATUM | Low | German |

---

### modified_at

| Attribute | Value |
|-----------|-------|
| **Category** | System |
| **Data Type** | DATETIME, TIMESTAMP |
| **Is Critical** | No |
| **Description** | Last modification timestamp |

**Known Variants:**
| Variant | Occurrence | Source |
|---------|------------|--------|
| GEAENDERT | High | German |
| MODIFIED | Medium | English |
| UPDATED | Medium | English |
| UPDATED_AT | Medium | English |
| LAST_MODIFIED | Low | English |

---

### is_deleted

| Attribute | Value |
|-----------|-------|
| **Category** | System |
| **Data Type** | BIT, BOOLEAN, INTEGER |
| **Is Critical** | No |
| **Description** | Soft delete flag |

**Known Variants:**
| Variant | Occurrence | Source |
|---------|------------|--------|
| DELKZ | High | German (delete flag) |
| GELOESCHT | Medium | German |
| DELETED | Medium | English |
| IS_DELETED | Medium | English |
| AKTIV | Low | German (active - inverted) |

---

## Entity Summary

### Critical Entities (Always Review)

| Entity | Reason |
|--------|--------|
| patient_id | Core identifier, errors propagate |
| birth_date | PII, compliance |
| patient_name | PII, compliance |
| insurance_id | Billing accuracy |

### High-Value Entities

| Entity | Reason |
|--------|--------|
| insurance_type | Business logic depends on it |
| diagnosis_code | Clinical accuracy |
| procedure_code | Billing accuracy |

### Common Problem Entities

| Entity | Problem | Solution |
|--------|---------|----------|
| patient_name | Often split into first/last | Map to sub-entities |
| birth_date | Multiple date formats | Pattern detection |
| is_deleted | Inverted logic (AKTIV) | Check sample values |

---

## Usage in System

### Seeding the Database

```sql
INSERT INTO canonical_entities (name, category, data_type, is_critical) VALUES
('patient_id', 'patient', 'integer', true),
('birth_date', 'patient', 'date', true),
('patient_name', 'patient', 'string', true),
('patient_first_name', 'patient', 'string', true),
('patient_last_name', 'patient', 'string', true),
('gender', 'patient', 'string', false),
('insurance_id', 'insurance', 'integer', true),
('insurance_name', 'insurance', 'string', false),
('insurance_type', 'insurance', 'string', false),
('chart_note', 'clinical', 'text', false),
('diagnosis_code', 'clinical', 'string', false),
('procedure_code', 'clinical', 'string', false),
('appointment_date', 'appointment', 'datetime', false),
('provider_id', 'appointment', 'integer', false),
('created_at', 'system', 'datetime', false),
('modified_at', 'system', 'datetime', false),
('is_deleted', 'system', 'boolean', false);
```

### Seeding Known Variants

```sql
INSERT INTO column_variants (entity_id, column_name, confidence, status) VALUES
-- patient_id variants
((SELECT id FROM canonical_entities WHERE name = 'patient_id'), 'PATNR', 1.0, 'verified'),
((SELECT id FROM canonical_entities WHERE name = 'patient_id'), 'PAT_NR', 1.0, 'verified'),
((SELECT id FROM canonical_entities WHERE name = 'patient_id'), 'PATIENTENNUMMER', 1.0, 'verified'),
-- birth_date variants
((SELECT id FROM canonical_entities WHERE name = 'birth_date'), 'GEBDAT', 1.0, 'verified'),
((SELECT id FROM canonical_entities WHERE name = 'birth_date'), 'GEBURTSDATUM', 1.0, 'verified'),
-- ... etc
```

---

## Extending the Schema

### Adding New Entities

1. Identify the business concept
2. Determine category and data type
3. Mark critical if PII or core identifier
4. Document known variants
5. Add to database seed
6. Update this document

### Adding New Variants

When discovered through matching:
1. Human verifies the mapping
2. System adds to column_variants
3. Increment occurrence_count if seen again

---

*This document is the source of truth for what we're mapping to.*
