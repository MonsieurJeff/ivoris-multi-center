# Implementation

Code architecture and operational considerations for the schema matching pipeline.

---

## Recommended Project Structure

```
dental-schema-matcher/
├── profiler/
│   ├── __init__.py
│   ├── schema_profiler.py      # Extract rich profiles from any DB
│   ├── pattern_detector.py     # Detect data patterns
│   └── sql/
│       └── profile_templates.sql
│
├── classifier/
│   ├── __init__.py
│   ├── llm_classifier.py       # LLM-based semantic classification
│   ├── batch_classifier.py     # Efficient batch processing
│   └── prompts/
│       ├── column_classifier.txt
│       ├── table_classifier.txt
│       └── batch_classifier.txt
│
├── matcher/
│   ├── __init__.py
│   ├── canonical_schema.yml    # Golden reference schema
│   ├── cross_db_matcher.py     # Match against canonical
│   ├── similarity.py           # String similarity algorithms
│   └── known_mappings/         # Learned from each center
│       ├── center_munich.yml
│       ├── center_berlin.yml
│       └── center_hamburg.yml
│
├── validator/
│   ├── __init__.py
│   ├── mapping_validator.py    # Test mappings with real queries
│   ├── validation_tests.py     # Individual test implementations
│   └── report_generator.py     # Generate validation reports
│
├── pipeline/
│   ├── __init__.py
│   ├── orchestrator.py         # Run full 4-phase pipeline
│   └── config.yml              # Pipeline configuration
│
├── reports/
│   └── mapping_report.py       # Generate confidence reports
│
└── cli.py                      # Command-line interface
```

---

## Pipeline Orchestration

```python
class SchemaMappingPipeline:
    """Orchestrate the 4-phase schema matching pipeline"""

    def __init__(self, config: dict):
        self.profiler = SchemaProfiler(config['db_connection'])
        self.classifier = SchemaClassifier(config['llm_client'])
        self.matcher = CrossDatabaseMatcher(config['canonical_schema'])
        self.validator = MappingValidator(config['db_connection'])

    def run(self, target_schema: str, center_id: str) -> dict:
        """Run full pipeline on a new database"""

        # Phase 1: Profile
        print("Phase 1: Profiling schema...")
        profiles = self.profiler.profile_schema(target_schema)
        print(f"  Profiled {len(profiles)} columns")

        # Phase 2: LLM Classification
        print("Phase 2: LLM classification...")
        classifications = self.classifier.classify_batch(profiles)
        print(f"  Classified {len(classifications)} columns")

        # Phase 3: Cross-Database Matching
        print("Phase 3: Cross-database matching...")
        mappings = []
        for profile, classification in zip(profiles, classifications):
            mapping = self.matcher.match_column(profile, classification)
            mappings.append(mapping)

        high_conf = sum(1 for m in mappings if m.confidence >= 0.85)
        print(f"  {high_conf} high-confidence matches")

        # Phase 4: Validation
        print("Phase 4: Validating mappings...")
        mapping_dict = self._mappings_to_dict(mappings)
        validation_results = self.validator.validate_mapping(mapping_dict)

        passed = sum(1 for r in validation_results if r.passed)
        print(f"  {passed}/{len(validation_results)} validations passed")

        # Generate report
        report = {
            'center_id': center_id,
            'schema': target_schema,
            'profiles': profiles,
            'classifications': classifications,
            'mappings': mappings,
            'validation': validation_results,
            'recommendation': self._get_recommendation(mappings, validation_results)
        }

        return report
```

---

## LLM Considerations

### Operational Model

**Key insight:** LLM classification happens only at client onboarding, not during daily operations.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      OPERATIONAL LIFECYCLE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  CLIENT ONBOARDING (One-time)                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ 1. Profile schema                                                 │   │
│  │ 2. LLM classifies UNKNOWN columns only                           │   │
│  │ 3. Human reviews and confirms mappings                           │   │
│  │ 4. Validated mappings stored in database                         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│                              ▼                                           │
│  DAILY OPERATIONS (Recurring)                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ • Load human-verified mappings from storage                      │   │
│  │ • Execute extraction query                                        │   │
│  │ • NO LLM calls required                                          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  SCHEMA UPDATE (Rare)                                                   │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ • Detect new/changed columns                                      │   │
│  │ • LLM classifies only the DELTA                                  │   │
│  │ • Human confirms new mappings                                     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| **API Cost** | One-time at onboarding; batch columns (10-20 per call); reuse across clients |
| **Hallucination** | Human review required before storing; Phase 4 validation catches errors |
| **Privacy** | Use local LLM (Llama, Mistral) or anonymize sample values before sending |
| **Latency** | Not a concern - onboarding is async, not blocking daily operations |
| **Rate Limits** | Implement retry with exponential backoff for onboarding batch |

### Cost Analysis

| Scenario | LLM Calls | Cost (Claude Haiku) |
|----------|-----------|---------------------|
| First client (487 tables, ~2000 columns) | ~100 batched calls | ~$0.50 |
| Subsequent client (90% known columns) | ~10-20 calls | ~$0.05 |
| Daily extraction | 0 calls | $0.00 |
| Schema update (5 new columns) | 1 call | ~$0.005 |

**Annual cost for 10 clients:** < $5.00 total

### Filtering Logic

```python
def filter_columns_for_llm(profiles: list, canonical: dict, verified_mappings: dict) -> list:
    """Only send truly unknown columns to LLM"""

    needs_llm = []

    for profile in profiles:
        column_key = f"{profile['table']}.{profile['column']}"

        # 1. Already human-verified? Skip LLM
        if column_key in verified_mappings:
            continue

        # 2. Exact match in canonical known_names? Skip LLM
        if is_in_canonical(profile['column'], canonical):
            continue

        # 3. Previously classified (same column name from another client)? Skip LLM
        if profile['column'] in classification_cache:
            continue

        # 4. Truly unknown - needs LLM classification
        needs_llm.append(profile)

    return needs_llm
```

### Local LLM Option

For sensitive data, use local models:

```python
# Using Ollama with local Llama model
from langchain.llms import Ollama

classifier = SchemaClassifier(
    client=Ollama(model="llama2:13b"),
    model="local"
)

# Or using vLLM for faster inference
from vllm import LLM

local_llm = LLM(model="meta-llama/Llama-2-13b-chat-hf")
```

---

**Next:** [ML Enhancement](06-ml-enhancement.md) - Machine learning for improved matching at scale.
