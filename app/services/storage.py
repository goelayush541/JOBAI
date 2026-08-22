import uuid
import os
import shutil
from pathlib import Path
from fastapi import UploadFile
from app.config import get_settings

settings = get_settings()

LOCAL_STORAGE_DIR = Path("local_uploads/resumes")
LOCAL_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class StorageService:
    async def upload_resume(self, user_id: uuid.UUID, file: UploadFile) -> str:
        if settings.GCP_PROJECT_ID:
            from google.cloud import storage
            client = storage.Client(project=settings.GCP_PROJECT_ID)
            bucket = client.bucket(settings.GCS_BUCKET_NAME)
            blob_name = f"resumes/{user_id}/{uuid.uuid4()}_{file.filename}"
            blob = bucket.blob(blob_name)
            content = await file.read()
            blob.upload_from_string(content, content_type=file.content_type)
            return f"gs://{settings.GCS_BUCKET_NAME}/{blob_name}"

        user_dir = LOCAL_STORAGE_DIR / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        file_path = user_dir / f"{uuid.uuid4()}_{file.filename}"
        content = await file.read()
        file_path.write_bytes(content)
        return f"local://{file_path}"

    def delete_resume(self, file_url: str) -> None:
        if settings.GCP_PROJECT_ID:
            from google.cloud import storage
            client = storage.Client(project=settings.GCP_PROJECT_ID)
            bucket = client.bucket(settings.GCS_BUCKET_NAME)
            blob_name = file_url.replace(f"gs://{settings.GCS_BUCKET_NAME}/", "")
            bucket.blob(blob_name).delete()
            return

        if file_url.startswith("local://"):
            path = Path(file_url.replace("local://", ""))
            if path.exists():
                path.unlink()


storage_service = StorageService()
