import io
from uuid import UUID

import docx2txt
import pdfplumber
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import ResumeResponse
from app.services.auth import get_current_user
from app.services.storage import storage_service

router = APIRouter(prefix="/resumes", tags=["Resumes"])


async def extract_text(file: UploadFile) -> str:
    content = await file.read()
    await file.seek(0)
    if file.filename.endswith(".pdf"):
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif file.filename.endswith(".docx"):
        return docx2txt.process(io.BytesIO(content))
    elif file.filename.endswith(".txt"):
        return content.decode("utf-8")
    return ""


@router.post("/", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    allowed = {".pdf", ".docx", ".txt"}
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"File type {ext} not supported")

    file_url = await storage_service.upload_resume(current_user.user_id, file)
    await file.seek(0)
    parsed_text = await extract_text(file)

    resume = Resume(
        user_id=current_user.user_id,
        file_url=file_url,
        file_name=file.filename,
        parsed_text=parsed_text,
        is_active=True,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return resume


@router.get("/", response_model=list[ResumeResponse])
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Resume).where(Resume.user_id == current_user.user_id)
    )
    return [ResumeResponse.model_validate(r) for r in result.scalars().all()]


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Resume).where(
            Resume.resume_id == UUID(resume_id),
            Resume.user_id == current_user.user_id,
        )
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    storage_service.delete_resume(resume.file_url)
    await db.delete(resume)
    await db.commit()
