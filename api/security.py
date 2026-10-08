import bcrypt
import hashlib
import hmac
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException, Request, Response

from api.database import connect_database
from contextlib import closing


COOKIE_NAME = "interview_coach_session"
SESSION_LIFETIME = timedelta(days=7)
LOGIN_ATTEMPT_WINDOW = 15 * 60
LOGIN_ATTEMPT_LIMIT = 10
JWT_ISSUER = "ai-interview-coach"
JWT_AUDIENCE = "ai-interview-coach-web"
PASSWORD_HASH_ITERATIONS = 310_000
ENVIRONMENT = os.environ.get("APP_ENV", "development").lower()
JWT_SECRET = os.environ.get("JWT_SECRET")
if ENVIRONMENT == "production" and (
    not JWT_SECRET or len(JWT_SECRET.encode("utf-8")) < 32
):
    raise RuntimeError("Set JWT_SECRET to a random value of at least 32 bytes in production.")
JWT_SIGNING_KEY = JWT_SECRET or secrets.token_urlsafe(48)
COOKIE_SECURE = os.environ.get(
    "AUTH_COOKIE_SECURE", "true" if ENVIRONMENT == "production" else "false"
).lower() in {"1", "true", "yes"}
if ENVIRONMENT == "production" and not COOKIE_SECURE:
    raise RuntimeError("AUTH_COOKIE_SECURE must be true in production.")

_DUMMY_PASSWORD_HASH = bcrypt.hashpw(b"not-a-real-password", bcrypt.gensalt())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode(
        "ascii"
    )


def verify_password(password: str, row: Any) -> bool:
    candidate = password.encode("utf-8")
    if row["password_scheme"] == "bcrypt":
        if len(candidate) > 72:
            return False
        try:
            return bcrypt.checkpw(candidate, row["password_hash"].encode("ascii"))
        except ValueError:
            return False
    if row["password_scheme"] == "bcrypt_sha256":
        digest = hashlib.sha256(candidate).hexdigest().encode("ascii")
        try:
            return bcrypt.checkpw(digest, row["password_hash"].encode("ascii"))
        except ValueError:
            return False

    legacy_hash = hashlib.pbkdf2_hmac(
        "sha256",
        candidate,
        bytes.fromhex(row["password_salt"]),
        PASSWORD_HASH_ITERATIONS,
    )
    if not hmac.compare_digest(legacy_hash.hex(), row["password_hash"]):
        return False
    return True


def hash_long_legacy_password(password: str) -> str:
    digest = hashlib.sha256(password.encode("utf-8")).hexdigest().encode("ascii")
    return bcrypt.hashpw(digest, bcrypt.gensalt(rounds=12)).decode("ascii")


def verify_unknown_user_password(password: str) -> None:
    digest = hashlib.sha256(password.encode("utf-8")).hexdigest().encode("ascii")
    bcrypt.checkpw(digest, _DUMMY_PASSWORD_HASH)


def enforce_login_rate_limit(request: Request) -> None:
    ip_hash = _request_ip_hash(request)
    now = int(time.time())
    with closing(connect_database()) as connection:
        row = connection.execute(
            "SELECT attempts, window_started FROM auth_login_attempts WHERE ip_hash = ?",
            (ip_hash,),
        ).fetchone()
    if (
        row is not None
        and row["window_started"] > now - LOGIN_ATTEMPT_WINDOW
        and row["attempts"] >= LOGIN_ATTEMPT_LIMIT
    ):
        retry_after = row["window_started"] + LOGIN_ATTEMPT_WINDOW - now
        raise HTTPException(
            status_code=429,
            detail="Too many sign-in attempts. Wait a few minutes and try again.",
            headers={"Retry-After": str(max(retry_after, 1))},
        )


def record_failed_login(request: Request) -> None:
    ip_hash = _request_ip_hash(request)
    now = int(time.time())
    window_floor = now - LOGIN_ATTEMPT_WINDOW
    with closing(connect_database()) as connection:
        connection.execute(
            """
            INSERT INTO auth_login_attempts (ip_hash, attempts, window_started)
            VALUES (?, 1, ?)
            ON CONFLICT(ip_hash) DO UPDATE SET
                attempts = CASE
                    WHEN auth_login_attempts.window_started <= ? THEN 1
                    ELSE auth_login_attempts.attempts + 1
                END,
                window_started = CASE
                    WHEN auth_login_attempts.window_started <= ? THEN excluded.window_started
                    ELSE auth_login_attempts.window_started
                END
            """,
            (ip_hash, now, window_floor, window_floor),
        )


def clear_failed_logins(request: Request) -> None:
    with closing(connect_database()) as connection:
        connection.execute(
            "DELETE FROM auth_login_attempts WHERE ip_hash = ?",
            (_request_ip_hash(request),),
        )


def _request_ip_hash(request: Request) -> str:
    ip_address = request.client.host if request.client else "unknown"
    return hmac.new(
        JWT_SIGNING_KEY.encode("utf-8"),
        ip_address.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def issue_session(response: Response, user_id: int) -> None:
    now = datetime.now(timezone.utc)
    expires_at = now + SESSION_LIFETIME
    session_id = secrets.token_urlsafe(32)
    token = jwt.encode(
        {
            "sub": str(user_id),
            "jti": session_id,
            "iat": now,
            "exp": expires_at,
            "iss": JWT_ISSUER,
            "aud": JWT_AUDIENCE,
        },
        JWT_SIGNING_KEY,
        algorithm="HS256",
    )
    with closing(connect_database()) as connection:
        connection.execute(
            "INSERT INTO auth_sessions (user_id, jti, expires_at) VALUES (?, ?, ?)",
            (user_id, session_id, int(expires_at.timestamp())),
        )
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=int(SESSION_LIFETIME.total_seconds()),
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/api",
    )


def get_current_user(request: Request) -> dict[str, Any]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise _unauthorized("Please log in to access this feature.")
    try:
        claims = jwt.decode(
            token,
            JWT_SIGNING_KEY,
            algorithms=["HS256"],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            options={"require": ["sub", "jti", "iat", "exp", "iss", "aud"]},
        )
        user_id = int(claims["sub"])
        session_id = claims["jti"]
        expires_at = int(claims["exp"])
    except jwt.ExpiredSignatureError as exc:
        raise _unauthorized("Your session has expired. Please log in again.") from exc
    except (jwt.InvalidTokenError, TypeError, ValueError, KeyError) as exc:
        raise _unauthorized("Your session is invalid. Please log in again.") from exc

    with closing(connect_database()) as connection:
        row = connection.execute(
            """
            SELECT u.id, u.full_name, u.email, s.jti
            FROM auth_sessions AS s
            JOIN users AS u ON u.id = s.user_id
            WHERE s.jti = ? AND s.user_id = ? AND s.revoked_at IS NULL
                AND s.expires_at > ?
            """,
            (session_id, user_id, int(time.time())),
        ).fetchone()
    if row is None or expires_at <= int(time.time()):
        raise _unauthorized("Your session is no longer active. Please log in again.")
    return dict(row)


def current_user(request: Request) -> dict[str, Any]:
    user = getattr(request.state, "current_user", None)
    return user if user is not None else get_current_user(request)


def clear_session(response: Response) -> None:
    response.delete_cookie(
        COOKIE_NAME,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/api",
    )


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )
