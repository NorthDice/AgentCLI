from fastapi import FastAPI
from fastapi import HTTPException
from typing import List
from models.todo import Todo
from models.crud import create_todo, get_todos, get_todo, update_todo, delete_todo

app = FastAPI()

@app.post("/todos/", response_model=Todo)
def create_todo_endpoint(todo: Todo):
    return create_todo(todo)

@app.get("/todos/", response_model=List[Todo])
def get_todos_endpoint():
    return get_todos()

@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo_endpoint(todo_id: int):
    return get_todo(todo_id)

@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo_endpoint(todo_id: int, updated_todo: Todo):
    return update_todo(todo_id, updated_todo)

@app.delete("/todos/{todo_id}")
def delete_todo_endpoint(todo_id: int):
    return delete_todo(todo_id)
