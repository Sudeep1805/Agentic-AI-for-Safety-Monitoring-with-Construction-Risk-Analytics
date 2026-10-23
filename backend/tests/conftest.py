import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.database import Base, make_engine, make_session_factory
from app.main import create_app
from app.models.upload import SiteUpload
from app.models.project import Project
from app.models.session import UserSession
from app.models.user import User


@pytest.fixture
def settings(tmp_path):
    return Settings(_env_file=None, upload_dir=tmp_path / "uploads", max_upload_bytes=1024 * 1024,
                    max_image_pixels=1_000_000, cors_origins=["http://localhost:5173"])


@pytest.fixture
def session_factory():
    # Only the isolated verification script sets these variables. Never use the app's .env.
    if os.environ.get("FOUNDATION_TEST_MYSQL_PORT"):
        settings = Settings(
            _env_file=None, mysql_host="127.0.0.1",
            mysql_port=int(os.environ["FOUNDATION_TEST_MYSQL_PORT"]),
            mysql_database=os.environ["FOUNDATION_TEST_MYSQL_DATABASE"],
            mysql_user="root", mysql_password=os.environ["FOUNDATION_TEST_MYSQL_PASSWORD"],
        )
        assert settings.mysql_database.startswith("foundation_test_")
        engine = make_engine(settings)
    else:
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    yield factory
    with factory() as session:
        session.execute(delete(SiteUpload))
        session.execute(delete(Project))
        session.execute(delete(UserSession))
        session.execute(delete(User))
        session.commit()
    engine.dispose()


@pytest.fixture
def client(settings, session_factory):
    with TestClient(create_app(settings, session_factory)) as client:
        response = client.post("/api/auth/signup", json={
            "email": "fixture@example.com", "full_name": "Fixture User", "password": "fixture-password"
        })
        assert response.status_code == 201
        client.headers.update({"Authorization": f"Bearer {response.json()['access_token']}"})
        yield client
