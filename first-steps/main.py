"""
To run the app we have two commands:
1. Using fastapi:
    - fastapi dev main.py || This is for development run mode
    - fastapi run main.py || This is for production run mode
2. Using uvicorn:
    - uvicorn main:app --reload || Also we can change the run port using "--port 4242"
"""

import os
from datetime import datetime
from fastapi import FastAPI, Query, Body, HTTPException, Path, status, Depends
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List, Union, Literal
from math import ceil
from sqlalchemy import create_engine, Integer, String, Text, DateTime, select, func
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blog.db")
print("Conectado a: ", DATABASE_URL)

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=True, future=True, **engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False, class_=Session)


class Base(DeclarativeBase):
    pass


class PostORM(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[String] = mapped_column(
        String(100), nullable=False, index=True)
    content: Mapped[String] = mapped_column(Text, nullable=False)
    create_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)  # dev


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(title="Mini Blog")

BLOG_POST = [
    {"id": 1, "title": "Hola desde FastAPI", "content": "Mi primer post"},
    {"id": 2, "title": "Mi segundo post con FastAPI",
        "content": "Mi segundo post usando FastAPI"},
    {"id": 3, "title": "DJango vs FastAPI", "content": "FastAPI es más rápido"},
]


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


class PostBase(BaseModel):
    title: str
    content: str
    tags: Optional[List[Tag]] = Field(default_factory=list)
    authors: Optional[List[Author]] = None


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
    authors: list[Author] = None

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
), include_content: bool = Query(default=True, description="Mostrar contenido")):
    for post in BLOG_POST:
        if post["id"] == post_id:
            if not include_content:
                # It returns a dictionary with PostSummary type in case that include_content equals False
                return {"id": post["id"], "title": post["title"]}

            return post  # It returns a dictionary with Post PostPublic type

    return HTTPException(status_code=404, detail="Post no encontrado")


@app.get("/get/by-tags", response_model=list[PostPublic])
def filter_by_tags(
    tags: list[str] = Query(
        min_length=2,
        description="Una o más etiquetas. Ejemplo: ?tags=python&tags=fastapi",
    )
):
    tags_lower = [tag.lower() for tag in tags]

    return [
        post for post in BLOG_POST
        if any(tag["name"].lower() in tags_lower
               for tag in post.get("tags", []))
    ]


@app.post(
    "/posts",
    response_model=PostPublic,
    response_description="Nuevo post creado",
    status_code=status.HTTP_201_CREATED
)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    new_post = PostORM(title=post.title, content=post.content)

    try:
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        return new_post
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al crear el post")


@app.put("/posts/{post_id}",
         response_model=PostPublic,
         response_description="Post actualizado",
         response_model_exclude_none=True
         )
def update_post(post_id: int, data: PostUpdate):
    for post in BLOG_POST:
        if post["id"] == post_id:
            playload = data.model_dump(exclude_unset=True)
            if "title" in playload:
                post["title"] = playload["title"]
            if "content" in playload:
                post["content"] = playload["content"]
            return post
            # return {"message": "Se ha actualizado el post", "data": post}

    raise HTTPException(status_code=404, detail="Post no encontrado")


# If don't want to return any value, use "status_code=204"
@app.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int):
    for index, post in enumerate(BLOG_POST):
        if post["id"] == post_id:
            BLOG_POST.pop(index)
            return

    raise HTTPException(status_code=404, detail="Post no encontrado")
