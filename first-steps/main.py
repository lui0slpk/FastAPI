"""
To run the app we have two commands:
1. Using fastapi:
    - fastapi dev main.py || This is for development run mode
    - fastapi run main.py || This is for production run mode
2. Using uvicorn:
    - uvicorn main:app --reload || Also we can change the run port using --port 4242
"""

from fastapi import FastAPI

app = FastAPI(title="Mini Blog")

@app.get("/")
def home():
    return {'message': 'Bienvenidos a Mini Blog por Luis'}