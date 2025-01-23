from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import resume_routes
from routers import job_routes
def create_app():
    app = FastAPI(title="Skill Gap Analysis API")

    # CORS settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(resume_routes.router, prefix="/resumes", tags=["Resumes"])
    app.include_router(job_routes.router, prefix="/jobs", tags=["Jobs"])

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
