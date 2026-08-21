import pytest
import time
from fastapi.testclient import TestClient
from web.main import app
from web.auth import verify_telegram_auth
from web.storage import count_stats, load_guides, save_guides


def test_verify_telegram_auth_invalid():
    # Empty data or invalid hash should return False
    assert verify_telegram_auth({}) is False
    assert verify_telegram_auth({"id": "123", "hash": "invalid"}) is False


def test_verify_telegram_auth_expired(monkeypatch):
    import web.auth as auth_mod
    monkeypatch.setattr(auth_mod, "BOT_TOKEN", "fake_token")

    old_auth_date = int(time.time()) - 100000  # > 24 hours ago
    data = {
        "id": "123",
        "auth_date": str(old_auth_date),
        "hash": "somehash"
    }
    assert verify_telegram_auth(data) is False


def test_count_stats(monkeypatch, tmp_path):
    import web.storage as storage
    guides_file = tmp_path / "guides.json"
    users_file = tmp_path / "users.json"

    monkeypatch.setattr(storage, "GUIDES_FILE", str(guides_file))
    monkeypatch.setattr(storage, "USERS_FILE", str(users_file))
    monkeypatch.setattr(storage, "DATA_DIR", str(tmp_path))

    save_guides({
        "c1": {"title": "Cat 1", "guide": [{"t": "g1"}, {"t": "g2"}]},
        "c2": {"title": "Cat 2", "guide": [{"t": "g3"}]}
    })

    stats = count_stats()
    assert stats["categories"] == 2
    assert stats["guides"] == 3
    assert stats["users"] == 0


def test_public_access_routes():
    client = TestClient(app)

    # GET / should be accessible without session (200 OK)
    resp_dashboard = client.get("/")
    assert resp_dashboard.status_code == 200
    assert "Категории" in resp_dashboard.text

    # GET /category/happ should be accessible without session (200 OK)
    resp_cat = client.get("/category/happ")
    assert resp_cat.status_code == 200

    # GET /guide/happ/0/view should be accessible without session (200 OK)
    resp_guide = client.get("/guide/happ/0/view")
    assert resp_guide.status_code == 200

    # POST /category/add without session should redirect to /login (303)
    resp_add = client.post("/category/add", data={"category_id": "test", "title": "Test"}, follow_redirects=False)
    assert resp_add.status_code == 303
    assert resp_add.headers["location"] == "/login"
