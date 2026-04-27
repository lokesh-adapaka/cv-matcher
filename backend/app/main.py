import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import cv, jobs, match

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("CV Matcher API starting up...")
    yield
    logger.info("CV Matcher API shutting down...")


app = FastAPI(
    title="AI CV Matcher & Generator",
    description="Upload your CV, find matching jobs, and generate tailored CVs",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cv.router, prefix="/api/cv", tags=["CV"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(match.router, prefix="/api/match", tags=["Match"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
