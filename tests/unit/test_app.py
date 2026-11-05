import pytest

from app import create_app


@pytest.mark.parametrize(
    "path, expected",
    [
        ("/health", {"status": "ok"}),
        ("/version", {"version": "1.0.0"}),
    ],
)
def test_api_responses(client, path, expected):
    response = client.get(path)

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == expected


def test_default_settings(app):
    assert app.config["APP_VERSION"] == "1.0.0"
    assert app.config["APP_PORT"] == 8000


@pytest.mark.parametrize("version", ["2.0.0", "abc123def456"])
def test_version_from_environment(monkeypatch, version):
    monkeypatch.setenv("APP_VERSION", version)

    application = create_app()

    with application.test_client() as client:
        response = client.get("/version")

    assert response.status_code == 200
    assert response.get_json() == {"version": version}


@pytest.mark.parametrize("version", ["", " ", "\t"])
def test_empty_version_is_rejected(monkeypatch, version):
    monkeypatch.setenv("APP_VERSION", version)

    with pytest.raises(ValueError, match="APP_VERSION must not be empty"):
        create_app()


@pytest.mark.parametrize("port", ["abc", "", "80.5"])
def test_non_integer_port_is_rejected(monkeypatch, port):
    monkeypatch.setenv("APP_PORT", port)

    with pytest.raises(ValueError, match="APP_PORT must be an integer"):
        create_app()


@pytest.mark.parametrize("port", ["0", "-1", "65536"])
def test_out_of_range_port_is_rejected(monkeypatch, port):
    monkeypatch.setenv("APP_PORT", port)

    with pytest.raises(
        ValueError,
        match="APP_PORT must be between 1 and 65535",
    ):
        create_app()


@pytest.mark.parametrize("port", ["1", "8000", "65535"])
def test_valid_port_is_accepted(monkeypatch, port):
    monkeypatch.setenv("APP_PORT", port)

    application = create_app()

    assert application.config["APP_PORT"] == int(port)


def test_unknown_route_returns_404(client):
    response = client.get("/unknown")

    assert response.status_code == 404