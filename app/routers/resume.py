from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, File, HTTPException, UploadFile
from openai import RateLimitError
from app.core import database
from config.variables import MAX_FILE_SIZE_MB
from app.core.logger import get_logger
from app.models import ErrorResponse, ParsedResume, UploadResponse
from app.services.llm_service import llm_client
from app.services import parser as resume_parser
from app.core.exceptions import ParserError, ScannedPDFError, UnsupportedFileTypeError


logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["Resume"])

MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {"pdf", "docx"}


@router.post(
    "/upload",
    response_model=UploadResponse,  # schema of the success response body
    responses={
        400: {"model": ErrorResponse},  # invalid file type / size 
        429: {"model": ErrorResponse},  # OpenAI rate limit hit
        500: {"model": ErrorResponse},  # LLM or validation failure
        503: {"model": ErrorResponse},  # LLM or DB unreachable
    },
    summary="Upload and parse a resume",
)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a PDF or DOCX resume and receive structured information extracted by AI.

    Accepted formats: **PDF**, **DOCX** — max **10MB**.

    On success, returns a `document_id` you can use to retrieve the result later,
    along with the full extracted resume data including contact details, work experience,
    education, skills, and certifications.
    """
    logger.info(f"Upload request — filename={file.filename}")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = file.filename.lower().split(".")[-1]
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Only PDF and DOCX files are accepted, got: .{ext or 'unknown'}",
        )

    file_bytes = await file.read()

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        limit_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds the {limit_mb}MB limit",
        )

    logger.info(f"File validated — {file.filename} ({len(file_bytes) / 1024:.1f} KB)")

    try:
        raw_text = resume_parser.extract_text(file_bytes, file.filename)
    except ScannedPDFError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UnsupportedFileTypeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ParserError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        extraction = await llm_client.parse_resume(raw_text)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="LLM rate limit exceeded — please wait and retry",
        )
    except (ConnectionError, TimeoutError) as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected LLM error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during parsing")

    document_id = str(uuid4())

    resume = ParsedResume(
        document_id=document_id,
        created_at=datetime.utcnow(),
        **extraction.model_dump(),
    )

    await database.save_resume(resume)

    return UploadResponse(
        document_id=document_id,
        message="Resume parsed successfully",
        data=resume,
    )


@router.get(
    "/resume/{document_id}",
    response_model=UploadResponse,
    responses={
        404: {"model": ErrorResponse}
    },
    summary="Retrieve a previously parsed resume",
)
async def get_resume(document_id: str):
    """
    Retrieve a previously parsed resume using the `document_id` returned at upload time.

    Returns the full structured resume data if found, or **404** if the ID does not exist.
    """
    logger.info(f"Retrieve request — document_id={document_id}")

    resume = await database.get_resume(document_id)
    if not resume:
        raise HTTPException(
            status_code=404,
            detail=f"Resume with ID '{document_id}' not found",
        )

    return UploadResponse(
        document_id=document_id,
        message="Resume retrieved successfully",
        data=resume,
    )
