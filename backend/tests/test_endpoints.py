import os
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from App.main import app
from App.database import create_tables


class EndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_db = Path(tempfile.gettempdir()) / "test_resume_scanner.db"
        if test_db.exists():
            try:
                test_db.unlink()
            except OSError:
                pass
        os.environ["DATABASE_PATH"] = str(test_db)
        create_tables()
        cls.client = TestClient(app)


    def test_health_and_root(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"status": "OK"})

        res_api = self.client.get("/api/health")
        self.assertEqual(res_api.status_code, 200)

        res_home = self.client.get("/")
        self.assertEqual(res_home.status_code, 200)
        self.assertIn("text/html", res_home.headers["content-type"])
        self.assertIn("AI Resume Scanning System", res_home.text)

    def test_job_roles_and_matching(self):
        # Test GET /api/jobs/roles
        res_roles = self.client.get("/api/jobs/roles")
        self.assertEqual(res_roles.status_code, 200)
        roles = res_roles.json()
        self.assertTrue(len(roles) > 0)
        self.assertTrue(any(r["title"] == "Python Developer" for r in roles))

        # Test POST /api/jobs/match
        res_match = self.client.post("/api/jobs/match", json={"skills": "Python, SQL, Django, Git"})
        self.assertEqual(res_match.status_code, 200)
        matches = res_match.json()
        self.assertTrue(len(matches) > 0)
        top_match = matches[0]
        self.assertEqual(top_match["title"], "Python Developer")
        self.assertGreater(top_match["match_score"], 50)

    def test_auth_flow(self):
        test_email = f"test_{os.urandom(4).hex()}@example.com"
        # Register
        res_reg = self.client.post("/api/auth/register", json={
            "name": "Jane Tester",
            "email": test_email,
            "password": "securepassword123"
        })
        self.assertEqual(res_reg.status_code, 200)
        user_id = res_reg.json().get("user_id")
        self.assertIsNotNone(user_id)

        # Login
        res_login = self.client.post("/api/auth/login", json={
            "email": test_email,
            "password": "securepassword123"
        })
        self.assertEqual(res_login.status_code, 200)
        data = res_login.json()
        self.assertEqual(data["name"], "Jane Tester")
        self.assertEqual(data["user_id"], user_id)

        # Login with bad password
        res_bad = self.client.post("/api/auth/login", json={
            "email": test_email,
            "password": "wrongpassword"
        })
        self.assertEqual(res_bad.status_code, 401)

    def test_resume_upload_endpoint(self):
        sample_pdf = Path(__file__).resolve().parents[2] / "sample_resume.pdf"
        if not sample_pdf.exists():
            return

        with open(sample_pdf, "rb") as f:
            res = self.client.post(
                "/api/resume/upload",
                files={"file": ("sample_resume.pdf", f, "application/pdf")},
                data={
                    "expected_role": "Python Developer",
                    "user_id": "1",
                },
            )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("overall_score", data)
        self.assertIn("resume_skills", data)
        self.assertIn("matching_jobs", data)
        self.assertIn("tailored_resume_docx_base64", data)


if __name__ == "__main__":
    unittest.main()

