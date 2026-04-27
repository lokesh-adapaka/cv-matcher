from pydantic import BaseModel, Field
from datetime import datetime


class Experience(BaseModel):
    title: str = ""
    company: str = ""
    duration: str = ""
    description: str = ""


class Education(BaseModel):
    degree: str = ""
    institution: str = ""
    year: str = ""


class ParsedCV(BaseModel):
    id: str = ""
    name: str = ""
    email: str = ""
    phone: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    raw_text: str = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class CVUploadResponse(BaseModel):
    cv_id: str
    parsed_cv: ParsedCV
    message: str = "CV uploaded and parsed successfully"


class CVGenerateRequest(BaseModel):
    cv_id: str
    job_id: str


class TailoredCV(BaseModel):
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    keywords_added: list[str] = Field(default_factory=list)
