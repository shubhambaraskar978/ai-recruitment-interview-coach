import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any


DATABASE_PATH = Path(
    os.environ.get(
        "AUTH_DATABASE_PATH",
        Path(__file__).resolve().parents[1] / "data" / "accounts.sqlite3",
    )
)
_INITIALIZED_PATHS: set[Path] = set()
_SCHEMA_LOCK = threading.Lock()


def connect_database() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=15, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 15000")
    path = DATABASE_PATH.resolve()
    if path not in _INITIALIZED_PATHS:
        with _SCHEMA_LOCK:
            if path not in _INITIALIZED_PATHS:
                _ensure_schema(connection)
                _INITIALIZED_PATHS.add(path)
    return connection


def encode_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def decode_json(value: str) -> Any:
    return json.loads(value)


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_salt TEXT NOT NULL DEFAULT '',
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS auth_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            jti TEXT NOT NULL UNIQUE,
            expires_at INTEGER NOT NULL,
            revoked_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS auth_login_attempts (
            ip_hash TEXT PRIMARY KEY,
            attempts INTEGER NOT NULL,
            window_started INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS resume_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            filename TEXT NOT NULL,
            resume_text TEXT NOT NULL,
            analysis TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(id, user_id)
        );

        CREATE TABLE IF NOT EXISTS job_match_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            resume_analysis_id INTEGER,
            job_description TEXT NOT NULL,
            analysis TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(resume_analysis_id, user_id)
                REFERENCES resume_analyses(id, user_id)
        );

        CREATE TABLE IF NOT EXISTS interview_sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            state_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(id, user_id)
        );

        CREATE TABLE IF NOT EXISTS practice_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            interview_id TEXT NOT NULL,
            question_index INTEGER NOT NULL,
            answer TEXT NOT NULL,
            evaluation_json TEXT NOT NULL,
            skipped INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(interview_id, question_index),
            FOREIGN KEY(interview_id, user_id)
                REFERENCES interview_sessions(id, user_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS interview_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            interview_id TEXT NOT NULL UNIQUE,
            report_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(interview_id, user_id)
                REFERENCES interview_sessions(id, user_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_auth_sessions_user
            ON auth_sessions(user_id, expires_at);
        CREATE INDEX IF NOT EXISTS idx_auth_login_attempts_window
            ON auth_login_attempts(window_started);
        CREATE INDEX IF NOT EXISTS idx_resume_analyses_user
            ON resume_analyses(user_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_job_match_analyses_user
            ON job_match_analyses(user_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_interview_sessions_user
            ON interview_sessions(user_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_practice_history_user
            ON practice_history(user_id, created_at DESC);
        """
    )
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(users)").fetchall()
    }
    if "password_scheme" not in columns:
        connection.execute(
            "ALTER TABLE users ADD COLUMN password_scheme TEXT NOT NULL "
            "DEFAULT 'pbkdf2_sha256'"
        )
    connection.commit()
