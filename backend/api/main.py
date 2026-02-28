from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.routes import auth, documents, workflows, prompts, analyze, executions, audit_logs, compliance, users, rbac, legal_research
from api import analytics, case_analytics
from models.database import Base, engine, get_db
from services.metrics_service import PrometheusMiddleware, get_metrics_response
from sqlalchemy.orm import Session

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (only if not in testing)
    import os
    if os.getenv("TESTING") != "true":
        Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Veritas AI API", lifespan=lifespan)

# Register Prometheus Middleware
app.add_middleware(PrometheusMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a master API router
api_router = APIRouter(prefix="/api")

# Mount routers to api_router
api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(workflows.router)
api_router.include_router(prompts.router)
api_router.include_router(analyze.router)
api_router.include_router(executions.router)
api_router.include_router(audit_logs.router)
api_router.include_router(compliance.router)
api_router.include_router(users.router)
api_router.include_router(rbac.router)
api_router.include_router(legal_research.router)
api_router.include_router(analytics.router)
api_router.include_router(case_analytics.router)

# Include the master router in the app
app.include_router(api_router)

@app.get("/api/metrics")
async def metrics():
    return get_metrics_response()

@app.get("/api/ping-db")
async def ping_db(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "veritas-ai-api"}


@app.get("/")
async def root():
    return {"message": "Welcome to Veritas AI API"}
