import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routers import job_routes as jobs
from services.optimized_job_analyzer import skill_extractor_instance

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

os.makedirs("workspace", exist_ok=True)

app = FastAPI(title="SkillBridge API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("→ %s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("← %d", response.status_code)
    return response


app.include_router(jobs.router)


@app.get("/")
async def root():
    return {"message": "SkillBridge API is running", "version": "0.2.0"}


@app.on_event("startup")
async def startup_event():
    logger.info("Startup: loading SkillNER + SpaCy model (this may take a moment)…")
    _ = skill_extractor_instance
    logger.info("Startup complete — ready to accept requests.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
