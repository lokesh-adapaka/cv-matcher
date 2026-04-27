import uuid
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from app.models.cv import CVUploadResponse, ParsedCV, CVGenerateRequest
from app.services.cv_parser import extract_text_from_pdf
from app.services.ai_service import extract_cv_data, generate_tailored_cv
from app.services.cv_generator import generate_cv_pdf
from app.db.local_db import upsert_item, read_item

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/upload", response_model=CVUploadResponse)
async def upload_cv(file: UploadFile = File(...)):
    """Upload a PDF CV, extract text, and parse with AI."""
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Read file
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Extract text from PDF
    try:
        raw_text = extract_text_from_pdf(contents)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if not raw_text:
        raise HTTPException(
            status_code=422,
            detail="Could not extract any text from the PDF. Please upload a text-based PDF.",
        )

    # Parse with AI
    try:
        parsed_data = extract_cv_data(raw_text)
    except Exception as e:
        logger.error(f"AI extraction failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze CV with AI")

    # Create CV record
    cv_id = str(uuid.uuid4())[:8]
    cv_record = {
        "id": cv_id,
        **parsed_data,
        "raw_text": raw_text,
    }

    # Store in CosmosDB
    try:
        upsert_item("cvs", cv_record)
    except Exception as e:
        logger.error(f"Failed to store CV: {e}")
        raise HTTPException(status_code=500, detail="Failed to save CV data")

    parsed_cv = ParsedCV(**cv_record)
    return CVUploadResponse(cv_id=cv_id, parsed_cv=parsed_cv)


@router.get("/{cv_id}")
async def get_cv(cv_id: str):
    """Retrieve a parsed CV by ID."""
    cv_data = read_item("cvs", cv_id, cv_id)
    if not cv_data:
        raise HTTPException(status_code=404, detail="CV not found")
    return cv_data


@router.post("/generate")
async def generate_cv(request: CVGenerateRequest):
    """Generate a tailored CV PDF for a specific job."""
    # Fetch CV
    cv_data = read_item("cvs", request.cv_id, request.cv_id)
    if not cv_data:
        raise HTTPException(status_code=404, detail="CV not found")

    # Fetch job
    job_data = read_item("jobs", request.job_id, request.job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")

    # Generate tailored CV content with AI
    try:
        tailored = generate_tailored_cv(cv_data, job_data)
    except Exception as e:
        logger.error(f"Tailored CV generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate tailored CV")

    # Generate PDF
    try:
        pdf_bytes = generate_cv_pdf(
            name=cv_data.get("name", ""),
            email=cv_data.get("email", ""),
            phone=cv_data.get("phone", ""),
            cv_data=tailored,
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    filename = f"tailored_cv_{request.cv_id}_{request.job_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
