from backend.app import create_app


def test_health():
    app = create_app()
    client = app.test_client()
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.get_json()
    assert data.get("ok") is True
