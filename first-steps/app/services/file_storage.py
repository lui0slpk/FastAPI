import os
import shutil
import uuid
from fastapi import UploadFile, HTTPException, status


MEDIA_DIR = "app/media"
ALLOW_EXT = ["image/png", "image/jpeg"]


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
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": filename,
        "content_type": file.content_type,
        "url": f"/media/{filename}"
    }
