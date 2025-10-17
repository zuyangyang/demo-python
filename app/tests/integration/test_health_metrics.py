from fastapi.testclient import TestClient


def test_healthz(client: TestClient) -> None:
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"ok": True}


def test_metrics_has_expected_keys(client: TestClient) -> None:
    res = client.get("/metrics")
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert "app_name" in data and isinstance(data["app_name"], str)
    assert "uptime_sec" in data and isinstance(data["uptime_sec"], (int, float))


