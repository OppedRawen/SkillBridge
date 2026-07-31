# SkillBridge Codebase Audit

> Audit date: 2026-07-31  
> Branch audited: `rebuild` (HEAD `5d1a6e0`)  
> Scope: full repository, all commits, all files — read-only investigation only.

---

## 1. File / Module Inventory

### Backend (`Backend/src/`)

#### Entry Point
| File | Role |
|------|------|
| `main.py` | FastAPI app factory. Configures CORS (allows `localhost:3000`), registers `jobs.router`, creates `workspace/` and `vector_cache/` directories on startup, pre-initialises `SkillExtractorSingleton`, `EmbeddingService`, and `OptimizedVectorDatabase` during the startup event. |

#### Routers
| File | Role |
|------|------|
| `routers/job_routes.py` | **The only active router** (mounted at `/jobs`). Three endpoints: `GET /jobs/test`, `POST /jobs/jobAnalyzer` (main analysis flow), `GET /jobs/similar-skills/{skill}`. |
| `routers/resume_routes.py` | Defines `GET /` and `POST /analyze`. **Never registered** with the FastAPI app — `main.py` does not call `app.include_router(resume_routes.router)`. Dead code. |

#### Services
| File | Role | Status |
|------|------|--------|
| `services/optimized_job_analyzer.py` | **Primary skill extractor**. Singleton pattern wrapping SpaCy (`en_core_web_lg`) + SkillNER. Provides `analyze_job_description()` (extracts weighted skills using context keywords like "must", "required") and `analyze_resume()`. Loaded once at module import. | Active |
| `services/embedding_service.py` | Wraps `sentence-transformers/all-MiniLM-L6-v2` (forced to CPU). Provides `get_embedding()`, `get_embeddings()` (batched), `calculate_similarity()`, `find_best_matches()`. | Active |
| `services/optimized_vector_database.py` | In-memory ChromaDB wrapper (intended as a cache for skill embeddings). **Has a critical initialisation bug** — see Section 3. | Broken |
| `services/vector_database.py` | Earlier in-memory ChromaDB wrapper using the deprecated `chromadb.Client()` constructor. Used by `EnhancedGapAnalyzer`. Creates a brand-new empty collection on every instantiation; no persistence. | Semi-active / outdated API |
| `services/job_description_analyzer.py` | Module-level duplicate of job skill extraction (loads `nlp` and `skill_extractor` at import time). Imported by `skill_agent.py`. Functionally identical to `optimized_job_analyzer.py`. | Orphaned duplicate |
| `services/resume_analyzer.py` | Module-level duplicate of resume skill extraction. Also imported by `skill_agent.py`. Same logic as `optimized_job_analyzer.analyze_resume()`. | Orphaned duplicate |
| `services/resume_service.py` | `analyze_resume_and_job()` — full async pipeline (parse PDF via PyPDF2, extract skills, categorise missing skills using the fine-tuned sentence transformer). Belongs to the old `resume_routes.py` path. | Orphaned |
| `services/llm_service.py` | **Loads Llama-2-7b-chat-hf at module import time** (unconditionally, not lazily). Provides `generate_recommendations()`. Nobody currently imports this file. | Dead code |

#### Agents
| File | Role | Status |
|------|------|--------|
| `agents/agent_config.py` | Creates 5 AutoGen agents (UserProxy + DocumentAgent + SkillAgent + GapAgent + ResourceAgent) and a GroupChatManager. Requires `OPENAI_API_KEY`. | Active but underused |
| `agents/enhanced_gap_agent.py` | `EnhancedGapAnalyzer` — semantic skill matching using `EmbeddingService` + `VectorDatabase` (old). **This is the class actually called in the request flow.** | Active |
| `agents/optimized_gap_agent.py` | `OptimizedGapAnalyzer` — a near-identical rewrite using `OptimizedVectorDatabase` instead. Added in the final commit but **never wired into `job_routes.py`**. | Written but unreachable |
| `agents/gap_agent.py` | `identify_skill_gaps()` — simple exact-match dict comparison. Used when `use_semantic=False`. | Active (non-semantic path) |
| `agents/document_agent.py` | Registers `process_resume()` and `process_job_description()` functions with the AutoGen UserProxy. Functions are registered but **never called** through the agent framework. | Registered, never used |
| `agents/skill_agent.py` | Registers `extract_job_skills()` and `extract_resume_skills()` with UserProxy. Same situation — registered but **never invoked** through agents. | Registered, never used |
| `agents/resource_agent.py` | `get_learning_resources()` — calls **OpenAI GPT-3.5-turbo** with top-5 missing skills + job description. Returns freeform text recommendations. | Active |
| `agents/extraction_agent.py` | Old `ExtractionAgent(AssistantAgent)` class with async `generate_reply()`. Calls `analyze_resume_and_job()` from `resume_service.py`. Part of the original multi-agent design. | Dead code |
| `agents/recommendation_agent.py` | Old `RecommendationAgent(AssistantAgent)` class. Calls `self.run_llm()` (method does not exist on `AssistantAgent`). Part of the original design. | Dead code (also broken) |

#### Early Infrastructure (all orphaned)
| File | Role |
|------|------|
| `extraction/skill_extractor.py` | Simple keyword/related-terms skill matcher reading from `data/skills.json`. Replaced by SkillNER. |
| `analysis/gap_analysis.py` | `analyze_skill_gap()` — set-based matched/missing skills. Replaced by weighted dict approach. |
| `reports/report_generator.py` | `generate_report()` — formats and optionally saves a JSON skill-gap report. Never called in the active path. |
| `recommendations/recommender.py` | Empty file (1 line). |
| `parsing/resume_parser.py` | `parse_resume_pdf()` — uses PyPDF2. Used only by `resume_service.py` (itself orphaned). |
| `models/model_loader.py` | `load_ner_model()` (custom SpaCy NER) and `load_sentence_transformer()` (fine-tuned model). Used only by `resume_service.py`. |
| `models/skill_matcher.py` | BERT word-level skill matcher. Has dead code after a `return` statement (lines 51–94 are unreachable). Never imported anywhere. |
| `models/bart_summarizer.py` | BART summarisation pipeline wrapper. Never imported anywhere. |
| `manager.py` | `run_multi_agent_flow()` — orchestrates `ExtractionAgent` → `RecommendationAgent`. The original multi-agent design. Never called. |
| `utils/text_cleaning.py` | Simple `preprocess_text()` (lowercase + whitespace). Not imported anywhere in the active path. |

#### Utilities (active)
| File | Role |
|------|------|
| `utils/pdf_utils.py` | `extract_text_from_pdf()` using **pdfminer.six**. Handles file objects, file paths, and dicts with a `'file'` key. Active. |
| `utils/numpy_converter.py` | `convert_numpy_to_python()` — recursively converts NumPy types to Python natives for JSON serialisation. Active. |

#### Models on Disk
| Path | Description |
|------|-------------|
| `src/models/model-best/` | Custom SpaCy NER model trained on a labelled skills dataset. Not used in the active request path (SkillNER is used instead). |
| `src/models/fine_tuned_sentence_transformer/` | `all-mpnet-base-v2` fine-tuned on **9 training samples** via CosineSimilarityLoss. Tracked in Git LFS. Not used in the active request path (`all-MiniLM-L6-v2` from HuggingFace Hub is used instead). |

#### Data Files
| Path | Description |
|------|-------------|
| `data/skills.json` | Manual skill dictionary with `name` + `related_terms`. Used only by orphaned `extraction/skill_extractor.py`. |
| `data/Refined_Skills_Entity_Recognition.json` | Training annotation data for the custom NER model. |
| `data/auto_labeled_output.json` | Auto-labelled training data. |
| `data/train.spacy`, `data/dev.spacy` | Compiled SpaCy binary training corpora. |
| `data/config.cfg` | SpaCy NER training configuration (tok2vec + NER pipeline, 20,000 steps, GPU allocator set to `"pytorch"`). |
| `data/convert_to_spacy.py` | Script to convert JSON annotations to SpaCy `.spacy` format. |
| `data/jupyterlab/sentenceTransformers.py` | Jupyter-era experiment combining the custom NER model with sentence-transformers for soft skill detection. Not production code. |
| `data/job_title_des.csv` | CSV of job titles/descriptions. Not referenced in code. |
| `skill_db_relax_20.json` (3 copies: `Backend/`, `src/`, `src/services/`) | Large relaxed skill database. Three identical copies in different directories. Not referenced in active code. |
| `token_dist.json` (3 copies) | Token distribution data. Three copies in `Backend/`, `src/`, `src/services/`. Not referenced in active code. |
| `output/skill_gap_report.json`, `src/output/skill_gap_report.json` | Both empty. |
| `assets/Jake_s_Resume.pdf` | Sample resume for testing. |

---

### Frontend (`frontend/src/`)

| File | Role | Status |
|------|------|--------|
| `App.js` | React Router setup. Five routes: `/`, `/analyze`, `/recommendations`, `/jobs`, `/jobanalyze`. | Active |
| `components/Navbar.jsx` | Navigation links to all five routes. | Active |
| `pages/Home.jsx` | Static landing page text. | Active (trivial) |
| `pages/Jobanalyzer.jsx` | **Primary active page.** PDF upload + job description textarea + semantic toggle. POSTs to `/jobs/jobAnalyzer`, displays missing/matching/resume-only skill lists and LLM recommendations. | Active |
| `pages/ResumeAnalyzer.jsx` | PDF upload + job description. POSTs to `http://127.0.0.1:8000/resumes/analyze`. **Backend endpoint does not exist.** Expects `categorized_missing_skills` in response. | Broken (dead endpoint) |
| `pages/Recommendations.jsx` | GETs from `http://127.0.0.1:8000/recommendations` on mount. **No such endpoint exists.** Shows "No resources found, or endpoint not yet implemented." on every load. | Broken (dead endpoint) |
| `pages/Jobsearch.jsx` | Has a search input and button; the API call is commented out. Logs to console only. | Stub — never implemented |

---

## 2. End-to-End Data Flow

### Active Happy Path: `/jobanalyze` → `/jobs/jobAnalyzer`

```
User (browser)
  │ POST /jobs/jobAnalyzer  (multipart: file=PDF, job_description=str, use_semantic=bool)
  ▼
job_routes.py :: job_analyzer()
  │
  ├─ 1. create_agents()                            ← agent_config.py
  │       Creates 5 AutoGen agents + GroupChatManager.
  │       Requires OPENAI_API_KEY. Costs API init time.
  │       register_document_agent_functions(user_proxy)   ← registers functions, never called
  │       register_skill_agent_functions(user_proxy)       ← registers functions, never called
  │       EnhancedGapAnalyzer(threshold=0.7).register_functions(user_proxy)  ← registered, never called
  │       [Agents are created but no group chat is initiated — all wasted overhead]
  │
  ├─ 2. Save PDF to temp file (tempfile.NamedTemporaryFile)
  │
  ├─ 3. extract_text_from_pdf(temp_path)           ← utils/pdf_utils.py (pdfminer.six)
  │       Returns resume text string.
  │
  ├─ 4. analyze_job_description(job_description)   ← services/optimized_job_analyzer.py
  │       SpaCy + SkillNER → dict{skill_text: weight}
  │       Weight = 1.0 base + 2.0 if "must/required" nearby + 1.0 if "preferred" nearby
  │
  ├─ 5. analyze_resume(resume_text)                ← services/optimized_job_analyzer.py
  │       SpaCy + SkillNER → dict{skill_text: 1.0}
  │
  ├─ 6a. if use_semantic=True:
  │       EnhancedGapAnalyzer.identify_semantic_skill_gaps(job_skills, resume_skills)
  │         ├─ _get_or_create_embeddings(job_skills, "job")
  │         │    EmbeddingService.get_embeddings() → all-MiniLM-L6-v2 on CPU
  │         │    VectorDatabase.add_or_update_skill() → in-memory ChromaDB (ephemeral)
  │         ├─ _get_or_create_embeddings(resume_skills, "resume")
  │         └─ O(N×M) cosine similarity loop → {missing, matching, resume_only}
  │       analysis_type = "semantic"
  │
  └─ 6b. if use_semantic=False:
          identify_skill_gaps(job_skills, resume_skills)  ← agents/gap_agent.py
          Exact string match only.
          analysis_type = "exact"

  ├─ 7. get_learning_resources(missing_skills, job_description)  ← agents/resource_agent.py
  │       Calls OpenAI GPT-3.5-turbo with top 5 missing skills.
  │       Returns freeform text recommendations.
  │       [If OPENAI_API_KEY is missing/invalid → returns error string]
  │
  └─ 8. convert_numpy_to_python(response_data) → JSON response
         {status, file_name, analysis_type, analysis:{job_skills, resume_skills,
          matching_skills, missing_skills, resume_only_skills, similarity_threshold},
          llm_output}
```

### Where the Flow Breaks or Dead-Ends

| Break point | Reason |
|-------------|--------|
| AutoGen agent creation (Step 1) | Requires `OPENAI_API_KEY` even before processing begins. If missing, the entire request fails with a `ValueError` before the PDF is even read. |
| AutoGen agents after creation | The 5 agents are fully initialised (spending time and tokens) but no `user_proxy.initiate_chat()` call is ever made. They are wasted scaffolding. |
| `OptimizedVectorDatabase` (startup event) | `self.client` is referenced before being assigned. The startup event will log an error and continue, meaning `global_services['vector_db']` is never populated. |
| `optimized_gap_agent.py` | `OptimizedGapAnalyzer` was written as a replacement for `EnhancedGapAnalyzer` but is never imported or instantiated in `job_routes.py`. |
| `VectorDatabase` (old, used in `EnhancedGapAnalyzer`) | Uses `chromadb.Client()` which is deprecated and removed in chromadb ≥ 0.4. `requirements.txt` pins `chromadb==0.6.3`, so this will likely raise `AttributeError: module 'chromadb' has no attribute 'Client'` at runtime. |
| `resume_routes.py` | Router exists but is never mounted. `/resumes/analyze` returns 404. |
| `Recommendations.jsx` | Fetches `/recommendations` on page load; endpoint never implemented. Always shows "not yet implemented." |
| `ResumeAnalyzer.jsx` | Posts to `/resumes/analyze`; 404 every time. |
| `Jobsearch.jsx` | API call is commented out entirely. Search button does nothing. |

---

## 3. Incomplete, Broken, or Dead-Code Areas

### Critical Bugs

**A. `optimized_vector_database.py` — `self.client` never assigned**

```python
class OptimizedVectorDatabase:
    def __init__(self):
        try:
            self.skills_collection = self.client.get_collection(...)  # ← AttributeError here
        except Exception:
            self.skills_collection = self.client.create_collection(...)  # ← also broken
        except Exception as e:
            ...
            raise
```
There is no line that assigns `self.client`. The class is instantiated during the startup event, which catches the resulting `AttributeError`, logs it, and continues. The class is therefore never usable. `OptimizedGapAnalyzer` (which depends on it) is also broken by extension, though it is not called anyway.

**B. `vector_database.py` — uses removed ChromaDB API**

`chromadb.Client()` was removed in chromadb 0.4+. The installed version is `chromadb==0.6.3`. `VectorDatabase()`, which is used inside the active `EnhancedGapAnalyzer`, will raise `AttributeError: module 'chromadb' has no attribute 'Client'` at the start of every semantic analysis request.

**C. `agents/recommendation_agent.py` — calls non-existent method**

`self.run_llm(prompt_for_llm)` — `AssistantAgent` in AutoGen has no `run_llm()` method. This file is not called in the active path, but it would crash immediately if invoked.

**D. `services/llm_service.py` — executes at import time**

The Llama-2 tokenizer/model load and pipeline creation happen at module scope (not inside a function). Any `import` of this file blocks and tries to download ~14 GB from HuggingFace (or load from cache). Nobody currently imports it, but it is never safe to add it back without refactoring.

### Incomplete Implementations

- **`recommendations/recommender.py`** — completely empty (1 blank line).
- **`Jobsearch.jsx`** — search button does nothing; API call is commented out.
- **`Recommendations.jsx`** — page always shows "no resources found"; no backend route.
- **`reports/report_generator.py`** — logic is complete but never called from any route.
- **`data/dev.json`** — referenced by `config.cfg` but its counterpart `train.json` is not present (only compiled `.spacy` versions).
- **AutoGen group chat** — agents are created and functions are registered, but `user_proxy.initiate_chat()` (or equivalent) is never called. The multi-agent orchestration is entirely bypassed.

### Dead / Commented-Out Code

- `models/skill_matcher.py` lines 51–94: entire function body duplicated after a `return` statement (unreachable).
- `services/llm_service.py` lines 4–13 (block comment): old path-based Llama-2 loading approach; the active code uses the HuggingFace Hub path instead.
- `Jobsearch.jsx` lines 8–9: commented-out API call.
- `utils/text_cleaning.py`: imported nowhere; only defines `preprocess_text()`.

---

## 4. Abandoned Experiments / Duplicate Approaches

The codebase contains two distinct "generations" of implementation that overlap extensively.

### Generation 1 (commits `1d3fe21` → `c1dfdde`, roughly Jan 2025)
- Custom SpaCy NER model trained on labelled skills data → `models/model-best/`
- Fine-tuned sentence transformer on 9 samples → `models/fine_tuned_sentence_transformer/`
- PyPDF2 for PDF parsing → `parsing/resume_parser.py`
- Manual skill dictionary → `data/skills.json`
- Simple set-based gap analysis → `analysis/gap_analysis.py`
- Async custom agent classes (ExtractionAgent + RecommendationAgent + manager) → `agents/extraction_agent.py`, `agents/recommendation_agent.py`, `manager.py`
- Local Llama-2-7b for recommendations → `services/llm_service.py`
- BART summariser → `models/bart_summarizer.py`
- BERT word-level skill matching → `models/skill_matcher.py`

### Generation 2 (commits `a41cbb2` → `ff39f71`, Feb–Mar 2025)
- SkillNER library (EMSI database) replaces the custom NER → `services/optimized_job_analyzer.py`
- pdfminer.six replaces PyPDF2 → `utils/pdf_utils.py`
- `all-MiniLM-L6-v2` from HuggingFace Hub replaces the fine-tuned model → `services/embedding_service.py`
- OpenAI GPT-3.5-turbo replaces Llama-2 → `agents/resource_agent.py`
- AutoGen framework replaces hand-rolled async agents → `agents/agent_config.py`
- ChromaDB in-memory replaces raw NumPy cosine search → `services/vector_database.py` → `services/optimized_vector_database.py`
- Weighted dict gap analysis replaces set-based → `agents/gap_agent.py`, `agents/enhanced_gap_agent.py`, `agents/optimized_gap_agent.py`

Generation 1 files were **left in place** rather than deleted. All are still on disk and many are still imported (triggering redundant model loads at startup).

### Specific Duplications

| Concern | Approach A | Approach B |
|---------|-----------|-----------|
| PDF text extraction | `parsing/resume_parser.py` (PyPDF2) | `utils/pdf_utils.py` (pdfminer.six) |
| Job skill extraction | `services/job_description_analyzer.py` (module-level) | `services/optimized_job_analyzer.py` (singleton class) |
| Resume skill extraction | `services/resume_analyzer.py` (module-level) | `services/optimized_job_analyzer.py` (singleton class) |
| Vector storage | `services/vector_database.py` (`chromadb.Client()`) | `services/optimized_vector_database.py` (missing client init) |
| Gap analysis — exact | `analysis/gap_analysis.py` (set-based) | `agents/gap_agent.py` (dict-based) |
| Gap analysis — semantic | `agents/enhanced_gap_agent.py` (uses old VectorDatabase) | `agents/optimized_gap_agent.py` (uses broken OptimizedVectorDatabase) |
| LLM for recommendations | `services/llm_service.py` (Llama-2-7b, local) | `agents/resource_agent.py` (OpenAI GPT-3.5-turbo) |
| Skill corpus | `data/skills.json` (manual) | `skillNer.general_params.SKILL_DB` (EMSI) |
| `skill_db_relax_20.json` | `Backend/skill_db_relax_20.json` | `Backend/src/skill_db_relax_20.json` | (also `Backend/src/services/skill_db_relax_20.json`) |
| `token_dist.json` | `Backend/token_dist.json` | `Backend/src/token_dist.json` (also `Backend/src/services/token_dist.json`) |

The `skill_db_relax_20.json` and `token_dist.json` files appear three times each without any code in the active path referencing them.

### Startup Redundancy
Because `skill_agent.py` imports `job_description_analyzer.py` and `resume_analyzer.py`, and `job_routes.py` imports `skill_agent.py`, the SpaCy `en_core_web_lg` model and SkillNER are loaded **twice** at startup: once via `optimized_job_analyzer.py` (singleton) and once more via the module-level load in `job_description_analyzer.py`. This doubles memory usage for the NLP model on startup.

---

## 5. Dependencies, Environment Variables, and External Services

### Environment Variables Required

| Variable | Where used | Required for |
|----------|-----------|--------------|
| `OPENAI_API_KEY` | `agents/agent_config.py`, `agents/resource_agent.py` | AutoGen agent initialisation + GPT-3.5-turbo learning resource generation. **If missing, every `/jobs/jobAnalyzer` request fails immediately at Step 1 (agent creation).** |

No `.env.example` file exists. No setup documentation explains how to create a `.env` file. The `Backend/.gitIgnore` correctly excludes `.env` from version control.

### External Services

| Service | Usage | Notes |
|---------|-------|-------|
| **OpenAI API** | `agents/resource_agent.py` — GPT-3.5-turbo for recommendations. `agents/agent_config.py` — LLM config for AutoGen agents. | Requires a paid API key. Called on every analysis request. |
| **HuggingFace Hub** | `services/embedding_service.py` — downloads `all-MiniLM-L6-v2` on first run. | Downloaded to local cache; subsequent runs use cache. Forced to CPU via `CUDA_VISIBLE_DEVICES=-1`. |
| **ChromaDB** (in-memory) | `services/vector_database.py`, `services/optimized_vector_database.py` | No persistence across requests; acts as a per-request embedding cache only. `chromadb==0.6.3` is pinned but the `chromadb.Client()` API used in `vector_database.py` was removed before 0.6. |

### Python Dependencies of Note

The `requirements.txt` is a full pip-freeze dump (232 packages) including JupyterLab, Jupyter kernels, `cupy-cuda12x`, and `bitsandbytes` — all development-only tools that are never required for the production server.

| Package | Version | Status |
|---------|---------|--------|
| `fastapi` | 0.115.6 | Active |
| `uvicorn` | 0.34.0 | Active |
| `spacy` | 3.8.3 | Active |
| `en_core_web_lg` | 3.8.0 | Active (installed from GitHub release URL) |
| `skillNer` | 1.0.3 | Active |
| `sentence-transformers` | 3.3.1 | Active |
| `chromadb` | 0.6.3 | Active but both wrappers are broken |
| `openai` | 1.65.3 | Active (new SDK syntax used correctly) |
| `autogen` / `pyautogen` | 0.7.6 | Installed; agents created but not orchestrated |
| `pdfminer.six` | 20240706 | Active |
| `torch` | 2.5.1 | Active (via sentence-transformers) |
| `transformers` | 4.48.0 | Active (via sentence-transformers) |
| `PyPDF2` | 3.0.1 | Orphaned (only `resume_parser.py` which is orphaned) |
| `python-dotenv` | 1.0.1 | Active |

### Setup Instructions — What Exists vs. What's Needed

**What exists:**
- `README.md` — states features and known issues. No setup steps.
- `Backend/.gitIgnore` — standard Python gitignore.
- `Backend/.gitattributes` — Git LFS tracking for model files.

**What is missing:**
- No `.env.example` showing required environment variables.
- No instructions for which Python version to use (code uses f-strings throughout; Python 3.8+ assumed; `models/fine_tuned_sentence_transformer/README.md` states Python 3.12.0 was used for training).
- No instructions for how to install dependencies (`pip install -r Backend/requirements.txt`).
- No instructions for how to start the backend (`uvicorn main:app --reload` from `Backend/src/`).
- No instructions for how to start the frontend (`npm start` from `frontend/`).
- No instructions for when to run `data/convert_to_spacy.py` or how to retrain the NER model.
- No database setup required (ChromaDB is in-memory only).

---

## Summary Table of Active vs. Dead Code

| Module | Active? | Notes |
|--------|---------|-------|
| `main.py` | Yes | Startup bug: OptimizedVectorDatabase fails silently |
| `routers/job_routes.py` | Yes | AutoGen agents wasted; chromadb call will fail |
| `routers/resume_routes.py` | **No** | Not mounted in app |
| `services/optimized_job_analyzer.py` | Yes | Core skill extractor; loads at import |
| `services/embedding_service.py` | Yes | Loaded per-request via EnhancedGapAnalyzer |
| `services/optimized_vector_database.py` | **No** | `self.client` bug, never usable |
| `services/vector_database.py` | **Broken** | Uses removed `chromadb.Client()` API |
| `services/job_description_analyzer.py` | **No** | Orphaned duplicate; causes double model load |
| `services/resume_analyzer.py` | **No** | Orphaned duplicate; causes double model load |
| `services/resume_service.py` | **No** | Belongs to unregistered resume route |
| `services/llm_service.py` | **No** | Dead; crashes on import |
| `agents/agent_config.py` | Partial | Agents created but not orchestrated |
| `agents/enhanced_gap_agent.py` | **Broken** | Uses broken `VectorDatabase` |
| `agents/optimized_gap_agent.py` | **No** | Written but never called from routes |
| `agents/gap_agent.py` | Yes (non-semantic path) | Simple exact match |
| `agents/document_agent.py` | **No** | Functions registered, never invoked |
| `agents/skill_agent.py` | **No** | Functions registered, never invoked |
| `agents/resource_agent.py` | Yes | Calls OpenAI API |
| `agents/extraction_agent.py` | **No** | Old design, broken `run_llm()` |
| `agents/recommendation_agent.py` | **No** | Old design, broken `run_llm()` |
| `manager.py` | **No** | Old orchestrator, never called |
| `extraction/skill_extractor.py` | **No** | Replaced by SkillNER |
| `analysis/gap_analysis.py` | **No** | Replaced by weighted approach |
| `reports/report_generator.py` | **No** | Never called from routes |
| `recommendations/recommender.py` | **No** | Empty file |
| `parsing/resume_parser.py` | **No** | Used only by orphaned resume_service |
| `models/model_loader.py` | **No** | Used only by orphaned resume_service |
| `models/skill_matcher.py` | **No** | Dead code; dead code within dead code |
| `models/bart_summarizer.py` | **No** | Never imported |
| `utils/pdf_utils.py` | Yes | Active |
| `utils/numpy_converter.py` | Yes | Active |
| `utils/text_cleaning.py` | **No** | Never imported |
| `pages/Jobanalyzer.jsx` | Yes | Primary UI |
| `pages/ResumeAnalyzer.jsx` | **Broken** | Hits dead endpoint |
| `pages/Recommendations.jsx` | **Broken** | Hits dead endpoint |
| `pages/Jobsearch.jsx` | **No** | Stub only |
| `pages/Home.jsx` | Yes (trivial) | Static text |
