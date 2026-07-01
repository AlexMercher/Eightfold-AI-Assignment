# Pipeline Command Reference

> Single reference for operating the Resume Identity Resolution Pipeline.
> All commands are invoked via: `python cli.py <command> [arguments]`
> Working directory must be the project root.

---

## Environment Setup

```bash
# Activate virtual environment
conda activate ./venv

# All commands below assume this env is active and CWD is project root
# Set PYTHONPATH so the app package is discoverable
set PYTHONPATH=.        # Windows
export PYTHONPATH=.     # Linux/Mac
```

---

## `pipeline --help`

**Purpose**: Show all available commands.

```bash
python cli.py --help
```

**Expected Output**:
```
usage: pipeline [-h] [--verbose] [--quiet] {version,doctor,verify,test,ingest,normalize,compare,resolve,merge,project,run,visualize,stats,config,explain} ...

Resume Identity Resolution Pipeline CLI

Orchestrates the ingestion, normalization, comparison, resolution, and projection of candidate profiles.

positional arguments:
  {version,doctor,verify,test,ingest,normalize,compare,resolve,merge,project,run,visualize,stats,config,explain}
                        Available commands

options:
  -h, --help            show this help message and exit
  --verbose, -v         Enable verbose logging (DEBUG level)
  --quiet, -q           Suppress logging output (WARNING level and above only)

See commands.md for full documentation and examples.
```

---

## `pipeline version`

**Purpose**: Print the pipeline version string.

```bash
python cli.py version
```

**Expected Output**:
```
Pipeline v1.0.0
```

---

## `pipeline doctor`

**Purpose**: Comprehensive system health check. Verifies Python environment, dependencies, YAML configuration files, output directories, sample datasets, and CLI availability.

```bash
python cli.py doctor
```

**Expected Output (all passing)**:
```
Running pipeline doctor...

  [Environment]
  [PASS] Python version (3.10.0)
  [PASS] Virtual Environment

  [Configuration]
  [PASS] skills_aliases.yaml
  [PASS] company_aliases.yaml
  [PASS] job_title_aliases.yaml
  [PASS] comparators.yaml
  [PASS] blocking.yaml
  [PASS] eligibility.yaml
  [PASS] rules.yaml
  [PASS] weights.yaml
  [PASS] thresholds.yaml
  [PASS] conflict.yaml
  [PASS] confidence.yaml
  [PASS] projection default.yaml

  [Datasets]
  [PASS] Master.csv
  [PASS] generated_data/ directory
  [PASS] matching_candidates.csv
  [PASS] conflict_candidates.csv
  [PASS] new_candidates.csv
  [PASS] Resumes/ directory

  [Dependencies]
  [PASS] pydantic importable
  [PASS] pyyaml importable
  [PASS] pandas importable
  [PASS] rapidfuzz importable
  [PASS] networkx importable
  [PASS] matplotlib importable
  [PASS] phonenumbers importable
  [PASS] pytest importable
  [PASS] PyMuPDF importable
  [PASS] paddleocr importable

  [Output]
  [PASS] output/ directory writable

  [CLI]
  [PASS] cli.py exists

  [Verification Scripts]
  [PASS] verify_identity_resolution.py
  [PASS] verify_resolution.py
  [PASS] verify_normalization.py
  [PASS] verify_comparison.py
  [PASS] verify_projection.py

  Doctor check PASSED. System is healthy.
```

**Common Errors & Warnings**:
- `[FAIL] Configuration directory` — Run from the project root directory.
- `[WARNING] Virtual Environment` — Ensure you are running inside conda or a venv.
- `[WARNING] paddleocr importable` — Optional dependency for PDF ingestion is missing.

---

## `pipeline verify`

**Purpose**: Execute all architecture verification scripts, confirming every module satisfies its architectural contract.

```bash
python cli.py verify
```

**Expected Output**:
```
Running architecture verification...

Script                              | Status     | Time
------------------------------------------------------------
verify_normalization.py             | PASS       | 0.70s
verify_comparison.py                | PASS       | 1.15s
verify_identity_resolution.py       | PASS       | 0.40s
verify_resolution.py                | PASS       | 0.45s
verify_projection.py                | PASS       | 0.40s

=== Error Details ===
None.

  [PASS] All verification checks passed.
```

**Common Errors**:
- `[FAIL] One or more verification checks failed.` — Check the `=== Error Details ===` block for raw `stdout` and `stderr` to debug the specific architecture invariant failure. Use `--verbose` for full stack traces on other commands.

---

## `pipeline test`

**Purpose**: Run the full automated test suite using pytest.

```bash
python cli.py test
```

Or run directly with verbose output:
```bash
python -m pytest tests/test_adapters.py tests/test_normalization.py tests/test_comparison.py tests/test_resolution.py tests/test_cli.py tests/test_e2e.py -v
```

**Expected Output**:
```
collected N items
PASSED tests/test_adapters.py::test_csv_adapter_registration
PASSED tests/test_normalization.py::test_normalization_engine
...
N passed in Xs
```

---

## `pipeline ingest`

**Purpose**: Ingest input files (PDFs or CSVs) and emit Canonical Candidates. Runs the full pipeline internally and reports ingest metrics.

**Syntax**:
```bash
python cli.py ingest --inputs <file1> [<file2> ...]
```

**Arguments**:
- `--inputs` *(required)*: One or more input file paths. Accepts `.csv` and `.pdf` files.

**Examples**:

```bash
# Ingest Master CSV
python cli.py ingest --inputs Master.csv

# Ingest multiple CSVs
python cli.py ingest --inputs Master.csv generated_data/matching_candidates.csv

# Ingest all generated CSVs
python cli.py ingest --inputs Master.csv generated_data/matching_candidates.csv generated_data/conflict_candidates.csv generated_data/new_candidates.csv

# Ingest resume PDFs
python cli.py ingest --inputs "Resumes/Internship_Resume_Himanshu.pdf"

# Mixed inputs
python cli.py ingest --inputs Master.csv "Resumes/Internship_Resume_Himanshu.pdf"
```

**Expected Output**:
```
Executing up to ingest...
Completed ingest. Outputs available in output\2026-07-01_XX-XX-XX
```

**Supported Input Types**:
| Type | Extension | Adapter |
|------|-----------|---------|
| Structured CSV | `.csv` | `CsvSourceAdapter` |
| Resume PDF | `.pdf`, `.PDF` | `ResumeSourceAdapter` |

---

## `pipeline normalize`

**Purpose**: Run ingestion + normalization on candidates. Normalizes names, emails, phones, skills, companies, job titles, education, locations, dates, and URLs.

**Syntax**:
```bash
python cli.py normalize --inputs <file1> [<file2> ...]
```

**Examples**:
```bash
python cli.py normalize --inputs Master.csv
python cli.py normalize --inputs Master.csv generated_data/matching_candidates.csv
```

---

## `pipeline compare`

**Purpose**: Run ingestion, normalization, blocking, and eligibility checks. Generates candidate pairs for identity resolution.

**Syntax**:
```bash
python cli.py compare --inputs <file1> [<file2> ...]
```

**Examples**:
```bash
python cli.py compare --inputs Master.csv generated_data/matching_candidates.csv
python cli.py compare --inputs Master.csv generated_data/conflict_candidates.csv
```

---

## `pipeline resolve`

**Purpose**: Run through identity resolution. Determines MATCH / NO_MATCH / REVIEW for each eligible pair.

**Syntax**:
```bash
python cli.py resolve --inputs <file1> [<file2> ...]
```

**Examples**:
```bash
python cli.py resolve --inputs Master.csv generated_data/matching_candidates.csv
```

---

## `pipeline merge`

**Purpose**: Run through merge stage. Merges identity clusters, applies conflict resolution, and generates provenance.

**Syntax**:
```bash
python cli.py merge --inputs <file1> [<file2> ...]
```

**Examples**:
```bash
python cli.py merge --inputs Master.csv generated_data/matching_candidates.csv
```

---

## `pipeline project`

**Purpose**: Run full pipeline including projection. Maps merged canonical profiles to the configured output schema.

**Syntax**:
```bash
python cli.py project --inputs <file1> [<file2> ...] [--projection <config>]
```

**Arguments**:
- `--inputs` *(required)*: One or more input files.
- `--projection` *(optional)*: The name of a projection profile in `config/projection/` (e.g., `default`, `ats`, `minimal`, `assignment_example`) or a path to a custom YAML file. Defaults to `default`.

**Examples**:
```bash
python cli.py project --inputs Master.csv generated_data/matching_candidates.csv --projection ats
```

---

## `pipeline run`

**Purpose**: Run the **complete end-to-end pipeline** — ingest → normalize → compare → resolve → merge → project → visualize. Saves all artifacts to a timestamped output directory.

**Syntax**:
```bash
python cli.py run --inputs <file1> [<file2> ...] [--output <dir>] [--projection <config>]
```

**Arguments**:
- `--inputs` *(required)*: One or more input files.
- `--output` *(optional)*: Base output directory (default: `output/`).
- `--projection` *(optional)*: The name of a projection profile in `config/projection/` (e.g., `default`, `ats`, `minimal`, `assignment_example`) or a path to a custom YAML file. Defaults to `default`.

**Examples**:

```bash
# Minimal run: Master only
python cli.py run --inputs Master.csv

# Standard run: Master + matching candidates
python cli.py run --inputs Master.csv generated_data/matching_candidates.csv

# Conflict detection run
python cli.py run --inputs Master.csv generated_data/conflict_candidates.csv

# Full demo run: all generated datasets
python cli.py run --inputs Master.csv generated_data/matching_candidates.csv generated_data/conflict_candidates.csv generated_data/new_candidates.csv

# Resume + CSV mixed run
python cli.py run --inputs Master.csv "Resumes/Internship_Resume_Himanshu.pdf"

# All resumes + Master
python cli.py run --inputs Master.csv "Resumes/Ashwin-resume-end-final (1).pdf" "Resumes/G MADHUSUDAN.pdf" "Resumes/Hanin_CV_General.PDF"
```

**Expected Output**:
```
Generated:
graph.png
graph.dot
graph.mmd

Run completed successfully.

Candidates:
18

Eligible pairs:
11

MATCH:
4

REVIEW:
2

NO MATCH:
5

Merged Profiles:
14

Execution Time:
1.21 s

Output Directory:
output\2026-07-01_18-30-12
```

**Output Artifacts** (in `output/<timestamp>/`):
| File | Description |
|------|-------------|
| `projected_candidates.json` | Final merged and projected candidates |
| `cluster_summary.json` | Per-cluster status and contradiction list |
| `statistics.json` | Execution metrics (timings, counts) |
| `graph.png` | Candidate identity graph (Matplotlib) |
| `graph.dot` | Graphviz DOT format |
| `graph.mmd` | Mermaid graph format |

---

## `pipeline visualize`

**Purpose**: Run pipeline and generate all graph visualizations.

**Syntax**:
```bash
python cli.py visualize --inputs <file1> [<file2> ...]
```

**Examples**:
```bash
python cli.py visualize --inputs Master.csv generated_data/matching_candidates.csv
```

**Generated Files**:
- `graph.png` — PNG rendering via NetworkX + Matplotlib
- `graph.dot` — DOT language (renderable with Graphviz: `dot -Tpng graph.dot -o output.png`)
- `graph.mmd` — Mermaid markdown (renderable in any Mermaid viewer)

---

## `pipeline stats`

**Purpose**: Print statistics from a previous pipeline run.

**Syntax**:
```bash
python cli.py stats --run-dir <path>
```

**Arguments**:
- `--run-dir` *(required)*: Path to the timestamped run directory (e.g. `output/2026-07-01_03-16-38`).

**Examples**:
```bash
python cli.py stats --run-dir output/2026-07-01_03-16-38
```

**Expected Output**:
```
=== PIPELINE STATS ===
Candidates: 16
Normalized: 16
Eligible Pairs: 3
MATCH: 2
Clusters: 14
Merged Candidates: 14
Execution Time: 0.06s
```

---

## `pipeline explain`

**Purpose**: Given two candidate IDs, run the pipeline and display the full resolution path: normalization, comparators, evidence bundle, rule engine, similarity, decision, merge, conflict resolution, provenance, and confidence.

**Syntax**:
```bash
python cli.py explain <candidate_a_id> <candidate_b_id> --inputs <file1> [<file2> ...]
```

**Arguments**:
- `candidate_a` *(positional)*: ID of the first candidate.
- `candidate_b` *(positional)*: ID of the second candidate.
- `--inputs` *(required)*: Input files to load candidates from.

**Examples**:
```bash
python cli.py explain MASTER_001 GEN_MATCH_001 --inputs Master.csv generated_data/matching_candidates.csv
python cli.py explain MASTER_003 GEN_CONFLICT_003 --inputs Master.csv generated_data/conflict_candidates.csv
```

**Expected Output**:
```
Explaining resolution path for 'MASTER_001' and 'GEN_MATCH_001'...
------------------------------------------------------------
[NORMALIZATION]
  Candidate A (MASTER_001):
    Name:   John Doe
    Emails: ['john.doe@example.com']
  Candidate B (GEN_MATCH_001):
    Name:   John Doe
    Emails: ['john.doe@example.com']

Blocking
--------
Matched via:
email
exact_name

Eligibility
-----------
Rule:
shared_email

Identity Rule
-------------
email_exact_match

Similarity
----------
Skipped (terminating rule)

Decision
--------
MATCH

Cluster
-------
VALID

Confidence
----------
MEDIUM
------------------------------------------------------------
```

---

## `pipeline config`

**Purpose**: Validate and display configuration files.

```bash
python cli.py config
```

**Expected Output**:
```
Config command placeholder. See config/ directory for YAMLs.
```

Configuration files are located in:
```
config/
├── augmentation.yaml
├── comparison/
│   ├── comparators.yaml       # Comparator thresholds and algorithms
│   ├── blocking.yaml          # Active blocking strategies
│   └── eligibility.yaml       # Eligibility rule definitions
├── normalization/
│   ├── skills_aliases.yaml    # Skill normalization aliases
│   ├── company_aliases.yaml   # Company name aliases
│   ├── job_title_aliases.yaml # Job title aliases
│   ├── education_aliases.yaml # Degree aliases
│   └── location_aliases.yaml  # Location aliases
├── identity_resolution/
│   ├── rules.yaml             # Hard terminating rules
│   ├── weights.yaml           # Similarity weights per field
│   └── thresholds.yaml        # Decision thresholds
└── resolution/
    ├── conflict.yaml          # Source priority order for conflict resolution
    ├── confidence.yaml        # Confidence level thresholds
    └── projection.yaml        # Output field mapping
```

---

## Runtime Configuration

The pipeline supports **runtime configuration** via `config/resolution/projection.yaml`:

### Field Selection
Only include specific fields in output:
```yaml
projection_map:
  id: "merged_candidate_id"
  name: "personal_info.name"
  emails: "contact_info.emails"
```

### Field Renaming
Map internal field names to external names:
```yaml
projection_map:
  full_name: "personal_info.name"    # internal -> external rename
  contact_emails: "contact_info.emails"
```

### Provenance Toggle
Provenance is tracked at the field level via `ProvenanceRecord` in `merge_engine.py`. The `MergeResult.provenance` dict maps each field name to its contributing candidate IDs.

### Conflict Resolution Priority
Configured in `config/resolution/conflict.yaml`:
```yaml
source_priorities:
  - Master.csv
  - matching_candidates.csv
  - conflict_candidates.csv
```
Priority order: **Frequency > Source Priority > Alphabetical fallback**.

---

## Complete Demo Sequence

Run the full demonstration in this order:

```bash
# 1. Health check
python cli.py doctor

# 2. Architecture verification  
python cli.py verify

# 3. Run tests
python -m pytest tests/test_adapters.py tests/test_normalization.py tests/test_comparison.py tests/test_resolution.py tests/test_cli.py tests/test_e2e.py -v

# 4. Full pipeline: structured sources
python cli.py run --inputs Master.csv generated_data/matching_candidates.csv generated_data/conflict_candidates.csv generated_data/new_candidates.csv

# 5. View statistics from that run
python cli.py stats --run-dir output/<timestamp>

# 6. Explain a specific pair
python cli.py explain <id_a> <id_b> --inputs Master.csv generated_data/matching_candidates.csv

# 7. Generate visualizations
python cli.py visualize --inputs Master.csv generated_data/matching_candidates.csv
```
