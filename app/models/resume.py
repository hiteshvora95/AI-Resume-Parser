from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    """
    Personal contact details extracted from the resume.
    """
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None


class WorkExperience(BaseModel):
    """
    Job entry from the resume's work history.
    """
    company: str
    role: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    responsibilities: List[str] = []


class Education(BaseModel):
    """
    Education entry — degree, where it was obtained, and the year of completion.
    """
    degree: str
    institution: str
    year: Optional[str] = None


class Skills(BaseModel):
    """
    Skills from the resume.
    technical: programming languages, tools, frameworks, etc.
    soft: communication, leadership, teamwork, etc.
    """
    technical: List[str] = []
    soft: List[str] = []


class Certification(BaseModel):
    """
    A professional certification or course completion listed on the resume.
    """
    name: str
    issuer: Optional[str] = None
    year: Optional[str] = None


class ResumeExtraction(BaseModel):
    """
    The structured output returned by the LLM after parsing a resume.
    """
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: Optional[str] = None
    work_experience: List[WorkExperience] = []
    education: List[Education] = []
    skills: Skills = Field(default_factory=Skills)
    certifications: List[Certification] = []


class ParsedResume(BaseModel):
    """
    The complete resume document as stored in MongoDB.
    """
    document_id: str
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: Optional[str] = None
    work_experience: List[WorkExperience] = []
    education: List[Education] = []
    skills: Skills = Field(default_factory=Skills)
    certifications: List[Certification] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UploadResponse(BaseModel):
    """
    Response shape returned after successfully uploading and parsing a resume.
    """
    document_id: str
    message: str
    data: ParsedResume


class ErrorResponse(BaseModel):
    """
    Standardized error response shape for API endpoints when something goes wrong.
    """
    error: str
    detail: Optional[str] = None
