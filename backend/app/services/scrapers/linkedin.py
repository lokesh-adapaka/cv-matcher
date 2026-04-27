from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from app.services.scrapers.rate_limiter import check_and_increment

logger = logging.getLogger(__name__)

LINKEDIN_JOBS_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"


def _generate_job_id(external_id: str) -> str:
    raw = f"linkedin_{external_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _clean_text(text: str) -> str:
    """Remove excess whitespace from scraped text."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def scrape_linkedin_jobs(
    keywords: list[str],
    location: str = "",
    page: int = 1,
    results_per_page: int = 25,
    max_detail_fetches: int = 10,
) -> list[dict]:
    """Scrape job listings from LinkedIn's public guest job search API.

    Fetches the listing page, then enriches up to *max_detail_fetches* jobs
    with their full description by visiting individual job pages.
    """
    check_and_increment("linkedin")
    query = " ".join(keywords)
    start = (page - 1) * results_per_page

    params = {
        "keywords": query,
        "location": location or "United States",
        "start": start,
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            response = client.get(LINKEDIN_JOBS_URL, params=params, headers=headers)
            response.raise_for_status()
            html = response.text
    except httpx.HTTPError as e:
        logger.error(f"LinkedIn scrape request failed: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    job_cards = soup.find_all("li")

    jobs = []
    for card in job_cards:
        try:
            title_el = card.find("h3", class_="base-search-card__title")
            company_el = card.find("h4", class_="base-search-card__subtitle")
            location_el = card.find("span", class_="job-search-card__location")
            link_el = card.find("a", class_="base-card__full-link")

            if not title_el:
                continue

            title = _clean_text(title_el.get_text())
            company = _clean_text(company_el.get_text()) if company_el else ""
            job_location = _clean_text(location_el.get_text()) if location_el else ""

            job_url = ""
            external_id = ""
            if link_el and link_el.get("href"):
                job_url = link_el["href"].split("?")[0]
                # Extract job ID from URL like /jobs/view/1234567890
                id_match = re.search(r"/view/(\d+)", job_url)
                if id_match:
                    external_id = id_match.group(1)

            if not external_id:
                external_id = hashlib.md5(f"{title}{company}".encode()).hexdigest()[:12]

            # Try to get the date
            date_el = card.find("time")
            date_text = ""
            if date_el and date_el.get("datetime"):
                date_text = date_el["datetime"]

            job = {
                "id": _generate_job_id(external_id),
                "title": title,
                "company": company,
                "location": job_location,
                "description": "",  # Full description requires visiting each job page
                "requirements": "",
                "salary": "",
                "url": job_url,
                "source": "linkedin",
                "posted_date": date_text,
                "created_at": datetime.utcnow().isoformat(),
            }
            jobs.append(job)
        except Exception as e:
            logger.warning(f"Failed to parse LinkedIn job card: {e}")
            continue

    logger.info(f"Scraped {len(jobs)} jobs from LinkedIn for '{query}'")

    # Enrich jobs with full descriptions (up to max_detail_fetches)
    enriched = 0
    for job in jobs:
        if enriched >= max_detail_fetches:
            break
        if not job["url"]:
            continue
        try:
            detail = scrape_linkedin_job_detail(job["url"])
            if detail.get("description"):
                job["description"] = detail["description"]
            if detail.get("salary"):
                job["salary"] = detail["salary"]
            enriched += 1
        except Exception as e:
            logger.warning(f"Failed to fetch detail for LinkedIn job {job['id']}: {e}")

    logger.info(f"Enriched {enriched}/{len(jobs)} LinkedIn jobs with descriptions")
    return jobs


def scrape_linkedin_job_detail(job_url: str) -> dict:
    """Fetch full description for a single LinkedIn job posting."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            response = client.get(job_url, headers=headers)
            response.raise_for_status()
            html = response.text
    except httpx.HTTPError as e:
        logger.error(f"LinkedIn job detail request failed: {e}")
        return {}

    soup = BeautifulSoup(html, "html.parser")

    description_el = soup.find("div", class_="show-more-less-html__markup")
    description = ""
    if description_el:
        description = _clean_text(description_el.get_text())

    criteria_items = soup.find_all("li", class_="description__job-criteria-item")
    salary = ""
    for item in criteria_items:
        header = item.find("h3")
        if header and "salary" in header.get_text().lower():
            value = item.find("span")
            if value:
                salary = _clean_text(value.get_text())

    return {
        "description": description,
        "salary": salary,
    }
