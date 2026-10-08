# AI Recruitment Interview Coach

A Streamlit app for analyzing resumes against job descriptions, generating
personalized interview questions, and evaluating candidate answers with Groq.

## Project layout

```text
.
|-- app/
|   |-- main.py                 # Streamlit application entry point
|   `-- __init__.py
|-- data/
|   |-- interview_data/         # Local interview data (ignored by Git)
|   `-- resumes/                # Local resume files (ignored by Git)
|-- src/
|   |-- ai/                     # Resume, job-match, and interview AI services
|   |-- resume/                 # Resume parsing utilities
|   `-- __init__.py
|-- tests/                      # Automated tests
|-- .env.example                # Environment variable template
|-- requirements.txt
`-- README.md
```

# AI Interview Coach

A resume-aware interview practice application. The original Streamlit app remains available; a separate React/Vite interface and FastAPI adapter provide a responsive web experience while reusing the existing Python AI services.

## Architecture

```text
React + Vite (frontend/) -> FastAPI (api/main.py) -> existing Python AI services (src/)
Original Streamlit app (app/main.py) ---------------------------> existing Python AI services (src/)
```

The API adapter does not replace or modify the AI prompts and business logic. It calls the existing PDF extractor, resume analyzer, job matcher, question generator, answer evaluator, and interview report generator. The Streamlit entry point remains intact.

## Features

- PDF resume extraction and AI analysis
- Resume-to-job-description comparison
- Personalized question generation
- Answer-by-answer evaluation and final AI interview report
- Responsive dashboard, interview workspace, report, and question-level analytics
- Light and dark themes, with theme preference saved in the browser
- Accessible upload, form, loading, error, empty, and mobile navigation states

## Requirements and environment

- Python and the project virtual environment
- Node.js 20 or newer and npm
- A Groq API key for AI-backed operations

Copy `.env.example` to `.env` and configure `GROQ_API_KEY`. Set `JWT_SECRET` to a cryptographically random value of at least 32 bytes for persistent sessions across API restarts and for every non-development deployment. Never put AI credentials or JWT signing secrets in frontend environment variables.

For production, also set `APP_ENV=production`, `AUTH_COOKIE_SECURE=true`, and `AUTH_ALLOWED_ORIGINS` to the exact HTTPS origins serving the frontend. The API refuses to start in production without a sufficiently long JWT secret and secure cookies.

Generate a local secret with `python -c "import secrets; print(secrets.token_urlsafe(48))"` and copy it into `.env` as `JWT_SECRET`.

## Backend setup

From the project root, activate the Python environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run the React-facing API:

```powershell
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

The health check is available at `http://127.0.0.1:8000/api/health`.

The original Streamlit app can still be started separately:

```powershell
streamlit run app/main.py
```

## Frontend setup

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`. The Vite development server proxies `/api` to `http://127.0.0.1:8000`. Copy `frontend/.env.example` to `frontend/.env` only if you need to override `VITE_API_BASE_URL`.

Create a production bundle with `npm run build` from `frontend/`.

## API routes

- `GET /api/health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- `GET /api/account/dashboard`
- `POST /api/resume/analyze` (multipart PDF upload, maximum 8 MB)
- `POST /api/job-match/analyze`
- `POST /api/interviews`
- `GET /api/interviews/{id}`
- `POST /api/interviews/{id}/answer`
- `POST /api/interviews/{id}/skip`
- `POST /api/interviews/{id}/next`
- `POST /api/interviews/{id}/complete`
- `GET /api/interviews/{id}/report`

The interview generator currently accepts resume text, a job description, and question count. Interview type, difficulty, and company-specific prompts are not supported by the existing AI function and are not presented as active controls.
Except for health, registration and login, API routes require a valid session cookie. Login is throttled after 10 failed attempts per client IP in a 15-minute window.

## Data and limitations

- Passwords are hashed with bcrypt. JWTs are issued in seven-day, HttpOnly, SameSite=Lax cookies; active sessions are stored and revocable in SQLite. API middleware validates each protected request and checks account ownership for interview, report, and dashboard queries.
- SQLite defaults to `data/accounts.sqlite3` (override with `AUTH_DATABASE_PATH`). Resume analyses, role matches, interview state, answer history, and reports have user foreign keys; interview and report lookups are scoped to the signed-in user. Original uploaded PDF files are not retained.
- Profile practice preferences remain local to the browser and are namespaced by account; resume analyses, role matches, interview sessions, reports, and answer history are persisted to SQLite.
- The frontend restores the session from the HttpOnly cookie and loads the account's latest resume/match plus interview and practice history from the API. Protected routes return users to their intended page after login. Login and signup are public; application routes and APIs require authentication.
- This deployment uses a local SQLite file and is intended for a single-host deployment. For horizontal scaling, move the schema and transactions to managed PostgreSQL, persist the signing key in a secret manager, configure HTTPS and exact allowed origins, and add edge-level rate limiting plus backup/retention policies. Do not use SQLite on an ephemeral disk. Email verification, password reset, and MFA are not configured.
- Analytics currently visualizes the latest completed report and shows recent saved answer history. Speech transcription is not implemented.
- The AI resume and job match services return narrative analysis, so the UI displays their actual text rather than inventing structured scores or skill lists.
- Voice input is not implemented.
- Scanned/image-only PDFs may not yield extractable text.

## Project structure

```text
api/                         FastAPI adapter around existing Python services
app/main.py                  Original Streamlit application
frontend/src/components/     Shared UI and application shell
frontend/src/context/        Browser session and theme state
frontend/src/pages/          Landing, workspace, interview, report, and settings pages
frontend/src/services/       Centralized Axios API client
src/ai/                      Existing AI analysis and interview functions
src/resume/                  Existing PDF extraction utility
data/                        Local interview and resume data directories
```

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

	```powershell
	python -m pip install -r requirements.txt
	```

3. Copy `.env.example` to `.env` and set `GROQ_API_KEY`.
4. Start the app:

	```powershell
	streamlit run app/main.py
	```

`GROQ_BASE_URL` and `GROQ_MODEL` are optional; defaults are defined by the AI
service modules. Keep API keys and uploaded candidate documents out of version
control.
