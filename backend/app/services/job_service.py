from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta
import httpx
from app.config import get_settings
from app.db.local_db import upsert_item, query_items
from app.services.scrapers.linkedin import scrape_linkedin_jobs
from app.services.scrapers.stepstone import scrape_stepstone_jobs
from app.services.scrapers.rate_limiter import RateLimitExceeded, remaining

logger = logging.getLogger(__name__)

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs"
JOB_CACHE_TTL_HOURS = 24


def _generate_job_id(source: str, external_id: str) -> str:
    raw = f"{source}_{external_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _is_cache_valid(job: dict) -> bool:
    created = job.get("created_at", "")
    if not created:
        return False
    try:
        created_dt = datetime.fromisoformat(created)
        return datetime.utcnow() - created_dt < timedelta(hours=JOB_CACHE_TTL_HOURS)
    except ValueError:
        return False


def search_jobs_adzuna(
    keywords: list[str],
    location: str = "",
    country: str = "us",
    page: int = 1,
    results_per_page: int = 20,
) -> list[dict]:
    """Search jobs via the Adzuna API."""
    settings = get_settings()

    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        logger.warning("Adzuna API credentials not configured")
        return []

    query = " ".join(keywords)
    params = {
        "app_id": settings.adzuna_app_id,
        "app_key": settings.adzuna_app_key,
        "results_per_page": results_per_page,
        "what": query,
        "content-type": "application/json",
    }
    if location:
        params["where"] = location

    url = f"{ADZUNA_BASE_URL}/{country}/search/{page}"

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as e:
        logger.error(f"Adzuna API request failed: {e}")
        return []

    jobs = []
    for result in data.get("results", []):
        job_id = _generate_job_id("adzuna", str(result.get("id", "")))
        salary_min = result.get("salary_min", "")
        salary_max = result.get("salary_max", "")
        salary = ""
        if salary_min and salary_max:
            salary = f"${int(salary_min):,} - ${int(salary_max):,}"
        elif salary_min:
            salary = f"From ${int(salary_min):,}"

        job = {
            "id": job_id,
            "title": result.get("title", ""),
            "company": result.get("company", {}).get("display_name", ""),
            "location": result.get("location", {}).get("display_name", ""),
            "description": result.get("description", ""),
            "requirements": "",  # Adzuna doesn't separate requirements
            "salary": salary,
            "url": result.get("redirect_url", ""),
            "source": "adzuna",
            "created_at": datetime.utcnow().isoformat(),
        }
        jobs.append(job)

        # Cache in CosmosDB
        try:
            upsert_item("jobs", job)
        except Exception as e:
            logger.warning(f"Failed to cache job {job_id}: {e}")

    return jobs


def get_cached_jobs(keywords: list[str], limit: int = 50) -> list[dict]:
    """Retrieve jobs from CosmosDB cache that match keywords."""
    if not keywords:
        return []

    # Build a query that checks description for keyword matches
    conditions = []
    parameters = []
    for i, kw in enumerate(keywords[:5]):  # Limit to 5 keywords
        param_name = f"@kw{i}"
        conditions.append(f"CONTAINS(LOWER(c.description), {param_name})")
        parameters.append({"name": param_name, "value": kw.lower()})

    where_clause = " OR ".join(conditions)
    query = f"SELECT TOP {limit} * FROM c WHERE ({where_clause})"

    try:
        results = query_items("jobs", query, parameters)
        # Filter out stale cache entries
        return [job for job in results if _is_cache_valid(job)]
    except Exception as e:
        logger.warning(f"Failed to query cached jobs: {e}")
        return []


# Valid sources for job search
VALID_SOURCES = {"adzuna", "linkedin", "stepstone", "all"}


def search_jobs(
    skills: list[str],
    location: str = "",
    country: str = "us",
    page: int = 1,
    sources: list[str] | None = None,
    job_titles: list[str] | None = None,
) -> tuple[list[dict], int]:
    """Search for jobs matching given skills. Uses cache first, then APIs/scrapers.

    Args:
        sources: List of sources to search. Options: 'adzuna', 'linkedin', 'stepstone', 'all'.
                 Defaults to ['adzuna'] for backwards compatibility.
        job_titles: Optional list of job titles to use as search keywords and to filter results.
    """
    if sources is None:
        sources = ["adzuna"]

    if "all" in sources:
        sources = ["adzuna", "linkedin", "stepstone"]

    # Try cache first
    cached = get_cached_jobs(skills)
    if len(cached) >= 10:
        logger.info(f"Returning {len(cached)} cached jobs")
        if job_titles:
            cached = _filter_by_titles(cached, job_titles)
        return cached, len(cached)

    # Use job titles as primary search keywords when provided, otherwise use skills
    if job_titles:
        search_keywords = job_titles[:5]
    else:
        search_keywords = skills[:5] if len(skills) > 5 else skills
    all_jobs: list[dict] = []

    for source in sources:
        try:
            if source == "adzuna":
                jobs = search_jobs_adzuna(
                    keywords=search_keywords,
                    location=location,
                    country=country,
                    page=page,
                )
                all_jobs.extend(jobs)
            elif source == "linkedin":
                jobs = scrape_linkedin_jobs(
                    keywords=search_keywords,
                    location=location,
                    page=page,
                )
                # Cache LinkedIn results
                for job in jobs:
                    try:
                        upsert_item("jobs", job)
                    except Exception as e:
                        logger.warning(f"Failed to cache LinkedIn job {job['id']}: {e}")
                all_jobs.extend(jobs)
            elif source == "stepstone":
                jobs = scrape_stepstone_jobs(
                    keywords=search_keywords,
                    location=location,
                    country=country,
                    page=page,
                )
                # Cache StepStone results
                for job in jobs:
                    try:
                        upsert_item("jobs", job)
                    except Exception as e:
                        logger.warning(f"Failed to cache StepStone job {job['id']}: {e}")
                all_jobs.extend(jobs)
            else:
                logger.warning(f"Unknown job source: {source}")
        except RateLimitExceeded as e:
            logger.warning(f"Rate limit hit for {source}, skipping ({e})")
        except Exception as e:
            logger.error(f"Failed to fetch jobs from {source}: {e}")

    total = len(all_jobs)
    logger.info(f"Fetched {total} jobs from {sources} for keywords: {search_keywords}")

    # Filter by job titles if provided
    if job_titles:
        all_jobs = _filter_by_titles(all_jobs, job_titles)
        logger.info(f"Filtered to {len(all_jobs)} jobs matching titles: {job_titles}")

    return all_jobs, len(all_jobs)


def _filter_by_titles(jobs: list[dict], titles: list[str]) -> list[dict]:
    """Keep only jobs whose title matches at least one of the given title keywords."""
    title_terms = [t.lower() for t in titles]
    filtered = []
    for job in jobs:
        job_title = job.get("title", "").lower()
        if any(term in job_title for term in title_terms):
            filtered.append(job)
    return filtered
