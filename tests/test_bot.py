import os
import pytest

os.environ["BOT_TOKEN"] = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz123456789"

from config import is_admin
import bot


def test_is_admin_check(monkeypatch):
    import config
    monkeypatch.setattr(config, "ADMIN_ID", [12345, 67890])
    assert is_admin(12345) is True
    assert is_admin(67890) is True
    assert is_admin(99999) is False


def test_search_guides(monkeypatch):
    mock_data = {
        "cat1": {
            "title": "Windows Setup",
            "guide": [
                {"title": "How to install WireGuard", "text": "Step 1: download installer"},
                {"title": "AmneziaVPN guide", "text": "Instructions for Windows"}
            ]
        },
        "cat2": {
            "title": "iOS Setup",
            "guide": [
                {"title": "Shadowsocks on iOS", "text": "App Store configuration"}
            ]
        }
    }
    monkeypatch.setattr("bot.load_guides", lambda: mock_data)

    res_wg = bot._search_guides("wireguard")
    assert len(res_wg) == 1
    assert res_wg[0][2]["title"] == "How to install WireGuard"

    res_win = bot._search_guides("windows")
    assert len(res_win) == 1
    assert res_win[0][2]["title"] == "AmneziaVPN guide"

    res_empty = bot._search_guides("nonexistent_term")
    assert len(res_empty) == 0
