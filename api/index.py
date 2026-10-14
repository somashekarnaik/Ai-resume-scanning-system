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

from App.main import app
from fastapi import Request
from fastapi.responses import JSONResponse


@app.middleware("http")
async def vercel_rewrite_middleware(request: Request, call_next):
    # Vercel internal rewrites point to /api/index.py
    # Restore the intended client route path from query param or headers
    orig_path = (
        request.query_params.get("__orig_path")
        or request.headers.get("x-matched-path")
        or request.headers.get("x-now-route-matches")
    )
    if orig_path and request.scope.get("path") in ["/api/index.py", "/api/index"]:
        clean_path = orig_path.split("?")[0]
        request.scope["path"] = clean_path

    response = await call_next(request)
    return response


# Export handler for Vercel Serverless Functions
handler = app
