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


def test_public_access_api_routes(monkeypatch):
    client = TestClient(app)

    mock_guides = {
        "cat1": {
            "title": "Category 1",
            "guide": [
                {"title": "Guide 1", "text": "Content 1"},
                {"title": "Hidden Guide", "text": "Content Hidden", "is_hidden": True}
            ]
        },
        "cat_hidden": {
            "title": "Hidden Category",
            "is_hidden": True,
            "guide": [{"title": "G1", "text": "T1"}]
        }
    }
    monkeypatch.setattr("web.main.load_guides", lambda: mock_guides)

    # GET /api/categories should be 200
    resp_cats = client.get("/api/categories")
    assert resp_cats.status_code == 200
    cats_list = resp_cats.json()["categories"]
    assert any(c["id"] == "cat1" for c in cats_list)
    assert not any(c["id"] == "cat_hidden" for c in cats_list)

    # GET /api/category/cat1 should be 200
    resp_cat = client.get("/api/category/cat1")
    assert resp_cat.status_code == 200
    cat_data = resp_cat.json()
    assert cat_data["title"] == "Category 1"
    assert len(cat_data["guides"]) == 1
    assert cat_data["guides"][0]["title"] == "Guide 1"

    # GET hidden category should return 404
    resp_cat_hidden = client.get("/api/category/cat_hidden")
    assert resp_cat_hidden.status_code == 404

    # GET /api/guides/cat1/0 should be 200
    resp_guide = client.get("/api/guides/cat1/0")
    assert resp_guide.status_code == 200
    assert resp_guide.json()["guide"]["title"] == "Guide 1"

    # GET hidden guide should return 404
    resp_guide_hidden = client.get("/api/guides/cat1/1")
    assert resp_guide_hidden.status_code == 404

    # POST /api/categories without session should return 401
    resp_add = client.post("/api/categories", json={"id": "test", "title": "Test"})
    assert resp_add.status_code == 401
