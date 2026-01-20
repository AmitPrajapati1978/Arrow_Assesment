# Heavy Equipment Inventory Ingestion Pipeline

## Overview

This project implements a scalable ingestion pipeline for normalizing messy heavy equipment inventory data into a clean, structured internal format.  
The system is designed to balance **LLM intelligence** with **backend efficiency**, making it suitable for high-throughput ingestion of **millions of records**.

The pipeline is split into four clear stages:

- **Objective A** – Category normalization  
- **Objective B** – Feature extraction  
- **Objective C** – Manufacturer normalization  
- **Objective D** – Final schema shaping & output  

Each stage is modular, independently testable, and production-oriented.

---

## Objective A – Categorization Strategy

### Goal
Map noisy, external `source_category` values to a standardized internal taxonomy while avoiding per-record LLM usage.

---

### Attempt 1: Embedding-Based Similarity (Rejected)

**Approach**
- Normalized `source_category` strings.
- Used `all-MiniLM-L6-v2` embeddings.
- Matched against taxonomy using cosine similarity.

**Result**
- Worked for descriptive categories (e.g., *Bulldozers*, *Mini Excavator*).
- Failed for industry acronyms and shorthand:
  - `SSL`
  - `CTL`
  - `TLB`
- Lacked domain-specific reasoning.

**Decision**
- Rejected due to inconsistent accuracy.
- Embeddings alone were insufficient without industry context.

---

### Attempt 2: LLM-Based Category Mapping (Final Approach)

**Approach**
- Extracted **unique** `source_category` values (~20–25 total).
- Normalized values before inference.
- Sent only:
  - Unique normalized source categories
  - Internal taxonomy list
- Requested a **single JSON mapping** from LLM.
- Applied mapping locally to all records.

**Accuracy**
- ~80–85% correct across 250 records.
- Errors limited to genuinely ambiguous categories.

---

### Optimization & Scalability

- **Deduplication:** 1 LLM call instead of 250
- **Minimal Prompt Size:** No raw inventory records sent
- **Deterministic Output:** `temperature = 0`
- **Persistent Cache:** Mapping stored on disk
- **Scales to Millions:** Cost does not grow with record count

---

### Final Outcome

This approach provides strong semantic understanding while keeping LLM usage **bounded, cost-efficient, and production-safe**.

---

## Objective B – Feature Extraction Strategy

### Goal
Extract structured attributes from the unstructured `description` field with **zero LLM usage**.

Extracted attributes:
- **Cabin:** `EROPS`, `OROPS`, `Unknown`
- **Drive:** `4WD`, `AWD`, `Tracks`, `Wheels`, `Unknown`
- **Hours:** Integer meter reading

---

### Design Principles

- Deterministic logic
- No per-record AI calls
- O(n) time complexity
- Low latency and zero marginal cost

---

### Implementation

#### Cabin Detection
- `ENCLOSED CAB`, `EROPS` → `EROPS`
- `OPEN STATION`, `OROPS` → `OROPS`
- Else → `Unknown`

Enclosed indicators take priority when conflicting terms appear.

---

#### Drive Detection
- `TRACK`, `TRACKS` → `Tracks`
- `AWD` → `AWD`
- `4WD`, `4X4` → `4WD`
- `2WD` → `Wheels`
- Else → `Unknown`

No inference based on category to avoid false positives.

---

#### Hours Extraction
- Regex targets only:
  - `HRS`
  - `HOURS`
  - `METER READS`
- Prevents false extraction from model numbers (e.g., `D6T`, `ZX350`).
---
### Handling Conflicting Cabin Indicators (EROPS vs OROPS)

In a small number of records, the unstructured `description` field contains indicators for both `EROPS` and `OROPS`.

To handle this deterministically and avoid ambiguity, a priority rule is applied:
- If an enclosed indicator (`EROPS`, `ENCLOSED CAB`) is present, the cabin is classified as `EROPS`
- Otherwise, if an open indicator (`OROPS`, `OPEN STATION`) is present, the cabin is classified as `OROPS`

This decision is based on the assumption that enclosed configurations represent a more specific and restrictive setup, and descriptions may reference historical or optional configurations.

The priority rule ensures:
- A single, consistent output value per record
- Deterministic behavior across runs
- No reliance on probabilistic inference or per-record LLM calls

This tradeoff favors consistency and scalability over attempting to infer intent from ambiguous free-text descriptions.
---

### Performance

- **LLM Calls:** 0
- **Latency:** Microseconds per record
- **Cost:** $0 incremental cost
- **Scalability:** Linear with record count

---

## Objective C – Manufacturer Normalization Strategy

### Goal
Normalize messy manufacturer values into a single canonical brand name.

Examples:
- `CAT`, `Caterpillar Inc.` → `Caterpillar`
- `Deere`, `J. Deere` → `John Deere`

---

### Attempt 1: Rule-Based Mapping (Baseline)

**Approach**
- Normalized strings (case & punctuation).
- Used predefined lookup table.

**Result**
- Fast and reliable for known manufacturers.
- Failed for unseen vendor variants.

**Decision**
- Kept as baseline, but insufficient alone.

---

### Attempt 2: LLM + Persistent Cache (Final Approach)

**Approach**
1. Normalize manufacturer strings into stable keys
2. Lookup in persistent cache (`manufacturer_mapping.json`)
3. Collect unseen values
4. Send **only unseen unique values** to LLM
5. Store results back to cache
6. Apply mapping locally

**Key Characteristics**
- LLM used only as a bootstrap mechanism
- Deterministic runtime behavior
- Cache grows over time
- Zero repeated LLM calls for known manufacturers

---

### Scalability

- **Cold start:** One LLM call per new manufacturer set
- **Warm runs:** Zero LLM calls
- **Lookup time:** O(1)
- **Production-safe & auditable**

---

## Objective D – Structured Output

### Goal
Produce a clean, contract-compliant output file.

### Final Schema

```json
{
  "serial_number": "...",
  "description": "...",
  "category": "...",
  "make": "...",
  "model": "...",
  "extracted_features": {
    "cabin": "...",
    "drive": "...",
    "hours": 1234
  }
}
