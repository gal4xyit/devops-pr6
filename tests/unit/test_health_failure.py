def test_health_failure_mode(client, monkeypatch):
    monkeypatch.setenv("FAIL_HEALTH", "1")

    response = client.get("/health")

    assert response.status_code == 503
    assert response.get_json()["status"] == "error"