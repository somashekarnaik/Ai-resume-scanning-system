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

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "BACKEND_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(

    CORSMiddleware,

    allow_origins=cors_origins,
    allow_credentials=False,

    allow_methods=["*"],

    allow_headers=["*"]

)


create_tables()


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
def home():

    return {

        "message":
            "AI Resume Scanning System Backend is Running"

    }


@app.get("/health")
def health():

    return {

        "status":
            "OK"

    }