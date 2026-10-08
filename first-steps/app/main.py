"""
To run the app we have two commands:
1. Using fastapi:
    - fastapi dev main.py || This is for development run mode
    - fastapi run main.py || This is for production run mode
2. Using uvicorn:
    - uvicorn main:app --reload || Also we can change the run port using "--port 4242"
"""

from datetime import datetime
from fastapi import FastAPI, Query, Body, HTTPException, Path, status, Depends
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List, Union, Literal
from math import ceil
from sqlalchemy import Integer, String, Text, DateTime, select, func, UniqueConstraint, ForeignKey, Table, Column
from sqlalchemy.orm import Session, Mapped, mapped_column, relationship, selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from dotenv import load_dotenv

load_dotenv()


post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey(
        "posts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
)


class AuthorORM(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    posts: Mapped[List["PostORM"]] = relationship(back_populates="author")


class TagsORM(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(30), unique=True, index=True)

    posts: Mapped[List["PostORM"]] = relationship(
        secondary=post_tags,
        back_populates="tags",
        lazy="selectin",
        passive_deletes=True
    )


class PostORM(Base):
    __tablename__ = "posts"
    __table_args__ = (UniqueConstraint("title", name="unique_post_table"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[String] = mapped_column(
        String(100), nullable=False, index=True)
    content: Mapped[String] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)

    author_id: Mapped[int | None] = mapped_column(ForeignKey("authors.id"))
    author: Mapped[AuthorORM | None] = relationship(back_populates="posts")

    tags: Mapped[List["TagsORM"]] = relationship(
        secondary=post_tags,
        back_populates="posts",
        lazy="selectin",
        passive_deletes=True
    )


Base.metadata.create_all(bind=engine)  # dev


app = FastAPI(title="Mini Blog")


not_allowed_words = (
    "idiota",
    "estúpido",
    "imbécil",
    "pendejo",
    "cabron",
    "mierda",
    "puta",
    "puto",
    "coño",
    "joder"
)


class Tag(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=30,
        description="Nombre de la etiqueta"
    )

    model_config = ConfigDict(from_attributes=True)


class Author(BaseModel):
    name: str = Field(
        ...,
        min_length=3,
        max_length=20,
        description="Nombre del autor del post",
        examples=["John Doe"]
    )
    email: EmailStr = Field(
        ...,
        description="Correo electrónico del usuario",
        examples=["johndoe@example.com"]
    )

    model_config = ConfigDict(from_attributes=True)


class PostBase(BaseModel):
    title: str
    content: str
    tags: Optional[List[Tag]] = Field(default_factory=list)
    author: Optional[Author] = None

    model_config = ConfigDict(from_attributes=True)


class PostCreate(PostBase):
    title: str = Field(  # Automatic validations
        ...,
        min_length=3,
        max_length=30,
        description="Titulo del post (Mínimo 3 carateres, máximo 30)",
        examples=["Mi primer post con FastAPI"]
    )
    content: Optional[str] = Field(
        default="Contenido no disponible",
        min_length=1,
        max_length=500,
        description="Contenido del post (mínimo 1 caracter máx 500)",
        examples=[
            "Este es un contenido válido del post porque tiene más de 1 caracter"]
    )
    tags: List[Tag] = Field(default_factory=list)
    # En el nuevo python, usar list en lugar de List para tipar los datos, es más usado, además no hace falta importar librerias como Typing
    author: Author = None

    # Custom validations | "title" is the data that we want to validate
    @field_validator("title")
    @classmethod  # This will allow to each class to inherit this validation
    # This will recieve cls instead of self
    def not_words_allowed(cls, value: str) -> str:
        for word in not_allowed_words:
            if word in value.lower():
                raise ValueError(
                    f"El título no puede contener la palabra '{word}'")
        return value


class PostUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=30
    )
    content: Optional[str] = None


# This will be our response model, it's like a map of what we want to return
class PostPublic(PostBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class PostSummary(BaseModel):  # This will be our response model
    id: int
    title: str

    model_config = ConfigDict(from_attributes=True)


class PaginatedPost(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int
    has_prev: bool
    has_next: bool
    order_by: Literal["id", "title"]
    direction: Literal["asc", "desc"]
    search: str | None = Field(default=None)
    items: list[PostPublic]


@app.get("/")
def home():
    return {'message': 'Bienvenidos a Mini Blog por Luis'}

# -------------- QUERY PARAMETER ---------------


@app.get("/posts", response_model=PaginatedPost)
def list_posts(
    text: str | None = Query(
        default=None,
        deprecated=True,
        description="Parámetro obsoleto, usa 'query o search' en su lugar"
    ),
    query: str | None = Query(
        default=None,
        description="Texto para buscar por título",
        alias="search",
        max_length=30,
        pattern=r"^[\w\sáéíóúÁÉÍÓÚüÜ-]+$"
    ),
    per_page: int = Query(
        default=10, ge=1, le=50,
        description="Numero de resultados (1-50)"
    ),
    page: int = Query(
        default=1, ge=1,
        description="Número de página (>=1)"
    ),
    order_by: Literal["id", "title"] = Query(
        default="id", description="Campo de orden"
    ),
    direction: Literal["asc", "desc"] = Query(
        default="asc", description="Dirección de orden (Asc/Desc)"
    ),
    db: Session = Depends(get_db)
):

    results = select(PostORM)

    query = query or text

    if query:
        results = results.where(PostORM.title.ilike(f"%{query}%"))

    total = db.scalar(select(func.count()).select_from(
        results.subquery())) or 0
    total_pages = ceil(total / per_page) if total > 0 else 0

    current_page = 1 if total_pages == 0 else min(page, total_pages)

    if order_by == "id":
        order_col = PostORM.id
    else:
        order_col = func.lower(PostORM.title)

    results = results.order_by(
        order_col.asc() if direction == "asc" else order_col.desc()
    )

    # results = sorted(
    #     results, key=lambda post: post[order_by], reverse=(direction == "desc"))

    if total_pages == 0:
        items: List[PostORM] = []
    else:
        start = (current_page - 1) * per_page
        items = db.execute(results.limit(
            per_page).offset(start)).scalars().all()

    has_prev = current_page > 1
    has_next = current_page < total_pages if total_pages > 0 else False

    return PaginatedPost(
        page=current_page, per_page=per_page,
        total=total, total_pages=total_pages,
        has_prev=has_prev, has_next=has_next,
        order_by=order_by, direction=direction,
        search=query, items=items
    )

# ------------- PATH PARAMETER --------------


@app.get(
    "/posts/{post_id}",
    # Union will let FastAPI validate the two of the response models
    response_model=Union[PostPublic, PostSummary],
    response_description="Post encontrado"
)
def get_post(post_id: int = Path(
    ...,
    ge=1,
    title="ID del post",
    description="Identificador entero del post. Debe ser mayor a 1",
    example=1
), include_content: bool = Query(default=True, description="Mostrar contenido"), db: Session = Depends(get_db)):

    post = db.get(PostORM, post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    if include_content:
        return PostPublic.model_validate(post, from_attributes=True)

    return PostSummary.model_validate(post, from_attributes=True)


@app.get("/get/by-tags", response_model=list[PostPublic])
def filter_by_tags(
    tags: list[str] = Query(
        min_length=1,
        description="Una o más etiquetas. Ejemplo: ?tags=python&tags=fastapi",
    ),
    db: Session = Depends(get_db)
):
    normalized_tag_names = [tag.strip().lower() for tag in tags if tag.strip()]

    if not normalized_tag_names:
        return []

    post_list = (
        select(PostORM)
        .options(
            selectinload(PostORM.tags),
            joinedload(PostORM.author),
        )
        .where(PostORM.tags.any(func.lower(TagsORM.name).in_(normalized_tag_names)))
        .order_by(PostORM.id.asc())
    )

    posts = db.execute(post_list).scalars().all()

    return posts


@app.post(
    "/posts",
    response_model=PostPublic,
    response_description="Nuevo post creado",
    status_code=status.HTTP_201_CREATED
)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    author_obj = None

    if post.author:
        author_obj = db.execute(
            select(AuthorORM).where(AuthorORM.email == post.author.email)
        ).scalar_one_or_none()

        if not author_obj:
            author_obj = AuthorORM(
                name=post.author.name,
                email=post.author.email
            )
            db.add(author_obj)
            db.flush()

    new_post = PostORM(
        title=post.title, content=post.content, author=author_obj)

    for tag in post.tags:
        tag_obj = db.execute(
            select(TagsORM).where(TagsORM.name.ilike(tag.name))
        ).scalar_one_or_none()

        if not tag_obj:
            tag_obj = TagsORM(name=tag.name)
            db.add(tag_obj)
            db.flush()

        new_post.tags.append(tag_obj)

    try:
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        return new_post
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="El título ya existe, prueba con otro")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al crear el post")


@app.put("/posts/{post_id}",
         response_model=PostPublic,
         response_description="Post actualizado",
         response_model_exclude_none=True
         )
def update_post(post_id: int, data: PostUpdate, db: Session = Depends(get_db)):
    post = db.get(PostORM, post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    updated_data = data.model_dump(exclude_unset=True)
    for key, value in updated_data.items():
        setattr(post, key, value)

    db.commit()
    db.refresh(post)

    return post


# If don't want to return any value, use "status_code=204"
@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT, response_description="Post eliminado")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.get(PostORM, post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    db.delete(post)
    db.commit()

    return
