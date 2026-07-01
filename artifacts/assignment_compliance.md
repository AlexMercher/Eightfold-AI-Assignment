# Assignment Compliance Audit — Eightfold Resume Identity Resolution

> **Audit Date:** 2026-07-01  
> **Regression state:** pytest 40/40 PASS · doctor PASS · verify PASS · E2E PASS

---

## Data Sources

| Requirement | Implemented | Verified | Evidence | Notes |
|---|---|---|---|---|
| Structured source (CSV) | ✅ Yes | ✅ Yes | `app/adapters/csv_adapter.py`, `CsvSourceAdapter.process()` reads `Master.csv` → Candidate objects | Column-agnostic via `CsvMapper` |
| Unstructured source (PDF) | ✅ Yes | ✅ Yes | `app/adapters/resume_adapter.py` → `ResumeSourceAdapter`; PDF text via PyMuPDF + PaddleOCR fallback | Hyperlink extraction via `page.get_links()` |
| Multiple source ingestion simultaneously | ✅ Yes | ✅ Yes | `cli.py run --inputs Master.csv Resumes/resume.pdf` accepted; `SourceRouter` dispatches by MIME type | `SourceRouter.register_adapter()` design |
| Source-agnostic adapters | ✅ Yes | ✅ Yes | `BaseSourceAdapter` abstract base; `SourceRouter` routes by `SourceTypeDetector` | No hardcoded switch statements |

---

## Canonical Model

| Requirement | Implemented | Verified | Evidence | Notes |
|---|---|---|---|---|
| Canonical candidate model | ✅ Yes | ✅ Yes | `app/models/canonical/candidate.py` — `Candidate` Pydantic model with `PersonalInfo`, `ContactInfo`, `ProfessionalInfo`, `Education`, `SocialProfile`, `Project`, `Certification`, `provenance` | Single source of truth |
| Normalization applied to canonical model | ✅ Yes | ✅ Yes | `app/pipeline/normalization/engine.py` — `NormalizationEngine` applies all registered normalizers in sequence | In-place field updates |
| Field-level provenance | ✅ Yes | ✅ Yes | `MergeResult.provenance` dict of `ProvenanceRecord`; GitHub enrichment writes `ProvenanceEntry` to `candidate.provenance` | Both enrichment and merge provenance implemented |
| Immutable pipeline (no cross-stage mutation) | ✅ Yes | ✅ Yes | GitHub adapter: `model_copy(deep=True)` before mutation; `_set_if_empty` prevents overwrite; `audit_github_enrichment.py` proved zero mutations | Verified by automated audit script |

---

## Normalization

| Requirement | Implemented | Verified | Evidence | Notes |
|---|---|---|---|---|
| Email normalization | ✅ Yes | ✅ Yes | `normalizers/email.py` — lowercases, strips whitespace, validates RFC format | `verify_normalization.py` PASS |
| Phone normalization (E.164) | ✅ Yes | ✅ Yes | `normalizers/phone.py` — uses `phonenumbers` library; default region IN | E.164 output e.g. `+919693933515` |
| Name normalization | ✅ Yes | ✅ Yes | `normalizers/name.py` — title-case, whitespace collapse | `verify_normalization.py` PASS |
| URL normalization | ✅ Yes | ✅ Yes | `normalizers/url.py` — prepends `https://`; `GitHubURLClassifier` filters to PROFILE type only; discards repo/gist/placeholder URLs | `app/utils/constants.py` for reserved routes |
| Skills normalization | ✅ Yes | ✅ Yes | `normalizers/skill.py` — alias dictionary from `skills_aliases.yaml`; fuzzy matching threshold configurable | `verify_normalization.py` PASS |
| Location normalization | ✅ Yes | ✅ Yes | `normalizers/location.py` — `LocationParser` + `StructuredLocation`; `location_aliases.yaml` | Structured city/country extraction |
| Company normalization | ✅ Yes | ✅ Yes | `normalizers/company.py` — `company_aliases.yaml` | |
| Job title normalization | ✅ Yes | ✅ Yes | `normalizers/job_title.py` — `job_title_aliases.yaml` | |
| Education normalization | ✅ Yes | ✅ Yes | `normalizers/education.py` — degree aliases via `education_aliases.yaml` | |
| Date normalization | ✅ Yes | ✅ Yes | `normalizers/date.py` — pandas `to_datetime` free-text parsing | |
| Configurable normalization | ✅ Yes | ✅ Yes | All alias dictionaries in `config/normalization/*.yaml`; modifiable without code changes | |

---

## Identity Resolution

| Requirement | Implemented | Verified | Evidence | Notes |
|---|---|---|---|---|
| Blocking | ✅ Yes | ✅ Yes | `comparison/blocking/engine.py` — inverted-index; strategies: email, phone, github, linkedin, company_city, name_company, name_university | `verify_comparison.py` PASS |
| Eligibility | ✅ Yes | ✅ Yes | `comparison/eligibility.py` — boolean rule evaluator; short-circuit; `eligibility.yaml` | `verify_comparison.py` PASS |
| Comparators | ✅ Yes | ✅ Yes | 11 comparators: name, email, phone, github, linkedin, portfolio, company, location, education, job_title, skill | `comparators.yaml` thresholds + algorithms |
| Similarity scoring | ✅ Yes | ✅ Yes | `similarity_engine.py` — weighted sum from `weights.yaml`; excludes missing fields to avoid false deflation | `verify_identity_resolution.py` PASS |
| Rule engine | ✅ Yes | ✅ Yes | `rule_engine.py` — `rules.yaml`; terminating rules (exact email/github/linkedin → MATCH immediately) | Terminating rule skips similarity |
| Graph construction | ✅ Yes | ✅ Yes | `resolution/graph.py` — BFS connected components from MATCH edges; adjacency list | `verify_resolution.py` PASS |
| Cluster validation | ✅ Yes | ✅ Yes | `resolution/validator.py` — `ClusterValidator` detects disjoint contacts → INVALID; annotates contradictions | CLI output shows contradiction list |
| Merge engine | ✅ Yes | ✅ Yes | `resolution/merge_engine.py` — field-level scalar + array merge; `ConflictResolver` per scalar field; `wrap_single()` for INVALID | `verify_resolution.py` PASS |
| Conflict resolution | ✅ Yes | ✅ Yes | `resolution/conflict_resolver.py` — frequency → source priority → alphabetical fallback; `conflict.yaml` | |
| Confidence engine | ✅ Yes | ✅ Yes | `resolution/confidence_engine.py` — HIGH/MEDIUM/LOW from conflict count + source density; `confidence.yaml` | explain shows `MEDIUM` for INVALID standalone |
| INVALID cluster enforcement | ✅ Yes | ✅ Yes | Coordinator calls `wrap_single(c)` per candidate; no `merged_` ID created; original ID preserved | 16-test regression suite passes |

---

## Runtime Configuration

| Requirement | Implemented | Verified | Evidence | Notes |
|---|---|---|---|---|
| Runtime configuration (no code change) | ✅ Yes | ✅ Yes | `ProjectionEngine` reads YAML/JSON at startup; any new `.yaml` or `.json` produces new schema | `--projection assignment_example` CLI flag |
| Field selection | ✅ Yes | ✅ Yes | `fields:` dict in YAML — any subset of canonical fields can be selected | `minimal.yaml` vs `default.yaml` differ |
| Field renaming | ✅ Yes | ✅ Yes | YAML key name becomes output key; `candidate_uuid` vs `candidate_id` in `ats.yaml` | |
| `from` (dot-notation path) | ✅ Yes | ✅ Yes | `path_resolver.py` — `personal_info.name`, `contact_info.emails`, etc. | `verify_projection.py` PASS |
| Nested paths | ✅ Yes | ✅ Yes | `PathResolver.resolve()` walks nested Pydantic models | Deep path `professional_info.current_company` tested |
| Array indexing | ✅ Yes | ✅ Yes | `contact_info.emails[0]` syntax in `minimal.yaml` and `ats.yaml` | `verify_projection.py` PASS |
| `on_missing: null` | ✅ Yes | ✅ Yes | Returns `None` in output JSON | `default.yaml` uses this |
| `on_missing: omit` | ✅ Yes | ✅ Yes | Key not emitted in output dictionary | `minimal.yaml` uses this |
| `on_missing: error` | ✅ Yes | ✅ Yes | Raises `ProjectionError`; `candidate_id` always required | `verify_projection.py` PASS |
| Array mapping (`map:`) | ✅ Yes | ✅ Yes | `skills: {from: professional_info.skills, map: {name: name}}` produces list of dicts | `assignment_example.json` uses this for skills, experience, education |
| Include confidence | ✅ Yes | ✅ Yes | `include_confidence: true` in config; `ConfidenceResult` added to `dictionary_view` | `ats.yaml` and `assignment_example.json` |
| Include provenance | ✅ Yes | ✅ Yes | `include_provenance: true`; each field's `ProvenanceRecord` added | `assignment_example.json` |
| Include sources | ✅ Yes | ✅ Yes | `include_sources: true`; set union of all source candidate IDs added | `assignment_example.json` |
| YAML config | ✅ Yes | ✅ Yes | `default.yaml`, `minimal.yaml`, `ats.yaml`, `assignment_example.yaml` all load correctly | |
| JSON config | ✅ Yes | ✅ Yes | `assignment_example.json` loads via `json.load()`; `.json` suffix auto-detected | `verify_projection.py` PASS |

---

## Projection Profiles

| Profile | Implemented | Verified | Schema differs from others |
|---|---|---|---|
| `default.yaml` | ✅ Yes | ✅ Yes | 8 fields; no provenance/confidence |
| `minimal.yaml` | ✅ Yes | ✅ Yes | 3 fields (`id`, `name`, `email[0]`); array indexing |
| `ats.yaml` | ✅ Yes | ✅ Yes | 7 fields with renamed keys (`candidate_uuid`, `primary_email`); confidence ON |
| `assignment_example.json` | ✅ Yes | ✅ Yes | 12+ fields; `map:` arrays for skills/experience/education; provenance + confidence + sources all ON |

All four profiles project the **same canonical Candidate** to different output schemas — zero code changes required.

---

## CLI Commands

| Command | Implemented | Verified | Evidence |
|---|---|---|---|
| `version` | ✅ Yes | ✅ Yes | Prints `Pipeline v1.0.0` |
| `doctor` | ✅ Yes | ✅ Yes | 32 checks — Python, configs, datasets, deps, output dir, CLI, verify scripts — all PASS |
| `verify` | ✅ Yes | ✅ Yes | Runs 5 verification scripts via subprocess; all PASS |
| `run` | ✅ Yes | ✅ Yes | Full E2E; generates all 6 artifacts; ASSIGNMENT PRESENTATION SUMMARY displayed |
| `ingest` | ✅ Yes | ✅ Yes | Prints ingested candidate IDs |
| `normalize` | ✅ Yes | ✅ Yes | Prints normalized field summaries |
| `compare` | ✅ Yes | ✅ Yes | Prints blocking pairs and eligibility results |
| `resolve` | ✅ Yes | ✅ Yes | Prints MATCH/NO_MATCH/REVIEW decisions |
| `merge` | ✅ Yes | ✅ Yes | Prints merged candidate summaries |
| `project` | ✅ Yes | ✅ Yes | Supports `--projection` flag |
| `visualize` | ✅ Yes | ✅ Yes | Generates graph.png, graph.dot, graph.mmd |
| `explain` | ✅ Yes | ✅ Yes | Full trace: normalization → blocking key → eligibility rule → identity rule → similarity → decision → cluster → confidence |
| `stats` | ✅ Yes | ✅ Yes | Reads `statistics.json`; prints 12 stat fields with timings |
| `config` | ✅ Yes | ✅ Yes | Loads and prints all 9 YAML configs with key summaries |
| `--verbose` / `--quiet` global flags | ✅ Yes | ✅ Yes | Global flags before subcommand |
| Help text | ✅ Yes | ✅ Yes | `--help` on all subcommands; epilog references `commands.md` |
| Friendly errors | ✅ Yes | ✅ Yes | File not found → `ERROR: Input file not found`; unsupported type → clear message |
| Output summaries | ✅ Yes | ✅ Yes | ASSIGNMENT PRESENTATION SUMMARY table with cluster counts, timing, artifacts list |

---

## Graph

| Requirement | Implemented | Verified | Evidence |
|---|---|---|---|
| VALID cluster shown | ✅ Yes | ✅ Yes | Solid blue edges in `graph.png`; nodes connected |
| INVALID cluster shown | ✅ Yes | ✅ Yes | Dashed red edge in `graph.png` with legend "INVALID match (rejected)" |
| WARNING cluster supported | ✅ Yes | ✅ Yes | `ClusterStatus.WARNING` path in coordinator; rendered as solid blue |
| Disconnected graph (singletons) | ✅ Yes | ✅ Yes | BFS emits isolated single-node components; all 8 nodes shown |
| PNG export | ✅ Yes | ✅ Yes | `graph.png` generated at 300dpi with spring layout, legend, labels |
| DOT export | ✅ Yes | ✅ Yes | `graph.dot` — valid Graphviz syntax; INVALID edge has `[style=dashed color=red]` |
| Mermaid export | ✅ Yes | ✅ Yes | `graph.mmd` — INVALID edges use `-. INVALID .-` dotted syntax |

---

## Documentation Consistency

| Document | Status | Notes |
|---|---|---|
| `README.md` | ✅ Consistent | Pipeline stages match implementation; CLI examples match actual commands |
| `commands.md` | ✅ Consistent | 16 commands documented with examples; matches `cli.py` subparser definitions |
| `results.md` | ✅ Consistent | Auto-appended by `run_e2e()`; compliance checklist accurate |
| `file_context.md` | ✅ Consistent | Architecture sections, bug fixes, and verification results match codebase |

---

## Generated Artifact Consistency

All artifacts verified from run `output/2026-07-01_09-08-46`:

| Artifact | Generated | Internally Consistent |
|---|---|---|
| `projected_candidates.json` | ✅ Yes | 8 candidates (6 `merged_*` + 2 original IDs for INVALID cluster) |
| `statistics.json` | ✅ Yes | 8 raw, 1 match, 7 clusters, timing breakdown |
| `cluster_summary.json` | ✅ Yes | 7 entries: 6 VALID + 1 INVALID (with contradictions listed) |
| `graph.png` | ✅ Yes | 8 nodes, 1 dashed red edge, 0 false solid edges |
| `graph.dot` | ✅ Yes | All 8 nodes; INVALID edge has `[style=dashed color=red]` |
| `graph.mmd` | ✅ Yes | All 8 nodes; INVALID edge uses dotted Mermaid syntax |

Note: 7 cluster summary entries → 8 projected candidates, because the INVALID cluster (size 2) produces 2 independent projections referencing the same cluster object. This is correct by design.

---

## Testing

| Suite | Status | Count |
|---|---|---|
| `pytest tests/` | ✅ PASS | 40/40 |
| `cli.py doctor` | ✅ PASS | 32/32 checks |
| `cli.py verify` | ✅ PASS | 5/5 scripts |
| `cli.py run --inputs Master.csv` | ✅ PASS | 8 candidates, 7 clusters |
| `cli.py run --inputs Master.csv --projection assignment_example` | ✅ PASS | Full JSON with provenance + confidence + sources |

---

## Summary

**No assignment requirements were found to be missing.** All requirements are implemented and verified with evidence.

**Intentional exclusions (explicitly out of scope):**
- LinkedIn enrichment API (requires OAuth)
- Repository-level GitHub enrichment (only profile-level implemented)
- Distributed execution / caching (single-machine pipeline)
- Large-scale optimization (sufficient for assignment dataset)
