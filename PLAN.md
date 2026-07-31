# SkillBridge — Implementation Plan

> Status: **DRAFT — awaiting approval before any code changes**  
> Based on: AUDIT.md (2026-07-31)  
> Goal: one complete, reliable end-to-end flow

---

## Target Flow (What "Done" Looks Like)

```
User visits /jobanalyze
  → uploads PDF resume + pastes job description
  → clicks Analyze
  → sees:
      • Missing skills  (ranked by importance)
      • Matched skills  (with semantic similarity score if in semantic mode)
      • Extra skills on resume (not required by the job)
      • Learning recommendations  (from OpenAI, or a clear "no API key" message)
```

This is exactly what `Jobanalyzer.jsx` already renders — the UI itself needs almost no changes. Every problem is in the backend pipeline.

---

## Root Causes to Fix (in priority order)

| # | Problem | Impact |
|---|---------|--------|
| 1 | AutoGen `create_agents()` called on every request | Fails immediately if `OPENAI_API_KEY` is absent; wastes ~1 s and API quota even when present; agents do nothing useful |
| 2 | `EnhancedGapAnalyzer` uses `VectorDatabase` which calls `chromadb.Client()` (removed in v0.4+) | Semantic analysis crashes on every request |
| 3 | `skill_agent.py` imports `job_description_analyzer.py` and `resume_analyzer.py` at module level | SpaCy `en_core_web_lg` + SkillNER loaded twice, doubling startup memory |
| 4 | Startup event tries to instantiate `OptimizedVectorDatabase` (broken: `self.client` never assigned) | Logged error on every startup; confusing but not fatal |
| 5 | `OPENAI_API_KEY` is required for agent creation even when the LLM is only needed at the end | Any missing-key error prevents skill analysis entirely |

---

## Verdict on Every Existing File

### `Backend/src/` — Core Application

| File | Verdict | Reason |
|------|---------|--------|
| `main.py` | **KEEP, refactor** | Remove `OptimizedVectorDatabase` from the startup event; the rest (CORS, router registration, `skill_extractor_instance` pre-load) is correct. |
| `routers/job_routes.py` | **KEEP, refactor** | Remove the `create_agents()` block entirely from the request handler; the rest of the pipeline (extract → analyze → gap → resources) is the right structure. |
| `routers/resume_routes.py` | **DISCARD** | Router is never mounted, hits a dead service, and duplicates the job analyzer flow; no value in keeping it. |

### `Backend/src/services/`

| File | Verdict | Reason |
|------|---------|--------|
| `services/optimized_job_analyzer.py` | **KEEP as-is** | The singleton pattern, SkillNER integration, and contextual weight computation are the best skill extraction in the repo; no changes needed. |
| `services/embedding_service.py` | **KEEP as-is** | Clean wrapper around `all-MiniLM-L6-v2`; CPU-forced correctly; `calculate_similarity()` is all we need. |
| `services/vector_database.py` | **DISCARD** | `chromadb.Client()` was removed from the installed version; the in-memory cache is ephemeral per-request anyway so provides no real benefit; replacing with direct numpy similarity is simpler and faster. |
| `services/optimized_vector_database.py` | **DISCARD** | Has the `self.client` bug and is never called from any route; superseded by the refactored gap analyzer. |
| `services/job_description_analyzer.py` | **DISCARD** | Exact duplicate of `optimized_job_analyzer.py` logic; only reason it exists is as a transitional file; removing it fixes the double model-load at startup. |
| `services/resume_analyzer.py` | **DISCARD** | Same as above — duplicate of `optimized_job_analyzer.analyze_resume()`; remove to fix double load. |
| `services/resume_service.py` | **DISCARD** | Belongs entirely to the dead `resume_routes.py` path; uses orphaned `model_loader.py` and PyPDF2. |
| `services/llm_service.py` | **DISCARD** | Loads Llama-2-7b at import time unconditionally; nobody imports it now; dangerous to leave in the project. |

### `Backend/src/agents/`

| File | Verdict | Reason |
|------|---------|--------|
| `agents/agent_config.py` | **DISCARD from request path** (keep file, stop calling it) | The 5-agent AutoGen setup is wasted overhead; agents are never orchestrated; removing the `create_agents()` call from the route eliminates the hard `OPENAI_API_KEY` dependency at the start of every request. The file itself can stay for future use. |
| `agents/enhanced_gap_agent.py` | **KEEP, refactor** | The semantic matching logic (`identify_semantic_skill_gaps`, `_get_or_create_embeddings`, embedding comparison loop) is correct and is the code actually called in the flow; just replace `VectorDatabase` with direct calls to `EmbeddingService`. |
| `agents/optimized_gap_agent.py` | **DISCARD** | Near-identical to `enhanced_gap_agent.py` but uses the broken `OptimizedVectorDatabase` and is never wired into any route; the refactored `enhanced_gap_agent.py` replaces it. |
| `agents/gap_agent.py` | **KEEP as-is** | Clean, simple exact-match fallback (`use_semantic=False` path); 80 lines, no dependencies, no bugs. |
| `agents/resource_agent.py` | **KEEP, small refactor** | The OpenAI call is correct (new SDK syntax); only change needed is graceful fallback when `OPENAI_API_KEY` is absent so it returns an informative string instead of raising. |
| `agents/document_agent.py` | **DISCARD** | Functions are registered with the AutoGen proxy but never invoked; PDF extraction is done directly in the route using `pdf_utils.py`. |
| `agents/skill_agent.py` | **DISCARD** | Same situation — registered, never called, and its imports of `job_description_analyzer.py` / `resume_analyzer.py` are what cause the double model load; removing it fixes that. |
| `agents/extraction_agent.py` | **DISCARD** | Old design; `self.run_llm()` doesn't exist; dead code. |
| `agents/recommendation_agent.py` | **DISCARD** | Old design; same broken `self.run_llm()` issue; dead code. |

### `Backend/src/` — Early Infrastructure (all Generation 1)

| File | Verdict | Reason |
|------|---------|--------|
| `extraction/skill_extractor.py` | **DISCARD** | Simple keyword matcher replaced by SkillNER; `data/skills.json` it depends on is not maintained. |
| `analysis/gap_analysis.py` | **DISCARD** | Set-based gap analysis replaced by the weighted dict approach in `gap_agent.py`. |
| `reports/report_generator.py` | **DISCARD** | Never called from any route; formatting logic is trivial to re-add later if needed. |
| `recommendations/recommender.py` | **DISCARD** | Empty file. |
| `parsing/resume_parser.py` | **DISCARD** | PyPDF2-based; used only by orphaned `resume_service.py`. |
| `manager.py` | **DISCARD** | Old orchestrator for the two broken agent classes; dead code. |
| `models/model_loader.py` | **DISCARD** | Used only by orphaned `resume_service.py`; the custom NER and fine-tuned ST are not in the active path. |
| `models/skill_matcher.py` | **DISCARD** | Dead code with unreachable code inside it; never imported. |
| `models/bart_summarizer.py` | **DISCARD** | Never imported anywhere. |

### `Backend/src/utils/`

| File | Verdict | Reason |
|------|---------|--------|
| `utils/pdf_utils.py` | **KEEP as-is** | Handles all three input forms (file object, path string, dict); uses pdfminer.six correctly. |
| `utils/numpy_converter.py` | **KEEP as-is** | Necessary and correct; prevents NumPy serialisation errors in JSON responses. |
| `utils/text_cleaning.py` | **DISCARD** | Never imported; trivial enough to inline if ever needed. |

### Models on Disk

| Path | Verdict | Reason |
|------|---------|--------|
| `src/models/model-best/` | **KEEP (do not delete)** | Custom SpaCy NER trained on project data; not in the active path today but may be valuable if SkillNER coverage proves insufficient. Keep for now; document that it is unused. |
| `src/models/fine_tuned_sentence_transformer/` | **UNCERTAIN** | Fine-tuned on only 9 samples — almost certainly not better than `all-MiniLM-L6-v2`. I'd recommend keeping the files (they're in LFS, so they cost no checkout weight) but not using them until the training set is meaningfully expanded. |

### Data Files

| Path | Verdict | Reason |
|------|---------|--------|
| `data/skills.json` | **KEEP (do not delete)** | Used by the custom NER training pipeline; not in the active path but part of the model lineage. |
| `data/Refined_Skills_Entity_Recognition.json`, `auto_labeled_output.json`, `train.spacy`, `dev.spacy`, `config.cfg`, `convert_to_spacy.py` | **KEEP (do not delete)** | NER training artefacts; no active path dependency but required if NER is ever retrained. |
| `data/jupyterlab/sentenceTransformers.py` | **KEEP (do not delete)** | Jupyter experiment; harmless in `data/`; not imported anywhere. |
| `skill_db_relax_20.json` (×3 copies) | **KEEP one, delete two** | Three identical copies; keep the one in `Backend/` root; delete `src/` and `src/services/` copies. None are imported in active code — flag as **uncertain** whether this file is needed for SkillNER or is truly orphaned. |
| `token_dist.json` (×3 copies) | **Same as above** | Keep `Backend/` copy, delete the two `src/` copies; unknown whether it feeds any active path. |
| `data/job_title_des.csv` | **KEEP (do not delete)** | Not referenced in code but may be source training data; harmless. |
| `assets/Jake_s_Resume.pdf` | **KEEP** | Useful for manual end-to-end testing. |

### Frontend

| File | Verdict | Reason |
|------|---------|--------|
| `src/App.js` | **KEEP, minor edit** | Remove routes for `/analyze`, `/recommendations`, `/jobs` until those features exist; they currently lead to broken pages. |
| `src/components/Navbar.jsx` | **KEEP, minor edit** | Remove links to the three broken pages. |
| `src/pages/Home.jsx` | **KEEP as-is** | Placeholder; harmless. |
| `src/pages/Jobanalyzer.jsx` | **KEEP as-is** | This page is almost completely correct; it already handles both semantic and exact modes, shows all three skill buckets, and displays LLM output. No changes needed unless the backend response shape changes. |
| `src/pages/ResumeAnalyzer.jsx` | **DISCARD** | Hits a permanently dead endpoint (`/resumes/analyze`); the `Jobanalyzer.jsx` already covers the same user need better. |
| `src/pages/Recommendations.jsx` | **DISCARD** | Hits a non-existent endpoint; recommendations are now embedded in the `Jobanalyzer.jsx` response. |
| `src/pages/Jobsearch.jsx` | **DISCARD** | API call is commented out; provides no functionality. Remove the route and page. |

---

## Concrete Changes Required

### Change 1 — Fix `EnhancedGapAnalyzer` (`agents/enhanced_gap_agent.py`)

**What to do:** Remove the `VectorDatabase` import and all `self.vector_db.*` calls. Replace `_get_or_create_embeddings()` with a simple method that calls `self.embedding_service.get_embeddings()` directly and returns the list. Keep the similarity loop and result structure exactly as-is.

**Why:** `VectorDatabase` uses `chromadb.Client()` which was removed from `chromadb==0.6.3`. The in-memory cache it provided is ephemeral per-request anyway (a new `VectorDatabase()` was created on every request), so removing it has zero functional cost.

**Risk:** Low. The embedding logic and cosine comparison are identical; only the caching layer is removed.

---

### Change 2 — Remove AutoGen from the request handler (`routers/job_routes.py`)

**What to do:** Delete the `create_agents()` block (the `try/except` at lines 53–76), the `register_document_agent_functions()` call, the `register_skill_agent_functions()` call, and the `enhanced_gap_analyzer.register_functions()` call. Remove the imports of `agent_config`, `document_agent`, `skill_agent`. Keep the `EnhancedGapAnalyzer` import and instantiation.

**Why:** The agents are created but never orchestrated; removing them eliminates the hard `OPENAI_API_KEY` pre-requisite, removes ~0.5–1 s of overhead, and removes a blocking failure mode.

**Risk:** Low. No agent messages are currently sent; nothing in the actual processing path changes.

---

### Change 3 — Fix startup event and imports (`main.py`)

**What to do:** Remove `OptimizedVectorDatabase` from the startup event (and its import). Keep `EmbeddingService` pre-init if desired, but it is not strictly needed since `EnhancedGapAnalyzer` creates its own instance. The critical pre-init is `skill_extractor_instance` — keep that.

**Why:** `OptimizedVectorDatabase.__init__` references `self.client` before it is assigned; the current startup event logs an error and sets no global service — confusing.

**Risk:** None. `OptimizedVectorDatabase` is not used anywhere after this fix.

---

### Change 4 — Remove duplicate model-loading imports

**What to do:** In `routers/job_routes.py`, remove the import of `agents.skill_agent` (`register_skill_agent_functions`). `skill_agent.py` imports `job_description_analyzer.py` and `resume_analyzer.py`, both of which load `en_core_web_lg` + SkillNER at module scope, doubling startup memory.

**Why:** The actual skill extraction already comes from `optimized_job_analyzer.py` (the singleton); the module-level loaders in `job_description_analyzer.py` and `resume_analyzer.py` are never called.

**Risk:** Low. The registered functions are never invoked anyway.

---

### Change 5 — Make OpenAI key optional (`agents/resource_agent.py`)

**What to do:** Wrap `OpenAI(api_key=...)` in a `try/except` or check `os.getenv("OPENAI_API_KEY")` at the top of `get_learning_resources()`; if the key is absent or the call fails, return a graceful string like `"Learning resources unavailable (OPENAI_API_KEY not configured)."` instead of raising.

**Why:** The skill gap analysis itself has no dependency on OpenAI; users should receive their skill breakdown even without an API key.

**Risk:** None; purely additive fallback.

---

### Change 6 — Clean up frontend routes (`App.js`, `Navbar.jsx`)

**What to do:** Remove the `/analyze`, `/recommendations`, and `/jobs` routes from `App.js` and remove their `<Link>` entries from `Navbar.jsx`. Remove (or archive) `ResumeAnalyzer.jsx`, `Recommendations.jsx`, `Jobsearch.jsx`.

**Why:** Three pages that currently show broken behaviour or do nothing mislead users and obscure what actually works.

**Risk:** None; removing non-functional routes is safe.

---

## File Disposition Summary

### Files to modify (6 total)
1. `Backend/src/main.py` — remove `OptimizedVectorDatabase` from startup
2. `Backend/src/routers/job_routes.py` — remove AutoGen block + skill_agent import
3. `Backend/src/agents/enhanced_gap_agent.py` — remove ChromaDB dependency
4. `Backend/src/agents/resource_agent.py` — add graceful fallback for missing API key
5. `frontend/src/App.js` — remove three broken routes
6. `frontend/src/components/Navbar.jsx` — remove three broken links

### Files to delete (18 total)
**Backend:**
- `src/routers/resume_routes.py`
- `src/services/vector_database.py`
- `src/services/optimized_vector_database.py`
- `src/services/job_description_analyzer.py`
- `src/services/resume_analyzer.py`
- `src/services/resume_service.py`
- `src/services/llm_service.py`
- `src/agents/optimized_gap_agent.py`
- `src/agents/document_agent.py`
- `src/agents/skill_agent.py`
- `src/agents/extraction_agent.py`
- `src/agents/recommendation_agent.py`
- `src/manager.py`
- `src/extraction/skill_extractor.py`
- `src/analysis/gap_analysis.py`
- `src/reports/report_generator.py`
- `src/recommendations/recommender.py`
- `src/parsing/resume_parser.py`
- `src/models/model_loader.py`
- `src/models/skill_matcher.py`
- `src/models/bart_summarizer.py`
- `src/utils/text_cleaning.py`

**Frontend:**
- `src/pages/ResumeAnalyzer.jsx`
- `src/pages/Recommendations.jsx`
- `src/pages/Jobsearch.jsx`

**Data (duplicates only — keep originals):**
- `src/skill_db_relax_20.json` (keep `Backend/skill_db_relax_20.json`)
- `src/services/skill_db_relax_20.json`
- `src/token_dist.json` (keep `Backend/token_dist.json`)
- `src/services/token_dist.json`

### Files to keep untouched
- `src/main.py` — after Change 3 above
- `src/agents/gap_agent.py`
- `src/agents/agent_config.py` (kept in place, just not called from the route)
- `src/services/optimized_job_analyzer.py`
- `src/services/embedding_service.py`
- `src/utils/pdf_utils.py`
- `src/utils/numpy_converter.py`
- `src/models/model-best/` (entire directory)
- `src/models/fine_tuned_sentence_transformer/` (entire directory)
- All `data/` training artefacts
- `frontend/src/pages/Jobanalyzer.jsx`
- `frontend/src/pages/Home.jsx`
- `frontend/package.json`, `tailwind.config.js`, etc.
- `Backend/requirements.txt` (no changes yet — see open question below)
- `README.md` (update after code is working)

---

## Open Questions / Uncertainties

**1. Is `chromadb` still needed after the ChromaDB removal?**
After removing `vector_database.py` and `optimized_vector_database.py`, `chromadb` has no callers. It can likely be removed from `requirements.txt` — but I want to verify nothing else imports it before recommending that.

**2. Are `skill_db_relax_20.json` and `token_dist.json` used by SkillNER internally?**
These files appear in `Backend/` root and in two `src/` subdirectories but are not referenced in any Python `import` or `open()` call I found. It is possible SkillNER's `SKILL_DB` writes or reads them at runtime. **I recommend leaving all three copies in place until the app is running and we can confirm whether SkillNER touches them** — then delete the two `src/` duplicates.

**3. Does `agent_config.py` need `OPENAI_API_KEY` at import time?**
The `get_config_list()` function reads the env var but is only called inside `create_agents()`. Once `create_agents()` is removed from the request path, the import of `agent_config.py` is harmless even without a key. I believe this is safe, but it should be confirmed after the route change.

**4. Should semantic mode default to `True` or `False` after the ChromaDB fix?**
Currently the frontend defaults to `use_semantic=True`. After fixing `EnhancedGapAnalyzer`, semantic mode should work correctly. I recommend keeping the default as `True` — but flagging this because the semantic path is slower (embedding generation per request) and has not been tested after the fix.

**5. The `VectorDatabase` removal eliminates per-request embedding caching.**
The old design cached embeddings in ChromaDB so repeated skills across requests could avoid re-embedding. Since `VectorDatabase` was in-memory and ephemeral anyway (new instance per request), this cache was never actually used across requests — so removing it has zero functional cost. **However**, if the goal is to add a persistent cache later, that is a separate feature, not part of this plan.

**6. `requirements.txt` cleanup**
The requirements file includes ~80 packages that are development/Jupyter tools (`jupyterlab`, `ipykernel`, `cupy-cuda12x`, `bitsandbytes`, etc.) and have no runtime role. Splitting into `requirements.txt` (runtime) and `requirements-dev.txt` (development) is good hygiene — but out of scope for getting the flow working. Flag for a follow-up task.

---

## What This Plan Does NOT Address

- The custom NER model (`model-best/`) and fine-tuned sentence transformer are kept but remain unused. Integrating them is a future decision.
- The `/recommendations`, `/jobs/search` routes are removed, not rebuilt. They are separate features.
- No database is introduced. State is entirely per-request.
- No authentication, rate limiting, or error monitoring.
- No production deployment configuration (the app currently assumes `localhost`).
- No automated tests. Manual testing with `assets/Jake_s_Resume.pdf` is the verification path for now.

---

*Awaiting approval before any code changes.*
