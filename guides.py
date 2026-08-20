"""
Модуль доступа к гайдам.

Гайды хранятся в JSON-файле (data/guides.json) и редактируются
через Telegram-админ-панель (или вручную в файле).
"""

import json
import os
import re

# Путь к файлу с контентом
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
GUIDES_FILE = os.path.join(DATA_DIR, "guides.json")


def load_guides() -> dict:
    """Загружает словарь гайдов из JSON-файла."""
    if not os.path.exists(GUIDES_FILE):
        return {}
    with open(GUIDES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_guides(guides: dict) -> None:
    """Сохраняет словарь гайдов в JSON-файл."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(GUIDES_FILE, "w", encoding="utf-8") as f:
        json.dump(guides, f, ensure_ascii=False, indent=2)


# ---------- Очистка HTML для Telegram ----------

# Теги, которые Telegram умеет рендерить (HTML Parse Mode).
# Каноничные варианты: <b> <i> <u> <s> <code> <pre> <a href="..."> <tg-spoiler>.
_CANON_TAG = re.compile(
    r"</?(?:\s*)(b|i|u|s|code|pre|tg-spoiler|a(?:\s+href=[\"'][^\"']*[\"'])?)>",
    re.IGNORECASE,
)


def clean_html_for_telegram(text: str) -> str:
    """
    Превращает HTML из веб-редактора (TinyMCE) в HTML, понятный Telegram.

    - Блочные теги (<p>, <div>, <section>, <br> и т.п.) заменяются на перенос строки.
    - Из ссылок <a> сохраняется только href.
    - <strong>/<em>/<ins>/<del>/<strike> приводятся к <b>/<i>/<u>/<s>.
    - Неизвестные теги удаляются, их содержимое сохраняется.
    - Всё, что выглядит как "<...>" и не является валидным тегом Telegram,
      экранируется (выводится как текст).
    """
    if not text:
        return text or ""

    import html

    # HTML-комментарии и служебные блоки полностью удаляем
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"<(script|style|iframe)[^>]*>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Блочные теги -> перенос строки
    block = re.compile(
        r"</?(?:p|div|section|article|header|footer|table|tr|td|th|ul|ol|li|br|hr|"
        r"blockquote|h[1-6])\b[^>]*>",
        flags=re.IGNORECASE,
    )
    text = block.sub("\n", text)

    # У ссылок оставляем только href
    text = re.sub(
        r"<a\s+[^>]*href\s*=\s*[\"']([^\"']*)[\"'][^>]*>",
        r'<a href="\1">',
        text,
        flags=re.IGNORECASE,
    )

    # Декодируем безопасные HTML-сущности (пробелы, кавычки, юникод-коды),
    # НО НЕ трогаем &lt; &gt; &amp; (это значимые и используются пусть остаются).
    # Так < из &lt; не превратится в тег.
    text = (
        text.replace("&nbsp;", " ")
            .replace("&quot;", '"')
            .replace("&#39;", "'")
            .replace("&middot;", "·")
            .replace("&copy;", "©")
    )
    # Декодируем юникод-коды вида &#NNN; / &#xHHHH;
    text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
    text = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), text)

    # Разбираем посимвольно: строим выход, сохраняя только каноничные теги
    out = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == "<":
            # ищем конец тега
            end = text.find(">", i)
            if end == -1:
                # нет закрывающей > — просто экранируем
                out.append("&lt;")
                i += 1
                continue
            raw = text[i:end + 1]
            m = _CANON_TAG.fullmatch(raw)
            if m:
                # Канонический тег — нормализуем регистр и добавляем как есть
                tag_name = m.group(1)
                if raw.lower().startswith("<a"):
                    out.append(raw)  # уже с href
                elif raw.startswith("</"):
                    out.append(f"</{tag_name.lower()}>")
                else:
                    out.append(f"<{tag_name.lower()}>")
                i = end + 1
            elif re.match(r"</?\s*[a-zA-Z]", raw):
                # Настоящий (но неподдержанный) HTML-тег — убираем его,
                # содержимое остаётся.
                i = end + 1
            else:
                # Это не тег, а одиночный '<' из обычного текста — экранируем.
                out.append("&lt;")
                i += 1
        else:
            # Обычный текст. Экранируем '&', если это НЕ корректная сущность
            # (<, >, amp, &#NN; и т.п.) — такие оставляем как есть.
            if ch == "&" and not re.match(r"&(lt|gt|amp|quot|#\d+);", text[i:i + 10]):
                out.append("&amp;")
            else:
                out.append(ch)
            i += 1

    text = "".join(out)

    # Приводим <strong>/<em>/<ins>/<del>/<strike> к каноничным <b>/<i>/<u>/<s>
    # (на случай, если они попали в текст не через блочную обработку).
    replacements = [
        ("<strong>", "<b>"), ("</strong>", "</b>"),
        ("<em>", "<i>"), ("</em>", "</i>"),
        ("<ins>", "<u>"), ("</ins>", "</u>"),
        ("<del>", "<s>"), ("</del>", "</s>"),
        ("<strike>", "<s>"), ("</strike>", "</s>"),
    ]
    for a, b in replacements:
        text = text.replace(a, b).replace(a.upper(), b)

    # Чистим лишние пустые строки (больше двух подряд)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# Актуальный срез гайдов для использования в боте (загружается при старте)
GUIDES = load_guides()
