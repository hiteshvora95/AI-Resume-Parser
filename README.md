# Resume Parser

A resume parsing service that accepts PDF and DOCX files, extracts structured information using LLM, stores results in MongoDB, and exposes everything through a FastAPI backend and a Streamlit UI.

---

## What it does

Upload a resume → get back structured JSON with contact details, work experience, education, skills, and certifications. Each parsed resume gets a unique document ID you can use to retrieve it later.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Uvicorn |
| LLM | OpenAI GPT-4o mini via LangChain |
| File Parsing | PyMuPDF (PDF), python-docx (DOCX) |
| Database | MongoDB (Motor async driver) |
| UI | Streamlit |
| Containerization | Docker + Docker Compose |
| Logging | Loguru |

---

## Project Structure

```
├── app/
│   ├── core/
│   │   ├── database.py         # MongoDB connection and CRUD
│   │   ├── exceptions.py       # Custom exception classes
│   │   └── logger.py           # Loguru setup
│   ├── models/
│   │   └── resume.py           # Pydantic schemas
│   ├── routers/
│   │   └── resume.py           # API endpoints
│   ├── services/
│   │   ├── llm_service.py      # LangChain + OpenAI integration
│   │   ├── parser.py           # PDF/DOCX text extraction
│   │   └── prompts.py          # LLM system prompt
│   └── main.py                 # FastAPI app entry point
├── config/
│   └── variables.py            # Environment config loader
├── env_config/
│   ├── .env.example            # Template — copy to .env.local
│   └── .env.local              # Local secrets (not committed)
├── ui/
│   └── streamlit_app.py        # Streamlit frontend
├── .env                        # Sets ENVIRONMENT=local (not committed)
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Getting Started

### Prerequisites

- Docker and Docker Compose installed
- OpenAI API key

### 1. Clone the repo

```bash
git clone <repo-url>
cd Resume_Parser
```

### 2. Set up environment files

```bash
# Create the base .env file
echo "ENVIRONMENT=local" > .env

# Copy the example and fill in your values
cp env_config/.env.example env_config/.env.local
```

Edit `env_config/.env.local`:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=resume_parser
MAX_FILE_SIZE_MB=10
LOG_LEVEL=INFO
API_BASE_URL=http://localhost:8000
```

### 3. Start the services

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| UI | http://localhost:8501 |

---

## API Endpoints

### `POST /api/upload`

Upload a PDF or DOCX resume for parsing.

**Request:** `multipart/form-data` with a `file` field

**Response:**
```json
{
  "document_id": "3f2a1b4c-...",
  "message": "Resume parsed successfully",
  "data": {
    "contact": { "name": "...", "email": "...", "phone": "...", "location": "..." },
    "summary": "...",
    "work_experience": [...],
    "education": [...],
    "skills": { "technical": [...], "soft": [...] },
    "certifications": [...]
  }
}
```

**Error codes:**

| Code | Reason |
|---|---|
| 400 | Invalid file type, too large, empty, or unreadable |
| 429 | OpenAI rate limit hit — wait and retry |
| 500 | Unexpected parsing or validation error |
| 503 | LLM or database unreachable |

---

### `GET /api/resume/{document_id}`

Retrieve a previously parsed resume by its document ID.

**Response:** Same `data` object as the upload response, plus `document_id` and `created_at`.

**Error codes:**

| Code | Reason |
|---|---|
| 404 | Document ID not found |

---

### `GET /health`

Basic health check — returns `{ "status": "ok" }`.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ | — | Your OpenAI API key |
| `OPENAI_MODEL` | ❌ | `gpt-4o-mini` | Model to use for extraction |
| `MONGODB_URL` | ✅ | — | MongoDB connection string |
| `DATABASE_NAME` | ❌ | `resume_parser` | MongoDB database name |
| `MAX_FILE_SIZE_MB` | ❌ | `10` | Max upload size in MB |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level |
| `API_BASE_URL` | ❌ | `http://localhost:8000` | Base URL for UI → API calls |

---

## Running Locally (without Docker)

```bash
pip install -r requirements.txt

# API
uvicorn app.main:app --reload --port 8000

# UI (separate terminal)
streamlit run ui/streamlit_app.py --server.port 8501
```

Make sure MongoDB is running locally on port 27017.

---

## Notes

- Resume text is capped at 12,000 tokens before being sent to the LLM
- LLM calls retry automatically on timeout with exponential backoff (2s → 4s → 8s)
- All parsed resumes are stored in MongoDB and retrievable by document ID
