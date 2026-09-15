# FastAPI Mini Blog Notes

This file summarizes the logic and patterns used in the FastAPI app in `main.py`. It focuses on the application structure, route design, validation, and data handling. Installation and environment setup are intentionally not repeated here because they are already covered in `configuration.md`.

---

## 1. Application setup

A FastAPI app is created with `FastAPI()` and can receive metadata such as the title.

```python
from fastapi import FastAPI, Query, Body, HTTPException, Path
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Union, Literal
from math import ceil

app = FastAPI(title="Mini Blog")
```

### What this means

- `FastAPI()` creates the API application object.
- `title="Mini Blog"` adds a friendly name in the OpenAPI documentation.
- The app can later be used to define routes with decorators like `@app.get()` and `@app.post()`.

---

## 2. In-memory database simulation

This project uses a Python list as a simple temporary data store.

```python
BLOG_POST = [
    {"id": 1, "title": "Hola desde FastAPI", "content": "Mi primer post"},
    {"id": 2, "title": "Mi segundo post con FastAPI", "content": "Mi segundo post usando FastAPI"},
    {"id": 3, "title": "DJango vs FastAPI", "content": "FastAPI es más rápido"},
]
```

### Why this is useful

- It helps us understand how a REST API works without a database.
- It is simple and useful for studying CRUD logic.
- It is a good example of how to manipulate data in memory before connecting to a real database.

---

## 3. Pydantic models and validation

Pydantic is a validation library used to define the structure of request bodies and automatically validate incoming data.

```python
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
    title: str = Field(
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
    authors: list[Author] = None

    @field_validator("title")
    @classmethod
    def not_words_allowed(cls, value: str) -> str:
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

class PostPublic(PostBase):
    id: int

class PostSummary(BaseModel):
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
```

### Key ideas

- `Tag` and `Author` are nested models used inside a post.
- `EmailStr` automatically validates that the email follows a correct email format.
- `tags` contains a list of tags with validation for name length.
- `authors` is a list of authors, and each author includes a valid `email`.
- `PostCreate` inherits from `PostBase` and adds automatic validation with `Field(...)` and custom validation with `@field_validator`.
- `PostPublic` and `PostSummary` define the expected response structure.
- `PaginatedPost` contains the page metadata and the list of returned posts.

### Automatic validations

These are validations applied directly by Pydantic from the field definition.

```python
title: str = Field(
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
```

### What this does

- `min_length=3` ensures the title has at least 3 characters.
- `max_length=30` limits the title length.
- `min_length=1` prevents empty content.
- `max_length=500` caps the content length.
- `EmailStr` validates email addresses automatically.
- `Field(default_factory=list)` creates an independent empty list for each model instance.
- `Field` also improves the generated Swagger docs with descriptions and examples.

### Custom validation example

This project also checks that certain words are not allowed in the title.

```python
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
```

```python
@field_validator("title")
@classmethod
def not_words_allowed(cls, value: str) -> str:
    for word in not_allowed_words:
        if word in value.lower():
            raise ValueError(f"El título no puede contener la palabra '{word}'")
    return value
```

This is a custom business rule: even when the data type is valid, the app rejects content that violates the project rules.

---

## 4. Response models and pagination

FastAPI uses `response_model` to define the shape of the API response.

```python
@app.get("/posts", response_model=PaginatedPost)
def list_posts(
    query: str | None = Query(default=None, alias="search", max_length=30),
    per_page: int = Query(default=10, ge=1, le=50),
    page: int = Query(default=1, ge=1),
    order_by: Literal["id", "title"] = Query(default="id"),
    direction: Literal["asc", "desc"] = Query(default="asc")
):
    ...
```

```python
@app.get("/posts/{post_id}", response_model=Union[PostPublic, PostSummary], response_description="Post encontrado")
def get_post(
    post_id: int = Path(
        ...,
        ge=1,
        title="ID del post",
        description="Identificador entero del post. Debe ser mayor a 1",
        example=1
    ),
    include_content: bool = Query(default=True, description="Mostrar contenido")
):
    ...
```

### Why this is useful

- It documents the response structure clearly.
- It validates that the return value matches the expected schema.
- It improves Swagger/OpenAPI documentation.
- It allows different shapes depending on the endpoint logic, such as returning a summary without content.
- `Path(...)` adds validation on path parameters, for example `ge=1` ensures IDs are positive integers.
- `PaginatedPost` also reports `total`, `total_pages`, `has_prev`, and `has_next`.

---

## 5. Query parameters and pagination

Query parameters are values sent in the URL after `?`.

```python
@app.get("/posts", response_model=PaginatedPost)
def list_posts(
    query: str | None = Query(
        default=None,
        alias="search",
        max_length=30,
        pattern=r"^[\w\sáéíóúÁÉÍÓÚüÜ-]+$"
    ),
    per_page: int = Query(default=10, ge=1, le=50),
    page: int = Query(default=1, ge=1),
    order_by: Literal["id", "title"] = Query(default="id"),
    direction: Literal["asc", "desc"] = Query(default="asc")
):
    ...
```

### Explanation

- `query` is a nullable string exposed as the `search` query parameter.
- `max_length=30` and `pattern` validate the search text automatically.
- `per_page` accepts values from 1 to 50, and `page` must be at least 1.
- `order_by` only accepts `id` or `title`; `direction` only accepts `asc` or `desc`.
- The endpoint filters, sorts, slices the results, and returns pagination metadata.

### Example

```http
GET /posts?search=FastAPI&page=1&per_page=10&order_by=title&direction=asc
```

This can be used to search by title.

---

## 6. Path parameters

Path parameters are variables included in the URL path.

```python
@app.get("/posts/{post_id}")
def get_post(
    post_id: int = Path(
        ...,
        ge=1,
        title="ID del post",
        description="Identificador entero del post. Debe ser mayor a 1",
        example=1
    ),
    include_content: bool = Query(default=True, description="Mostrar contenido")
):
    for post in BLOG_POST:
        if post["id"] == post_id:
            if not include_content:
                return {"id": post["id"], "title": post["title"]}

            return {"data": post}

    return {"error": "Post no encontrado"}
```

### What is happening here

- `post_id` is extracted from the URL, for example `/posts/2`.
- FastAPI converts it to `int` because the type is `int`.
- `Path(...)` adds validation to the route parameter, such as `ge=1` meaning the ID must be greater than or equal to 1.
- `include_content` is a boolean query parameter, such as `?include_content=false`.
- If the post is found, it returns the object; otherwise, it returns an error.

This demonstrates how to combine path parameters and query parameters in one route.

---

## 7. POST route: creating a new post

```python
@app.post("/posts", response_model=PostPublic, response_description="Nuevo post creado")
def create_post(post: PostCreate):
    new_id = (BLOG_POST[-1]["id"] + 1) if BLOG_POST else 1
    new_post = {
        "id": new_id,
        "authors": [author.model_dump() for author in post.authors] if post.authors else None,
        "title": post.title,
        "content": post.content,
        "tags": [tag.model_dump() for tag in post.tags]
    }
    BLOG_POST.append(new_post)

    return new_post
```

### Explanation

- The request body is validated automatically using `PostCreate`.
- `post.title` and `post.content` are accessed as attributes because the model is converted into an object.
- `post.tags` and `post.authors` contain nested Pydantic models.
- `model_dump()` converts each nested model into a dictionary before storing it in the in-memory list.
- A new ID is generated from the last element in `BLOG_POST`.
- The new post is appended to the in-memory list.
- `response_model=PostPublic` controls the structure returned to the client.

### Example JSON body

```json
{
	"title": "My new post",
	"content": "This is a new post created with FastAPI",
	"tags": [{ "name": "fastapi" }],
	"authors": [{ "name": "John Doe", "email": "johndoe@example.com" }]
}
```

---

## 8. PUT route: update an existing post

```python
@app.put("/posts/{post_id}")
def update_post(post_id: int, data: PostUpdate):
    for post in BLOG_POST:
        if post["id"] == post_id:
            playload = data.model_dump(exclude_unset=True)
            if "title" in playload: post["title"] = playload["title"]
            if "content" in playload: post["content"] = playload["content"]
            return {"message": "Se ha actualizado el post", "data": post}

    raise HTTPException(status_code=404, detail="Post no encontrado")
```

### Important concepts

#### `model_dump(exclude_unset=True)`

This converts the Pydantic model into a dictionary while excluding fields that were not sent by the client.

```python
payload = data.model_dump(exclude_unset=True)
```

Example:

```json
{
	"title": "Updated title"
}
```

If a field is not included in the request, it is ignored. This prevents accidentally overwriting existing values with `None` or empty data.

### Why this is important

This pattern allows partial updates:

- You can update only `title`.
- You can update only `content`.
- You do not need to send the entire object every time.

### Error handling

```python
raise HTTPException(status_code=404, detail="Post no encontrado")
```

This raises an HTTP 404 error if the post does not exist.

---

## 9. DELETE route: removing a resource

```python
@app.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int):
    for index, post in enumerate(BLOG_POST):
        if post["id"] == post_id:
            BLOG_POST.pop(index)
            return

    raise HTTPException(status_code=404, detail="Post no encontrado")
```

### Explanation

- `status_code=204` means the server responds successfully without any body content.
- This is typical for delete operations.
- If the post is not found, the function raises a 404 error.
- In a delete endpoint, it is common to return nothing when the operation succeeds.

### Rule of thumb

- `200 OK`: return data
- `201 Created`: resource successfully created
- `204 No Content`: successful deletion with no body
- `404 Not Found`: resource missing

---

## 10. `Body(...)` and request-body requirement

In FastAPI, `Body(...)` is used to force a body to be required in the request.

```python
post: dict = Body(...)
```

### Meaning

- The ellipsis `...` indicates a required value.
- If the client does not send a body, FastAPI will respond with a validation error.

This pattern is useful when you want to declare the body explicitly in a function signature.

In this project, however, the code uses Pydantic models instead, which is cleaner and more structured for validation.

---

## 11. HTTPException

`HTTPException` is used to return an explicit HTTP error.

```python
raise HTTPException(status_code=404, detail="Post no encontrado")
```

### Why use it

- It keeps the API behavior clear.
- It lets you return a standard HTTP error with a message.
- It is more readable and maintainable than returning a custom dict in every failure case.

---

## 12. Summary of the API

This mini app implements a simple blog API with these routes:

- `GET /` → home message
- `GET /posts` → search, sort, and paginate posts
- `GET /posts/{post_id}` → get one post by id
- `POST /posts` → create a new post
- `PUT /posts/{post_id}` → update an existing post
- `DELETE /posts/{post_id}` → delete a post

This is a classic beginner-friendly example of REST API design in FastAPI.

---

## 13. Study checklist

Before moving on, make sure you understand:

- What a FastAPI app is and how routes are defined
- The difference between `Query`, `Path`, and `Body`
- How `BaseModel` validates request data
- How nested models such as `Tag` and `Author` work
- How `EmailStr` validates email addresses
- How pagination metadata is calculated and returned
- How `Literal` restricts ordering options to predefined values
- Why `model_dump(exclude_unset=True)` is useful for partial updates
- How `HTTPException` is used for 404 and other errors
- Why `status_code=204` is used in delete endpoints
- How data is manipulated with an in-memory list before using a database

This project is a great introduction to building APIs with FastAPI and understanding the core flow of request → validation → processing → response.
