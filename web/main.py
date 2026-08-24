"""
FastAPI-приложение — веб-редактор контента RedheadGuy Guide Bot.

Запуск (в контейнере):
    uvicorn web.main:app --host 0.0.0.0 --port 8000
"""

import logging
import os
import secrets

from fastapi import FastAPI, Request, Form, Response, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from .config import SITE_NAME, BOT_USERNAME, is_admin
from .auth import verify_telegram_auth
from .storage import load_guides, save_guides, backup_guides, count_stats

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Общая с ботом папка медиа (media/photos) — монтируется как volume.
# В контейнере web она лежит на одном уровне с web/: /app/media
MEDIA_DIR = os.path.join(os.path.dirname(BASE_DIR), "media")
PHOTOS_DIR = os.path.join(MEDIA_DIR, "photos")
os.makedirs(PHOTOS_DIR, exist_ok=True)

app = FastAPI(title="RedheadGuy Admin")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

logger = logging.getLogger("web")

# Простой in-memory «хранитель» сессий (для простоты; в проде используйте Redis/DB)
_active_sessions: dict[str, int] = {}  # token -> telegram_id


def _set_session_cookie(response: Response, telegram_id: int) -> None:
    token = secrets.token_urlsafe(32)
    _active_sessions[token] = telegram_id
    response.set_cookie("session", token, max_age=60 * 60 * 24, httponly=True, samesite="lax")


def _get_session_user(request: Request) -> int | None:
    token = request.cookies.get("session")
    if token and token in _active_sessions:
        uid = _active_sessions[token]
        if is_admin(uid):
            return uid
    return None


# ---------- Страницы ----------
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = _get_session_user(request)
    guides = load_guides()
    stats = count_stats()

    # Сортируем категории по sort_order
    sorted_categories = sorted(
        guides.items(),
        key=lambda x: (x[1].get("sort_order", 0), x[0])
    )

    # Если пользователь не админ — отдаем только публичные (видимые) категории
    if user is None:
        display_categories = [
            (cid, cat) for cid, cat in sorted_categories
            if not cat.get("is_hidden", False)
        ]
    else:
        display_categories = sorted_categories

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "guides": dict(display_categories),
            "stats": stats,
            "site_name": SITE_NAME,
            "session_user": user,
        },
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "site_name": SITE_NAME, "bot_username": BOT_USERNAME},
    )


@app.api_route("/auth", methods=["GET", "POST"], name="auth")
async def auth_login(response: Response, request: Request):
    """
    Приём данных от Telegram Login Widget.

    Виджет может отправить данные двумя способами:
    - GET  — параметры в query-string  (?id=...&hash=...&auth_date=...)
    - POST — параметры в теле формы (x-www-form-urlencoded)

    Читаем и объединяем оба источника.
    """
    params = dict(request.query_params)
    if request.method == "POST":
        try:
            form = await request.form()
            for key, value in form.items():
                params[key] = str(value)
        except Exception:
            pass

    if not verify_telegram_auth(params):
        return RedirectResponse(url="/login?error=auth_fail", status_code=303)
    try:
        telegram_id = int(params["id"])
    except (KeyError, ValueError):
        return RedirectResponse(url="/login?error=auth_fail", status_code=303)
    # Устанавливаем cookie на самом возвращаемом response (303 redirect),
    # чтобы Set-Cookie точно дошёл до браузера.
    redirect = RedirectResponse(url="/", status_code=303)
    _set_session_cookie(redirect, telegram_id)
    return redirect


@app.get("/logout")
async def logout(response: Response):
    response.delete_cookie("session")
    return RedirectResponse(url="/login", status_code=303)


# ---------- CRUD категорий ----------
@app.post("/category/add")
async def category_add(request: Request, category_id: str = Form(...), title: str = Form(...),
                       is_hidden: bool = Form(default=False),
                       sort_order: int = Form(default=0),
                       row_number: int = Form(default=1)):
    if _get_session_user(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    guides = load_guides()
    cid = category_id.strip().lower().replace(" ", "_")
    if not cid or not title.strip():
        return RedirectResponse(url="/", status_code=303)
    if cid not in guides and cid:
        guides[cid] = {
            "title": title.strip(),
            "is_hidden": is_hidden,
            "sort_order": sort_order,
            "row_number": row_number,
            "guide": [],
        }
        backup_guides()
        save_guides(guides)
    return RedirectResponse(url="/", status_code=303)


@app.post("/category/{category_id}/delete")
async def category_delete(request: Request, category_id: str):
    if _get_session_user(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    guides = load_guides()
    if category_id in guides:
        del guides[category_id]
        backup_guides()
        save_guides(guides)
    return RedirectResponse(url="/", status_code=303)


@app.post("/category/{category_id}/rename")
async def category_rename(request: Request, category_id: str, title: str = Form(...),
                          is_hidden: bool = Form(default=False),
                          sort_order: int = Form(default=0),
                          row_number: int = Form(default=1)):
    if _get_session_user(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    guides = load_guides()
    if category_id in guides and title.strip():
        guides[category_id]["title"] = title.strip()
        guides[category_id]["is_hidden"] = is_hidden
        guides[category_id]["sort_order"] = sort_order
        guides[category_id]["row_number"] = row_number
        backup_guides()
        save_guides(guides)
    return RedirectResponse(url=f"/category/{category_id}", status_code=303)


# ---------- Страницы категории / CRUD гайда ----------
@app.get("/category/{category_id}", response_class=HTMLResponse)
async def category_page(request: Request, category_id: str):
    user = _get_session_user(request)
    guides = load_guides()
    if category_id not in guides:
        return RedirectResponse(url="/", status_code=303)
    category = dict(guides[category_id])

    # Если обычный пользователь и категория скрыта — отдаем 404/редирект
    if user is None and category.get("is_hidden", False):
        return JSONResponse({"detail": "Not found"}, status_code=404)

    # Сортируем гайды внутри категории по sort_order, сохраняя исходный индекс
    raw_guides = category.get("guide", [])
    indexed_guides = [
        {"orig_idx": idx, **g} for idx, g in enumerate(raw_guides)
    ]
    indexed_guides.sort(key=lambda x: (x.get("sort_order", 0), x["orig_idx"]))
    category["sorted_guides"] = indexed_guides

    return templates.TemplateResponse(
        "category.html",
        {
            "request": request,
            "category": category,
            "category_id": category_id,
            "site_name": SITE_NAME,
            "session_user": user,
        },
    )


@app.get("/guide/{category_id}/new", response_class=HTMLResponse)
async def guide_new_page(request: Request, category_id: str):
    if _get_session_user(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    guides = load_guides()
    if category_id not in guides:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        "guide_edit.html",
        {
            "request": request,
            "category_id": category_id,
            "index": None,
            "guide": {},
            "is_new": True,
            "site_name": SITE_NAME,
        },
    )


@app.get("/guide/{category_id}/{index}", response_class=HTMLResponse)
async def guide_page(request: Request, category_id: str, index: int):
    user = _get_session_user(request)
    guides = load_guides()
    category = guides.get(category_id)
    if not category or index >= len(category["guide"]):
        return RedirectResponse(url="/", status_code=303)
    guide = category["guide"][index]

    if user is not None:
        return templates.TemplateResponse(
            "guide_edit.html",
            {
                "request": request,
                "category_id": category_id,
                "index": index,
                "guide": guide,
                "is_new": False,
                "site_name": SITE_NAME,
                "session_user": user,
            },
        )
    return templates.TemplateResponse(
        "guide_view.html",
        {
            "request": request,
            "category": category,
            "category_id": category_id,
            "index": index,
            "guide": guide,
            "site_name": SITE_NAME,
            "session_user": None,
        },
    )


@app.get("/guide/{category_id}/{index}/view", response_class=HTMLResponse)
async def guide_view_page(request: Request, category_id: str, index: int):
    user = _get_session_user(request)
    guides = load_guides()
    category = guides.get(category_id)
    if not category or index < 0 or index >= len(category.get("guide", [])):
        return JSONResponse({"detail": "Not found"}, status_code=404)
    guide = category["guide"][index]

    if user is None and (category.get("is_hidden", False) or guide.get("is_hidden", False)):
        return JSONResponse({"detail": "Not found"}, status_code=404)

    return templates.TemplateResponse(
        "guide_view.html",
        {
            "request": request,
            "category": category,
            "category_id": category_id,
            "index": index,
            "guide": guide,
            "site_name": SITE_NAME,
            "session_user": user,
        },
    )


@app.post("/guide/{category_id}/save")
async def guide_save(request: Request, category_id: str, index: str = Form(default="new"),
                     title: str = Form(...), text: str = Form(...),
                     url: str = Form(default=""), url_label: str = Form(default=""),
                     show_bot_links: bool = Form(default=False),
                     is_hidden: bool = Form(default=False),
                     sort_order: int = Form(default=0),
                     row_number: int = Form(default=1),
                     photo_remove: str = Form(default=""),
                     photo: UploadFile = File(default=None)):
    if _get_session_user(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    guides = load_guides()
    if category_id not in guides:
        return RedirectResponse(url="/", status_code=303)

    new_guide = {
        "title": title.strip(),
        "text": text,
        "is_hidden": is_hidden,
        "sort_order": sort_order,
        "row_number": row_number,
    }
    if url.strip():
        new_guide["url"] = url.strip()
        new_guide["url_label"] = url_label.strip() or "🔗 Открыть"
    if show_bot_links:
        new_guide["show_bot_links"] = True

    # --- Загрузка картинки (необязательно) ---
    # При редактировании сохраняем старую картинку, если новую не загрузили.
    old_photo = None
    if index and index != "new":
        try:
            old_photo = guides[category_id]["guide"][int(index)].get("photo")
        except (IndexError, KeyError, ValueError):
            old_photo = None

    if photo_remove == "1":
        new_guide["photo"] = None  # галочка «удалить картинку»
    elif photo is not None and photo.filename:
        ext = os.path.splitext(photo.filename or "")[1].lower() or ".jpg"
        allowed = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
        if ext not in allowed:
            ext = ".jpg"
        fname = f"{secrets.token_hex(8)}{ext}"
        dest = os.path.join(PHOTOS_DIR, fname)
        data = await photo.read()
        with open(dest, "wb") as f:
            f.write(data)
        # Храним относительный путь так же, как бот: media/photos/<имя>
        # с Unix-разделителями (кросс-платформенно).
        new_guide["photo"] = f"media/photos/{fname}"
    elif old_photo:
        new_guide["photo"] = old_photo

    if new_guide.get("photo") is None:
        new_guide.pop("photo", None)

    backup_guides()
    category = guides[category_id]
    if index and index != "new":
        try:
            idx = int(index)
            category["guide"][idx] = new_guide
        except (ValueError, IndexError):
            category["guide"].append(new_guide)
    else:
        category["guide"].append(new_guide)
    save_guides(guides)
    return RedirectResponse(url=f"/category/{category_id}", status_code=303)


@app.post("/guide/{category_id}/{index}/delete")
async def guide_delete(request: Request, category_id: str, index: int):
    if _get_session_user(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    guides = load_guides()
    category = guides.get(category_id)
    if category and 0 <= index < len(category["guide"]):
        category["guide"].pop(index)
        backup_guides()
        save_guides(guides)
    return RedirectResponse(url=f"/category/{category_id}", status_code=303)


# ---------- Сортировка (drag-and-drop) ----------
@app.post("/category/{category_id}/reorder")
async def category_reorder(request: Request, category_id: str):
    if _get_session_user(request) is None:
        return JSONResponse({"ok": False}, status_code=403)
    body = await request.json()
    order = body.get("order")
    if not isinstance(order, list):
        return JSONResponse({"ok": False}, status_code=400)
    guides = load_guides()
    category = guides.get(category_id)
    if not category:
        return JSONResponse({"ok": False}, status_code=404)
    # Переставляем guide согласно order (индексы новых позиций)
    guide_list = category["guide"]
    new_list = []
    for pos in order:
        pos = int(pos)
        if 0 <= pos < len(guide_list):
            new_list.append(guide_list[pos])
    # Если что-то потерялось/добавилось — добавляем остаток
    if len(new_list) != len(guide_list):
        existing = set(id(g) for g in new_list)
        for g in guide_list:
            if id(g) not in existing:
                new_list.append(g)
    category["guide"] = new_list
    backup_guides()
    save_guides(guides)
    return JSONResponse({"ok": True})


@app.post("/reorder_categories")
async def reorder_categories(request: Request):
    if _get_session_user(request) is None:
        return JSONResponse({"ok": False}, status_code=403)
    body = await request.json()
    order = body.get("order")
    if not isinstance(order, list):
        return JSONResponse({"ok": False}, status_code=400)
    guides = load_guides()
    keys = list(guides.keys())
    new_keys = []
    for key in order:
        key = str(key)
        if key in guides and key not in new_keys:
            new_keys.append(key)
    for key in keys:
        if key not in new_keys:
            new_keys.append(key)
    new_guides = {k: guides[k] for k in new_keys}
    backup_guides()
    save_guides(new_guides)
    return JSONResponse({"ok": True})


@app.post("/category/{category_id}/update_layout")
async def category_update_layout(request: Request, category_id: str):
    if _get_session_user(request) is None:
        return JSONResponse({"ok": False}, status_code=403)
    body = await request.json()
    guides = load_guides()
    if category_id not in guides:
        return JSONResponse({"ok": False}, status_code=404)

    if "row_number" in body:
        try:
            guides[category_id]["row_number"] = int(body["row_number"])
        except ValueError:
            pass
    if "sort_order" in body:
        try:
            guides[category_id]["sort_order"] = int(body["sort_order"])
        except ValueError:
            pass

    backup_guides()
    save_guides(guides)
    return JSONResponse({"ok": True})


@app.post("/category/{category_id}/guide/{index}/update_layout")
async def guide_update_layout(request: Request, category_id: str, index: int):
    if _get_session_user(request) is None:
        return JSONResponse({"ok": False}, status_code=403)
    body = await request.json()
    guides = load_guides()
    cat = guides.get(category_id)
    if not cat or index < 0 or index >= len(cat.get("guide", [])):
        return JSONResponse({"ok": False}, status_code=404)

    guide = cat["guide"][index]
    if "row_number" in body:
        try:
            guide["row_number"] = int(body["row_number"])
        except ValueError:
            pass
    if "sort_order" in body:
        try:
            guide["sort_order"] = int(body["sort_order"])
        except ValueError:
            pass

    backup_guides()
    save_guides(guides)
    return JSONResponse({"ok": True})
