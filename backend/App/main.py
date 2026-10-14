import os

from fastapi import FastAPI

from fastapi.middleware.cors import (
    CORSMiddleware
)

from .database import (
    create_tables
)

from .Routes import (
    auth,
    resume,
    jobs,
    assistant
)


app = FastAPI(

    title="AI Resume Scanning System",

    description=
        "AI powered resume analysis and job matching system",

    version="1.0.0"

)

cors_origins_env = os.getenv("BACKEND_CORS_ORIGINS", "*").strip()
if cors_origins_env == "*" or not cors_origins_env:
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app" if cors_origins != ["*"] else None,
    allow_credentials=True if cors_origins != ["*"] else False,
    allow_methods=["*"],
    allow_headers=["*"],
)


try:
    create_tables()
except Exception as error:
    print(f"Warning: Database initialization returned: {error}")



app.include_router(
    auth.router
)

app.include_router(
    resume.router
)

app.include_router(
    jobs.router
)

app.include_router(
    assistant.router
)


@app.get("/")
@app.get("/api")
def home():
    return {
        "message": "AI Resume Scanning System Backend is Running"
    }


@app.get("/health")
@app.get("/api/health")
def health():
    return {
        "status": "OK"
    }
