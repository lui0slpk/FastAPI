"""
To run the app we have two commands:
1. Using fastapi:
    - fastapi dev main.py || This is for development run mode
    - fastapi run main.py || This is for production run mode
2. Using uvicorn:
    - uvicorn main:app --reload || Also we can change the run port using "--port 4242"
"""

from fastapi import FastAPI, Query, Body, HTTPException, Path
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Union

app = FastAPI(title="Mini Blog")

BLOG_POST = [
    {"id": 1, "title": "Hola desde FastAPI", "content": "Mi primer post"},
    {"id": 2, "title": "Mi segundo post con FastAPI", "content": "Mi segundo post usando FastAPI"},
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
    name: str = Field(..., min_length=2, max_length=30, description="Nombre de la etiqueta")

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
    title: str = Field( # Automatic validations
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
        examples=["Este es un contenido válido del post porque tiene más de 1 caracter"]
    )
    tags: List[Tag] = Field(default_factory=list)
    authors: list[Author] = None # En el nuevo python, usar list en lugar de List para tipar los datos, es más usado, además no hace falta importar librerias como Typing
    
    @field_validator("title") # Custom validations | "title" is the data that we want to validate
    @classmethod # This will allow to each class to inherit this validation
    def not_words_allowed(cls, value: str) -> str: # This will recieve cls instead of self
        for word in not_allowed_words:
            if word in value.lower():
                raise ValueError(f"El título no puede contener la palabra '{word}'")
        return value

class PostUpdate(BaseModel):
    title: str | None = Field(
            default=None,
            min_length=3,
            max_length=30
        )
    content: Optional[str] = None

class PostPublic(PostBase): # This will be our response model, it's like a map of what we want to return
    id: int

class PostSummary(BaseModel): # This will be our response model
    id: int
    title: str

@app.get("/")
def home():
    return {'message': 'Bienvenidos a Mini Blog por Luis'}

# -------------- QUERY PARAMETER ---------------
@app.get("/posts", response_model= List[PostPublic]) # Our endpoint will return a PostPublic list with all its attributes
def list_posts(query: str | None = Query(default=None, description="Texto para buscar por título")):
    if query:        
        return [post for post in BLOG_POST if query.lower() in post["title"].lower()] # This will return list, so it's estructure it's the same of PostPublic

    return BLOG_POST # Here, we will return a list, as our response model is a PostPublic list

# ------------- PATH PARAMETER --------------
@app.get("/posts/{post_id}", response_model= Union[PostPublic, PostSummary], response_description= "Post encontrado") # Union will let FastAPI validate the two of the response modelss
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
                return {"id": post["id"], "title": post["title"]} # It returns a dictionary with PostSummary type in case that include_content equals False
            
            return post # It returns a dictionary with Post PostPublic type
    
    return HTTPException(status_code=404, detail="Post no encontrado")

@app.post("/posts", response_model=PostPublic, response_description= "Nuevo post creado")
def create_post(post: PostCreate):
    new_id = (BLOG_POST[-1]["id"]+1) if BLOG_POST else 1
    new_post = {"id": new_id,
                "authors": [author.model_dump() for author in post.authors] if post.authors else None,
                "title": post.title,
                "content": post.content,
                "tags": [tag.model_dump() for tag in post.tags] # Here, post is an instance of PostCreate, which has tags attribute, so tag will be an instance of post
                }
    # Remember that x.model_dump() will return an object/dict of the model
    BLOG_POST.append(new_post)
    
    return new_post
    # return {"message": "Un nuevo post se ha creado", "data": new_post}


@app.put("/posts/{post_id}", response_model=PostPublic, response_description= "Post actualizado", response_model_exclude_none=True)
def update_post(post_id: int, data: PostUpdate):
    for post in BLOG_POST:
        if post["id"] == post_id:
            playload = data.model_dump(exclude_unset=True)
            if "title" in playload: post["title"] = playload["title"]
            if "content" in playload: post["content"] = playload["content"]
            return post
            # return {"message": "Se ha actualizado el post", "data": post}

    raise HTTPException(status_code=404, detail="Post no encontrado")


@app.delete("/posts/{post_id}", status_code=204) # If don't want to return any value, use "status_code=204"
def delete_post(post_id: int):
    for index, post in enumerate(BLOG_POST):
        if post["id"] == post_id:
            BLOG_POST.pop(index)
            return
    
    raise HTTPException(status_code=404, detail="Post no encontrado")