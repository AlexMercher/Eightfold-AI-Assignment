# Technical Design — Resume Identity Resolution Pipeline
### Himanshu Ranjan — Eightfold.ai Assignment

---

## 1. Pipeline Overview

```
Input Sources (CSV, PDF)
        ↓
SourceRouter + Adapters
  Detects file type by MIME/extension; dispatches to CsvSourceAdapter or
  ResumeSourceAdapter. Each adapter yields independent Candidate objects
  without leaking source schema into the pipeline.
        ↓
Canonical Model
  All candidates are represented as a single Pydantic schema (Candidate)
  containing PersonalInfo, ContactInfo, ProfessionalInfo, Education,
  SocialProfile, and a provenance list. This model is immutable once
  produced by an adapter.
        ↓
NormalizationEngine
  Runs 10 independent normalizers in sequence: name (title-case),
  email (lowercase + RFC validation), phone (E.164 via phonenumbers),
  URL (protocol prepend + GitHub profile classification), skills
  (alias dictionary), company, job title, education, location, and date.
  All normalizer dictionaries live in config/normalization/*.yaml.
        ↓
GitHub Enrichment (GitHubAdapter)
  If the normalized candidate has a classified GitHub profile URL,
  the GitHub REST API is called. Only empty fields are filled
  (_set_if_empty); existing data is never overwritten. Candidates are
  deep-copied before enrichment — the original is never mutated.
  Provenance entries record every field written.
        ↓
BlockingEngine
  Builds an inverted index across 7 configurable strategies (email, phone,
  GitHub, LinkedIn, company+city, name+company, name+university) to
  produce a unique pool of CandidatePairs in O(bucket^2) per bucket.
  Eliminates infeasible N^2 comparisons.
        ↓
EligibilityEngine
  Evaluates boolean rule combinations from eligibility.yaml on each pair.
  Short-circuits on first passing rule. Only eligible pairs proceed to
  identity resolution.
        ↓
Comparators (11 total)
  Stateless, pure functions for name, email, phone, GitHub, LinkedIn,
  portfolio, company, location, education, job title, and skill.
  Each returns a ComparisonResult (matched, score, algorithm).
  Thresholds and algorithms are configurable in comparators.yaml.
        ↓
EvidenceCollector → RuleEngine → SimilarityEngine → DecisionEngine
  EvidenceCollector runs all active comparators once per pair and
  assembles an EvidenceBundle. RuleEngine checks terminating rules
  (exact email/GitHub/LinkedIn → MATCH immediately, skipping similarity).
  SimilarityEngine computes a weighted score from weights.yaml, excluding
  missing fields. DecisionEngine applies thresholds.yaml to emit
  MATCH / NO_MATCH / REVIEW.
        ↓
CandidateGraph
  MATCH decisions are added as edges in an adjacency list. BFS extracts
  connected components — each component is a candidate cluster.
        ↓
ClusterValidator
  Inspects each cluster for contradictions (disjoint emails, disjoint
  phones) without mutating graph topology. Annotates the cluster as
  VALID, WARNING, or INVALID.
        ↓
MergeEngine + ConflictResolver
  VALID/WARNING: merge() reduces the cluster field-by-field. Scalar
  conflicts resolved by frequency → source priority → alphabetical.
  Arrays are union-deduplicated. ProvenanceRecords are emitted per field.
  INVALID: wrap_single() wraps each source candidate independently into
  a MergeResult, preserving the original candidate_id. No synthetic
  merged identity is ever created.
        ↓
ConfidenceEngine
  Evaluates each MergeResult against conflict count and source density.
  Emits HIGH / MEDIUM / LOW using thresholds from confidence.yaml.
  Runs for both VALID merged profiles and INVALID standalone projections.
        ↓
ProjectionEngine
  Maps the canonical Candidate into the client-requested output schema
  defined by a YAML or JSON config file. Supports field renaming, nested
  dot-notation paths, array indexing, array mapping, and three
  on_missing behaviors (null, omit, error). Optionally appends
  provenance, confidence, and source lists to the output.
        ↓
Final Output
  projected_candidates.json  — one object per projected candidate
  cluster_summary.json       — one entry per connected component
  statistics.json            — timing and count summary
  graph.png / graph.dot / graph.mmd — identity graph visualization
```

---

## 2. Canonical Output Schema

The `Candidate` model is the pipeline's single source of truth. Every stage reads from and writes to this model; no raw strings or ad-hoc dicts cross stage boundaries.

**Key normalization decisions:**
- **Emails** — lowercased and RFC-validated; duplicates removed.
- **Phones** — normalized to E.164 (`+91XXXXXXXXXX`) using `phonenumbers` with India as default region.
- **Names** — title-cased with whitespace collapsed.
- **URLs** — protocol ensured (`https://`); GitHub URLs are classified by `GitHubURLClassifier` into PROFILE / REPO / GIST / RESERVED / PLACEHOLDER / ROOT — only PROFILE-type URLs are kept as social profiles. This prevents placeholder URLs (e.g., `https://github`) from generating false identity matches.
- **Skills** — fuzzy-matched against `skills_aliases.yaml`; `normalized_name` populated for downstream comparisons.
- **Locations** — parsed into `StructuredLocation(city, state, country)` using `location_aliases.yaml`.
- **Provenance** — every field written by GitHub enrichment carries a `ProvenanceEntry(field, source, value)`; every merged field carries a `ProvenanceRecord(source_candidates, merge_decision_path)`.

---

## 3. Merge / Conflict Resolution Policy

**Matching:** Two candidates are compared only if they share at least one blocking key. Terminating rules (exact GitHub, LinkedIn, or email match) immediately produce MATCH and skip weighted similarity. Non-terminating comparisons feed into a weighted similarity score; MATCH threshold is configurable in `thresholds.yaml`.

**Graph Clustering:** MATCH decisions form edges in an undirected graph. Connected components are extracted by BFS. Each component is a candidate cluster.

**Validation:** `ClusterValidator` marks a cluster INVALID if any two candidates within it have disjoint emails AND disjoint phones — a signal that the shared identifier was a coincidence (e.g., a shared placeholder LinkedIn URL). Contradictions are recorded verbatim.

**Merge strategy:**
- *Scalar fields:* `ConflictResolver` applies (1) frequency — most common value wins; (2) source priority from `conflict.yaml`; (3) alphabetical as a deterministic tiebreaker.
- *Array fields:* Set union with deduplication (by lowercase key).
- *INVALID clusters:* `MergeEngine.wrap_single()` wraps each candidate directly into a `MergeResult` without renaming the ID or resolving conflicts. The original `candidate_id` is preserved.

**Confidence:** `ConfidenceEngine` assigns HIGH (≤1 conflict, ≥2 sources), MEDIUM (≤3 conflicts, ≥1 source), or LOW otherwise. Runs identically for merged and standalone candidates.

---

## 4. Runtime Configurable Output

The `ProjectionEngine` is entirely data-driven. Switching output schemas requires only a different config file — no code changes.

**Config structure (YAML or JSON):**
```yaml
fields:
  <output_key>:
    from: <dot.notation.path>    # resolves into the canonical Candidate
    on_missing: null | omit | error
    map:                          # optional: project each list item to a dict
      <sub_key>: <sub_path>

include_provenance: true | false
include_confidence: true | false
include_sources:    true | false
```

**Key capabilities:**
- **Field renaming** — YAML key is the output key; `candidate_id` can become `candidate_uuid`.
- **Nested paths** — `personal_info.name`, `professional_info.current_company`.
- **Array indexing** — `contact_info.emails[0]` extracts the first element.
- **Array mapping** — `from: professional_info.skills` + `map: {name: name}` produces `[{"name": "Python"}, ...]`.
- **on_missing: omit** — key absent from output entirely when field is null/empty.
- **on_missing: error** — raises `ProjectionError`; used to enforce required fields like `candidate_id`.
- **Provenance / Confidence / Sources** — appended as top-level keys when enabled.

Four profiles ship with the project: `default` (8 fields), `minimal` (3 fields + array indexing), `ats` (7 renamed fields + confidence), `assignment_example` (full schema with map arrays, provenance, confidence, and sources).

---

## 5. Edge Cases

**Handled:**

1. **Placeholder social URLs** — PDFs frequently contain the word "GitHub" or "LinkedIn" without a real URL. The old heuristic invented `https://github`, causing false matches. The fix: hyperlink annotations are extracted from PDF byte streams (`page.get_links()`), and `GitHubURLClassifier` rejects any URL that is not a valid GitHub profile path. Placeholder usernames in `constants.py` are also rejected.

2. **INVALID clusters (contradictory identifiers)** — Himanshu Ranjan and Madhusudan G share a generic placeholder LinkedIn URL but have completely disjoint emails and phones. The `ClusterValidator` detects the contradiction and marks the cluster INVALID. The `ResolutionCoordinator` projects each candidate independently with their original IDs. No synthetic merged identity is created. The graph still shows the edge — dashed red — to faithfully represent the identity resolution decision.

3. **GitHub enrichment isolation** — Enrichment runs after normalization and before blocking, so it can improve profile completeness. An automated audit script verified that blocking pairs, eligibility decisions, identity matches, graph topology, and projected candidate count are byte-for-byte identical with and without enrichment enabled.

4. **Missing contact information** — Candidates with no email, phone, or social profiles produce no blocking pairs and remain as disconnected nodes in the graph. They are projected as standalone candidates without going through any merge path.

5. **Multi-source ingestion** — CSV and PDF candidates can be mixed in a single run. Each source adapter is registered with `SourceRouter`; the rest of the pipeline is entirely source-agnostic.

**Intentionally excluded (scope/time):**
- LinkedIn enrichment API (OAuth required; not in scope)
- Repository-level GitHub enrichment (only GitHub profile metadata fetched)
- Distributed execution or caching (single-machine, sub-second pipeline)
- Large-scale indexing optimization (sufficient for assignment dataset; blocked pairs O(bucket^2) per bucket)
