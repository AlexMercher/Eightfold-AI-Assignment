# Resume Extraction Project

A professional pipeline for extracting structured data from digital and scanned resumes.

# 📄 Resume Extractor & Identity Resolution Pipeline

A production-ready, high-accuracy resume extraction and identity resolution system that
converts PDF resumes into structured JSON, normalizes data, and resolves duplicate identities across datasets.

**⚡ 100% Deterministic & Non-LLM Based**  
This pipeline is built entirely on deterministic heuristics, NLP (spaCy), fuzzy matching (RapidFuzz), and boolean rule engines. It guarantees absolute consistency, strict rule enforcement, and 100% explainability without any risk of AI hallucinations or API cost overheads.

---

## 🎯 Identity Resolution Pipeline (CLI)

The repository includes a powerful deterministic Identity Resolution Engine operated via `cli.py`. It orchestrates ingestion, normalization, comparison, blocking, eligibility, conflict resolution, and projection.

For full CLI documentation, see [commands.md](commands.md).

```bash
# Full end-to-end run
python cli.py run --inputs Master.csv "Resumes/John_Doe.pdf"

# View system health
python cli.py doctor

# Verify architecture invariants
python cli.py verify

# View detailed explanation of a match decision
python cli.py explain <id_A> <id_B> --inputs Master.csv
```

---

## 🏗️ Architecture

```
Source Ingestion (Adapters)
  ↳ Normalization Engine (Format & Type Standardization)
    ↳ Comparison Engine (Blocking & Eligibility)
      ↳ Identity Resolution (Rules, Similarity & Decision Logic)
        ↳ Resolution Pipeline (Cluster Graph & Validation)
          ↳ Merge Engine (Conflict Resolution & Provenance)
            ↳ Projection Engine (Configurable Schema Output)
```

---

## 🚀 Quick Start & Installation

### 1. Setup Environment
We recommend using a virtual environment (like `conda` or `venv`).
```bash
# Example using conda
conda create --prefix ./venv python=3.10 -y
conda activate ./venv
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_md
```

### 3. Verify Installation
Run the built-in doctor script to ensure all dependencies and configurations are healthy:
```bash
python cli.py doctor
```

### 4. Run the Pipeline
Use the `cli.py` to run the end-to-end identity resolution pipeline on your data:
```bash
# Run on the primary Master.csv dataset
python cli.py run --inputs Master.csv

# Run with a specific projection output format
python cli.py run --inputs Master.csv --projection assignment_example
```

For full documentation on available commands (including `doctor`, `verify`, `explain`, and `stats`), see [commands.md](commands.md).

 
## 🧪 Running Tests

```bash
# 1. Run architecture and invariant verification
python cli.py verify

# 2. Run the full pytest test suite
pytest
```

---

## 📁 Project Structure

```
resume_extractor/
├── app/
│   ├── adapters/            # Ingestion layer (CSV, Resumes)
│   ├── core/                # Core extraction & parsing (PyMuPDF)
│   ├── extraction/          # Explicit field extractors (Contacts, GitHub links)
│   ├── models/              # Canonical schemas and enums
│   ├── nlp/                 # Text cleaning and NER (spaCy)
│   ├── pipeline/
│   │   ├── normalization/   # Standardization and cleaning rules
│   │   ├── comparison/      # Blocking, Comparators, Eligibility engine
│   │   ├── identity_resolution/ # Deterministic matching logic (Rules, Similarity)
│   │   └── resolution/      # Clustering, merging, conflicts, and projection
│   └── utils/               # Constants and logging
├── artifacts/               # Golden outputs and compliance documents
├── config/                  # YAML configurations (Thresholds, Conflict, Projection)
├── generated_data/          # Augmented testing datasets
├── logs/                    # Application and error logs
├── tests/                   # Extensive pytest suite
├── tools/                   # Developer tools for verification, scripts and diagnostics
├── cli.py                   # Primary entrypoint for pipeline execution
├── commands.md              # CLI reference guide
├── file_context.md          # Comprehensive architectural index
├── technical_design.md      # Final technical design document
├── Master.csv               # Primary demonstration dataset
├── .env.example             # Example environment configuration
└── requirements.txt
```
---

 
## 👥 Author

- **Name**: Himanshu Ranjan