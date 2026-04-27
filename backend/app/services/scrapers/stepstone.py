from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from app.services.scrapers.rate_limiter import check_and_increment

logger = logging.getLogger(__name__)

# StepStone country base URLs
STEPSTONE_URLS = {
    "de": "https://www.stepstone.de/jobs/{query}/in-{location}",
    "at": "https://www.stepstone.at/jobs/{query}/in-{location}",
    "be": "https://www.stepstone.be/jobs/{query}/in-{location}",
}

STEPSTONE_SEARCH_URL = "https://www.stepstone.de/work/{query}"


def _generate_job_id(external_id: str) -> str:
    raw = f"stepstone_{external_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _clean_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def scrape_stepstone_jobs(
    keywords: list[str],
    location: str = "",
    country: str = "de",
    page: int = 1,
    max_detail_fetches: int = 10,
) -> list[dict]:
    """Scrape job listings from StepStone.

    Fetches the listing page, then enriches up to *max_detail_fetches* jobs
    with their full description by visiting individual job pages.
    """
    check_and_increment("stepstone")
    query = "-".join(kw.lower().strip() for kw in keywords)

    # Build URL
    if country in STEPSTONE_URLS and location:
        location_slug = location.lower().replace(" ", "-")
        url = STEPSTONE_URLS[country].format(query=query, location=location_slug)
    else:
        url = STEPSTONE_SEARCH_URL.format(query=query)

    params = {}
    if page > 1:
        params["page"] = page
    if location and country not in STEPSTONE_URLS:
        params["where"] = location

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            html = response.text
    except httpx.HTTPError as e:
        logger.error(f"StepStone scrape request failed: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")

    jobs = []

    # StepStone uses article tags or specific data attributes for job cards
    job_cards = soup.find_all("article", attrs={"data-testid": re.compile(r"job-item")})

    # Fallback: look for common listing structures
    if not job_cards:
        job_cards = soup.find_all("article")

    if not job_cards:
        # Try anchor-based approach for listing links
        job_cards = soup.find_all("a", attrs={"data-testid": re.compile(r"job-item")})

    for card in job_cards:
        try:
            # Try multiple selectors for title
            title_el = (
                card.find(attrs={"data-testid": "job-item-title"})
                or card.find("h2")
                or card.find("h3")
            )
            if not title_el:
                continue

            title = _clean_text(title_el.get_text())

            # Company name
            company_el = card.find(
                attrs={"data-testid": re.compile(r"company|employer")}
            ) or card.find("span", class_=re.compile(r"company|employer", re.I))
            company = _clean_text(company_el.get_text()) if company_el else ""

            # Location
            location_el = card.find(
                attrs={"data-testid": re.compile(r"location")}
            ) or card.find("span", class_=re.compile(r"location", re.I))
            job_location = _clean_text(location_el.get_text()) if location_el else ""

            # Job URL
            link_el = card.find("a", href=True) if card.name != "a" else card
            job_url = ""
            external_id = ""
            if link_el and link_el.get("href"):
                href = link_el["href"]
                if href.startswith("/"):
                    base = STEPSTONE_URLS.get(country, STEPSTONE_SEARCH_URL).split("/work/")[0]
                    if "/work/" not in STEPSTONE_URLS.get(country, ""):
                        base = f"https://www.stepstone.{country}"
                    job_url = base + href
                else:
                    job_url = href
                # Extract external ID from URL
                id_match = re.search(r"--(\d+)$", job_url) or re.search(r"/(\d+)(?:\?|$)", job_url)
                if id_match:
                    external_id = id_match.group(1)

            if not external_id:
                external_id = hashlib.md5(f"{title}{company}".encode()).hexdigest()[:12]

            # Salary (rarely shown on listing pages)
            salary_el = card.find(attrs={"data-testid": re.compile(r"salary")})
            salary = _clean_text(salary_el.get_text()) if salary_el else ""

            # Snippet / short description
            snippet_el = card.find(attrs={"data-testid": re.compile(r"snippet|description")})
            snippet = _clean_text(snippet_el.get_text()) if snippet_el else ""

            job = {
                "id": _generate_job_id(external_id),
                "title": title,
                "company": company,
                "location": job_location,
                "description": snippet,
                "requirements": "",
                "salary": salary,
                "url": job_url,
                "source": "stepstone",
                "created_at": datetime.utcnow().isoformat(),
            }
            jobs.append(job)
        except Exception as e:
            logger.warning(f"Failed to parse StepStone job card: {e}")
            continue

    logger.info(f"Scraped {len(jobs)} jobs from StepStone for '{' '.join(keywords)}'")

    # Enrich jobs with full descriptions (up to max_detail_fetches)
    enriched = 0
    for job in jobs:
        if enriched >= max_detail_fetches:
            break
        if not job["url"]:
            continue
        try:
            detail = scrape_stepstone_job_detail(job["url"])
            if detail.get("description"):
                job["description"] = detail["description"]
            if detail.get("salary"):
                job["salary"] = detail["salary"]
            enriched += 1
        except Exception as e:
            logger.warning(f"Failed to fetch detail for StepStone job {job['id']}: {e}")

    logger.info(f"Enriched {enriched}/{len(jobs)} StepStone jobs with descriptions")
    return jobs


def scrape_stepstone_job_detail(job_url: str) -> dict:
    """Fetch full description for a single StepStone job posting."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            response = client.get(job_url, headers=headers)
            response.raise_for_status()
            html = response.text
    except httpx.HTTPError as e:
        logger.error(f"StepStone job detail request failed: {e}")
        return {}

    soup = BeautifulSoup(html, "html.parser")

    # Description
    desc_el = (
        soup.find(attrs={"data-testid": "job-description"})
        or soup.find("div", class_=re.compile(r"job-description|listing-content", re.I))
    )
    description = _clean_text(desc_el.get_text()) if desc_el else ""

    # Salary
    salary_el = soup.find(attrs={"data-testid": re.compile(r"salary")})
    salary = _clean_text(salary_el.get_text()) if salary_el else ""

    return {
        "description": description,
        "salary": salary,
    }
