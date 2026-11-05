import pytest

from app import create_app


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    monkeypatch.delenv("APP_VERSION", raising=False)
    monkeypatch.delenv("APP_PORT", raising=False)


@pytest.fixture
def app():
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    with app.test_client() as test_client:
        yield test_client