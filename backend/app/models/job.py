from pydantic import BaseModel, Field
from datetime import datetime


class Job(BaseModel):
    id: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    description: str = ""
    requirements: str = ""
    salary: str = ""
    url: str = ""
    source: str = "adzuna"
    posted_date: str = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class JobSearchResponse(BaseModel):
    jobs: list[Job] = Field(default_factory=list)
    total: int = 0
    page: int = 1


class MatchResult(BaseModel):
    job_id: str
    cv_id: str
    job_title: str = ""
    company: str = ""
    location: str = ""
    salary: str = ""
    job_url: str = ""
    match_percentage: float = 0.0
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    match_explanation: str = ""


class MatchResponse(BaseModel):
    cv_id: str
    matches: list[MatchResult] = Field(default_factory=list)
    total_jobs_analyzed: int = 0
