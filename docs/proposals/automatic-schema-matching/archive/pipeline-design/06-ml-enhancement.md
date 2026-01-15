# ML Enhancement

Machine learning techniques to improve schema matching at scale.

---

## ML Viability by Data Scale

Not all ML techniques require the same amount of data. Here's when each becomes viable:

| Technique | Min Examples | Min Databases | Training Required |
|-----------|--------------|---------------|-------------------|
| **Rule-based + LLM** | 0 | 1 | No |
| **Embeddings (pre-trained)** | 0 | 1 | No - uses existing models |
| **Few-shot LLM prompting** | 10-50 | 3-5 | No - examples in prompt |
| **Traditional ML (RF/XGBoost)** | 100+ per class | 30-50 | Yes |
| **Fine-tuned classifier** | 500+ | 100+ | Yes |
| **Deep learning from scratch** | 5000+ | 500+ | Yes - not practical |

### Data Scale Calculation

```
Databases × Relevant Columns = Training Examples

15 databases × 50 columns = 750 examples   → Embeddings + Few-shot
50 databases × 50 columns = 2500 examples  → Traditional ML viable
200 databases × 50 columns = 10000 examples → Fine-tuning viable
```

---

## Enhancement 1: Embedding-Based Value Matching

Use pre-trained sentence embeddings for **fuzzy value matching** without any training.

**Why it works:**
- Pre-trained on billions of text examples
- Multilingual models understand German
- Handles typos, abbreviations, variations
- "DAK Gesundheit" ≈ "DAK-Gesundheit" ≈ "DAK" (similarity ~0.85)

```python
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Dict, List, Tuple

class EmbeddingMatcher:
    """Use pre-trained embeddings for semantic value matching"""

    def __init__(self, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        # Pre-trained multilingual model (handles German)
        self.model = SentenceTransformer(model_name)
        self.value_embeddings: Dict[str, Dict[str, np.ndarray]] = {}
        self.indexed = False

    def index_value_bank(self, value_bank: Dict[str, List[str]]):
        """Pre-compute embeddings for all verified values (run once at startup)"""
        print(f"Indexing {sum(len(v) for v in value_bank.values())} values...")

        for entity, values in value_bank.items():
            self.value_embeddings[entity] = {}
            # Batch encode for efficiency
            embeddings = self.model.encode([str(v) for v in values])
            for value, embedding in zip(values, embeddings):
                self.value_embeddings[entity][str(value)] = embedding

        self.indexed = True
        print(f"Indexed {len(self.value_embeddings)} entities")

    def find_similar_values(self, sample_values: List[str],
                           threshold: float = 0.7) -> Dict[str, float]:
        """Find which entity's value bank is most similar to samples"""
        if not self.indexed:
            raise RuntimeError("Call index_value_bank() first")

        # Encode sample values
        sample_embeddings = self.model.encode([str(v) for v in sample_values])

        entity_scores = {}
        for entity, value_embs in self.value_embeddings.items():
            if not value_embs:
                continue

            similarities = []
            for sample_emb in sample_embeddings:
                # Find best match in this entity's bank
                best_sim = max(
                    self._cosine_similarity(sample_emb, v_emb)
                    for v_emb in value_embs.values()
                )
                similarities.append(best_sim)

            # Average similarity across samples
            avg_score = np.mean(similarities)
            if avg_score >= threshold:
                entity_scores[entity] = float(avg_score)

        return dict(sorted(entity_scores.items(), key=lambda x: -x[1]))

    def find_best_match(self, sample_values: List[str]) -> Tuple[str, float, List[str]]:
        """Find the single best matching entity"""
        scores = self.find_similar_values(sample_values, threshold=0.5)

        if not scores:
            return None, 0.0, []

        best_entity = max(scores, key=scores.get)
        best_score = scores[best_entity]

        # Find which specific values matched
        matched = []
        bank = self.value_embeddings[best_entity]
        sample_embs = self.model.encode([str(v) for v in sample_values])

        for sample, sample_emb in zip(sample_values, sample_embs):
            for bank_value, bank_emb in bank.items():
                if self._cosine_similarity(sample_emb, bank_emb) >= 0.8:
                    matched.append(f"{sample} ≈ {bank_value}")
                    break

        return best_entity, best_score, matched

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# Usage example
embedding_matcher = EmbeddingMatcher()
embedding_matcher.index_value_bank({
    'insurance_name': ['DAK Gesundheit', 'AOK Bayern', 'BARMER', 'Techniker Krankenkasse'],
    'insurance_type': ['P', 'GKV', 'PKV', '1', '2', '3'],
})

# This will match even with variations
entity, score, matches = embedding_matcher.find_best_match([
    'DAK-Gesundheit',      # Slight variation
    'AOK Baden-Württemberg', # Different AOK
    'TK'                    # Abbreviation
])
# Result: ('insurance_name', 0.82, ['DAK-Gesundheit ≈ DAK Gesundheit', ...])
```

**Integration with matching pipeline:**

```python
def match_with_embeddings(profile: dict, embedding_matcher: EmbeddingMatcher) -> float:
    """Add embedding score to matching signals"""

    entity, score, matches = embedding_matcher.find_best_match(profile['sample_values'])

    if score >= 0.8:
        return {
            'entity': entity,
            'confidence': score,
            'method': 'embedding_match',
            'details': matches
        }

    return None
```

---

## Enhancement 2: Few-Shot LLM Prompting

Include verified examples in LLM prompts to improve accuracy by 10-20%:

```python
class FewShotClassifier:
    """LLM classifier with few-shot examples from verified mappings"""

    def __init__(self, llm_client, verified_mappings_db):
        self.llm = llm_client
        self.db = verified_mappings_db
        self.examples_per_entity = 3

    def get_examples(self) -> str:
        """Build examples section from verified mappings"""
        examples = []

        entities = ['patient_id', 'date', 'insurance_type', 'insurance_name',
                   'chart_note', 'service_code', 'soft_delete']

        for entity in entities:
            verified = self.db.execute("""
                SELECT table_name, column_name, data_type, sample_values
                FROM verified_mappings
                WHERE canonical_entity = ?
                ORDER BY confidence DESC
                LIMIT ?
            """, [entity, self.examples_per_entity]).fetchall()

            for v in verified:
                examples.append(f"""
Example: {v['table_name']}.{v['column_name']}
  Type: {v['data_type']}
  Samples: {v['sample_values'][:50]}...
  → Classification: {entity}""")

        return "\n".join(examples)

    def create_prompt(self, profile: dict) -> str:
        """Create few-shot prompt with verified examples"""

        examples = self.get_examples()

        return f"""You are classifying database columns from German dental practice software.

## Verified Examples from Similar Databases
{examples}

## Column to Classify
Table: {profile['table']}
Column: {profile['column']}
Data Type: {profile['data_type']}
Sample Values: {profile['sample_values'][:5]}
Distinct Count: {profile['distinct_count']} of {profile['total_count']} rows
Null Percentage: {profile['null_pct']}%

## Task
Based on the examples above, classify this column.

Select ONE category:
- patient_id: Unique patient identifier (often ends in ID, NR)
- date: Date field (appointment, treatment, record date)
- insurance_type: Insurance classification code (GKV/PKV, 1-9, P)
- insurance_name: Insurance company name
- chart_note: Medical notes, remarks, comments (BEMERKUNG, NOTIZ)
- service_code: Treatment/procedure codes (LEISTUNG, ZIFFER)
- soft_delete: Deletion flag (DELKZ, DELETED, usually BIT type)
- other: None of the above

## Response (JSON)
{{
  "classification": "<category>",
  "confidence": "high|medium|low",
  "reasoning": "<brief explanation referencing similar examples>"
}}"""

    def classify(self, profile: dict) -> dict:
        """Classify column using few-shot prompt"""
        prompt = self.create_prompt(profile)

        response = self.llm.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        return json.loads(response.content[0].text)
```

**Why few-shot works:**
- LLM sees real examples from your domain
- Learns patterns like "PATNR = patient_id" from context
- No fine-tuning or training required
- Examples update automatically as you verify more mappings

---

## Enhancement 3: Feature Logging for Future ML

Start collecting structured features now to train ML models later:

```python
import re
from datetime import datetime
from typing import Dict, Any
import numpy as np

def extract_ml_features(profile: dict) -> Dict[str, Any]:
    """Extract ML-ready features from column profile"""

    column = profile['column'].upper()
    samples = [str(v) for v in profile['sample_values'] if v is not None]

    features = {
        # === Column Name Features ===
        'name_length': len(column),
        'name_word_count': len(re.findall(r'[A-Z][a-z]+|[A-Z]+(?=[A-Z]|$)', column)),

        # Suffix patterns
        'has_id_suffix': int(column.endswith(('ID', 'NR', 'KEY', 'NUM'))),
        'has_name_suffix': int(column.endswith(('NAME', 'BEZEICHNUNG', 'TEXT'))),
        'has_date_suffix': int(column.endswith(('DATUM', 'DATE', 'DAT', 'TIME'))),
        'has_flag_suffix': int(column.endswith(('KZ', 'FLAG', 'YN', 'BOOL'))),

        # Keyword presence
        'has_patient_keyword': int(any(kw in column for kw in ['PAT', 'PATIENT', 'KUNDE'])),
        'has_insurance_keyword': int(any(kw in column for kw in ['KASSE', 'VERS', 'INS'])),
        'has_delete_keyword': int(any(kw in column for kw in ['DEL', 'GELOE', 'STORNO'])),
        'has_note_keyword': int(any(kw in column for kw in ['BEMERK', 'NOTIZ', 'NOTE', 'TEXT', 'COMMENT'])),
        'has_code_keyword': int(any(kw in column for kw in ['CODE', 'LEIST', 'ZIFFER', 'GEBÜHR'])),
        'has_type_keyword': int(any(kw in column for kw in ['ART', 'TYP', 'TYPE', 'KIND'])),

        # === Data Type Features ===
        'is_int': int(profile['data_type'] in ['int', 'bigint', 'smallint', 'tinyint']),
        'is_varchar': int(profile['data_type'] in ['varchar', 'nvarchar', 'char', 'nchar']),
        'is_text': int(profile['data_type'] in ['text', 'ntext']),
        'is_bit': int(profile['data_type'] == 'bit'),
        'is_date_type': int(profile['data_type'] in ['date', 'datetime', 'datetime2']),
        'is_decimal': int(profile['data_type'] in ['decimal', 'numeric', 'money']),
        'max_length': profile.get('character_maximum_length') or 0,

        # === Statistical Features ===
        'cardinality_ratio': profile['distinct_count'] / max(profile['total_count'], 1),
        'null_percentage': profile['null_pct'],
        'is_unique': int(profile['distinct_count'] == profile['total_count']),
        'is_low_cardinality': int(profile['distinct_count'] < 20),
        'is_high_cardinality': int(profile['distinct_count'] > 1000),

        # === Value Pattern Features ===
        'avg_value_length': np.mean([len(s) for s in samples]) if samples else 0,
        'max_value_length': max([len(s) for s in samples]) if samples else 0,
        'min_value_length': min([len(s) for s in samples]) if samples else 0,

        'all_numeric': int(all(s.replace('.','').replace('-','').isdigit() for s in samples) if samples else False),
        'all_single_char': int(all(len(s) == 1 for s in samples) if samples else False),
        'has_date_pattern_yyyymmdd': int(any(re.match(r'^\d{8}$', s) for s in samples)),
        'has_date_pattern_iso': int(any(re.match(r'^\d{4}-\d{2}-\d{2}', s) for s in samples)),
        'has_german_chars': int(any(c in 'äöüßÄÖÜ' for s in samples for c in s)),
        'has_long_text': int(any(len(s) > 100 for s in samples)),

        # Value distribution hints
        'sample_0_1_only': int(set(samples).issubset({'0', '1', 'True', 'False', 'true', 'false'})),
        'sample_has_p': int('P' in samples or 'p' in samples),
    }

    return features


class MLFeatureLogger:
    """Log features for future ML training"""

    def __init__(self, db_connection):
        self.db = db_connection
        self._ensure_table()

    def _ensure_table(self):
        """Create training data table if not exists"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS ml_training_data (
                id INT IDENTITY PRIMARY KEY,
                client_id VARCHAR(100) NOT NULL,
                table_name VARCHAR(200) NOT NULL,
                column_name VARCHAR(200) NOT NULL,
                canonical_entity VARCHAR(100) NOT NULL,  -- The label
                features NVARCHAR(MAX) NOT NULL,         -- JSON features
                verified_by VARCHAR(100),
                created_at DATETIME DEFAULT GETDATE(),
                UNIQUE(client_id, table_name, column_name)
            )
        """)

    def log_verified_mapping(self, profile: dict, entity: str,
                            client_id: str, verified_by: str = None):
        """Log features + label when a mapping is verified"""
        features = extract_ml_features(profile)

        self.db.execute("""
            INSERT INTO ml_training_data
            (client_id, table_name, column_name, canonical_entity, features, verified_by)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (client_id, table_name, column_name) DO UPDATE
            SET canonical_entity = ?, features = ?, verified_by = ?
        """, [
            client_id, profile['table'], profile['column'],
            entity, json.dumps(features), verified_by,
            entity, json.dumps(features), verified_by
        ])

    def get_training_data(self) -> tuple:
        """Retrieve all logged data for ML training"""
        rows = self.db.execute("""
            SELECT canonical_entity, features
            FROM ml_training_data
        """).fetchall()

        X = [json.loads(r['features']) for r in rows]
        y = [r['canonical_entity'] for r in rows]

        return pd.DataFrame(X), y

    def get_statistics(self) -> dict:
        """Get training data statistics"""
        stats = self.db.execute("""
            SELECT
                canonical_entity,
                COUNT(*) as count,
                COUNT(DISTINCT client_id) as clients
            FROM ml_training_data
            GROUP BY canonical_entity
            ORDER BY count DESC
        """).fetchall()

        return {
            'total_examples': sum(s['count'] for s in stats),
            'per_entity': {s['canonical_entity']: s['count'] for s in stats},
            'clients_per_entity': {s['canonical_entity']: s['clients'] for s in stats}
        }
```

**Integration point - log when human verifies:**

```python
def on_mapping_verified(profile: dict, entity: str, client_id: str, user: str):
    """Called when human confirms a mapping"""

    # 1. Store in value bank (existing)
    value_bank.learn_values(entity, profile['sample_values'], client_id, user)

    # 2. Store column variant (existing)
    store_column_variant(entity, profile['column'], client_id, user)

    # 3. NEW: Log ML features for future training
    ml_logger.log_verified_mapping(profile, entity, client_id, user)
```

---

## Enhancement 4: Traditional ML (When Ready)

When you reach 50+ databases (~2500 examples), add ML classification:

```python
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import classification_report
import pandas as pd
import joblib

class TrainedSchemaClassifier:
    """Traditional ML classifier - use when you have enough data"""

    MIN_EXAMPLES_PER_CLASS = 50
    MIN_TOTAL_EXAMPLES = 500

    def __init__(self):
        self.model = None
        self.feature_columns = None
        self.is_trained = False
        self.training_stats = {}

    def evaluate_readiness(self, X: pd.DataFrame, y: list) -> dict:
        """Check if we have enough data to train"""
        from collections import Counter

        class_counts = Counter(y)

        return {
            'total_examples': len(y),
            'num_classes': len(class_counts),
            'examples_per_class': dict(class_counts),
            'min_class_count': min(class_counts.values()),
            'is_ready': (
                len(y) >= self.MIN_TOTAL_EXAMPLES and
                min(class_counts.values()) >= self.MIN_EXAMPLES_PER_CLASS
            ),
            'recommendation': self._get_recommendation(len(y), min(class_counts.values()))
        }

    def _get_recommendation(self, total: int, min_class: int) -> str:
        if total < self.MIN_TOTAL_EXAMPLES:
            needed = self.MIN_TOTAL_EXAMPLES - total
            return f"Need {needed} more examples total. Continue with rule-based matching."
        if min_class < self.MIN_EXAMPLES_PER_CLASS:
            return f"Some classes have < {self.MIN_EXAMPLES_PER_CLASS} examples. ML may be unreliable for rare classes."
        return "Ready for ML training. Recommend running cross-validation first."

    def train(self, X: pd.DataFrame, y: list, test_size: float = 0.2) -> dict:
        """Train the classifier"""

        # Check readiness
        readiness = self.evaluate_readiness(X, y)
        if not readiness['is_ready']:
            return {'success': False, 'reason': readiness['recommendation']}

        self.feature_columns = X.columns.tolist()

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, stratify=y, random_state=42
        )

        # Cross-validation first
        cv_model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        cv_scores = cross_val_score(cv_model, X_train, y_train, cv=5)

        if cv_scores.mean() < 0.7:
            return {
                'success': False,
                'reason': f'Cross-validation accuracy {cv_scores.mean():.2f} < 0.70 threshold',
                'cv_scores': cv_scores.tolist()
            }

        # Train final model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_leaf=5,
            random_state=42
        )
        self.model.fit(X_train, y_train)

        # Evaluate on test set
        y_pred = self.model.predict(X_test)

        self.is_trained = True
        self.training_stats = {
            'success': True,
            'cv_accuracy': float(cv_scores.mean()),
            'cv_std': float(cv_scores.std()),
            'test_accuracy': float((y_pred == y_test).mean()),
            'classification_report': classification_report(y_test, y_pred, output_dict=True),
            'feature_importance': dict(zip(
                self.feature_columns,
                self.model.feature_importances_.tolist()
            ))
        }

        return self.training_stats

    def predict(self, profile: dict) -> tuple:
        """Predict classification with confidence"""
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call train() first.")

        features = extract_ml_features(profile)
        X = pd.DataFrame([features])[self.feature_columns]

        proba = self.model.predict_proba(X)[0]
        predicted_class = self.model.classes_[proba.argmax()]
        confidence = float(proba.max())

        # Get top 3 predictions
        top_indices = proba.argsort()[-3:][::-1]
        top_predictions = [
            (self.model.classes_[i], float(proba[i]))
            for i in top_indices
        ]

        return predicted_class, confidence, top_predictions

    def save(self, path: str):
        """Save trained model"""
        joblib.dump({
            'model': self.model,
            'feature_columns': self.feature_columns,
            'training_stats': self.training_stats
        }, path)

    def load(self, path: str):
        """Load trained model"""
        data = joblib.load(path)
        self.model = data['model']
        self.feature_columns = data['feature_columns']
        self.training_stats = data['training_stats']
        self.is_trained = True
```

---

## ML Integration Roadmap

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ML INTEGRATION ROADMAP                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PHASE 1: NOW (15 databases, ~750 examples)                             │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ ✅ Rule-based matching (column names, data types)                  │ │
│  │ ✅ Value banks (verified values from previous clients)             │ │
│  │ ✅ LLM fallback (for unknown columns)                              │ │
│  │ 🆕 ADD: Embedding-based value matching (no training needed)        │ │
│  │ 🆕 ADD: Few-shot examples in LLM prompts                           │ │
│  │ 🆕 ADD: Feature logging for future ML                              │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│       │                                                                  │
│       │  Collect data...                                                │
│       ▼                                                                  │
│  PHASE 2: 30-50 databases (~1500-2500 examples)                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ □ Evaluate: Run cross-validation on collected features             │ │
│  │ □ If accuracy ≥ 70%: Add ML as signal (15% weight in scoring)     │ │
│  │ □ If accuracy < 70%: Continue collecting, stay in Phase 1         │ │
│  │ □ Monitor: Track which classes need more examples                  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│       │                                                                  │
│       │  Continue scaling...                                            │
│       ▼                                                                  │
│  PHASE 3: 100+ databases (~5000+ examples)                              │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ □ ML becomes significant signal (25% weight)                       │ │
│  │ □ Consider: Fine-tune small transformer (DistilBERT)              │ │
│  │ □ Consider: Ensemble methods (RF + XGBoost + Embeddings)          │ │
│  │ □ Auto-discovery: Cluster to find new canonical entities          │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│       │                                                                  │
│       ▼                                                                  │
│  PHASE 4: 500+ databases (Enterprise scale)                             │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ □ Full ML pipeline replaces most rule-based matching              │ │
│  │ □ LLM only for truly novel patterns                               │ │
│  │ □ Anomaly detection for schema drift                              │ │
│  │ □ Continuous learning from new verifications                      │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Updated Scoring Model by Phase

**Phase 1 (Now - 15 databases):**

| Signal | Weight | Notes |
|--------|--------|-------|
| Value bank match | 35% | Exact + embedding similarity |
| Column name match | 25% | Known variants |
| Embedding similarity | 20% | Pre-trained, no training |
| Data type match | 15% | Structural validation |
| Cross-DB consistency | 5% | Limited data |
| **LLM** | *Fallback* | If above < 0.70 |

**Phase 2 (50+ databases):**

| Signal | Weight | Notes |
|--------|--------|-------|
| Value bank match | 30% | |
| Column name match | 20% | |
| Embedding similarity | 15% | |
| **ML classifier** | **15%** | NEW |
| Data type match | 10% | |
| Cross-DB consistency | 10% | More reliable now |
| **LLM** | *Fallback* | If above < 0.75 |

**Phase 3 (100+ databases):**

| Signal | Weight | Notes |
|--------|--------|-------|
| **ML classifier** | **25%** | Primary signal |
| Value bank match | 25% | |
| Embedding similarity | 20% | |
| Column name match | 15% | |
| Cross-DB consistency | 10% | |
| Data type match | 5% | |
| **LLM** | *Fallback* | Rarely needed |

---

## Complete Enhanced Matching Pipeline

```python
class EnhancedSchemaMatcher:
    """Complete matching pipeline with all enhancements"""

    def __init__(self, config: dict):
        # Core components
        self.canonical = load_canonical_schema(config['canonical_path'])
        self.value_bank = ValueBank(config['db_connection'])

        # ML enhancements
        self.embedding_matcher = EmbeddingMatcher()
        self.embedding_matcher.index_value_bank(self.value_bank.get_all_values())

        self.few_shot_classifier = FewShotClassifier(
            config['llm_client'],
            config['db_connection']
        )

        self.ml_logger = MLFeatureLogger(config['db_connection'])

        # Optional: trained ML model (Phase 2+)
        self.ml_classifier = None
        if config.get('ml_model_path'):
            self.ml_classifier = TrainedSchemaClassifier()
            self.ml_classifier.load(config['ml_model_path'])

        # Scoring weights (adjust by phase)
        self.weights = config.get('scoring_weights', {
            'value_bank': 0.35,
            'column_name': 0.25,
            'embedding': 0.20,
            'data_type': 0.15,
            'cross_db': 0.05,
            'ml': 0.0  # Enable in Phase 2+
        })

    def match_column(self, profile: dict) -> ColumnMapping:
        """Match a column using all available signals"""

        scores = {}

        # 1. Column name match (fast, exact)
        name_match = self._match_by_name(profile['column'])
        if name_match and name_match['confidence'] >= 0.95:
            # Exact match in known variants - skip everything else
            return self._create_mapping(
                profile, name_match['entity'], name_match['confidence'],
                method='exact_name_match', llm_used=False
            )
        scores['column_name'] = name_match['confidence'] if name_match else 0.0

        # 2. Value bank match (exact values)
        value_match = self.value_bank.find_best_match(profile['sample_values'])
        if value_match and value_match.match_score >= 0.90:
            # Strong value match - high confidence
            return self._create_mapping(
                profile, value_match.entity, value_match.match_score,
                method='value_bank_match', llm_used=False
            )
        scores['value_bank'] = value_match.match_score if value_match else 0.0

        # 3. Embedding similarity (fuzzy value match)
        emb_entity, emb_score, emb_matches = self.embedding_matcher.find_best_match(
            profile['sample_values']
        )
        scores['embedding'] = emb_score

        # 4. Data type match
        type_scores = self._score_type_match(profile)
        scores['data_type'] = max(type_scores.values()) if type_scores else 0.0

        # 5. Cross-database consistency
        scores['cross_db'] = self._check_cross_db_consistency(profile['column'])

        # 6. ML classifier (if trained, Phase 2+)
        if self.ml_classifier and self.ml_classifier.is_trained:
            ml_entity, ml_conf, _ = self.ml_classifier.predict(profile)
            scores['ml'] = ml_conf
        else:
            scores['ml'] = 0.0

        # Calculate weighted score
        total_score = sum(
            scores[signal] * self.weights[signal]
            for signal in scores
        )

        # Determine best entity
        best_entity = self._determine_best_entity(
            name_match, value_match, emb_entity,
            ml_entity if self.ml_classifier else None,
            scores
        )

        # If combined score is high enough, accept without LLM
        if total_score >= 0.70 and best_entity:
            return self._create_mapping(
                profile, best_entity, total_score,
                method='combined_signals', llm_used=False,
                details=scores
            )

        # 7. LLM fallback with few-shot examples
        llm_result = self.few_shot_classifier.classify(profile)

        return self._create_mapping(
            profile, llm_result['classification'],
            self._llm_confidence_to_score(llm_result['confidence']),
            method='llm_few_shot', llm_used=True,
            details={'llm_reasoning': llm_result['reasoning']}
        )

    def on_verification(self, profile: dict, entity: str,
                       client_id: str, verified_by: str):
        """Called when human verifies a mapping - update all learning systems"""

        # Update value bank
        self.value_bank.learn_values(
            entity, profile['sample_values'], client_id, verified_by
        )

        # Update column variants
        self._store_column_variant(entity, profile['column'], client_id)

        # Log ML features
        self.ml_logger.log_verified_mapping(
            profile, entity, client_id, verified_by
        )

        # Re-index embeddings (or batch this)
        self.embedding_matcher.index_value_bank(self.value_bank.get_all_values())
```

---

**Next:** [Reference](07-reference.md) - Case study, checklists, SQL templates, and bibliography.
