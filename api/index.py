"""Vercel Serverless Python entrypoint for AI Resume Scanning System.

Exposes the ASGI FastAPI application for Vercel Python serverless runtime.
Handles path restoration from Vercel rewrites and environment defaults.
"""

import os
import sys
from pathlib import Path

# Add project root and backend folder to sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"

for folder in [str(backend_dir), str(root_dir)]:
    if folder not in sys.path:
        sys.path.insert(0, folder)

# Configure serverless writable paths
if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    os.environ.setdefault("DATABASE_PATH", "/tmp/resume_scanner.db")
    os.environ.setdefault("UPLOAD_DIR", "/tmp/uploads")

from App.main import app  # noqa: E402

# Export handler for Vercel Serverless Functions
handler = app
