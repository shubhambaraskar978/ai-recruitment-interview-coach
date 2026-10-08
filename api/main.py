import os
import re
import sqlite3
from contextlib import closing
from io import BytesIO
from uuid import uuid4

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from api.database import connect_database, decode_json, encode_json
from api.security import (
    clear_session,
    clear_failed_logins,
    current_user,
    enforce_login_rate_limit,
    get_current_user,
    hash_long_legacy_password,
    hash_password,
    issue_session,
    record_failed_login,
    verify_password,
    verify_unknown_user_password,
)
from src.ai.answer_evaluator import evaluate_answer
from src.ai.interview_generator import generate_interview_questions
from src.ai.interview_report import generate_interview_report
from src.ai.job_matcher import analyze_job_match
from src.ai.resume_analyzer import analyze_resume
from src.resume.pdf_extractor import extract_text_from_pdf


app = FastAPI(title="AI Interview Coach API", version="1.0.0")
ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.environ.get(
        "AUTH_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
MAX_RESUME_BYTES = 8 * 1024 * 1024


class TextRequest(BaseModel):
    resume_text: str = Field(min_length=1, max_length=100_000)


class JobMatchRequest(TextRequest):
    job_description: str = Field(min_length=1, max_length=50_000)


class InterviewRequest(JobMatchRequest):
    number_of_questions: int = Field(default=5, ge=1, le=20)


class AnswerRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=20_000)


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Enter your full name.")
        return value

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be 72 UTF-8 bytes or fewer.")
        return value


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 512:
            raise ValueError("Password is too long.")
        return value


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        origin = request.headers.get("origin")
        if origin and origin.rstrip("/") not in ALLOWED_ORIGINS:
            return JSONResponse(
                {"detail": "Request origin is not allowed."},
                status_code=403,
            )
        if request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse(
                {"detail": "Cross-site requests are not allowed."},
                status_code=403,
            )

        public_routes = {
            ("GET", "/api/health"),
            ("POST", "/api/auth/register"),
            ("POST", "/api/auth/login"),
        }
        if (
            request.method != "OPTIONS"
            and (request.method, request.url.path) not in public_routes
        ):
            try:
                request.state.current_user = get_current_user(request)
            except HTTPException as exc:
                return JSONResponse(
                    {"detail": exc.detail},
                    status_code=exc.status_code,
                    headers=exc.headers,
                )
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/auth/register", status_code=201)
def register(request: RegisterRequest, response: Response) -> dict:
    full_name = request.full_name
    email = request.email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")

    with closing(connect_database()) as connection:
        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO users
                        (full_name, email, password_salt, password_hash, password_scheme)
                    VALUES (?, ?, '', ?, 'bcrypt')
                    """,
                    (full_name, email, hash_password(request.password)),
                )
        except sqlite3.IntegrityError as exc:
            if _user_exists(connection, email):
                raise HTTPException(
                    status_code=409, detail="An account with this email already exists."
                ) from exc
            raise

        user_id = connection.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()["id"]
    issue_session(response, user_id)
    return {"user": {"id": user_id, "full_name": full_name, "email": email}}


@app.post("/api/auth/login")
def login(
    request: LoginRequest,
    response: Response,
    http_request: Request,
) -> dict:
    enforce_login_rate_limit(http_request)
    email = request.email.strip().lower()
    with closing(connect_database()) as connection:
        row = connection.execute(
            "SELECT id, full_name, email, password_salt, password_hash, password_scheme "
            "FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if row is None:
            verify_unknown_user_password(request.password)
            record_failed_login(http_request)
            raise HTTPException(status_code=401, detail="Email or password is incorrect.")
        if not verify_password(request.password, row):
            record_failed_login(http_request)
            raise HTTPException(status_code=401, detail="Email or password is incorrect.")
        user_id = row["id"]
        if row["password_scheme"] not in {"bcrypt", "bcrypt_sha256"}:
            new_scheme = (
                "bcrypt" if len(request.password.encode("utf-8")) <= 72 else "bcrypt_sha256"
            )
            new_hash = (
                hash_password(request.password)
                if new_scheme == "bcrypt"
                else hash_long_legacy_password(request.password)
            )
            connection.execute(
                "UPDATE users SET password_hash = ?, password_salt = '', "
                "password_scheme = ? WHERE id = ?",
                (new_hash, new_scheme, user_id),
            )

    clear_failed_logins(http_request)
    issue_session(response, user_id)
    return {
        "user": {
            "id": user_id,
            "full_name": row["full_name"],
            "email": row["email"],
        }
    }


@app.get("/api/auth/me")
def get_session_user(user: dict = Depends(current_user)) -> dict:
    return {"user": _public_user(user)}


@app.post("/api/auth/logout")
def logout(response: Response, user: dict = Depends(current_user)) -> dict:
    with closing(connect_database()) as connection:
        connection.execute(
            "UPDATE auth_sessions SET revoked_at = CURRENT_TIMESTAMP "
            "WHERE jti = ? AND user_id = ? AND revoked_at IS NULL",
            (user["jti"], user["id"]),
        )
    clear_session(response)
    return {"status": "ok"}


@app.get("/api/account/dashboard")
def get_account_dashboard(user: dict = Depends(current_user)) -> dict:
    with closing(connect_database()) as connection:
        resume_row = connection.execute(
            """
            SELECT id, filename, resume_text, analysis, created_at
            FROM resume_analyses WHERE user_id = ?
            ORDER BY created_at DESC, id DESC LIMIT 1
            """,
            (user["id"],),
        ).fetchone()
        resume_history_rows = connection.execute(
            """
            SELECT id, filename, analysis, created_at
            FROM resume_analyses WHERE user_id = ?
            ORDER BY created_at DESC, id DESC LIMIT 20
            """,
            (user["id"],),
        ).fetchall()
        match_row = connection.execute(
            """
            SELECT job_description, analysis, created_at
            FROM job_match_analyses
            WHERE user_id = ? AND resume_analysis_id = ?
            ORDER BY created_at DESC, id DESC LIMIT 1
            """,
            (user["id"], resume_row["id"] if resume_row else -1),
        ).fetchone()
        job_match_history_rows = connection.execute(
            """
            SELECT id, job_description, analysis, created_at
            FROM job_match_analyses WHERE user_id = ?
            ORDER BY created_at DESC, id DESC LIMIT 20
            """,
            (user["id"],),
        ).fetchall()
        interview_rows = connection.execute(
            """
            SELECT s.id, s.state_json, s.created_at, r.report_json
            FROM interview_sessions AS s
            LEFT JOIN interview_reports AS r ON r.interview_id = s.id
            WHERE s.user_id = ?
            ORDER BY s.created_at DESC
            """,
            (user["id"],),
        ).fetchall()
        practice_rows = connection.execute(
            """
            SELECT h.interview_id, h.question_index, h.answer, h.evaluation_json,
                   h.skipped, h.created_at, s.state_json
            FROM practice_history AS h
            JOIN interview_sessions AS s ON s.id = h.interview_id
            WHERE h.user_id = ? AND s.user_id = ?
            ORDER BY h.created_at DESC, h.id DESC
            LIMIT 50
            """,
            (user["id"], user["id"]),
        ).fetchall()

    interviews = []
    latest_report = None
    for row in interview_rows:
        state = decode_json(row["state_json"])
        report_details = decode_json(row["report_json"]) if row["report_json"] else None
        interview_summary = {
            "id": row["id"],
            "status": "complete"
            if state["current_index"] >= len(state["questions"])
            else "in_progress",
            "created_at": row["created_at"],
            "overall_score": (
                report_details["report"].get("overall_score")
                if report_details
                else None
            ),
        }
        interviews.append(interview_summary)
        if report_details and latest_report is None:
            latest_report = {
                "interview_id": row["id"],
                **report_details,
            }
    practice_history = []
    for row in practice_rows:
        state = decode_json(row["state_json"])
        practice_history.append(
            {
                "interview_id": row["interview_id"],
                "question_index": row["question_index"],
                "question": state["questions"][row["question_index"]],
                "answer": row["answer"],
                "evaluation": decode_json(row["evaluation_json"]),
                "skipped": bool(row["skipped"]),
                "created_at": row["created_at"],
            }
        )

    return {
        "user": _public_user(user),
        "resume": dict(resume_row) if resume_row else None,
        "resume_analyses": [dict(row) for row in resume_history_rows],
        "job_match": dict(match_row) if match_row else None,
        "job_matches": [dict(row) for row in job_match_history_rows],
        "interviews": interviews,
        "practice_history": practice_history,
        "latest_report": latest_report,
        "practice_history_count": _practice_history_count(user["id"]),
    }


@app.post("/api/resume/analyze")
async def resume_analysis(
    file: UploadFile = File(...),
    user: dict = Depends(current_user),
) -> dict:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Upload a PDF resume.")

    contents = await file.read(MAX_RESUME_BYTES + 1)
    if len(contents) > MAX_RESUME_BYTES:
        raise HTTPException(status_code=413, detail="The PDF must be 8 MB or smaller.")
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="The uploaded file is not a valid PDF.")

    try:
        resume_text = extract_text_from_pdf(BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Could not read this PDF.") from exc

    if not resume_text:
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted. The PDF may be scanned or image-based.",
        )

    analysis = analyze_resume(resume_text)
    if analysis.startswith("An error occurred"):
        raise HTTPException(status_code=502, detail="Resume analysis is temporarily unavailable.")
    with closing(connect_database()) as connection:
        result = connection.execute(
            """
            INSERT INTO resume_analyses (user_id, filename, resume_text, analysis)
            VALUES (?, ?, ?, ?)
            """,
            (user["id"], file.filename[:255], resume_text, analysis),
        )
        resume_analysis_id = result.lastrowid
    return {
        "id": resume_analysis_id,
        "filename": file.filename,
        "resume_text": resume_text,
        "analysis": analysis,
    }


@app.post("/api/job-match/analyze")
def job_match(
    request: JobMatchRequest,
    user: dict = Depends(current_user),
) -> dict:
    with closing(connect_database()) as connection:
        resume_row = connection.execute(
            "SELECT id, resume_text FROM resume_analyses WHERE user_id = ? "
            "ORDER BY created_at DESC, id DESC LIMIT 1",
            (user["id"],),
        ).fetchone()
    if resume_row is None:
        raise HTTPException(status_code=409, detail="Analyze a resume before matching a role.")

    result = analyze_job_match(resume_row["resume_text"], request.job_description)
    if result.startswith("An error occurred"):
        raise HTTPException(status_code=502, detail="Job matching is temporarily unavailable.")
    with closing(connect_database()) as connection:
        connection.execute(
            """
            INSERT INTO job_match_analyses
                (user_id, resume_analysis_id, job_description, analysis)
            VALUES (?, ?, ?, ?)
            """,
            (
                user["id"],
                resume_row["id"] if resume_row else None,
                request.job_description,
                result,
            ),
        )
    return {"analysis": result}


@app.post("/api/interviews")
def create_interview(
    request: InterviewRequest,
    user: dict = Depends(current_user),
) -> dict:
    with closing(connect_database()) as connection:
        resume_row = connection.execute(
            "SELECT resume_text FROM resume_analyses WHERE user_id = ? "
            "ORDER BY created_at DESC, id DESC LIMIT 1",
            (user["id"],),
        ).fetchone()
    if resume_row is None:
        raise HTTPException(status_code=409, detail="Analyze a resume before creating an interview.")

    generated = generate_interview_questions(
        resume_row["resume_text"],
        request.job_description,
        request.number_of_questions,
    )
    if generated.startswith("An error occurred"):
        raise HTTPException(status_code=502, detail="Interview generation is temporarily unavailable.")

    questions = []
    for raw_line in generated.splitlines():
        line = re.sub(r"^\s*[-*]\s*|^\*\*|\*\*$", "", raw_line.strip())
        match = re.match(r"^(?:Q(?:uestion)?\s*)?(\d+)[.\):\-]\s*(.+)$", line, re.IGNORECASE)
        if match:
            question = re.sub(
                r"\s+\*\*(?:Category|Difficulty|Interviewer is evaluating):.*$",
                "",
                match.group(2),
                flags=re.IGNORECASE,
            ).strip()
            if len(question) >= 10:
                questions.append(question)

    if not questions:
        questions = [
            line.strip()
            for line in generated.splitlines()
            if len(line.strip()) >= 20
            and ("?" in line or line.strip().lower().startswith(
                ("what ", "why ", "how ", "explain ", "describe ", "tell ")
            ))
        ]

    questions = questions[: request.number_of_questions]
    if not questions:
        raise HTTPException(status_code=502, detail="The generated questions could not be read. Please try again.")

    interview_id = str(uuid4())
    interview = {
        "resume_text": resume_row["resume_text"],
        "job_description": request.job_description,
        "questions": questions,
        "answers": [],
        "evaluations": [],
        "skipped_questions": [],
        "current_index": 0,
        "report": None,
    }
    with closing(connect_database()) as connection:
        connection.execute(
            "INSERT INTO interview_sessions (id, user_id, state_json) VALUES (?, ?, ?)",
            (interview_id, user["id"], encode_json(interview)),
        )
    return _interview_view(interview_id, interview)


@app.get("/api/interviews/{interview_id}")
def get_interview(
    interview_id: str,
    user: dict = Depends(current_user),
) -> dict:
    return _interview_view(interview_id, _get_interview(interview_id, user["id"]))


@app.post("/api/interviews/{interview_id}/answer")
def submit_answer(
    interview_id: str,
    request: AnswerRequest,
    user: dict = Depends(current_user),
) -> dict:
    interview = _get_interview(interview_id, user["id"])
    index = interview["current_index"]
    if index >= len(interview["questions"]):
        raise HTTPException(status_code=409, detail="This interview is already complete.")
    if len(interview["answers"]) > index:
        raise HTTPException(status_code=409, detail="This question already has a submitted answer.")

    evaluation = evaluate_answer(
        question=interview["questions"][index],
        candidate_answer=request.answer,
        resume_text=interview["resume_text"],
        job_description=interview["job_description"],
    )
    if evaluation.get("error"):
        raise HTTPException(status_code=502, detail="Answer evaluation is temporarily unavailable.")

    interview["answers"].append(request.answer)
    interview["evaluations"].append(evaluation)
    _save_interview(
        interview_id,
        user["id"],
        interview,
        {
            "question_index": index,
            "answer": request.answer,
            "evaluation": evaluation,
            "skipped": False,
        },
    )
    return {"evaluation": evaluation}


@app.post("/api/interviews/{interview_id}/skip")
def skip_question(
    interview_id: str,
    user: dict = Depends(current_user),
) -> dict:
    interview = _get_interview(interview_id, user["id"])
    index = interview["current_index"]
    if index >= len(interview["questions"]):
        raise HTTPException(status_code=409, detail="This interview is already complete.")
    if len(interview["answers"]) > index:
        raise HTTPException(status_code=409, detail="This question already has a submitted answer.")
    if index == len(interview["questions"]) - 1 and not any(interview["answers"]):
        raise HTTPException(status_code=409, detail="Submit at least one answer before completing the interview.")

    interview["answers"].append("")
    interview["evaluations"].append({})
    interview["skipped_questions"].append(index)
    next_index = index + 1
    if next_index >= len(interview["questions"]):
        _create_report(interview)
    interview["current_index"] = next_index
    _save_interview(
        interview_id,
        user["id"],
        interview,
        {
            "question_index": index,
            "answer": "",
            "evaluation": {},
            "skipped": True,
        },
    )
    return _interview_view(interview_id, interview)


@app.post("/api/interviews/{interview_id}/next")
def next_question(
    interview_id: str,
    user: dict = Depends(current_user),
) -> dict:
    interview = _get_interview(interview_id, user["id"])
    if len(interview["answers"]) <= interview["current_index"]:
        raise HTTPException(status_code=409, detail="Submit an answer before moving on.")
    next_index = interview["current_index"] + 1
    if next_index >= len(interview["questions"]):
        _create_report(interview)
    interview["current_index"] = next_index
    _save_interview(interview_id, user["id"], interview)
    return _interview_view(interview_id, interview)


@app.post("/api/interviews/{interview_id}/complete")
def complete_interview(
    interview_id: str,
    user: dict = Depends(current_user),
) -> dict:
    interview = _get_interview(interview_id, user["id"])
    if not any(interview["answers"]):
        raise HTTPException(status_code=409, detail="Submit at least one answer before ending the interview.")
    if interview["report"] is None:
        _create_report(interview)
    interview["current_index"] = len(interview["questions"])
    _save_interview(interview_id, user["id"], interview)
    return _interview_view(interview_id, interview)


@app.get("/api/interviews/{interview_id}/report")
def interview_report(
    interview_id: str,
    user: dict = Depends(current_user),
) -> dict:
    interview = _get_interview(interview_id, user["id"])
    if interview["report"] is None:
        raise HTTPException(status_code=409, detail="Complete the interview to generate its report.")
    return _report_details(interview)


def _get_interview(interview_id: str, user_id: int) -> dict:
    with closing(connect_database()) as connection:
        row = connection.execute(
            "SELECT state_json FROM interview_sessions WHERE id = ? AND user_id = ?",
            (interview_id, user_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Interview not found.")
    return decode_json(row["state_json"])


def _save_interview(
    interview_id: str,
    user_id: int,
    interview: dict,
    practice_entry: dict | None = None,
) -> None:
    with closing(connect_database()) as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            result = connection.execute(
                """
                UPDATE interview_sessions
                SET state_json = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
                """,
                (encode_json(interview), interview_id, user_id),
            )
            if result.rowcount != 1:
                raise HTTPException(status_code=404, detail="Interview not found.")
            if practice_entry is not None:
                connection.execute(
                    """
                    INSERT INTO practice_history
                        (user_id, interview_id, question_index, answer, evaluation_json, skipped)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        interview_id,
                        practice_entry["question_index"],
                        practice_entry["answer"],
                        encode_json(practice_entry["evaluation"]),
                        int(practice_entry["skipped"]),
                    ),
                )
            if interview["report"] is not None:
                connection.execute(
                    """
                    INSERT INTO interview_reports (user_id, interview_id, report_json)
                    VALUES (?, ?, ?)
                    ON CONFLICT(interview_id) DO UPDATE SET report_json = excluded.report_json
                    WHERE interview_reports.user_id = excluded.user_id
                    """,
                    (user_id, interview_id, encode_json(_report_details(interview))),
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def _practice_history_count(user_id: int) -> int:
    with closing(connect_database()) as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS total FROM practice_history WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    return row["total"]


def _report_details(interview: dict) -> dict:
    return {
        "report": interview["report"],
        "questions": interview["questions"],
        "answers": interview["answers"],
        "evaluations": interview["evaluations"],
        "skipped_questions": interview["skipped_questions"],
    }


def _user_exists(connection: sqlite3.Connection, email: str) -> bool:
    return (
        connection.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
        is not None
    )


def _create_report(interview: dict) -> None:
    report = generate_interview_report(
        interview["resume_text"],
        interview["job_description"],
        interview["questions"],
        interview["answers"],
        interview["evaluations"],
    )
    if report.get("error"):
        raise HTTPException(status_code=502, detail="The interview report is temporarily unavailable.")
    interview["report"] = report


def _interview_view(interview_id: str, interview: dict) -> dict:
    index = interview["current_index"]
    complete = index >= len(interview["questions"])
    return {
        "id": interview_id,
        "status": "complete" if complete else "in_progress",
        "current_question_index": index,
        "total_questions": len(interview["questions"]),
        "question": None if complete else interview["questions"][index],
        "completed_answers": index,
        "answered_questions": sum(bool(answer) for answer in interview["answers"]),
        "skipped_questions": interview["skipped_questions"],
        "current_evaluation": (
            interview["evaluations"][index]
            if index < len(interview["evaluations"])
            else None
        ),
    }


def _public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
    }