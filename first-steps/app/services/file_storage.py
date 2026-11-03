import os
import shutil
import uuid
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings


MEDIA_DIR = "app/media"
ALLOW_EXT = ["image/png", "image/jpeg"]
MAX_MB = settings.MAX_UPLOAD_MB
CHUNKS = 1024 * 1024


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

    # class _ChunkCounter:
    #     def __init__(self, f):
    #         self._f = f
    #         self.calls = 0
    #         self.sizes = []

    #     def read(self, n=-1):
    #         data = self._f.read(n)
    #         if data:
    #             self.calls += 1
    #             self.sizes.append(len(data))
    #         return data

    #     def __getattr__(self, name):  # delega cualquier otro atributo
    #         return getattr(self._f, name)

    # reader = _ChunkCounter(file.file)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer, length=CHUNKS)

    size = os.path.getsize(filepath)
    if size > MAX_MB * CHUNKS:
        os.remove(filepath)
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"El archivo es demasiado grande (>{MAX_MB} MB)"
        )

    return {
        "filename": filename,
        "content_type": file.content_type,
        "url": f"/media/{filename}"
        # "size": size,
        # "chunk_size_used": CHUNKS,
        # "chunk_calls": reader.calls,
        # "chunk_size": reader.sizes[:5]
    }
