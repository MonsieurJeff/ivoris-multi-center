# Validation

Phase 4 of the pipeline: Auto-validation and confidence scoring for schema mappings.

---

## Phase 4: Auto-Validation

### Goal
Verify proposed mappings with actual data before accepting them.

### Validation Tests

```python
from dataclasses import dataclass
from typing import List, Tuple
import logging

@dataclass
class ValidationResult:
    test_name: str
    passed: bool
    message: str
    severity: str  # 'error', 'warning', 'info'

class MappingValidator:
    def __init__(self, db_connection):
        self.db = db_connection
        self.logger = logging.getLogger(__name__)

    def validate_mapping(self, mapping: dict) -> List[ValidationResult]:
        """Run all validation tests on a proposed mapping"""
        results = []

        # Test 1: FK relationships work
        if mapping.get('patient_id') and mapping.get('chart_table'):
            results.append(self._test_fk_join(mapping))

        # Test 2: Date column has valid dates
        if mapping.get('date_column'):
            results.append(self._test_date_validity(mapping))

        # Test 3: Insurance values match expected patterns
        if mapping.get('insurance_type'):
            results.append(self._test_insurance_values(mapping))

        # Test 4: Soft delete filter works
        if mapping.get('soft_delete'):
            results.append(self._test_soft_delete(mapping))

        # Test 5: Sample extraction query works
        results.append(self._test_extraction_query(mapping))

        return results

    def _test_fk_join(self, mapping: dict) -> ValidationResult:
        """Test that FK relationships produce valid joins"""
        try:
            query = f"""
                SELECT COUNT(*) as cnt
                FROM {mapping['chart_table']} c
                JOIN {mapping['patient_table']} p
                ON c.{mapping['patient_id']} = p.{mapping['patient_pk']}
            """
            result = self.db.execute(query).fetchone()

            if result['cnt'] > 0:
                return ValidationResult(
                    "fk_join", True,
                    f"FK join produced {result['cnt']} rows",
                    "info"
                )
            else:
                return ValidationResult(
                    "fk_join", False,
                    "FK join produced 0 rows - check relationship",
                    "error"
                )
        except Exception as e:
            return ValidationResult(
                "fk_join", False,
                f"FK join failed: {str(e)}",
                "error"
            )

    def _test_date_validity(self, mapping: dict) -> ValidationResult:
        """Test that date column contains valid dates"""
        try:
            # Check for YYYYMMDD format
            query = f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE
                        WHEN TRY_CONVERT(DATE,
                            SUBSTRING({mapping['date_column']}, 1, 4) + '-' +
                            SUBSTRING({mapping['date_column']}, 5, 2) + '-' +
                            SUBSTRING({mapping['date_column']}, 7, 2)
                        ) IS NOT NULL THEN 1
                        ELSE 0
                    END) as valid_dates
                FROM {mapping['chart_table']}
                WHERE {mapping['date_column']} IS NOT NULL
            """
            result = self.db.execute(query).fetchone()

            pct = result['valid_dates'] / result['total'] * 100 if result['total'] > 0 else 0

            if pct > 95:
                return ValidationResult(
                    "date_validity", True,
                    f"{pct:.1f}% of dates are valid YYYYMMDD",
                    "info"
                )
            elif pct > 80:
                return ValidationResult(
                    "date_validity", True,
                    f"{pct:.1f}% valid - some invalid dates present",
                    "warning"
                )
            else:
                return ValidationResult(
                    "date_validity", False,
                    f"Only {pct:.1f}% valid - check date format",
                    "error"
                )
        except Exception as e:
            return ValidationResult(
                "date_validity", False,
                f"Date validation failed: {str(e)}",
                "error"
            )

    def _test_insurance_values(self, mapping: dict) -> ValidationResult:
        """Test that insurance type values match expected patterns"""
        try:
            query = f"""
                SELECT DISTINCT {mapping['insurance_type']} as val
                FROM {mapping['insurance_table']}
                WHERE {mapping['insurance_type']} IS NOT NULL
            """
            results = self.db.execute(query).fetchall()
            values = [r['val'] for r in results]

            expected = ['P', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'G', 'GKV', 'PKV']
            matches = [v for v in values if v in expected]

            if len(matches) > 0:
                return ValidationResult(
                    "insurance_values", True,
                    f"Found expected values: {matches[:5]}",
                    "info"
                )
            else:
                return ValidationResult(
                    "insurance_values", False,
                    f"Unexpected values: {values[:5]} - verify mapping",
                    "warning"
                )
        except Exception as e:
            return ValidationResult(
                "insurance_values", False,
                f"Insurance validation failed: {str(e)}",
                "error"
            )

    def _test_soft_delete(self, mapping: dict) -> ValidationResult:
        """Test that soft delete filter works"""
        try:
            query = f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN {mapping['soft_delete']} = 0
                             OR {mapping['soft_delete']} IS NULL
                        THEN 1 ELSE 0 END) as active
                FROM {mapping['chart_table']}
            """
            result = self.db.execute(query).fetchone()

            deleted_pct = (result['total'] - result['active']) / result['total'] * 100

            return ValidationResult(
                "soft_delete", True,
                f"{result['active']} active of {result['total']} total ({deleted_pct:.1f}% soft-deleted)",
                "info"
            )
        except Exception as e:
            return ValidationResult(
                "soft_delete", False,
                f"Soft delete test failed: {str(e)}",
                "warning"
            )

    def _test_extraction_query(self, mapping: dict) -> ValidationResult:
        """Test that the full extraction query works"""
        try:
            # Build and test extraction query
            query = self._build_extraction_query(mapping)
            result = self.db.execute(f"SELECT TOP 5 * FROM ({query}) t").fetchall()

            if len(result) > 0:
                return ValidationResult(
                    "extraction_query", True,
                    f"Extraction query returned {len(result)} sample rows",
                    "info"
                )
            else:
                return ValidationResult(
                    "extraction_query", False,
                    "Extraction query returned 0 rows",
                    "warning"
                )
        except Exception as e:
            return ValidationResult(
                "extraction_query", False,
                f"Extraction query failed: {str(e)}",
                "error"
            )

    def _build_extraction_query(self, mapping: dict) -> str:
        """Build extraction query from mapping"""
        # Implementation depends on mapping structure
        pass
```

---

## Validation Report

```python
def generate_validation_report(mappings: dict, results: List[ValidationResult]) -> str:
    """Generate human-readable validation report"""

    report = []
    report.append("=" * 60)
    report.append("SCHEMA MAPPING VALIDATION REPORT")
    report.append("=" * 60)
    report.append("")

    # Summary
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    report.append(f"Total Tests: {len(results)}")
    report.append(f"Passed: {passed}")
    report.append(f"Failed: {failed}")
    report.append("")

    # Details by severity
    errors = [r for r in results if r.severity == 'error' and not r.passed]
    warnings = [r for r in results if r.severity == 'warning']

    if errors:
        report.append("ERRORS (Must Fix):")
        for e in errors:
            report.append(f"  - [{e.test_name}] {e.message}")
        report.append("")

    if warnings:
        report.append("WARNINGS (Review):")
        for w in warnings:
            report.append(f"  - [{w.test_name}] {w.message}")
        report.append("")

    # Confidence assessment
    if failed == 0:
        report.append("RECOMMENDATION: Mapping validated - ready for production")
    elif len(errors) == 0:
        report.append("RECOMMENDATION: Mapping acceptable with warnings - review before production")
    else:
        report.append("RECOMMENDATION: Mapping has errors - requires investigation")

    return "\n".join(report)
```

---

## Confidence Scoring

### Combined Scoring Model

With value banks, the scoring weights shift to prioritize learned data over LLM calls:

| Signal | Weight | Source | Notes |
|--------|--------|--------|-------|
| **Value bank match** | **40%** | Verified values from previous clients | Primary signal |
| Column name match | 25% | Known variants in canonical schema | Fast lookup |
| Data type match | 20% | Profile vs expected types | Structural validation |
| Cross-DB consistency | 15% | Same mapping across centers | Reinforcement |
| LLM semantic match | *Fallback* | GPT-4/Claude classification | Only if above signals inconclusive |

**Key change:** LLM is no longer in the weighted scoring - it's a **fallback** when other signals don't reach the confidence threshold.

### Matching Priority Order

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      MATCHING PRIORITY LADDER                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. COLUMN NAME (Exact match in known variants)                         │
│     └─ Score ≥ 0.90 → Auto-accept, no further checks                   │
│                                                                          │
│  2. VALUE BANK (Sample values match verified bank)                      │
│     └─ Score ≥ 0.80 → Auto-accept, no LLM needed                       │
│                                                                          │
│  3. COMBINED SIGNALS (Name + Values + Type + Cross-DB)                  │
│     └─ Score ≥ 0.75 → Auto-accept, no LLM needed                       │
│                                                                          │
│  4. LLM CLASSIFICATION (Fallback for unknown columns)                   │
│     └─ Only reached if signals 1-3 are below thresholds                │
│     └─ Result still requires human verification                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Confidence Thresholds

| Score | Action | Human Review |
|-------|--------|--------------|
| **>= 0.85** | Auto-accept | None required |
| **0.60 - 0.84** | Flag for confirmation | Quick review |
| **< 0.60** | Requires investigation | Full analysis |

### Decision Matrix

```python
def recommend_action(mapping: ColumnMapping, validation_results: List[ValidationResult]) -> str:
    """Recommend action based on confidence and validation"""

    validation_passed = all(r.passed or r.severity != 'error' for r in validation_results)

    if mapping.confidence >= 0.85 and validation_passed:
        return "AUTO_ACCEPT"
    elif mapping.confidence >= 0.60 and validation_passed:
        return "QUICK_REVIEW"
    elif mapping.confidence >= 0.60 and not validation_passed:
        return "INVESTIGATE_VALIDATION"
    else:
        return "MANUAL_ANALYSIS"
```

---

## Human-in-the-Loop Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    HUMAN VERIFICATION WORKFLOW                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  LLM Classification Output                                              │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────────────┐                                                    │
│  │ Confidence ≥85% │──▶ Present to human: "Auto-accept? [Y/n]"         │
│  └─────────────────┘         │                                          │
│       │                      ▼                                          │
│       │               Human confirms ──▶ Store as VERIFIED              │
│       │                                                                  │
│  ┌─────────────────┐                                                    │
│  │ Confidence 60-84│──▶ Present to human: "LLM suggests X. Correct?"   │
│  └─────────────────┘         │                                          │
│       │                      ▼                                          │
│       │               Human corrects/confirms ──▶ Store as VERIFIED     │
│       │                                                                  │
│  ┌─────────────────┐                                                    │
│  │ Confidence <60% │──▶ Present to human: "Unknown column. Classify:"  │
│  └─────────────────┘         │                                          │
│                              ▼                                          │
│                        Human provides mapping ──▶ Store as VERIFIED     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

Once verified, mappings are **never re-classified** unless explicitly invalidated.

---

**Next:** [Implementation](05-implementation.md) - Code architecture and LLM considerations.
