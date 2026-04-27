import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from app.models.job import MatchResponse
from app.services.matcher import match_cv_to_jobs

logger = logging.getLogger(__name__)
router = APIRouter()


class MatchRequest(BaseModel):
    cv_id: str
    location: str = ""
    country: str = "us"
    sources: list[str] = Field(default_factory=lambda: ["adzuna"])
    job_titles: list[str] = Field(default_factory=list)


class JDMatchRequest(BaseModel):
    cv_id: str
    job_description: str = Field(..., min_length=20)


@router.post("", response_model=MatchResponse)
async def match_cv(request: MatchRequest):
    """Match a CV against relevant job listings."""
    try:
        result = match_cv_to_jobs(
            cv_id=request.cv_id,
            location=request.location,
            country=request.country,
            sources=request.sources,
            job_titles=request.job_titles,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Matching failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to match CV against jobs")

    return MatchResponse(**result)


@router.post("/jd-analyze")
async def analyze_jd(request: JDMatchRequest):
    """Match a CV against a pasted job description and get improvement suggestions."""
    from app.db.local_db import read_item
    from app.services.ai_service import analyze_jd_match

    cv = read_item("cvs", request.cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found. Please upload your CV first.")

    # CV fields (name, skills, experience, etc.) are stored at top level
    if not cv.get("skills") and not cv.get("experience"):
        raise HTTPException(status_code=400, detail="CV has no parsed data.")

    try:
        result = analyze_jd_match(cv, request.job_description)
    except Exception as e:
        logger.error(f"JD analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze job description against CV")

    return result


@router.get("/{cv_id}", response_model=MatchResponse)
async def get_match_results(cv_id: str):
    """Retrieve stored match results for a CV."""
    from app.db.local_db import read_item

    result = read_item("matches", f"match_{cv_id}", cv_id)
    if not result:
        raise HTTPException(status_code=404, detail="No match results found for this CV")

    return MatchResponse(**result)
