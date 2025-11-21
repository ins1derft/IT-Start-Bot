from fastapi.testclient import TestClient
from itstart_core_api.config import Settings
from itstart_core_api.main import create_app


def test_metrics_endpoint(monkeypatch):
    monkeypatch.setenv("POSTGRES_DSN", "sqlite+aiosqlite:///:memory:")
    app = create_app(Settings())
    client = TestClient(app)

    # simple request to increment counters
    client.get("/healthz")
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "http_requests_total" in resp.text
