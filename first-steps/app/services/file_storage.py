import os
import shutil
import uuid
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings


MEDIA_DIR = "app/media"
ALLOW_EXT = ["image/png", "image/jpeg"]
MAX_MB = settings.MAX_UPLOAD_MB


def ensure_media_dir() -> None:
    os.makedirs(MEDIA_DIR, exist_ok=True)


async def save_uploaded_file(file: UploadFile) -> dict:
    if file.content_type not in ALLOW_EXT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten imágenes PNG o JPEG"
        )

    ensure_media_dir()
    ext = os.path.splitext(file.filename)[-1]
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(MEDIA_DIR, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer, length=1024 * 1024)

    size = os.path.getsize(filepath)
    if size > MAX_MB * 1024 * 1024:
        os.remove(filepath)
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"El archivo es demasiado grande (>{MAX_MB} MB)"
        )

    return {
        "filename": filename,
        "content_type": file.content_type,
        "url": f"/media/{filename}"
    }
