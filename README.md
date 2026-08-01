# SkillBridge

Upload a resume and a job description — get back a breakdown of which skills you have, which you're missing, and what to learn to close the gap.

## How it works

1. **Skill extraction** — SkillNER (NLP library + SpaCy) pulls technical skills from both the resume and the job description, weighted by context ("required" skills score higher than "preferred").
2. **Gap analysis** — sentence-transformer embeddings (`all-MiniLM-L6-v2`) compare skills by semantic similarity, so "React.js" matches "React" even when wording differs.
3. **Learning resources** — GPT-3.5-turbo (optional) generates course and project suggestions for the top missing skills. When no API key is set the response falls back to a plain-text skill list.

## Running locally

### Prerequisites

- Python 3.10+
- Node.js 18+

### Backend

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install production dependencies
pip install -r Backend/requirements-prod.txt

# 3. Start the API (from the repo root)
cd Backend/src
uvicorn main:app --host 127.0.0.1 --port 8000
```

Startup takes ~10 s while SkillNER and SpaCy load. The first `/jobs/jobAnalyzer` request takes an extra ~20 s as the sentence-transformer model loads into memory; all subsequent requests are fast.

### Frontend

```bash
cd frontend
npm install
npm start
```

Open **http://localhost:3000/jobanalyze**, upload a PDF resume, paste a job description, and submit.

### Running tests

The test suite mocks the embedding model so no GPU, internet access, or SpaCy installation is required.

```bash
pip install -r Backend/requirements-ci.txt   # one-time, separate from the prod venv
cd Backend
pytest tests/ -v                              # 34 tests, all should pass in < 5 s
```

## Docker (backend only)

```bash
# Build (from repo root)
docker build -t skillbridge-api Backend/

# Run
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... skillbridge-api
```

The image pre-downloads the sentence-transformer model at build time, so the container starts without the usual 20 s warm-up delay.

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | No | GPT-3.5-turbo learning-resource recommendations. Omit for a plain-text fallback. |

Create `Backend/src/.env` to set variables without passing them on the command line:

```
OPENAI_API_KEY=sk-...
```

## API reference

### `POST /jobs/jobAnalyzer`

Multipart form upload.

| Field | Type | Notes |
|---|---|---|
| `file` | PDF | Text-based PDF (not a scanned image) |
| `job_description` | string | Full job posting, minimum 50 characters |
| `use_semantic` | bool | `true` (default) uses embedding similarity; `false` uses exact string matching |

**Success response**

```json
{
  "status": "success",
  "analysis_type": "semantic",
  "analysis": {
    "job_skills":        { "python": 3.0, "docker": 3.0 },
    "resume_skills":     { "python": 1.0, "javascript": 1.0 },
    "matching_skills":   { "python": { "job_weight": 3.0, "similarity_score": 1.0, ... } },
    "missing_skills":    { "docker": 3.0 },
    "resume_only_skills":{ "javascript": 1.0 }
  },
  "llm_output": "To develop Docker skills, start with..."
}
```

**Error responses** — HTTP 422 for invalid input (empty file, JD too short); HTTP 500 for unexpected server errors. PDF extraction failures return `{"status": "error", "message": "..."}` with HTTP 200 so the frontend can display the reason.

### `GET /jobs/test`

Health check. Returns `{"message": "Jobs API is working!"}`.

### `GET /`

Version info. Returns `{"message": "SkillBridge API is running", "version": "0.2.0"}`.

## Project structure

```
Backend/
  src/
    main.py                        # FastAPI app, startup, CORS
    routers/job_routes.py          # POST /jobs/jobAnalyzer endpoint
    agents/
      gap_agent.py                 # Exact string skill-gap matching
      enhanced_gap_agent.py        # Semantic (embedding-based) matching
      resource_agent.py            # GPT learning-resource recommendations
    services/
      embedding_service.py         # sentence-transformers wrapper
      optimized_job_analyzer.py    # SkillNER + SpaCy skill extraction
    utils/
      pdf_utils.py                 # pdfminer.six PDF text extraction
      numpy_converter.py           # numpy → Python type serialisation
  tests/
    test_gap_agent.py              # 18 tests — exact matching logic
    test_enhanced_gap_agent.py     # 16 tests — semantic matching logic
  Dockerfile
  requirements-prod.txt            # Production dependencies
  requirements-ci.txt              # Lightweight test-only dependencies
frontend/
  src/
    pages/Jobanalyzer.jsx          # Main UI
    pages/Home.jsx
```
