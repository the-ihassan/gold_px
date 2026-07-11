"""
Storage abstraction.

Today: STORAGE_BACKEND=local -> files saved under ./uploads and served
statically by FastAPI (see main.py StaticFiles mount).

Later: set STORAGE_BACKEND=cloudinary or =s3 and fill in the credentials
in .env. Only `upload_file()` in this module needs to change - no
endpoint code depends on which backend is active.
"""
import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException

from app.core.config import settings

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf", ".mp4", ".mov", ".doc", ".docx"}


def _validate_file(file: UploadFile) -> str:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' is not allowed")
    return ext


def upload_file(file: UploadFile, subfolder: str = "bookings") -> dict:
    """Returns {"url": str, "file_name": str, "file_type": str}"""
    ext = _validate_file(file)

    if settings.STORAGE_BACKEND == "local":
        target_dir = Path(settings.LOCAL_UPLOAD_DIR) / subfolder
        target_dir.mkdir(parents=True, exist_ok=True)

        stored_name = f"{uuid.uuid4().hex}{ext}"
        target_path = target_dir / stored_name

        size = 0
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        with open(target_path, "wb") as f:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    f.close()
                    os.remove(target_path)
                    raise HTTPException(status_code=400, detail="File exceeds max upload size")
                f.write(chunk)

        return {
            "url": f"/static/{subfolder}/{stored_name}",
            "file_name": file.filename,
            "file_type": ext.lstrip("."),
        }

    elif settings.STORAGE_BACKEND == "cloudinary":
        # import cloudinary.uploader
        # result = cloudinary.uploader.upload(file.file, folder=subfolder, resource_type="auto")
        # return {"url": result["secure_url"], "file_name": file.filename, "file_type": ext.lstrip(".")}
        raise HTTPException(status_code=501, detail="Cloudinary backend not configured yet")

    elif settings.STORAGE_BACKEND == "s3":
        # import boto3
        # s3 = boto3.client("s3", aws_access_key_id=..., aws_secret_access_key=...)
        # s3.upload_fileobj(file.file, settings.AWS_S3_BUCKET, key)
        # return {"url": f"https://{settings.AWS_S3_BUCKET}.s3.amazonaws.com/{key}", ...}
        raise HTTPException(status_code=501, detail="S3 backend not configured yet")

    raise HTTPException(status_code=500, detail="No valid STORAGE_BACKEND configured")
