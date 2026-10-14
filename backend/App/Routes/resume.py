import shutil
import uuid
import base64
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from ..database import save_resume
from ..services.docx_parser import extract_docx_text
from ..services.pdf_parser import extract_pdf_text
from ..services.resume_analyzer import analyze_resume
from ..services.job_matcher import (
    JOBS,
    MATCH_THRESHOLD,
    build_sample_resume,
    build_sample_resume_docx,
    build_tailored_resume_docx,
    get_job_description,
    match_jobs,
    review_resume_format,
)
from ..schemas import SampleResumeRequest

router = APIRouter(prefix="/api/resume", tags=["Resume"])

import os

def _resolve_upload_folder() -> Path:
    env_dir = os.getenv("UPLOAD_DIR")
    if env_dir:
        folder = Path(env_dir)
    elif os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        folder = Path("/tmp/uploads")
    else:
        folder = Path("uploads")
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError:
        folder = Path("/tmp/uploads")
        folder.mkdir(parents=True, exist_ok=True)
    return folder


UPLOAD_FOLDER = _resolve_upload_folder()


def _save_uploaded_file(file: UploadFile, subfolder: Path | None = None):
    if subfolder is None:
        subfolder = _resolve_upload_folder()
    subfolder.mkdir(parents=True, exist_ok=True)

    filename = file.filename or "upload"
    extension = Path(filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{extension}"
    file_path = subfolder / unique_name

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file_path, unique_name


@router.post("/sample-template")
async def download_sample_resume_template(data: SampleResumeRequest):
    job = next((job for job in JOBS if job["title"] == data.role_title), None)
    if job is None:
        raise HTTPException(status_code=400, detail="Unknown recommended job role.")

    document = build_sample_resume_docx(job, data.resume_skills)
    return StreamingResponse(
        document,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="sample-resume-template.docx"'},
    )


@router.post("/upload-photo")
async def upload_photo(photo: UploadFile = File(...)):
    extension = Path(photo.filename or "").suffix.lower()
    allowed_types = [".png", ".jpg", ".jpeg", ".webp"]

    if extension not in allowed_types:
        raise HTTPException(status_code=400, detail="Only image files are allowed for photo upload.")

    _, saved_filename = _save_uploaded_file(photo)
    return {
        "message": "Photo uploaded successfully.",
        "photo_filename": saved_filename,
    }


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    photo: UploadFile | None = File(default=None),
    job_description: str = Form(default=""),
    expected_role: str = Form(default="Python Developer"),
    user_id: int = Form(1),
):
    extension = Path(file.filename or "").suffix.lower()

    if extension not in [".pdf", ".docx"]:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed.")

    file_path, _ = _save_uploaded_file(file)

    photo_filename = None
    if photo is not None and photo.filename:
        photo_extension = Path(photo.filename).suffix.lower()
        if photo_extension not in [".png", ".jpg", ".jpeg", ".webp"]:
            raise HTTPException(status_code=400, detail="Only PNG, JPG, JPEG, and WEBP photos are allowed.")
        _, photo_filename = _save_uploaded_file(photo)

    try:
        if extension == ".pdf":
            resume_text = extract_pdf_text(str(file_path))
        else:
            resume_text = extract_docx_text(str(file_path))
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from resume.")

    expected_job = get_job_description(expected_role)
    if expected_job is None:
        raise HTTPException(status_code=400, detail="Select a supported expected job role.")
    if not job_description.strip():
        job_description = expected_job["description"]

    result = analyze_resume(resume_text, job_description)
    save_resume(user_id, file.filename, resume_text, result["overall_score"])
    matching_jobs = match_jobs(result["resume_skills"])
    expected_score = result["skill_score"]
    recommended_job = expected_job
    recommendation_reason = "Your resume meets the skill-match threshold for the selected role."
    if expected_score < MATCH_THRESHOLD:
        alternative = next(
            (
                job
                for job in matching_jobs
                if job["title"] != expected_role and job["match_score"] > 0
            ),
            None,
        )
        if alternative is not None:
            recommended_job = alternative
            recommendation_reason = (
                f"Your resume matched {expected_score}% of the selected role's listed skills. "
                f"The best available alternative is {alternative['title']} "
                f"({alternative['match_score']}% resume-skill match)."
            )
        else:
            recommendation_reason = (
                f"Your resume matched {expected_score}% of the selected role's listed skills. "
                "No stronger match was found in the current role catalog."
            )

    sample_resume = (
        build_sample_resume(recommended_job, result["resume_skills"])
        if recommended_job
        else None
    )
    format_review = review_resume_format(resume_text)
    tailored_resume_docx = build_tailored_resume_docx(
        recommended_job,
        resume_text,
        result["resume_skills"],
    )

    return {
        "filename": file.filename,
        "photo_filename": photo_filename,
        "matching_jobs": matching_jobs,
        "expected_role": expected_role,
        "expected_role_score": expected_score,
        "expected_role_match_threshold": MATCH_THRESHOLD,
        "recommended_job": recommended_job,
        "recommendation_reason": recommendation_reason,
        "sample_resume": sample_resume,
        "resume_preview": f"TARGET ROLE: {recommended_job['title']}\n\n{resume_text}",
        "format_review": format_review,
        "tailored_resume_docx_base64": base64.b64encode(
            tailored_resume_docx.getvalue()
        ).decode("ascii"),
        **result,
    }