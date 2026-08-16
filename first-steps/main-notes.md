# `main.py` Notes

## `Body()` Class

Usually we use `Body(...)` we force to FastAPI to require the body.
This `(...)` means that there's going to be some data, but we don't know what it would be

**Example:**

```python
@app.post("/posts")
def create_post(post: dict = Body(...)):
    if "title" not in post or "content" not in post:
        return {"error": "Title y Content son requeridos"}

    if not str(post["title"]).strip():
        return {"error": "Title no puede estar vacío"}

    new_id = (BLOG_POST[-1]["id"]+1) if BLOG_POST else 1
    new_post = {"id": new_id, "title": post["title"], "content": post["content"]}
    BLOG_POST.append(new_post)

    return {"message": "Un nuevo post se ha creado", "data": new_post}
```

## Returning nothing:

If don't want to return any value, use `status_code=204`

**Example:**

```python
@app.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int):
    for index, post in enumerate(BLOG_POST):
        if post["id"] == post_id:
            BLOG_POST.pop(index)
            return

    raise HTTPException(status_code=404, detail="Post no encontrado")
```

# Pydantic Notes

This an library that add type validations

## Importing Pydantic

```python
from pydantic import BaseModel
```

## Using Class Models

```python
class PostBase(BaseModel):
    title: str
    content: str

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: str
    content: str
```

## Converting Models to dict

```python
playload = data.model_dump(exclude_unset=True)
```

With the `model_dump()` method, we transform our model into a dict

```json
{
	"title": "Hello",
	"content": "World!!"
}
```

### Excluding items of a dict

This is used for excluding UNSET items, letting modify only those who were declared:

```python
playload = data.model_dump(exclude_unset=True)
```

This will prevent to set errors like this:

```json
{
	"title": "Hello",
	"content": None
}
```

We don't want to overwrite values that not were setted on the dict
