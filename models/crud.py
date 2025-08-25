from typing import List
from fastapi import HTTPException
from .todo import Todo
from .storage import todos

def create_todo(todo: Todo) -> Todo:
    if any(t.id == todo.id for t in todos):
        raise HTTPException(status_code=400, detail="Todo with this ID already exists")
    todos.append(todo)
    return todo

def get_todos() -> List[Todo]:
    return todos

def get_todo(todo_id: int) -> Todo:
    for todo in todos:
        if todo.id == todo_id:
            return todo
    raise HTTPException(status_code=404, detail="Todo not found")

def update_todo(todo_id: int, updated_todo: Todo) -> Todo:
    for i, todo in enumerate(todos):
        if todo.id == todo_id:
            todos[i] = updated_todo
            return updated_todo
    raise HTTPException(status_code=404, detail="Todo not found")

def delete_todo(todo_id: int) -> dict:
    for i, todo in enumerate(todos):
        if todo.id == todo_id:
            del todos[i]
            return {"message": "Todo deleted"}
    raise HTTPException(status_code=404, detail="Todo not found")
