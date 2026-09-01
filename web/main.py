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
from .auth import verify_telegram_auth, verify_telegram_webapp_init_data
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
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

logger = logging.getLogger("web")

_active_sessions: dict[str, int] = {}  # token -> telegram_id


def _set_session_cookie(response: Response, telegram_id: int) -> str:
    token = secrets.token_urlsafe(32)
    _active_sessions[token] = telegram_id
    response.set_cookie("session", token, max_age=60 * 60 * 24, httponly=True, samesite="lax")
    return token


def _get_session_user(request: Request) -> int | None:
    token = request.cookies.get("session")
    if not token and request.headers.get("authorization"):
        auth_header = request.headers.get("authorization") or ""
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if token and token in _active_sessions:
        uid = _active_sessions[token]
        if is_admin(uid):
            return uid
    return None


# ---------- REST API Endpoints ----------

@app.get("/api/config")
async def get_config(request: Request):
    user = _get_session_user(request)
    return {
        "site_name": SITE_NAME,
        "bot_username": BOT_USERNAME,
        "is_admin": user is not None,
        "user_id": user,
    }


@app.post("/api/auth/telegram-webapp")
async def auth_telegram_webapp(request: Request, response: Response):
    body = await request.json()
    init_data = body.get("initData", "")
    validated = verify_telegram_webapp_init_data(init_data)
    if not validated:
        return JSONResponse({"ok": False, "error": "Invalid Telegram Mini App initData or non-admin user"}, status_code=401)

    user_obj = validated.get("user_obj", {})
    user_id = user_obj.get("id")
    token = _set_session_cookie(response, user_id)
    return {"ok": True, "user": user_obj, "token": token}


@app.post("/api/auth/telegram-widget")
async def auth_telegram_widget(request: Request, response: Response):
    params = await request.json()
    if not verify_telegram_auth(params):
        return JSONResponse({"ok": False, "error": "Invalid auth signature"}, status_code=401)
    user_id = int(params["id"])
    token = _set_session_cookie(response, user_id)
    return {"ok": True, "user_id": user_id, "token": token}


@app.get("/api/auth/me")
async def auth_me(request: Request):
    user = _get_session_user(request)
    if user is None:
        return {"authenticated": False}
    return {"authenticated": True, "user_id": user}


@app.post("/api/auth/logout")
async def auth_logout(response: Response):
    response.delete_cookie("session")
    return {"ok": True}


@app.get("/api/stats/dashboard")
async def api_stats_dashboard(request: Request):
    user = _get_session_user(request)
    stats = count_stats()

    # Сбор последних элементов лога из analytics.log если есть
    recent_logs = []
    analytics_path = os.path.join(BASE_DIR, "..", "logs", "analytics.log")
    if os.path.exists(analytics_path):
        try:
            with open(analytics_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                recent_logs = [line.strip() for line in lines[-20:]]
                recent_logs.reverse()
        except OSError:
            pass

    return {
        "stats": stats,
        "is_admin": user is not None,
        "recent_logs": recent_logs,
    }


@app.get("/api/categories")
async def api_get_categories(request: Request):
    user = _get_session_user(request)
    guides = load_guides()

    # Сортируем категории по sort_order
    sorted_categories = sorted(
        guides.items(),
        key=lambda x: (x[1].get("sort_order", 0), x[0])
    )

    result = []
    for cid, cat in sorted_categories:
        is_hidden = cat.get("is_hidden", False)
        if user is None and is_hidden:
            continue

        raw_guides = cat.get("guide", [])
        guide_count = len([g for g in raw_guides if user is not None or not g.get("is_hidden", False)])

        result.append({
            "id": cid,
            "title": cat.get("title", ""),
            "is_hidden": is_hidden,
            "sort_order": cat.get("sort_order", 0),
            "row_number": cat.get("row_number", 1),
            "guide_count": guide_count,
        })

    return {"categories": result}


@app.get("/api/category/{category_id}")
async def api_get_category(request: Request, category_id: str):
    user = _get_session_user(request)
    guides = load_guides()
    if category_id not in guides:
        return JSONResponse({"error": "Category not found"}, status_code=404)

    cat = guides[category_id]
    if user is None and cat.get("is_hidden", False):
        return JSONResponse({"error": "Category not found"}, status_code=404)

    raw_guides = cat.get("guide", [])
    indexed_guides = []
    for idx, g in enumerate(raw_guides):
        is_h = g.get("is_hidden", False)
        if user is None and is_h:
            continue
        indexed_guides.append({
            "orig_idx": idx,
            "title": g.get("title", ""),
            "text": g.get("text", ""),
            "url": g.get("url"),
            "url_label": g.get("url_label"),
            "show_bot_links": g.get("show_bot_links", False),
            "photo": g.get("photo"),
            "is_hidden": is_h,
            "sort_order": g.get("sort_order", 0),
            "row_number": g.get("row_number", 1),
        })

    indexed_guides.sort(key=lambda x: (x.get("sort_order", 0), x["orig_idx"]))

    return {
        "id": category_id,
        "title": cat.get("title", ""),
        "is_hidden": cat.get("is_hidden", False),
        "sort_order": cat.get("sort_order", 0),
        "row_number": cat.get("row_number", 1),
        "guides": indexed_guides,
    }


@app.post("/api/categories")
async def api_add_category(request: Request):
    if _get_session_user(request) is None:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    body = await request.json()
    cid = str(body.get("id", "")).strip().lower().replace(" ", "_")
    title = str(body.get("title", "")).strip()
    is_hidden = bool(body.get("is_hidden", False))
    sort_order = int(body.get("sort_order", 0))
    row_number = int(body.get("row_number", 1))

    if not cid or not title:
        return JSONResponse({"error": "Invalid category ID or title"}, status_code=400)

    guides = load_guides()
    if cid in guides:
        return JSONResponse({"error": "Category ID already exists"}, status_code=400)

    guides[cid] = {
        "title": title,
        "is_hidden": is_hidden,
        "sort_order": sort_order,
        "row_number": row_number,
        "guide": [],
    }
    backup_guides()
    save_guides(guides)
    return {"ok": True, "id": cid}


@app.post("/api/categories/{category_id}/rename")
async def api_rename_category(request: Request, category_id: str):
    if _get_session_user(request) is None:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    body = await request.json()
    title = str(body.get("title", "")).strip()
    guides = load_guides()

    if category_id not in guides:
        return JSONResponse({"error": "Category not found"}, status_code=404)

    if title:
        guides[category_id]["title"] = title
    if "is_hidden" in body:
        guides[category_id]["is_hidden"] = bool(body["is_hidden"])
    if "sort_order" in body:
        guides[category_id]["sort_order"] = int(body["sort_order"])
    if "row_number" in body:
        guides[category_id]["row_number"] = int(body["row_number"])

    backup_guides()
    save_guides(guides)
    return {"ok": True}


@app.post("/api/categories/{category_id}/delete")
async def api_delete_category(request: Request, category_id: str):
    if _get_session_user(request) is None:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    guides = load_guides()
    if category_id in guides:
        del guides[category_id]
        backup_guides()
        save_guides(guides)
    return {"ok": True}


@app.get("/api/guides/{category_id}/{index}")
async def api_get_guide(request: Request, category_id: str, index: int):
    user = _get_session_user(request)
    guides = load_guides()
    cat = guides.get(category_id)
    if not cat or index < 0 or index >= len(cat.get("guide", [])):
        return JSONResponse({"error": "Guide not found"}, status_code=404)

    guide = cat["guide"][index]
    if user is None and (cat.get("is_hidden", False) or guide.get("is_hidden", False)):
        return JSONResponse({"error": "Guide not found"}, status_code=404)

    return {
        "category_id": category_id,
        "category_title": cat.get("title", ""),
        "index": index,
        "guide": guide,
    }


@app.post("/api/guides/{category_id}/save")
async def api_save_guide(
    request: Request,
    category_id: str,
    index: str = Form(default="new"),
    title: str = Form(...),
    text: str = Form(...),
    url: str = Form(default=""),
    url_label: str = Form(default=""),
    show_bot_links: bool = Form(default=False),
    is_hidden: bool = Form(default=False),
    sort_order: int = Form(default=0),
    row_number: int = Form(default=1),
    photo_remove: str = Form(default=""),
    photo: UploadFile = File(default=None)
):
    if _get_session_user(request) is None:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    guides = load_guides()
    if category_id not in guides:
        return JSONResponse({"error": "Category not found"}, status_code=404)

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

    old_photo = None
    if index and index != "new":
        try:
            old_photo = guides[category_id]["guide"][int(index)].get("photo")
        except (IndexError, KeyError, ValueError):
            old_photo = None

    if photo_remove == "1":
        new_guide["photo"] = None
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
        new_guide["photo"] = f"media/photos/{fname}"
    elif old_photo:
        new_guide["photo"] = old_photo

    if new_guide.get("photo") is None:
        new_guide.pop("photo", None)

    backup_guides()
    cat = guides[category_id]
    if index and index != "new":
        try:
            idx = int(index)
            cat["guide"][idx] = new_guide
        except (ValueError, IndexError):
            cat["guide"].append(new_guide)
    else:
        cat["guide"].append(new_guide)

    save_guides(guides)
    return {"ok": True, "category_id": category_id}


@app.post("/api/guides/{category_id}/{index}/delete")
async def api_delete_guide(request: Request, category_id: str, index: int):
    if _get_session_user(request) is None:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    guides = load_guides()
    cat = guides.get(category_id)
    if cat and 0 <= index < len(cat.get("guide", [])):
        cat["guide"].pop(index)
        backup_guides()
        save_guides(guides)
    return {"ok": True}


# Монтируем статические файлы собранного SPA-приложения (dist/)
FRONTEND_DIST_DIR = os.path.join(BASE_DIR, "..", "frontend", "dist")
if os.path.exists(FRONTEND_DIST_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Исключаем служебные эндпоинты
        if full_path.startswith("api/") or full_path.startswith("media/"):
            return JSONResponse({"error": "Not found"}, status_code=404)
        index_file = os.path.join(FRONTEND_DIST_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return JSONResponse({"error": "Frontend dist index.html not found"}, status_code=404)


# Legacy Jinja2 HTML routes removed in favor of pure SPA serving from frontend/dist
