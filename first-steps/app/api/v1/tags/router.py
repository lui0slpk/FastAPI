from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.tags.repository import TagRepository
from app.api.v1.tags.schemas import TagCreate, TagPublic, TagUpdate
from app.core.db import get_db
from app.core.security import get_current_user

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=dict, status_code=status.HTTP_200_OK, description="Tag list pagination")
def list_tags(
    page: int = Query(
        default=1, ge=1,
        description="Número de página (>=1)"
    ),
    per_page: int = Query(
        default=10, ge=1, le=50,
        description="Numero de resultados (1-50)"
    ),
    order_by: Literal["id", "name"] = Query(
        default="id", pattern="^(id|name)$",
        description="Campo de orden"
    ),
    direction: Literal["asc", "desc"] = Query(
        default="asc", pattern="^(asc|desc)$",
        description="Dirección de orden (Asc/Desc)"
    ),
    search: str | None = Query(
        default=None,
        description="Texto para buscar por título",
        alias="search",
        max_length=30,
        pattern=r"^[\w\sáéíóúÁÉÍÓÚüÜ-]+$"
    ),
    db: Session = Depends(get_db)
):
    repository = TagRepository(db)

    return repository.list_tags(
        search=search, order_by=order_by,
        direction=direction,
        page=page, per_page=per_page
    )


@router.post("", response_model=TagPublic, response_description="Tag creada (OK)", status_code=status.HTTP_201_CREATED, description="Create a new tag")
def create_tag(tag: TagCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    repository = TagRepository(db)

    try:
        tag_created = repository.create_tag(name=tag.name)

        db.commit()
        db.refresh(tag_created)

        return tag_created
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Ese tag ya existe")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al crear el tag")


@router.put("", response_model=TagPublic, response_description="Tag actualizada correctamente", status_code=status.HTTP_200_OK, description="Update an existing tag")
def update_tag(tag_id: int, payload: TagUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    repository = TagRepository(db)
    tag = repository.get(tag_id)

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag no encontrada")

    try:
        name = payload.name
        repository.update_tag(tag, name)

        db.commit()
        return TagPublic.model_validate(tag)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Ese tag ya existe")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al actualizar el tag")


@router.delete("/{tag_id}", response_description="Tag eliminada correctamente", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    repository = TagRepository(db)
    tag = repository.get(tag_id)

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag no encontrada")

    try:
        repository.delete_tag(tag)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al eliminar el tag")


@router.get("/popular")
def get_most_popular(db: Session = Depends(get_db), user=Depends(get_current_user)):
    repository = TagRepository(db)
    row = repository.most_popular()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No hay tags en uso")

    try:
        return row
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al encontrar el tag")
