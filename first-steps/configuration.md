# Installation and Configuration Notes

## How to install FastAPI Framework

- Using `pip`

  ```bash
  pip install "fastapi[standard]"
  ```

- Using `uv`

  **Ensure having uv installed**

  ```bash
  uv init awesome-project --bare
  cd awesome-project
  uv add "fastapi[standard]"
  ```

  **How to install uv**

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

## How to run a FastAPI server

```bash
uvicorn main:app --reload
```

## Using CURL to send an POST request

```bash
curl -X POST http://127.0.0.1:8000/posts -H "Content-Type: application/json" -d '{"title": "Nuevo post desde curl", "content": "Mi nuevo post desde Curl"}'
```

- `-X` it's the action we want to execute
- `-H` it's the header "Content-Type"
- `-d` it's the description "Body"
