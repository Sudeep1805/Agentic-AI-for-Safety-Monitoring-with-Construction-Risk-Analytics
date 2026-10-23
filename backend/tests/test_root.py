from fastapi.testclient import TestClient

from app.main import create_app


def test_root_returns_api_status(settings, session_factory):
    with TestClient(create_app(settings, session_factory)) as client:
        response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "site-risk-api"
    assert body["frontend_url"] == "http://127.0.0.1:5173"
    assert body["docs_url"] == "/docs"
    assert body["health_url"] == "/health"
