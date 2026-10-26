import os
import shutil
import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException, status

router = APIRouter(prefix="/upload", tags=["uploads"])

MEDIA_DIR = "app/media"


@router.post("/bytes")
async def upload_bytes(file: bytes = File(...)):
    return {
        "filename": "archivo_subido",
        "size_bytes": len(file)
    }


@router.post("/file")
async def upload_file(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "content_type": file.content_type
    }


@router.post("/save")
async def save_file(file: UploadFile = File(...)):
    if file.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten imágenes PNG o JPEG"
        )

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
