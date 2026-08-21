import os
import tempfile
import pytest

from guides import clean_html_for_telegram, save_guides, load_guides


def test_clean_html_for_telegram_tinymce():
    raw_html = "<p><strong class=\"bold\">Hello World</strong> and <em>Italic text</em></p>"
    cleaned = clean_html_for_telegram(raw_html)
    assert cleaned == "<b>Hello World</b> and <i>Italic text</i>"


def test_clean_html_for_telegram_links_and_tags():
    raw_html = '<p>Check <a href="https://example.com" target="_blank">this link</a> and <ins>underline</ins> or <del>strike</del></p>'
    cleaned = clean_html_for_telegram(raw_html)
    assert '<a href="https://example.com">this link</a>' in cleaned
    assert "<u>underline</u>" in cleaned
    assert "<s>strike</s>" in cleaned


def test_clean_html_for_telegram_unknown_tags_stripped():
    raw_html = "<div><span style='color:red;'>Span content</span> <script>alert(1)</script></div>"
    cleaned = clean_html_for_telegram(raw_html)
    assert "Span content" in cleaned
    assert "script" not in cleaned


def test_save_and_load_guides(monkeypatch, tmp_path):
    fake_guides_file = tmp_path / "guides.json"
    import guides
    monkeypatch.setattr(guides, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(guides, "GUIDES_FILE", str(fake_guides_file))

    sample_data = {
        "cat1": {
            "title": "Category 1",
            "guide": [{"title": "Guide 1", "text": "Content 1"}]
        }
    }

    save_guides(sample_data)
    assert fake_guides_file.exists()

    loaded = load_guides()
    assert loaded == sample_data
