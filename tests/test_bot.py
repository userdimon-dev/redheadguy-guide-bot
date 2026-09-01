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
                {"title": "AmneziaVPN guide", "text": "Instructions for Windows"},
                {"title": "Hidden WireGuard", "text": "Hidden text WireGuard", "is_hidden": True}
            ]
        },
        "cat2": {
            "title": "iOS Setup",
            "is_hidden": True,
            "guide": [
                {"title": "Shadowsocks on iOS", "text": "App Store configuration WireGuard"}
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


def test_keyboards_grid_and_hidden(monkeypatch):
    import keyboards
    monkeypatch.setattr(keyboards, "ENABLE_MINI_APP", False)
    sample_guides = {
        "cat1": {
            "title": "Cat 1",
            "sort_order": 2,
            "row_number": 1,
            "guide": [
                {"title": "G1", "text": "T1", "sort_order": 2, "row_number": 1},
                {"title": "G2_Hidden", "text": "T2", "is_hidden": True, "sort_order": 1, "row_number": 1},
                {"title": "G3", "text": "T3", "sort_order": 1, "row_number": 1}
            ]
        },
        "cat2_hidden": {
            "title": "Hidden Cat",
            "is_hidden": True,
            "sort_order": 1,
            "row_number": 1,
            "guide": []
        },
        "cat3": {
            "title": "Cat 3",
            "sort_order": 1,
            "row_number": 1,
            "guide": []
        }
    }
    monkeypatch.setattr("keyboards.load_guides", lambda: sample_guides)

    from keyboards import main_menu_keyboard, category_keyboard
    kb_main = main_menu_keyboard()
    rows = kb_main.inline_keyboard
    # row 0 should have Cat 3 and Cat 1, row 1 should have Search button
    assert len(rows[0]) == 2
    assert rows[0][0].text == "Cat 3"
    assert rows[0][1].text == "Cat 1"
    assert len(rows[1]) == 1
    assert rows[1][0].text == "🔍 Поиск"

    kb_cat1 = category_keyboard("cat1")
    cat_rows = kb_cat1.inline_keyboard
    assert len(cat_rows[0]) == 2
    assert cat_rows[0][0].text == "G3"
    assert cat_rows[0][1].text == "G1"
    assert len(cat_rows[1]) == 1
    assert cat_rows[1][0].text == "◀️ Назад"
