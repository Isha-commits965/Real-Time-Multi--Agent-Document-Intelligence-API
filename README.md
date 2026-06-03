# Real-Time Multi-Agent Document Intelligence API

## Project Description

This is a FastAPI backend for a legal consulting workflow. Users upload PDF or TXT documents, trigger multi-agent AI analysis, and poll job status as results arrive.

The service runs four specialized agents in parallel on each document:

1. **Summarizer** — 100–150 word summary, 3–5 key points, confidence score
2. **Entity Extractor** — people, organizations, dates, locations, monetary values, and numeric metrics with mention counts
3. **Sentiment & Tone Analyzer** — sentiment, tone, urgency, confidence, and supporting excerpts
4. **Document Classifier** — category (Contract, Legal Brief, Research Memo, etc.), confidence, and rationale

The `/analyze` endpoint returns a `job_id` immediately. Agents run in the background. Clients poll `GET /api/jobs/{job_id}` for live status, including partial results when some agents finish before others. If one agent fails, the others still complete and the job status becomes `partially_failed`.

Sample files are included in `sample_documents/` for testing.

---

## Setup Instructions

Follow these steps from the project root (the directory containing the `app/` folder).

### 1. Prerequisites

- Python 3.11 or later
- An OpenAI API key (optional — without it the app runs stub agents for local testing)

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
DATABASE_URL=sqlite:///./document_intelligence.db
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=10
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
LLM_TIMEOUT_SECONDS=60
```

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key. Leave empty for stub mode. |
| `LLM_TIMEOUT_SECONDS` | Per-request LLM timeout in seconds (default: 60) |

### 5. Run database migrations

```bash
alembic upgrade head
```

Or:

```bash
make migrate
```

### 6. Start the server

```bash
uvicorn app.main:app --reload --port 8001
```

Or:

```bash
make run
```

### 7. Verify the application

Open **http://localhost:8001/docs** for interactive Swagger UI, or:

```bash
curl http://localhost:8001/health
```

Expected response:

```json
{ "status": "ok" }
```

---

## API Documentation

Base URL: `http://localhost:8001`

### POST `/api/documents/upload`

Upload a PDF or TXT file. Text is extracted and stored immediately.

**Request**

```bash
curl -X POST http://localhost:8001/api/documents/upload \
  -F "file=@sample_documents/sample_research_memo.txt"
```

**Response** `200 OK`

```json
{
  "document_id": "doc_c0b7707174459a85c05bd03e",
  "filename": "sample_research_memo.txt",
  "file_type": "txt",
  "word_count": 920,
  "uploaded_at": "2026-06-03T06:29:13",
  "status": "ready"
}
```

**Error responses**

| Status | Example `detail` |
|--------|------------------|
| 400 | `"Only PDF and TXT files are supported"` |
| 400 | `"Uploaded file is empty"` |
| 400 | `"PDF contains no extractable text"` |
| 413 | `"File exceeds maximum size of 10MB"` |

---

### GET `/api/documents`

List all uploaded documents.

**Request**

```bash
curl http://localhost:8001/api/documents
```

**Response** `200 OK`

```json
{
  "documents": [
    {
      "document_id": "doc_c0b7707174459a85c05bd03e",
      "filename": "sample_research_memo.txt",
      "file_type": "txt",
      "word_count": 920,
      "uploaded_at": "2026-06-03T06:29:13",
      "status": "ready",
      "analysis_count": 1
    }
  ]
}
```

---

### POST `/api/documents/{document_id}/analyze`

Start analysis on a previously uploaded document. Returns immediately without waiting for agents to finish. Can be called multiple times on the same document (re-analyze).

**Request**

```bash
curl -X POST http://localhost:8001/api/documents/doc_c0b7707174459a85c05bd03e/analyze
```

**Response** `200 OK`

```json
{
  "job_id": "job_19e8ed7ab3f1993bdec5fdb5",
  "document_id": "doc_c0b7707174459a85c05bd03e",
  "status": "processing",
  "agents": {
    "summarizer": { "status": "running" },
    "entity_extractor": { "status": "running" },
    "sentiment_analyzer": { "status": "running" },
    "document_classifier": { "status": "running" }
  },
  "created_at": "2026-06-03T06:40:09"
}
```

**Error responses**

| Status | Example `detail` |
|--------|------------------|
| 404 | `"Document not found"` |

---

### GET `/api/jobs/{job_id}`

Retrieve current job status and agent results. Returns partial results while agents are still running.

**Request**

```bash
curl http://localhost:8001/api/jobs/job_19e8ed7ab3f1993bdec5fdb5
```

**Response — completed** `200 OK`

```json
{
  "job_id": "job_19e8ed7ab3f1993bdec5fdb5",
  "document_id": "doc_c0b7707174459a85c05bd03e",
  "document_name": "211_2020_12_51_71182_Judgement_15-May-2026.pdf",
  "status": "completed",
  "agents": {
    "summarizer": {
      "status": "completed",
      "processing_time_seconds": 9.9,
      "result": {
        "summary": "In Civil Appeal No. 7935 of 2026, the Supreme Court of India addressed...",
        "key_points": [
          "Accident resulted in the death of the family's breadwinner.",
          "Initial compensation awarded was Rs. 6,16,000, later increased to Rs. 8,26,000.",
          "Supreme Court determined the deceased's monthly income to be Rs. 10,000.",
          "Total compensation awarded is Rs. 20,40,000.",
          "Compensation to be paid within two months with interest."
        ],
        "confidence": 0.95
      },
      "error": null
    },
    "entity_extractor": {
      "status": "completed",
      "processing_time_seconds": 8.9,
      "result": {
        "people": [
          { "name": "Smt. Neelam", "role": "Appellant", "mentions": 1 }
        ],
        "organizations": [
          { "name": "Supreme Court of India", "mentions": 1 }
        ],
        "dates": [
          { "value": "May 15, 2026", "mentions": 1 }
        ],
        "locations": [
          { "value": "New Delhi", "mentions": 1 }
        ],
        "monetary_values": [
          { "value": "Rs.20,40,000", "mentions": 1 }
        ],
        "numeric_metrics": [
          { "value": "7%", "mentions": 2 }
        ]
      },
      "error": null
    },
    "sentiment_analyzer": {
      "status": "completed",
      "processing_time_seconds": 2.2,
      "result": {
        "sentiment": "positive",
        "tone": "formal",
        "urgency": "routine",
        "confidence": 0.85,
        "supporting_excerpts": [
          "The appeal stands allowed with the above directions"
        ]
      },
      "error": null
    },
    "document_classifier": {
      "status": "completed",
      "processing_time_seconds": 2.1,
      "result": {
        "category": "Legal Brief",
        "confidence": 0.85,
        "rationale": "The document outlines a legal case and the court's decision regarding a civil appeal."
      },
      "error": null
    }
  },
  "agents_completed": 4,
  "agents_failed": 0,
  "total_processing_time_seconds": 9.9,
  "created_at": "2026-06-03T06:40:09",
  "completed_at": "2026-06-03T06:40:19.242378"
}
```

**Response — partially failed** `200 OK`

```json
{
  "job_id": "job_6316b27a89661e7e633d66d1",
  "document_id": "doc_e31e810eb5f4142706e75ebc",
  "document_name": "211_2020_12_51_71182_Judgement_15-May-2026.pdf",
  "status": "partially_failed",
  "agents": {
    "summarizer": {
      "status": "completed",
      "processing_time_seconds": 29.2,
      "result": { "summary": "...", "key_points": ["..."], "confidence": 0.95 },
      "error": null
    },
    "entity_extractor": {
      "status": "failed",
      "processing_time_seconds": 31.6,
      "result": null,
      "error": "Request timed out."
    },
    "sentiment_analyzer": {
      "status": "completed",
      "processing_time_seconds": 3.1,
      "result": { "sentiment": "positive", "tone": "formal", "urgency": "routine", "confidence": 0.85, "supporting_excerpts": ["..."] },
      "error": null
    },
    "document_classifier": {
      "status": "completed",
      "processing_time_seconds": 1.9,
      "result": { "category": "Legal Brief", "confidence": 0.9, "rationale": "..." },
      "error": null
    }
  },
  "agents_completed": 3,
  "agents_failed": 1,
  "total_processing_time_seconds": 31.9,
  "created_at": "2026-06-03T06:29:13",
  "completed_at": "2026-06-03T06:29:45.359709"
}
```

**Response — in progress (partial results)** `200 OK`

While the job is still running, completed agents include `result`; others remain `"running"`:

```json
{
  "job_id": "job_475ca835a08d429aae16d6f7",
  "document_id": "doc_41daca2552871e763cb91e73",
  "document_name": "Case-Briefing.pdf",
  "status": "processing",
  "agents": {
    "summarizer": { "status": "completed", "processing_time_seconds": 6.5, "result": { "..." : "..." }, "error": null },
    "entity_extractor": { "status": "running", "processing_time_seconds": null, "result": null, "error": null },
    "sentiment_analyzer": { "status": "completed", "processing_time_seconds": 5.3, "result": { "..." : "..." }, "error": null },
    "document_classifier": { "status": "running", "processing_time_seconds": null, "result": null, "error": null }
  },
  "agents_completed": null,
  "agents_failed": null,
  "total_processing_time_seconds": null,
  "created_at": "2026-06-03T05:45:51",
  "completed_at": null
}
```

---

### GET `/api/jobs`

List all analysis jobs.

**Request**

```bash
curl http://localhost:8001/api/jobs
```

**Response** `200 OK`

```json
{
  "jobs": [
    {
      "job_id": "job_19e8ed7ab3f1993bdec5fdb5",
      "document_id": "doc_c0b7707174459a85c05bd03e",
      "document_name": "211_2020_12_51_71182_Judgement_15-May-2026.pdf",
      "status": "completed",
      "agents_completed": 4,
      "agents_failed": 0,
      "created_at": "2026-06-03T06:40:09",
      "completed_at": "2026-06-03T06:40:19.242378"
    }
  ]
}
```

---

## Design Decisions

**Framework and architecture.** I chose FastAPI for async support, automatic OpenAPI docs, and Pydantic validation. The codebase follows a thin-controller pattern: routes delegate to services, services own business logic, and SQLAlchemy models handle persistence. This keeps HTTP concerns separate from agent orchestration and makes each layer easy to test independently.

**Database.** SQLite via SQLAlchemy is sufficient for this assessment — zero external infrastructure, single-file storage, and adequate concurrency for several simultaneous upload-and-analyze requests. Three tables model the domain: `documents` (uploaded content and metadata), `analysis_jobs` (overall job state), and `agent_runs` (per-agent status, results, errors, and timing). Alembic manages schema migrations.

**Parallel agent execution.** All four agents start simultaneously using `asyncio.gather`. Each agent runs in its own try/except block and writes results to the database as soon as it finishes, enabling partial polling without waiting for the slowest agent. Total job time equals the slowest agent, not the sum of all four.

**Background processing.** The `/analyze` endpoint creates a job record and schedules processing via FastAPI `BackgroundTasks`, returning a `job_id` in under 500 ms. This satisfies the requirement that analysis must not block the HTTP response.

**LLM integration.** A shared `llm_client.py` wraps the OpenAI Chat Completions API with JSON response format. Each agent has its own prompt and Pydantic result schema for validation. If `OPENAI_API_KEY` is unset, stub agents return schema-valid placeholder data so the full flow can be demoed offline.

**Failure handling.** Agent failures (LLM timeout, invalid JSON, validation errors) are isolated — one failure does not cancel the others. Job status is derived after all agents finish: `completed` (all succeed), `partially_failed` (mixed), or `failed` (all fail).

**Entity extractor response shape.** Dates, locations, and monetary values use `{ "value", "mentions" }` objects rather than plain strings. This satisfies the agent requirement for per-entity mention counts, which goes beyond the simplified example in the assessment PDF.

**PDF text extraction.** PyPDF2 handles text-based PDFs without adding OCR complexity. Scanned image PDFs are rejected with a clear 400 error. TXT files support UTF-8 and Latin-1 decoding.

**Input validation.** Upload validates file type (PDF/TXT only), empty files, and a configurable size limit (`MAX_UPLOAD_SIZE_MB`). Errors return meaningful JSON `detail` messages with appropriate HTTP status codes.

**Logging.** Application-level logging records uploads, job creation, agent start/completion/failure, and job finalization for debugging and traceability during demos.

**Re-analyze.** Each call to `/analyze` on the same document creates a new job and increments `analysis_count`. Previous job results are preserved.
