from __future__ import annotations

import json
import logging
from openai import OpenAI
from app.config import get_settings

logger = logging.getLogger(__name__)

_client = None


def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        _client = OpenAI(
            api_key=settings.openai_api_key,
        )
    return _client


def extract_cv_data(raw_text: str) -> dict:
    """Use Azure OpenAI to extract structured data from CV text."""
    client = get_openai_client()
    settings = get_settings()

    prompt = """Analyze the following CV/resume text and extract structured information.
Return a JSON object with these exact fields:
{
    "name": "Full name of the person",
    "email": "Email address (or empty string if not found)",
    "phone": "Phone number (or empty string if not found)",
    "summary": "A brief professional summary (2-3 sentences). If not explicitly stated, generate one from the CV content.",
    "skills": ["list", "of", "technical", "and", "soft", "skills"],
    "experience": [
        {
            "title": "Job Title",
            "company": "Company Name",
            "duration": "Start - End",
            "description": "Brief description of responsibilities and achievements"
        }
    ],
    "education": [
        {
            "degree": "Degree name",
            "institution": "University/School name",
            "year": "Graduation year or period"
        }
    ]
}

IMPORTANT:
- Extract ALL skills mentioned, including those implied by job descriptions
- If a field is not found in the CV, use an empty string or empty list
- Return ONLY valid JSON, no markdown formatting or extra text

CV Text:
"""

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": "You are an expert CV/resume parser. Extract structured data accurately."},
            {"role": "user", "content": prompt + raw_text},
        ],
        temperature=0.1,
        max_tokens=2000,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse AI response as JSON: {content[:200]}")
        return {
            "name": "",
            "email": "",
            "phone": "",
            "summary": "",
            "skills": [],
            "experience": [],
            "education": [],
        }


def compute_match(cv_data: dict, jobs: list) -> list:
    """Use Azure OpenAI to compute match percentages between a CV and multiple jobs."""
    client = get_openai_client()
    settings = get_settings()

    cv_summary = f"""
Skills: {', '.join(cv_data.get('skills', []))}
Experience: {json.dumps(cv_data.get('experience', []), indent=1)}
Summary: {cv_data.get('summary', '')}
"""

    jobs_text = ""
    for i, job in enumerate(jobs):
        jobs_text += f"""
---JOB {i+1}---
ID: {job.get('id', '')}
Title: {job.get('title', '')}
Company: {job.get('company', '')}
Description: {job.get('description', '')[:500]}
Requirements: {job.get('requirements', '')[:300]}
"""

    prompt = f"""Analyze how well this candidate matches each job listing.

CANDIDATE CV:
{cv_summary}

JOB LISTINGS:
{jobs_text}

For EACH job, return a JSON object in this exact format:
{{
    "matches": [
        {{
            "job_id": "the job ID",
            "match_percentage": 75,
            "matched_skills": ["skill1", "skill2"],
            "missing_skills": ["skill3", "skill4"],
            "match_explanation": "Brief 1-2 sentence explanation of the match"
        }}
    ]
}}

RULES:
- match_percentage must be 0-100
- Be realistic and fair in scoring
- matched_skills = skills the candidate HAS that the job NEEDS
- missing_skills = skills the job NEEDS that the candidate LACKS
- Return ONLY valid JSON
"""

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": "You are an expert HR analyst. Evaluate candidate-job fit accurately and fairly."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=3000,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    try:
        result = json.loads(content)
        return result.get("matches", [])
    except json.JSONDecodeError:
        logger.error(f"Failed to parse match response: {content[:200]}")
        return []


def generate_tailored_cv(cv_data: dict, job_data: dict) -> dict:
    """Use Azure OpenAI to rewrite a CV tailored for a specific job."""
    client = get_openai_client()
    settings = get_settings()

    prompt = f"""Rewrite this CV to be optimized for the following job. 
Emphasize relevant skills and experience, incorporate keywords from the job description naturally.

IMPORTANT RULES:
- Do NOT fabricate experience, education, or skills the candidate doesn't have
- DO reorder skills to highlight the most relevant ones first
- DO reword experience descriptions to emphasize relevant aspects
- DO incorporate job-specific keywords where truthful
- DO write a targeted professional summary
- Keep all factual information (dates, company names, degrees) accurate

ORIGINAL CV DATA:
Name: {cv_data.get('name', '')}
Skills: {', '.join(cv_data.get('skills', []))}
Experience: {json.dumps(cv_data.get('experience', []), indent=2)}
Education: {json.dumps(cv_data.get('education', []), indent=2)}
Summary: {cv_data.get('summary', '')}

TARGET JOB:
Title: {job_data.get('title', '')}
Company: {job_data.get('company', '')}
Description: {job_data.get('description', '')}
Requirements: {job_data.get('requirements', '')}

Return a JSON object with the tailored CV:
{{
    "summary": "Targeted professional summary (3-4 sentences)",
    "skills": ["reordered", "and", "highlighted", "skills"],
    "experience": [
        {{
            "title": "Original title",
            "company": "Original company",
            "duration": "Original duration",
            "description": "Reworded to emphasize relevant aspects"
        }}
    ],
    "education": [
        {{
            "degree": "Original degree",
            "institution": "Original institution",
            "year": "Original year"
        }}
    ],
    "keywords_added": ["list", "of", "job", "keywords", "incorporated"]
}}
"""

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": "You are an expert CV writer. Optimize CVs for specific jobs while maintaining truthfulness."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=3000,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse tailored CV response: {content[:200]}")
        return {
            "summary": cv_data.get("summary", ""),
            "skills": cv_data.get("skills", []),
            "experience": cv_data.get("experience", []),
            "education": cv_data.get("education", []),
            "keywords_added": [],
        }


def analyze_jd_match(cv_data: dict, job_description: str) -> dict:
    """Analyze how well a CV matches a pasted job description and suggest CV improvements."""
    client = get_openai_client()
    settings = get_settings()

    cv_summary = f"""
Name: {cv_data.get('name', '')}
Skills: {', '.join(cv_data.get('skills', []))}
Experience: {json.dumps(cv_data.get('experience', []), indent=1)}
Education: {json.dumps(cv_data.get('education', []), indent=1)}
Summary: {cv_data.get('summary', '')}
"""

    prompt = f"""You are an expert ATS (Applicant Tracking System) analyst and career coach.

Analyze how well this candidate's CV matches the given job description. Be thorough and actionable.

CANDIDATE CV:
{cv_summary}

JOB DESCRIPTION:
{job_description}

Return a JSON object with this EXACT structure:
{{
    "match_percentage": 72,
    "overall_assessment": "2-3 sentence summary of how well the candidate fits this role",
    "matched_skills": ["skill1", "skill2"],
    "missing_skills": ["skill3", "skill4"],
    "keyword_suggestions": [
        {{
            "keyword": "the exact keyword or phrase to add",
            "where": "Which section of the CV to add it (summary/skills/experience)",
            "tip": "How to naturally incorporate this keyword"
        }}
    ],
    "cv_improvement_suggestions": [
        {{
            "section": "summary|skills|experience|education",
            "current": "What the CV currently says or lacks (brief)",
            "suggested": "What it should say instead or what to add",
            "reason": "Why this change helps with ATS and recruiters"
        }}
    ],
    "ats_tips": [
        "Specific tip for passing ATS screening for this job"
    ],
    "experience_rewrite_suggestions": [
        {{
            "original_title": "Original job title from CV",
            "original_description": "Brief current description",
            "suggested_description": "Reworded description emphasizing relevant aspects for this job"
        }}
    ]
}}

RULES:
- match_percentage must be 0-100, be realistic
- keyword_suggestions should include exact terms from the job description that are missing from the CV
- cv_improvement_suggestions should be specific and actionable
- experience_rewrite_suggestions should only reword, NEVER fabricate experience
- ats_tips should be practical for passing automated screening
- Return ONLY valid JSON
"""

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": "You are an expert ATS analyst and career coach. Provide detailed, actionable CV optimization advice."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=4000,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JD analysis response: {content[:200]}")
        return {
            "match_percentage": 0,
            "overall_assessment": "Analysis failed. Please try again.",
            "matched_skills": [],
            "missing_skills": [],
            "keyword_suggestions": [],
            "cv_improvement_suggestions": [],
            "ats_tips": [],
            "experience_rewrite_suggestions": [],
        }
