import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routers import job_routes as jobs
from services.optimized_job_analyzer import skill_extractor_instance

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Create workspace directory if it doesn't exist
workspace_dir = "workspace"
if not os.path.exists(workspace_dir):
    os.makedirs(workspace_dir)
    logger.info(f"Created workspace directory: {workspace_dir}")

# Initialize the FastAPI app
app = FastAPI(title="Skill Bridge API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request path: {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status code: {response.status_code}")
    return response

# Include routers
app.include_router(jobs.router)

@app.get("/")
async def root():
    """Root endpoint to verify API is running."""
    logger.info("Root endpoint called")
    return {"message": "Skill Bridge API is running"}

# Application startup event
@app.on_event("startup")
async def startup_event():
    """Initialize resources when the application starts."""
    logger.info("Starting application initialization...")
    
    # Pre-initialize the skill extractor singleton
    # This forces initialization during startup instead of on first request
    _ = skill_extractor_instance
    
    logger.info("Application initialization complete")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)