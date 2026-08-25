import uuid
import os
import hashlib
import hmac
import shutil
from pathlib import Path
from fastapi import UploadFile
from app.config import get_settings

settings = get_settings()

LOCAL_STORAGE_DIR = Path("local_uploads/resumes")
LOCAL_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _derive_key(password: str) -> bytes:
    return hashlib.sha256(password.encode()).digest()


def _encrypt(data: bytes, key: bytes) -> bytes:
    key_stream = bytearray()
    for i in range(len(data)):
        key_byte = key[i % len(key)]
        data_byte = data[i]
        key_stream.append(data_byte ^ key_byte)
    signature = hmac.new(key, bytes(key_stream), hashlib.sha256).digest()[:16]
    return signature + bytes(key_stream)


def _decrypt(data: bytes, key: bytes) -> bytes:
    signature = data[:16]
    encrypted = data[16:]
    expected = hmac.new(key, encrypted, hashlib.sha256).digest()[:16]
    if not hmac.compare_digest(signature, expected):
        raise ValueError("Data integrity check failed - file may be corrupted")
    key_stream = bytearray()
    for i in range(len(encrypted)):
        key_byte = key[i % len(key)]
        enc_byte = encrypted[i]
        key_stream.append(enc_byte ^ key_byte)
    return bytes(key_stream)


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

        if settings.ENCRYPTION_ENABLED:
            key = _derive_key(settings.ENCRYPTION_KEY)
            content = _encrypt(content, key)
            file_path.write_bytes(content)
            meta_path = file_path.with_suffix(file_path.suffix + ".enc")
            meta_path.write_text(f"{file.filename}:{file.content_type}")
        else:
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
            meta_path = path.with_suffix(path.suffix + ".enc")
            if meta_path.exists():
                meta_path.unlink()

    def get_decrypted_path(self, file_url: str) -> Path | None:
        if not file_url.startswith("local://"):
            return None
        path = Path(file_url.replace("local://", ""))
        if not path.exists():
            return None
        if settings.ENCRYPTION_ENABLED:
            key = _derive_key(settings.ENCRYPTION_KEY)
            encrypted = path.read_bytes()
            decrypted = _decrypt(encrypted, key)
            meta_path = path.with_suffix(path.suffix + ".enc")
            suffix = ""
            if meta_path.exists():
                meta = meta_path.read_text().split(":")
                if len(meta) == 2:
                    orig_name = meta[0]
                    if "." in orig_name:
                        suffix = "." + orig_name.rsplit(".", 1)[-1]
            decrypted_path = path.with_suffix(suffix)
            decrypted_path.write_bytes(decrypted)
            return decrypted_path
        return path


storage_service = StorageService()
