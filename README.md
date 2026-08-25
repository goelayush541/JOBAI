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
| POST | `/api/auth/signup` | Register account |
| POST | `/api/auth/login` | Get JWT token |
| GET | `/api/auth/me` | Current user profile |
| POST | `/api/resumes` | Upload resume (PDF/DOCX/TXT) |
| GET | `/api/resumes` | List resumes |
| GET | `/api/resumes/{id}` | Resume detail |
| POST | `/api/jobs` | Create job entry |
| GET | `/api/jobs` | List jobs |
| GET | `/api/jobs/{id}` | Job detail |
| PUT | `/api/jobs/{id}` | Update job |
| DELETE | `/api/jobs/{id}` | Delete job |
| POST | `/api/applications` | Create application (AI analysis triggered) |
| GET | `/api/applications` | List applications |
| GET | `/api/applications/{id}` | Application detail + AI insights |
| PATCH | `/api/applications/{id}/status` | Update status (timeline tracking) |
| GET | `/api/applications/{id}/history` | Status change history |
| POST | `/api/reminders` | Create reminder |
| GET | `/api/reminders` | List reminders |
| GET | `/api/dashboard` | Aggregated stats |

## Features
- **AI Resume-Job Matching** — Gemini analyzes skill alignment, scores relevance, identifies missing skills, and provides tailored suggestions
- **Application Status Tracking** — Append-only timeline (applied → interview → offer → rejected → withdrawn)
- **Deadline Reminders** — Cloud Tasks scheduling with local fallback
- **Dashboard** — Stats, recent activity, status distribution
- **JWT Auth** — bcrypt password hashing, role-based access
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
│   ├── api/                 # Route handlers (auth, resumes, jobs, applications, reminders, dashboard)
│   └── services/            # Gemini AI, GCS storage, Cloud Tasks, auth (JWT/bcrypt)
├── static/
│   └── index.html           # Complete frontend UI (no build step)
├── requirements.txt
├── .env                     # Local config (SQLite + mock services)
├── Dockerfile
├── docker-compose.yml
├── cloudbuild.yaml
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
- **Frontend:** Vanilla HTML/CSS/JS (zero dependencies)
- **Cloud:** Cloud Run, Cloud Storage, Cloud Tasks
