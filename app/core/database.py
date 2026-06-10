from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError, ServerSelectionTimeoutError

from app.core.logger import get_logger
logger = get_logger(__name__)
from config.variables import DATABASE_NAME, MONGODB_URL
from app.models import ParsedResume

_client: Optional[AsyncIOMotorClient] = None
_resumes_collection: Optional[AsyncIOMotorCollection] = None


def _get_collection() -> AsyncIOMotorCollection:
    """Return the resumes collection, or raise if connect() was never called."""
    if _resumes_collection is None:
        raise RuntimeError("Database not initialised — connect() must be called first.")
    return _resumes_collection


async def connect() -> None:
    """
    Open a connection to MongoDB and prepare the resumes collection.

    - Skips silently if already connected.
    - Pings the database to confirm the server is reachable.
    - Creates a unique index on document_id so duplicate saves are rejected at the DB level.
    - Raises RuntimeError if the server is unreachable or the connection fails.
    """
    global _client, _resumes_collection

    if _client is not None:
        logger.warning("connect() called while already connected — skipping")
        return

    try:
        _client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=5000)

        db = _client[DATABASE_NAME]
        await db.command("ping")
        _resumes_collection = db["resumes"]
        await _resumes_collection.create_index([("document_id", ASCENDING)], unique=True)

        logger.info(f"Connected to MongoDB — {MONGODB_URL} / {DATABASE_NAME}")

    except ServerSelectionTimeoutError as e:
        logger.error(f"MongoDB unreachable at {MONGODB_URL}: {e}")
        raise RuntimeError(f"Could not reach MongoDB at {MONGODB_URL}") from e

    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise RuntimeError(f"Could not connect to MongoDB: {e}") from e


async def disconnect() -> None:
    """
    Close the MongoDB connection and reset internal state.

    Safe to call even if connect() was never called or already disconnected.
    Always clears the client and collection references, even if close() raises.
    """
    global _client, _resumes_collection

    if _client:
        try:
            _client.close()
            logger.info("MongoDB connection closed")
        except Exception as e:
            logger.warning(f"Error while closing MongoDB connection: {e}")
        finally:
            _client = None
            _resumes_collection = None


async def save_resume(resume: ParsedResume) -> str:
    """
    Insert a parsed resume document into MongoDB.

    Raises:
        ValueError: if a document with the same document_id already exists.
        ConnectionError: if MongoDB is unreachable at the time of the insert.
        RuntimeError: for any other database error.
    """
    collection = _get_collection()

    doc = resume.model_dump()
    doc["created_at"] = resume.created_at.isoformat()

    try:
        await collection.insert_one(doc)
        logger.info(f"Resume saved — document_id={resume.document_id}")
        return resume.document_id

    except DuplicateKeyError:
        logger.error(f"Duplicate document_id detected: {resume.document_id}")
        raise ValueError(f"A resume with ID '{resume.document_id}' already exists")

    except ServerSelectionTimeoutError as e:
        logger.error(f"MongoDB unreachable during save: {e}")
        raise ConnectionError("Database is unreachable — please try again") from e

    except PyMongoError as e:
        logger.error(f"MongoDB error during save — document_id={resume.document_id}: {e}")
        raise RuntimeError(f"Failed to save resume: {e}") from e


async def get_resume(document_id: str) -> Optional[ParsedResume]:
    """
    Fetch a resume from MongoDB by its document_id.

    Raises:
        ValueError: if document_id is empty or blank.
        ConnectionError: if MongoDB is unreachable at the time of the query.
        RuntimeError: if the stored document exists but cannot be parsed (malformed data).
    """
    if not document_id or not document_id.strip():
        raise ValueError("document_id cannot be empty")

    collection = _get_collection()

    try:
        doc = await collection.find_one({"document_id": document_id})

    except ServerSelectionTimeoutError as e:
        logger.error(f"MongoDB unreachable during get — document_id={document_id}: {e}")
        raise ConnectionError("Database is unreachable — please try again") from e

    except PyMongoError as e:
        logger.error(f"MongoDB error during get — document_id={document_id}: {e}")
        raise RuntimeError(f"Failed to retrieve resume: {e}") from e

    if not doc:
        logger.info(f"Resume not found — document_id={document_id}")
        return None

    doc.pop("_id")

    try:
        resume = ParsedResume(**doc)
    except Exception as e:
        logger.error(f"Stored document is malformed — document_id={document_id}: {e}")
        raise RuntimeError("Stored resume data is malformed and could not be parsed") from e

    logger.info(f"Resume retrieved — document_id={document_id}")
    return resume
