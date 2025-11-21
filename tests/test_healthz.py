from fastapi.testclient import TestClient
from itstart_core_api.config import Settings
from itstart_core_api.main import create_app


def test_healthz_returns_ok():
    app = create_app(Settings(database_url="sqlite+aiosqlite:///:memory:", redis_url="redis://localhost:6379/0"))
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
