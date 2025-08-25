from fastapi.testclient import TestClient
from todo_api import app

client = TestClient(app)

def test_create_todo():
    response = client.post("/todos/", json={"id": 1, "title": "Test Todo", "description": "Test Desc", "completed": False})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Test Todo"

def test_get_todos():
    response = client.get("/todos/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_todo():
    client.post("/todos/", json={"id": 2, "title": "Second", "description": "", "completed": False})
    response = client.get("/todos/2")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 2

def test_update_todo():
    client.post("/todos/", json={"id": 3, "title": "UpdateMe", "description": "", "completed": False})
    response = client.put("/todos/3", json={"id": 3, "title": "Updated", "description": "Done", "completed": True})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"
    assert data["completed"] is True

def test_delete_todo():
    client.post("/todos/", json={"id": 4, "title": "DeleteMe", "description": "", "completed": False})
    response = client.delete("/todos/4")
    assert response.status_code == 200
    assert response.json()["message"] == "Todo deleted"
