# AI Job Application Tracker

> Gemini-powered job application tracker with AI-driven insights, tailored resume suggestions, and smart deadline reminders.

## Quick Start (VS Code)

### 1. Prerequisites
- Python 3.10+
- VS Code with Python extension

### 2. Setup
```bash
# Clone & enter project
cd JOBAI

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment
Copy `.env` and adjust values if needed. Defaults run in **local mock mode** (no GCP credentials required):
```
DATABASE_URL=sqlite+aiosqlite:///./jobtracker.db
GCP_PROJECT_ID=
GEMINI_MODEL=gemini-2.5-flash
SECRET_KEY=dev-secret-key-change-in-production
```

### 4. Run in VS Code
- **Option A (Recommended):** Press `F5` or use Run & Debug panel → "Run FastAPI (uvicorn)"
- **Option B:** Terminal → `uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload`

Open **http://127.0.0.1:8080** for the full UI, or **http://127.0.0.1:8080/docs** for Swagger.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/signup` | Register account |
| POST | `/api/v1/auth/login` | Get JWT token |
| GET | `/api/v1/auth/me` | Current user profile |
| POST | `/api/v1/resumes` | Upload resume (PDF/DOCX/TXT) |
| GET | `/api/v1/resumes` | List resumes |
| POST | `/api/v1/jobs` | Create job entry |
| GET | `/api/v1/jobs` | List jobs |
| GET | `/api/v1/jobs/{id}` | Job detail |
| PUT | `/api/v1/jobs/{id}` | Update job |
| DELETE | `/api/v1/jobs/{id}` | Delete job |
| POST | `/api/v1/applications` | Create application (AI analysis triggered) |
| GET | `/api/v1/applications` | List applications |
| GET | `/api/v1/applications/{id}` | Application detail + AI insights |
| POST | `/api/v1/applications/{id}/retry-analysis` | Retry failed Gemini analysis |
| PATCH | `/api/v1/applications/{id}/status` | Update status (auto-cancels reminders on withdrawal) |
| GET | `/api/v1/applications/{id}/history` | Status change history |
| POST | `/api/v1/reminders` | Create reminder (with channel: in_app/email/sms) |
| GET | `/api/v1/reminders` | List reminders |
| PATCH | `/api/v1/reminders/{id}/cancel` | Cancel a pending reminder |
| GET | `/api/v1/dashboard` | Stats + recent activity feed |
| GET | `/api/v1/metrics` | Success metrics (match accuracy, conversion rate, follow-up rate) |

## Features
- **AI Resume-Job Matching** — Gemini analyzes skill alignment, scores relevance, identifies missing skills, and provides tailored suggestions
- **Pending Analysis + Retry** — Failed analysis sets `pending_analysis` status with retry endpoint
- **Application Status Tracking** — Append-only timeline (applied → pending_analysis → interview → offer → rejected → withdrawn) with auto-cancel reminders on withdrawal
- **Deadline Reminders** — Cloud Tasks scheduling with channel support (in_app/email/sms) and local fallback
- **Dashboard** — Stats, recent activity feed, status distribution
- **Success Metrics** — Match accuracy, conversion rate, follow-up rate tracking
- **Encryption at Rest** — Local file encryption with HMAC integrity verification
- **Structured Logging** — Cloud Logging compatible, no stack traces exposed
- **Cloud Scheduler** — Mock + real Google Cloud Scheduler for recurring jobs
- **JWT Auth** — bcrypt password hashing, row-level access control
- **Full Frontend UI** — Single-page app with auth, dashboard, applications, resumes, jobs, and reminders

## Architecture
```
JOBAI/
├── app/
│   ├── main.py              # FastAPI entry point + static files
│   ├── config.py            # Pydantic settings from .env
│   ├── database.py          # Async SQLAlchemy + SQLite adapter
│   ├── models/              # ORM models (User, Resume, Job, Application, Reminder, AIInsight)
│   ├── schemas/             # Pydantic request/response schemas
│   ├── api/                 # Route handlers (auth, resumes, jobs, applications, reminders, dashboard, metrics)
│   └── services/            # Gemini AI, GCS storage, Cloud Tasks, Cloud Scheduler, Pub/Sub, auth (JWT/bcrypt)
├── static/
│   └── index.html           # Complete frontend UI (no build step)
├── tests/                   # Test suite
├── requirements.txt
├── .env                     # Local config (SQLite + mock services + encryption)
├── Dockerfile
├── docker-compose.yml
├── cloudbuild.yaml          # CI/CD with test step
└── .vscode/launch.json
```

## Production (Google Cloud)
```bash
# Set real GCP project
export GCP_PROJECT_ID=your-gcp-project-id

# Deploy
gcloud builds submit --config cloudbuild.yaml .
```

## Tech Stack
- **Backend:** FastAPI, SQLAlchemy (async), Pydantic v2
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **AI:** Google Gemini 2.5 Flash (Vertex AI)
- **Auth:** JWT + bcrypt
- **Security:** HMAC encryption at rest, structured logging
- **Frontend:** Vanilla HTML/CSS/JS (zero dependencies)
- **Cloud:** Cloud Run, Cloud Storage, Cloud Tasks, Pub/Sub
