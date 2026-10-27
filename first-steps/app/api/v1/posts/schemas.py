from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List, Literal, Annotated
from fastapi import Form

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
    image_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PostCreate(BaseModel):
    title: str = Field(  # Automatic validations
        ...,
        min_length=3,
        max_length=100,
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

    @classmethod
    def as_form(
        cls,
        title: Annotated[str, Form(min_length=3)],
        content: Annotated[str, Form(min_length=10)],
        tags: Annotated[list | None, Form()] = None
    ):
        tag_objs = [Tag(name=tag) for tag in (tags or [])]
        return cls(title=title, content=content, tags=tag_objs)


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
