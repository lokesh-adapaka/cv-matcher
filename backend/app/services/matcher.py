import logging
from app.db.local_db import read_item, upsert_item
from app.services.job_service import search_jobs
from app.services.ai_service import compute_match

logger = logging.getLogger(__name__)

BATCH_SIZE = 5  # Number of jobs to send to AI per request


def match_cv_to_jobs(
    cv_id: str,
    location: str = "",
    country: str = "us",
    sources: list[str] | None = None,
    job_titles: list[str] | None = None,
) -> dict:
    """Match a stored CV against relevant jobs."""
    # Fetch CV from CosmosDB
    cv_data = read_item("cvs", cv_id, cv_id)
    if not cv_data:
        raise ValueError(f"CV with id {cv_id} not found")

    skills = cv_data.get("skills", [])
    if not skills:
        raise ValueError("CV has no extracted skills to match against")

    # Fetch relevant jobs
    jobs, total = search_jobs(
        skills, location=location, country=country, sources=sources, job_titles=job_titles,
    )
    if not jobs:
        return {
            "cv_id": cv_id,
            "matches": [],
            "total_jobs_analyzed": 0,
        }

    # Process jobs in batches for AI matching
    all_matches = []
    for i in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[i : i + BATCH_SIZE]
        logger.info(f"Matching batch {i // BATCH_SIZE + 1}: {len(batch)} jobs")

        try:
            batch_matches = compute_match(cv_data, batch)
            # Enrich match results with job metadata
            job_lookup = {j["id"]: j for j in batch}
            for m in batch_matches:
                job = job_lookup.get(m.get("job_id", ""), {})
                m["cv_id"] = cv_id
                m["job_title"] = job.get("title", "")
                m["company"] = job.get("company", "")
                m["location"] = job.get("location", "")
                m["salary"] = job.get("salary", "")
                m["job_url"] = job.get("url", "")
            all_matches.extend(batch_matches)
        except Exception as e:
            logger.error(f"Failed to match batch: {e}")
            continue

    # Sort by match percentage descending
    all_matches.sort(key=lambda x: x.get("match_percentage", 0), reverse=True)

    # Store results in CosmosDB
    result = {
        "id": f"match_{cv_id}",
        "cv_id": cv_id,
        "matches": all_matches,
        "total_jobs_analyzed": len(jobs),
    }
    try:
        upsert_item("matches", result)
    except Exception as e:
        logger.warning(f"Failed to store match results: {e}")

    return result
