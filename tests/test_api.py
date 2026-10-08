import hashlib
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import pymupdf
from fastapi.testclient import TestClient

from api.main import app
from api.database import connect_database


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        database_path = Path(self.temp_dir.name) / "accounts.sqlite3"
        database_patcher = patch("api.database.DATABASE_PATH", database_path)
        database_patcher.start()
        self.addCleanup(database_patcher.stop)
        self.email = "candidate@example.com"
        self.password = "secure-password"
        registered = self.client.post(
            "/api/auth/register",
            json={
                "full_name": "Test Candidate",
                "email": self.email,
                "password": self.password,
            },
        )
        self.register_response = registered
        self.assertEqual(registered.status_code, 201)
        self.user = registered.json()["user"]
        with closing(connect_database()) as connection:
            connection.execute(
                """
                INSERT INTO resume_analyses
                    (user_id, filename, resume_text, analysis)
                VALUES (?, ?, ?, ?)
                """,
                (self.user["id"], "resume.pdf", "Python project experience", "Analysis"),
            )

    def make_pdf(self, text=""):
        document = pymupdf.open()
        page = document.new_page()
        if text:
            page.insert_text((72, 72), text)
        contents = document.tobytes()
        document.close()
        return contents

    def test_health(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_register_persists_account_and_login_returns_user(self):
        registration = self.client.post(
            "/api/auth/register",
            json={
                "full_name": "Second Candidate",
                "email": "SECOND@example.com",
                "password": "secure-password",
            },
        )
        login_client = TestClient(app)
        login = login_client.post(
            "/api/auth/login",
            json={"email": "second@example.com", "password": "secure-password"},
        )

        self.assertEqual(registration.status_code, 201)
        self.assertEqual(
            registration.json()["user"],
            {
                "id": registration.json()["user"]["id"],
                "full_name": "Second Candidate",
                "email": "second@example.com",
            },
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.json()["user"], registration.json()["user"])

    def test_register_rejects_duplicate_email_and_login_rejects_wrong_password(self):
        payload = {
            "full_name": "Second Candidate",
            "email": "second@example.com",
            "password": "secure-password",
        }
        self.client.post("/api/auth/register", json=payload)

        duplicate = self.client.post("/api/auth/register", json=payload)
        wrong_password = self.client.post(
            "/api/auth/login",
            json={"email": payload["email"], "password": "incorrect-password"},
        )

        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(wrong_password.status_code, 401)

    def test_legacy_long_password_is_migrated_to_bcrypt_sha256(self):
        legacy_password = "l" * 80
        salt = b"legacy-test-salt"
        legacy_hash = hashlib.pbkdf2_hmac(
            "sha256", legacy_password.encode(), salt, 310_000
        ).hex()
        with closing(connect_database()) as connection:
            connection.execute(
                """
                INSERT INTO users
                    (full_name, email, password_salt, password_hash, password_scheme)
                VALUES (?, ?, ?, ?, 'pbkdf2_sha256')
                """,
                ("Legacy User", "legacy@example.com", salt.hex(), legacy_hash),
            )

        migrated = self.client.post(
            "/api/auth/login",
            json={"email": "legacy@example.com", "password": legacy_password},
        )
        with closing(connect_database()) as connection:
            stored = connection.execute(
                "SELECT password_scheme, password_hash FROM users WHERE email = ?",
                ("legacy@example.com",),
            ).fetchone()

        self.assertEqual(migrated.status_code, 200)
        self.assertEqual(stored["password_scheme"], "bcrypt_sha256")
        self.assertTrue(stored["password_hash"].startswith("$2"))

    def test_auth_middleware_requires_a_valid_session_and_logout_revokes_it(self):
        anonymous = TestClient(app)
        blocked = [
            anonymous.get("/api/account/dashboard"),
            anonymous.get("/api/interviews/not-a-session"),
            anonymous.get("/api/interviews/not-a-session/report"),
            anonymous.post("/api/job-match/analyze"),
            anonymous.post("/api/resume/analyze"),
        ]
        self.assertTrue(all(response.status_code == 401 for response in blocked))

        session = self.client.get("/api/auth/me")
        logged_out = self.client.post("/api/auth/logout")
        after_logout = self.client.get("/api/auth/me")

        self.assertEqual(session.status_code, 200)
        self.assertEqual(session.json()["user"], self.user)
        self.assertEqual(logged_out.status_code, 200)
        self.assertEqual(after_logout.status_code, 401)
        self.assertIn("httponly", self.register_response.headers["set-cookie"].lower())
        self.assertIn("samesite=lax", self.register_response.headers["set-cookie"].lower())
        allowed_origin = anonymous.get(
            "/api/account/dashboard",
            headers={"Origin": "http://localhost:5173"},
        )
        preflight = anonymous.options(
            "/api/account/dashboard",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertEqual(
            allowed_origin.headers.get("access-control-allow-origin"),
            "http://localhost:5173",
        )
        self.assertEqual(preflight.status_code, 200)
        self.assertEqual(
            preflight.headers.get("access-control-allow-credentials"),
            "true",
        )

    def test_login_attempts_are_limited(self):
        with patch("api.security.LOGIN_ATTEMPT_LIMIT", 2):
            first = self.client.post(
                "/api/auth/login",
                json={"email": self.email, "password": "incorrect-password"},
            )
            second = self.client.post(
                "/api/auth/login",
                json={"email": self.email, "password": "incorrect-password"},
            )
            blocked = self.client.post(
                "/api/auth/login",
                json={"email": self.email, "password": self.password},
            )

        self.assertEqual(first.status_code, 401)
        self.assertEqual(second.status_code, 401)
        self.assertEqual(blocked.status_code, 429)
        self.assertIn("retry-after", blocked.headers)


    @patch("api.main.generate_interview_questions", return_value="Question 1. Explain a project decision you made.")
    def test_interviews_persist_and_are_private_to_their_owner(self, generate_questions):
        created = self.client.post(
            "/api/interviews",
            json={
                "resume_text": "Client data is ignored in favor of the saved account resume",
                "job_description": "Python developer role",
                "number_of_questions": 1,
            },
        )
        interview_id = created.json()["id"]

        other_client = TestClient(app)
        other_registration = other_client.post(
            "/api/auth/register",
            json={
                "full_name": "Other Candidate",
                "email": "other@example.com",
                "password": "other-password",
            },
        )
        forbidden_interview = other_client.get(f"/api/interviews/{interview_id}")
        other_dashboard = other_client.get("/api/account/dashboard")
        owner_client = TestClient(app)
        owner_client.post(
            "/api/auth/login",
            json={"email": self.email, "password": self.password},
        )
        persisted_interview = owner_client.get(f"/api/interviews/{interview_id}")

        self.assertEqual(created.status_code, 200)
        self.assertEqual(other_registration.status_code, 201)
        self.assertEqual(forbidden_interview.status_code, 404)
        self.assertEqual(other_dashboard.json()["interviews"], [])
        self.assertEqual(
            other_client.get(f"/api/interviews/{interview_id}/report").status_code,
            404,
        )
        self.assertEqual(persisted_interview.status_code, 200)
        self.assertEqual(persisted_interview.json()["id"], interview_id)
        generate_questions.assert_called_once_with(
            "Python project experience",
            "Python developer role",
            1,
        )

    def test_dashboard_contains_only_authenticated_accounts_saved_data(self):
        own_dashboard = self.client.get("/api/account/dashboard").json()
        other_client = TestClient(app)
        other_client.post(
            "/api/auth/register",
            json={
                "full_name": "Other Candidate",
                "email": "other@example.com",
                "password": "other-password",
            },
        )
        other_dashboard = other_client.get("/api/account/dashboard").json()

        self.assertEqual(own_dashboard["resume"]["filename"], "resume.pdf")
        self.assertEqual(own_dashboard["resume"]["resume_text"], "Python project experience")
        self.assertIsNone(other_dashboard["resume"])
        self.assertEqual(other_dashboard["practice_history_count"], 0)

    def test_passwords_are_bcrypt_hashed_and_practice_data_is_account_scoped(self):
        row = self.client.get("/api/account/dashboard").json()
        with closing(connect_database()) as connection:
            stored = connection.execute(
                "SELECT password_hash, password_scheme FROM users WHERE id = ?",
                (self.user["id"],),
            ).fetchone()
        self.assertEqual(stored["password_scheme"], "bcrypt")
        self.assertTrue(stored["password_hash"].startswith("$2"))
        self.assertNotIn(self.password, stored["password_hash"])
        self.assertEqual(row["practice_history"], [])

    @patch("api.main.analyze_resume", return_value="## Candidate Profile\nPython developer")
    def test_resume_pdf_is_extracted_and_analyzed(self, analyze_resume):
        response = self.client.post(
            "/api/resume/analyze",
            files={"file": ("resume.pdf", self.make_pdf("Python developer"), "application/pdf")},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Python developer", response.json()["resume_text"])
        analyze_resume.assert_called_once_with(response.json()["resume_text"])

    def test_resume_rejects_non_pdf_and_empty_text(self):
        invalid_file = self.client.post(
            "/api/resume/analyze",
            files={"file": ("resume.pdf", b"not a PDF", "application/pdf")},
        )
        empty_pdf = self.client.post(
            "/api/resume/analyze",
            files={"file": ("resume.pdf", self.make_pdf(), "application/pdf")},
        )

        self.assertEqual(invalid_file.status_code, 415)
        self.assertEqual(empty_pdf.status_code, 422)

    @patch("api.main.generate_interview_report")
    @patch("api.main.evaluate_answer")
    @patch("api.main.generate_interview_questions")
    def test_interview_lifecycle(self, generate_questions, evaluate, generate_report):
        generate_questions.return_value = "Question 1. Explain a project decision you made."
        evaluate.return_value = {
            "overall_score": 8,
            "technical_correctness": 8,
            "relevance": 8,
            "completeness": 8,
            "clarity": 8,
            "verdict": "Strong",
            "strengths": ["Clear example"],
            "improvements": ["Add an outcome"],
            "missing_points": [],
            "ideal_answer": "",
        }
        generate_report.return_value = {"overall_score": 8}

        created = self.client.post(
            "/api/interviews",
            json={
                "resume_text": "Python project experience",
                "job_description": "Python developer role",
                "number_of_questions": 1,
            },
        )
        self.assertEqual(created.status_code, 200)
        interview_id = created.json()["id"]

        answer = self.client.post(
            f"/api/interviews/{interview_id}/answer",
            json={"answer": "I made a measured design choice."},
        )
        self.assertEqual(answer.status_code, 200)

        completed = self.client.post(f"/api/interviews/{interview_id}/next")
        self.assertEqual(completed.status_code, 200)
        self.assertEqual(completed.json()["status"], "complete")

        report = self.client.get(f"/api/interviews/{interview_id}/report")
        self.assertEqual(report.status_code, 200)
        self.assertEqual(report.json()["report"]["overall_score"], 8)
        generate_report.assert_called_once()
        dashboard = self.client.get("/api/account/dashboard").json()
        other_client = TestClient(app)
        other_client.post(
            "/api/auth/register",
            json={
                "full_name": "Other Candidate",
                "email": "other@example.com",
                "password": "other-password",
            },
        )
        other_dashboard = other_client.get("/api/account/dashboard").json()
        self.assertEqual(dashboard["practice_history_count"], 1)
        self.assertEqual(dashboard["practice_history"][0]["answer"], "I made a measured design choice.")
        self.assertEqual(other_dashboard["practice_history"], [])
        self.assertEqual(len(dashboard["latest_report"]["evaluations"]), 1)

    @patch("api.main.generate_interview_report", return_value={"overall_score": 7})
    @patch("api.main.evaluate_answer")
    @patch("api.main.generate_interview_questions")
    def test_early_completion_reports_only_submitted_answers(
        self,
        generate_questions,
        evaluate,
        generate_report,
    ):
        generate_questions.return_value = (
            "Question 1. Explain a project decision you made.\n"
            "Question 2. Describe a technical challenge you solved."
        )
        evaluate.return_value = {
            "overall_score": 7,
            "technical_correctness": 7,
            "relevance": 7,
            "completeness": 7,
            "clarity": 7,
            "verdict": "Good",
            "strengths": [],
            "improvements": [],
            "missing_points": [],
            "ideal_answer": "",
        }
        created = self.client.post(
            "/api/interviews",
            json={
                "resume_text": "Python project experience",
                "job_description": "Python developer role",
                "number_of_questions": 2,
            },
        )
        interview_id = created.json()["id"]
        self.client.post(
            f"/api/interviews/{interview_id}/answer",
            json={"answer": "I made a design decision."},
        )

        completed = self.client.post(f"/api/interviews/{interview_id}/complete")
        report = self.client.get(f"/api/interviews/{interview_id}/report")

        self.assertEqual(completed.status_code, 200)
        self.assertEqual(completed.json()["status"], "complete")
        self.assertEqual(len(report.json()["answers"]), 1)
        self.assertEqual(len(report.json()["questions"]), 2)
        self.assertEqual(generate_report.call_args.args[3], ["I made a design decision."])

    @patch("api.main.evaluate_answer")
    @patch("api.main.generate_interview_questions")
    def test_skip_advances_without_evaluating_empty_answer(self, generate_questions, evaluate):
        generate_questions.return_value = (
            "Question 1. Explain a project decision you made.\n"
            "Question 2. Describe a technical challenge you solved."
        )
        created = self.client.post(
            "/api/interviews",
            json={
                "resume_text": "Python project experience",
                "job_description": "Python developer role",
                "number_of_questions": 2,
            },
        )
        interview_id = created.json()["id"]

        skipped = self.client.post(f"/api/interviews/{interview_id}/skip")
        current = self.client.get(f"/api/interviews/{interview_id}")

        self.assertEqual(skipped.status_code, 200)
        self.assertEqual(skipped.json()["current_question_index"], 1)
        self.assertEqual(current.json()["answered_questions"], 0)
        self.assertEqual(current.json()["skipped_questions"], [0])
        evaluate.assert_not_called()


if __name__ == "__main__":
    unittest.main()