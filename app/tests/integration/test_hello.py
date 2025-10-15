from fastapi.testclient import TestClient


def test_hello_default(client: TestClient) -> None:
    response = client.get("/api/v1/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World"}


def test_hello_with_name(client: TestClient) -> None:
    response = client.get("/api/v1/hello", params={"name": "Alice"})
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, Alice"}


