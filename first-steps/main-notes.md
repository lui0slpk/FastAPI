# FastAPI Mini Blog Notes

This file summarizes the logic and patterns used in the FastAPI app in `main.py`. It focuses on the application structure, route design, validation, and data handling. Installation and environment setup are intentionally not repeated here because they are already covered in `configuration.md`.

---

## 1. Application setup

A FastAPI app is created with `FastAPI()` and can receive metadata such as the title.

```python
from fastapi import FastAPI, Query, Body, HTTPException
from pydantic import BaseModel
from typing import Optional

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
class PostBase(BaseModel):
    title: str
    content: Optional[str] = "Contenido no disponible"

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: str
    content: Optional[str] = None
```

### Key ideas

- `BaseModel` is the base class from which request models inherit.
- `title: str` means `title` must be a string.
- `content: Optional[str] = "Contenido no disponible"` means content is optional and has a default value.
- `PostCreate` inherits from `PostBase`, so it has the same fields.
- `PostUpdate` is used when updating a post partially, so some fields may be absent.

This is one of the most important parts of FastAPI: request data is validated before the function runs.

---

## 4. Query parameters

Query parameters are values sent in the URL after `?`.

```python
@app.get("/posts")
def list_posts(query: str | None = Query(default=None, description="Texto para buscar por título")):
    if query:
        results = [post for post in BLOG_POST if query.lower() in post["title"].lower()]
        return {"data": results, "query": query}

    return {"data": BLOG_POST}
```

### Explanation

- `query` is a nullable string.
- `Query(...)` lets FastAPI treat it as a query parameter and optionally attach a description.
- If a user sends `/posts?query=FastAPI`, the API filters the list by matching the title.
- If no query is provided, it returns the full list.

### Example

```http
GET /posts?query=FastAPI
```

This can be used to search by title.

---

## 5. Path parameters

Path parameters are variables included in the URL path.

```python
@app.get("/posts/{post_id}")
def get_post(post_id: int, include_content: bool = Query(default=True, description="Mostrar contenido")):
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
- `include_content` is a boolean query parameter, such as `?include_content=false`.
- If the post is found, it returns the object; otherwise, it returns an error.

This demonstrates how to combine path parameters and query parameters in one route.

---

## 6. POST route: creating a new post

```python
@app.post("/posts")
def create_post(post: PostCreate):
    new_id = (BLOG_POST[-1]["id"] + 1) if BLOG_POST else 1
    new_post = {"id": new_id, "title": post.title, "content": post.content}
    BLOG_POST.append(new_post)

    return {"message": "Un nuevo post se ha creado", "data": new_post}
```

### Explanation

- The request body is validated automatically using `PostCreate`.
- `post.title` and `post.content` are accessed as attributes because the model is converted into an object.
- A new ID is generated from the last element in `BLOG_POST`.
- The new post is appended to the in-memory list.
- The response returns a message and the new created object.

### Example JSON body

```json
{
	"title": "My new post",
	"content": "This is a new post created with FastAPI"
}
```

---

## 7. PUT route: update an existing post

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

## 8. DELETE route: removing a resource

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

## 9. `Body(...)` and request-body requirement

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

## 10. HTTPException

`HTTPException` is used to return an explicit HTTP error.

```python
raise HTTPException(status_code=404, detail="Post no encontrado")
```

### Why use it

- It keeps the API behavior clear.
- It lets you return a standard HTTP error with a message.
- It is more readable and maintainable than returning a custom dict in every failure case.

---

## 11. Summary of the API

This mini app implements a simple blog API with these routes:

- `GET /` → home message
- `GET /posts` → list all posts or filter by query
- `GET /posts/{post_id}` → get one post by id
- `POST /posts` → create a new post
- `PUT /posts/{post_id}` → update an existing post
- `DELETE /posts/{post_id}` → delete a post

This is a classic beginner-friendly example of REST API design in FastAPI.

---

## 12. Study checklist

Before moving on, make sure you understand:

- What a FastAPI app is and how routes are defined
- The difference between `Query`, `Path`, and `Body`
- How `BaseModel` validates request data
- Why `model_dump(exclude_unset=True)` is useful for partial updates
- How `HTTPException` is used for 404 and other errors
- Why `status_code=204` is used in delete endpoints
- How data is manipulated with an in-memory list before using a database

This project is a great introduction to building APIs with FastAPI and understanding the core flow of request → validation → processing → response.
