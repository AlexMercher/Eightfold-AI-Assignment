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

### 3. Start with Docker

```bash
docker-compose up --build
```

### 4. Start Locally

```bash
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

---

## 📦 Tech Stack

| Layer            | Technology                        |
|------------------|-----------------------------------|
| API Framework    | FastAPI + Uvicorn                 |
| Digital PDF      | PyMuPDF + pdfplumber              |
| Scanned PDF      | PaddleOCR + PP-Structure          |
| Layout Analysis  | Geometric + heuristic analysis    |
| NLP / NER        | spaCy (en_core_web_md)            |
| Skill Matching   | RapidFuzz + ESCO taxonomy         |
| Database         | PostgreSQL + SQLAlchemy           |
| Export           | openpyxl (Excel) + pandas (CSV)   |
| Containerization | Docker + Docker Compose           |

---

## 🔌 API Endpoints

| Method | Endpoint                        | Description              |
|--------|---------------------------------|--------------------------|
| POST   | `/api/v1/upload/`               | Upload single resume     |
| POST   | `/api/v1/upload/batch`          | Upload multiple resumes  |
| GET    | `/api/v1/upload/{id}/status`    | Check processing status  |
| GET    | `/api/v1/upload/`               | List all resumes         |
| DELETE | `/api/v1/upload/{id}`           | Delete a resume          |
| POST   | `/api/v1/extract/{id}`          | Trigger extraction       |
| GET    | `/api/v1/extract/{id}/result`   | Get extraction result    |
| POST   | `/api/v1/extract/bulk`          | Bulk extract             |
| POST   | `/api/v1/export/`               | Generate Excel/CSV       |
| GET    | `/api/v1/export/download/{file}`| Download export file     |
| GET    | `/api/v1/export/stream/csv`     | Stream CSV response      |
| GET    | `/api/v1/export/{id}/excel`     | Export single to Excel   |
| GET    | `/health`                       | Health check             |

---

## 🧪 Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html


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
├── temp/                    # Temporary logs and tracebacks
├── tests/                   # Extensive pytest suite
├── tools/                   # Developer tools for verification, scripts and diagnostics
├── cli.py                   # Primary entrypoint for pipeline execution
├── commands.md              # CLI reference guide
├── file_context.md          # Comprehensive architectural index
├── technical_design.md      # Final technical design document
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and configure:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/resume_db
APP_ENV=development
DEBUG=True
OCR_USE_GPU=False
SKILLS_FUZZY_THRESHOLD=80
MAX_UPLOAD_SIZE_MB=10
```

---

## 📊 Extraction Output

```json
{
  "contact": {
    "full_name": "John Smith",
    "email": "john@example.com",
    "phone": "+1 555-123-4567",
    "linkedin": "https://linkedin.com/in/johnsmith"
  },
  "experience": [{
    "job_title": "Senior Software Engineer",
    "company": "Google",
    "start_date": "Jan 2021",
    "end_date": "Present",
    "is_current": true,
    "duration_years": 3.5
  }],
  "education": [{
    "degree": "Bachelor of Science",
    "field_of_study": "Computer Science",
    "institution": "MIT",
    "graduation_date": "Jun 2018",
    "gpa": "3.8/4.0"
  }],
  "skills": {
    "all": ["Python", "Django", "Docker", "AWS"],
    "programming_languages": ["Python"],
    "frameworks": ["Django"],
    "cloud_devops": ["Docker", "AWS"]
  },
  "confidence_scores": {
    "overall": 0.87,
    "contact": 0.95,
    "experience": 0.82
  }
}
```

---

## 👥 Author

- **Name**: Shewan Dagne
- **Email**: [shewan.dagne.1@gmail.com](mailto:shewan.dagne.1@gmail.com)
- **GitHub**: [sdagne](https://github.com/sdagne)
