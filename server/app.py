#!/usr/bin/env python3
"""VibeEmber's dependency-free, low-memory account and publishing API."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
import uuid
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from pathlib import Path
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs, urlparse
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server


BASE_PATH = os.environ.get("BASE_PATH", "/VibeEmber").rstrip("/")
DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).parent / "data")))
DB_PATH = Path(os.environ.get("DB_PATH", str(DATA_DIR / "vibe_ember.db")))
ADMIN_EMAIL = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "1") == "1"
SESSION_DAYS = 30
MAX_BODY = 32 * 1024
ALLOWED_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in os.environ.get("ALLOWED_ORIGINS", "https://wenxinxu.com").split(",")
    if origin.strip()
}
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
CATEGORIES = {"AI 工具", "微信小程序", "Web 应用", "移动 App", "教育", "生活方式", "浏览器插件", "其他"}
RATE_BUCKETS: dict[str, list[float]] = {}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.execute("PRAGMA journal_mode = WAL")
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('member', 'admin')),
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                csrf_token TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                tagline TEXT NOT NULL,
                url TEXT NOT NULL,
                category TEXT NOT NULL,
                help_needed TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
                rejection_reason TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                approved_at TEXT,
                reviewer_id TEXT REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS review_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                reviewer_id TEXT NOT NULL REFERENCES users(id),
                action TEXT NOT NULL CHECK (action IN ('approved', 'rejected')),
                reason TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
            CREATE INDEX IF NOT EXISTS idx_projects_owner_created ON projects(owner_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_projects_status_created ON projects(status, created_at DESC);
            """
        )
        db.execute("PRAGMA optimize")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    iterations = 310_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(actual.hex(), expected)
    except (ValueError, TypeError):
        return False


def json_response(start_response, data: dict | list, status: str = "200 OK", extra_headers=None):
    body = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "no-store"),
        ("X-Content-Type-Options", "nosniff"),
        ("X-Frame-Options", "SAMEORIGIN"),
        ("Referrer-Policy", "strict-origin-when-cross-origin"),
    ]
    if extra_headers:
        headers.extend(extra_headers)
    start_response(status, headers)
    return [body]


def read_json(environ) -> dict:
    content_type = environ.get("CONTENT_TYPE", "").split(";", 1)[0].strip().lower()
    if content_type != "application/json":
        raise ValueError("请使用 JSON 提交")
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError as exc:
        raise ValueError("无效的请求") from exc
    if length <= 0 or length > MAX_BODY:
        raise ValueError("请求内容过大或为空")
    try:
        value = json.loads(environ["wsgi.input"].read(length))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("无效的 JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("请求格式错误")
    return value


def clean_text(value, field: str, minimum: int, maximum: int) -> str:
    text = str(value or "").strip()
    if len(text) < minimum or len(text) > maximum:
        raise ValueError(f"{field}需要 {minimum}-{maximum} 个字符")
    return text


def request_ip(environ) -> str:
    forwarded = environ.get("HTTP_X_FORWARDED_FOR", "")
    return (forwarded.split(",", 1)[0] if forwarded else environ.get("REMOTE_ADDR", "unknown")).strip()


def rate_limited(key: str, limit: int = 12, window: int = 900) -> bool:
    current = time.time()
    attempts = [stamp for stamp in RATE_BUCKETS.get(key, []) if current - stamp < window]
    limited = len(attempts) >= limit
    if not limited:
        attempts.append(current)
    RATE_BUCKETS[key] = attempts
    return limited


def origin_allowed(environ) -> bool:
    origin = environ.get("HTTP_ORIGIN", "").rstrip("/")
    return not origin or origin in ALLOWED_ORIGINS


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def cookie_token(environ) -> str | None:
    cookie = SimpleCookie()
    try:
        cookie.load(environ.get("HTTP_COOKIE", ""))
        return cookie["vibe_session"].value if "vibe_session" in cookie else None
    except Exception:
        return None


def current_user(environ) -> tuple[sqlite3.Row | None, str | None]:
    token = cookie_token(environ)
    if not token:
        return None, None
    with connect() as db:
        row = db.execute(
            """
            SELECT users.id, users.email, users.name, users.role, sessions.csrf_token
            FROM sessions JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ? AND sessions.expires_at > ?
            """,
            (token_hash(token), now_iso()),
        ).fetchone()
    return (row, token) if row else (None, None)


def user_json(user: sqlite3.Row) -> dict:
    return {"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}


def create_session(user_id: str) -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(24)
    created = datetime.now(timezone.utc)
    expires = created + timedelta(days=SESSION_DAYS)
    with connect() as db:
        db.execute("DELETE FROM sessions WHERE expires_at <= ?", (now_iso(),))
        db.execute(
            "INSERT INTO sessions(token_hash, user_id, csrf_token, expires_at, created_at) VALUES(?,?,?,?,?)",
            (token_hash(token), user_id, csrf, expires.isoformat(timespec="seconds"), created.isoformat(timespec="seconds")),
        )
    return token, csrf


def session_cookie(token: str, clear: bool = False) -> str:
    parts = [f"vibe_session={'' if clear else token}", f"Path={BASE_PATH}/", "HttpOnly", "SameSite=Lax"]
    if COOKIE_SECURE:
        parts.append("Secure")
    parts.append("Max-Age=0" if clear else f"Max-Age={SESSION_DAYS * 86400}")
    return "; ".join(parts)


def csrf_valid(environ, user: sqlite3.Row) -> bool:
    supplied = environ.get("HTTP_X_CSRF_TOKEN", "")
    return bool(supplied) and hmac.compare_digest(supplied, user["csrf_token"])


def require_user(environ, start_response, admin=False):
    user, _ = current_user(environ)
    if not user:
        return None, json_response(start_response, {"error": "请先登录"}, "401 Unauthorized")
    if admin and user["role"] != "admin":
        return None, json_response(start_response, {"error": "需要管理员权限"}, "403 Forbidden")
    return user, None


def handle_register(environ, start_response):
    if not origin_allowed(environ):
        return json_response(start_response, {"error": "请求来源不被允许"}, "403 Forbidden")
    if rate_limited(f"register:{request_ip(environ)}"):
        return json_response(start_response, {"error": "操作太频繁，请稍后再试"}, "429 Too Many Requests")
    data = read_json(environ)
    email = str(data.get("email", "")).strip().lower()
    name = clean_text(data.get("name"), "昵称", 2, 30)
    password = str(data.get("password", ""))
    if not EMAIL_RE.match(email) or len(email) > 180:
        raise ValueError("请输入有效邮箱")
    if len(password) < 8 or len(password) > 128:
        raise ValueError("密码需要 8-128 个字符")
    user_id = str(uuid.uuid4())
    role = "admin" if ADMIN_EMAIL and email == ADMIN_EMAIL else "member"
    try:
        with connect() as db:
            db.execute(
                "INSERT INTO users(id,email,name,password_hash,role,created_at) VALUES(?,?,?,?,?,?)",
                (user_id, email, name, hash_password(password), role, now_iso()),
            )
    except sqlite3.IntegrityError:
        return json_response(start_response, {"error": "该邮箱已注册"}, "409 Conflict")
    token, csrf = create_session(user_id)
    return json_response(
        start_response,
        {"user": {"id": user_id, "email": email, "name": name, "role": role}, "csrfToken": csrf},
        "201 Created",
        [("Set-Cookie", session_cookie(token))],
    )


def handle_login(environ, start_response):
    if not origin_allowed(environ):
        return json_response(start_response, {"error": "请求来源不被允许"}, "403 Forbidden")
    ip = request_ip(environ)
    if rate_limited(f"login:{ip}"):
        return json_response(start_response, {"error": "尝试次数过多，请 15 分钟后再试"}, "429 Too Many Requests")
    data = read_json(environ)
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    with connect() as db:
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user or not verify_password(password, user["password_hash"]):
        time.sleep(0.25)
        return json_response(start_response, {"error": "邮箱或密码不正确"}, "401 Unauthorized")
    token, csrf = create_session(user["id"])
    return json_response(
        start_response,
        {"user": user_json(user), "csrfToken": csrf},
        extra_headers=[("Set-Cookie", session_cookie(token))],
    )


def project_json(row: sqlite3.Row, include_private=False) -> dict:
    data = {
        "id": row["id"], "name": row["name"], "tagline": row["tagline"], "url": row["url"],
        "category": row["category"], "helpNeeded": row["help_needed"], "status": row["status"],
        "createdAt": row["created_at"], "maker": row["maker_name"],
    }
    if include_private:
        data["rejectionReason"] = row["rejection_reason"]
        data["ownerEmail"] = row["owner_email"]
    return data


def handle_projects(environ, start_response):
    if environ["REQUEST_METHOD"] == "GET":
        with connect() as db:
            rows = db.execute(
                """
                SELECT projects.*, users.name AS maker_name, users.email AS owner_email
                FROM projects JOIN users ON users.id = projects.owner_id
                WHERE projects.status = 'approved' ORDER BY projects.approved_at DESC LIMIT 100
                """
            ).fetchall()
        return json_response(start_response, {"projects": [project_json(row) for row in rows]})

    user, error = require_user(environ, start_response)
    if error:
        return error
    if not origin_allowed(environ) or not csrf_valid(environ, user):
        return json_response(start_response, {"error": "安全校验失败，请刷新后重试"}, "403 Forbidden")
    data = read_json(environ)
    name = clean_text(data.get("name"), "产品名称", 2, 40)
    tagline = clean_text(data.get("tagline"), "一句话介绍", 6, 100)
    category = clean_text(data.get("category"), "产品类型", 2, 30)
    help_needed = clean_text(data.get("helpNeeded") or "征集真实体验与反馈", "所需帮助", 2, 300)
    url = str(data.get("url", "")).strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or len(url) > 500:
        raise ValueError("请输入有效的 HTTP(S) 产品链接")
    if category not in CATEGORIES:
        category = "其他"
    project_id = str(uuid.uuid4())
    created = now_iso()
    with connect() as db:
        db.execute(
            """INSERT INTO projects(id,owner_id,name,tagline,url,category,help_needed,status,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,'pending',?,?)""",
            (project_id, user["id"], name, tagline, url, category, help_needed, created, created),
        )
    return json_response(start_response, {"id": project_id, "status": "pending"}, "201 Created")


def handle_mine(environ, start_response):
    user, error = require_user(environ, start_response)
    if error:
        return error
    with connect() as db:
        rows = db.execute(
            """SELECT projects.*, users.name AS maker_name, users.email AS owner_email
            FROM projects JOIN users ON users.id = projects.owner_id
            WHERE projects.owner_id = ? ORDER BY projects.created_at DESC""",
            (user["id"],),
        ).fetchall()
    return json_response(start_response, {"projects": [project_json(row, True) for row in rows]})


def handle_admin_list(environ, start_response):
    user, error = require_user(environ, start_response, admin=True)
    if error:
        return error
    query = parse_qs(environ.get("QUERY_STRING", ""))
    status = query.get("status", ["pending"])[0]
    if status not in {"pending", "approved", "rejected"}:
        status = "pending"
    with connect() as db:
        rows = db.execute(
            """SELECT projects.*, users.name AS maker_name, users.email AS owner_email
            FROM projects JOIN users ON users.id = projects.owner_id
            WHERE projects.status = ? ORDER BY projects.created_at ASC LIMIT 200""",
            (status,),
        ).fetchall()
    return json_response(start_response, {"projects": [project_json(row, True) for row in rows]})


def handle_review(environ, start_response, project_id: str):
    user, error = require_user(environ, start_response, admin=True)
    if error:
        return error
    if not origin_allowed(environ) or not csrf_valid(environ, user):
        return json_response(start_response, {"error": "安全校验失败，请刷新后重试"}, "403 Forbidden")
    data = read_json(environ)
    action = str(data.get("action", ""))
    if action not in {"approved", "rejected"}:
        raise ValueError("审核操作无效")
    reason = str(data.get("reason", "")).strip()[:300]
    if action == "rejected" and len(reason) < 2:
        raise ValueError("驳回时请说明原因")
    updated = now_iso()
    with connect() as db:
        existing = db.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not existing:
            return json_response(start_response, {"error": "项目不存在"}, "404 Not Found")
        db.execute(
            """UPDATE projects SET status=?, rejection_reason=?, reviewer_id=?, updated_at=?,
            approved_at=CASE WHEN ?='approved' THEN ? ELSE NULL END WHERE id=?""",
            (action, reason if action == "rejected" else "", user["id"], updated, action, updated, project_id),
        )
        db.execute(
            "INSERT INTO review_audit(project_id,reviewer_id,action,reason,created_at) VALUES(?,?,?,?,?)",
            (project_id, user["id"], action, reason, updated),
        )
    return json_response(start_response, {"id": project_id, "status": action})


def application(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/").rstrip("/") or "/"
    try:
        if path == "/api/health" and method == "GET":
            return json_response(start_response, {"ok": True, "service": "vibe-ember-api"})
        if path == "/api/auth/register" and method == "POST":
            return handle_register(environ, start_response)
        if path == "/api/auth/login" and method == "POST":
            return handle_login(environ, start_response)
        if path == "/api/auth/me" and method == "GET":
            user, _ = current_user(environ)
            return json_response(start_response, {"user": user_json(user), "csrfToken": user["csrf_token"]} if user else {"user": None})
        if path == "/api/auth/logout" and method == "POST":
            user, token = current_user(environ)
            if user and csrf_valid(environ, user) and token:
                with connect() as db:
                    db.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash(token),))
            return json_response(start_response, {"ok": True}, extra_headers=[("Set-Cookie", session_cookie("", True))])
        if path == "/api/projects" and method in {"GET", "POST"}:
            return handle_projects(environ, start_response)
        if path == "/api/projects/mine" and method == "GET":
            return handle_mine(environ, start_response)
        if path == "/api/admin/projects" and method == "GET":
            return handle_admin_list(environ, start_response)
        review_match = re.fullmatch(r"/api/admin/projects/([0-9a-f-]{36})/review", path)
        if review_match and method == "POST":
            return handle_review(environ, start_response, review_match.group(1))
        return json_response(start_response, {"error": "接口不存在"}, "404 Not Found")
    except ValueError as exc:
        return json_response(start_response, {"error": str(exc)}, "400 Bad Request")
    except Exception:
        return json_response(start_response, {"error": "服务暂时异常"}, "500 Internal Server Error")


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class QuietHandler(WSGIRequestHandler):
    def log_message(self, fmt, *args):
        if os.environ.get("ACCESS_LOG", "0") == "1":
            super().log_message(fmt, *args)


if __name__ == "__main__":
    init_db()
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8790"))
    server = make_server(host, port, application, server_class=ThreadingWSGIServer, handler_class=QuietHandler)
    print(f"VibeEmber API listening on {host}:{port}", flush=True)
    server.serve_forever()
