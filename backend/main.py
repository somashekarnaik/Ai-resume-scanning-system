"""Backend entry point for AI Resume Scanning System.

Exposes the full FastAPI application from App.main, including authentication,
resume parsing and analysis, job matching, and career coaching routes.
"""

from App.main import app

__all__ = ["app"]