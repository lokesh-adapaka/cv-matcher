import logging
from fastapi import APIRouter, Query, HTTPException
from app.models.job import JobSearchResponse, Job
from app.services.job_service import search_jobs, VALID_SOURCES
from app.services.scrapers.rate_limiter import remaining, DAILY_LIMIT

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search", response_model=JobSearchResponse)
async def search_jobs_endpoint(
    skills: str = Query(..., description="Comma-separated list of skills to search for"),
    location: str = Query("", description="Location filter (city, state, or country)"),
    country: str = Query("us", description="Country code (us, gb, de, at, etc.)"),
    page: int = Query(1, ge=1, description="Page number"),
    sources: str = Query(
        "adzuna",
        description="Comma-separated job sources: adzuna, linkedin, stepstone, all",
    ),
    job_titles: str = Query(
        "",
        description="Comma-separated job titles to filter results by",
    ),
):
    """Search for jobs matching the given skills across one or more sources."""
    skill_list = [s.strip() for s in skills.split(",") if s.strip()]
    if not skill_list:
        raise HTTPException(status_code=400, detail="At least one skill is required")

    source_list = [s.strip().lower() for s in sources.split(",") if s.strip()]
    invalid = set(source_list) - VALID_SOURCES
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sources: {', '.join(invalid)}. Valid: {', '.join(sorted(VALID_SOURCES))}",
        )

    title_list = [t.strip() for t in job_titles.split(",") if t.strip()] if job_titles else []

    try:
        jobs, total = search_jobs(
            skill_list, location=location, country=country, page=page,
            sources=source_list, job_titles=title_list or None,
        )
    except Exception as e:
        logger.error(f"Job search failed: {e}")
        raise HTTPException(status_code=500, detail="Job search failed")

    return JobSearchResponse(
        jobs=[Job(**j) for j in jobs],
        total=total,
        page=page,
    )


@router.get("/rate-limits")
async def get_rate_limits():
    """Return remaining daily scrape requests per source."""
    return {
        "daily_limit": DAILY_LIMIT,
        "remaining": {
            "linkedin": remaining("linkedin"),
            "stepstone": remaining("stepstone"),
        },
    }
