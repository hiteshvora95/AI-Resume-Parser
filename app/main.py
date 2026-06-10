from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core import database
from app.core.logger import get_logger
logger = get_logger(__name__)
from app.routers import resume


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connect to MongoDB on startup and disconnect cleanly on shutdown."""
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(
    title="Resume Parser",
    description="Extract structured information from PDF and DOCX resumes.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(resume.router)


@app.get("/health", tags=["Health"])
def health():
    """Return a simple status check to confirm the API is running."""
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catch any unhandled exception and return a consistent 500 error response."""
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred", "detail": str(exc)},
    )
