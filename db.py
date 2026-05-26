"""
db.py — SQLite-backed User Management for TeleCloud-Downloader (multi-tenant).

Schema
------
users(
    user_id          INTEGER PRIMARY KEY,
    is_approved      INTEGER  NOT NULL DEFAULT 0,   -- 0 = False, 1 = True
    files_downloaded INTEGER  NOT NULL DEFAULT 0,
    bytes_downloaded INTEGER  NOT NULL DEFAULT 0,
    last_active_date TEXT,                           -- 'YYYY-MM-DD'; NULL = never active
    custom_quota_files INTEGER,                      -- NULL → use global MAX_DAILY_FILES
    custom_quota_bytes INTEGER,                      -- NULL → use global MAX_DAILY_BYTES
    default_quality  TEXT     NOT NULL DEFAULT '720',
    audio_mode       INTEGER  NOT NULL DEFAULT 0    -- 0 = False, 1 = True
)
"""

import sqlite3
import threading
from datetime import date
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# Database path — stored alongside the bot's config area so it
# survives Docker volume mounts exactly like user_configs.
# ──────────────────────────────────────────────────────────────
DB_PATH = "/app/user_configs/telecloud.db"

_local = threading.local()       # Per-thread connection
_db_lock = threading.Lock()      # Used only for DDL (CREATE TABLE)


def _get_conn() -> sqlite3.Connection:
    """Return a thread-local SQLite connection (auto-created on first use)."""
    if not hasattr(_local, "conn") or _local.conn is None:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.conn = conn
    return _local.conn


def init_db() -> None:
    """Create tables if they don't already exist. Call once at startup."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with _db_lock:
        conn = _get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id          INTEGER PRIMARY KEY,
                is_approved      INTEGER  NOT NULL DEFAULT 0,
                files_downloaded INTEGER  NOT NULL DEFAULT 0,
                bytes_downloaded INTEGER  NOT NULL DEFAULT 0,
                last_active_date TEXT,
                custom_quota_files INTEGER,
                custom_quota_bytes INTEGER,
                default_quality  TEXT    NOT NULL DEFAULT '720',
                audio_mode       INTEGER  NOT NULL DEFAULT 0
            )
        """)
        conn.commit()


# ──────────────────────────────────────────────────────────────
# CRUD helpers
# ──────────────────────────────────────────────────────────────

def add_user(user_id: int, approved: bool = False) -> None:
    """Insert a new user (no-op if already exists)."""
    conn = _get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id, is_approved) VALUES (?, ?)",
        (user_id, int(approved)),
    )
    conn.commit()


def approve_user(user_id: int) -> None:
    """Mark a user as approved (creates row if missing)."""
    conn = _get_conn()
    conn.execute(
        "INSERT INTO users (user_id, is_approved) VALUES (?, 1) "
        "ON CONFLICT(user_id) DO UPDATE SET is_approved=1",
        (user_id,),
    )
    conn.commit()


def reject_user(user_id: int) -> None:
    """Mark a user as NOT approved (creates row if missing)."""
    conn = _get_conn()
    conn.execute(
        "INSERT INTO users (user_id, is_approved) VALUES (?, 0) "
        "ON CONFLICT(user_id) DO UPDATE SET is_approved=0",
        (user_id,),
    )
    conn.commit()


def delete_user(user_id: int) -> None:
    """Completely remove a user from the database."""
    conn = _get_conn()
    conn.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    conn.commit()


def get_user(user_id: int) -> sqlite3.Row | None:
    """Return the users row for *user_id*, or None if not found."""
    conn = _get_conn()
    return conn.execute(
        "SELECT * FROM users WHERE user_id=?", (user_id,)
    ).fetchone()


def is_approved(user_id: int) -> bool:
    """Return True if the user exists and is_approved == 1."""
    row = get_user(user_id)
    return bool(row and row["is_approved"])


def get_all_approved_users() -> list[int]:
    """Return a list of user_ids for all approved users."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT user_id FROM users WHERE is_approved=1"
    ).fetchall()
    return [r["user_id"] for r in rows]


# ──────────────────────────────────────────────────────────────
# Quota / VIP helpers
# ──────────────────────────────────────────────────────────────

def set_custom_quota(user_id: int, files: int | None, bytes_: int | None) -> None:
    """Set per-user (VIP) quota. Pass None to clear a custom limit."""
    conn = _get_conn()
    conn.execute(
        "INSERT INTO users (user_id, custom_quota_files, custom_quota_bytes) VALUES (?, ?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET custom_quota_files=excluded.custom_quota_files, "
        "custom_quota_bytes=excluded.custom_quota_bytes",
        (user_id, files, bytes_),
    )
    conn.commit()


# ──────────────────────────────────────────────────────────────
# Settings helpers
# ──────────────────────────────────────────────────────────────

def update_setting(user_id: int, key: str, value) -> None:
    """Update a single column on the users row (key must be a valid column name)."""
    _ALLOWED = {"default_quality", "audio_mode"}
    if key not in _ALLOWED:
        raise ValueError(f"update_setting: unknown key '{key}'")
    conn = _get_conn()
    conn.execute(
        f"INSERT INTO users (user_id, {key}) VALUES (?, ?) "
        f"ON CONFLICT(user_id) DO UPDATE SET {key}=excluded.{key}",
        (user_id, value),
    )
    conn.commit()


# ──────────────────────────────────────────────────────────────
# Quota gate — called before every download
# ──────────────────────────────────────────────────────────────

def check_and_update_quota(
    user_id: int,
    file_size_bytes: int,
) -> tuple[bool, str]:
    """
    Check whether *user_id* is within their daily quota.

    Behaviour
    ---------
    • If ``current_date > last_active_date``, counters reset automatically
      (daily quota renewal).
    • If the user is not yet in the DB, they are inserted with 0 counters.
    • Limits are read from the users row first (custom VIP quota) and fall
      back to ``config.MAX_DAILY_FILES`` / ``config.MAX_DAILY_BYTES``.

    Returns
    -------
    (allowed: bool, reason: str)
        *allowed* is True when the download may proceed.
        *reason* is an empty string on success, or a Persian error message.
    """
    from config import MAX_DAILY_FILES, MAX_DAILY_BYTES  # avoid circular at module load

    today_str = date.today().isoformat()      # 'YYYY-MM-DD'
    conn = _get_conn()

    row = conn.execute(
        "SELECT * FROM users WHERE user_id=?", (user_id,)
    ).fetchone()

    if row is None:
        # New user — insert bare row then re-fetch
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,)
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM users WHERE user_id=?", (user_id,)
        ).fetchone()

    # ── Daily reset ───────────────────────────────────────────
    last_date = row["last_active_date"] or ""
    if last_date != today_str:
        conn.execute(
            "UPDATE users SET files_downloaded=0, bytes_downloaded=0, "
            "last_active_date=? WHERE user_id=?",
            (today_str, user_id),
        )
        conn.commit()
        # Re-read fresh counters (now 0)
        row = conn.execute(
            "SELECT * FROM users WHERE user_id=?", (user_id,)
        ).fetchone()

    # ── Resolve limits ────────────────────────────────────────
    max_files = row["custom_quota_files"] if row["custom_quota_files"] is not None else MAX_DAILY_FILES
    max_bytes = row["custom_quota_bytes"] if row["custom_quota_bytes"] is not None else MAX_DAILY_BYTES

    files_used = row["files_downloaded"]
    bytes_used = row["bytes_downloaded"]

    # ── Gate checks ───────────────────────────────────────────
    if files_used >= max_files:
        return False, (
            f"❌ سقف روزانه شما پر شده است.\n"
            f"📥 دانلودها: {files_used}/{max_files}\n"
            f"فردا دوباره امتحان کنید."
        )

    if bytes_used + file_size_bytes > max_bytes:
        from utils import fmt_size  # lazy import
        return False, (
            f"❌ حجم دانلود روزانه شما تمام شده است.\n"
            f"💾 مصرف: {fmt_size(bytes_used)} / {fmt_size(max_bytes)}\n"
            f"فردا دوباره امتحان کنید."
        )

    # ── Update counters ───────────────────────────────────────
    conn.execute(
        "UPDATE users SET files_downloaded=files_downloaded+1, "
        "bytes_downloaded=bytes_downloaded+?, last_active_date=? "
        "WHERE user_id=?",
        (file_size_bytes, today_str, user_id),
    )
    conn.commit()
    return True, ""


# ──────────────────────────────────────────────────────────────
# Post-download byte accounting
# ──────────────────────────────────────────────────────────────

def record_download_bytes(user_id: int, file_size_bytes: int) -> None:
    """
    Increment bytes_downloaded by the *actual* size of a completed file.

    Called after a successful download once the file is on disk and its
    real size is known via os.path.getsize().  Intentionally separate from
    check_and_update_quota so the pre-download gate can run at enqueue time
    (before the size is known) while byte accounting is still accurate.

    No-op if user_id is not in the database (admin bypass path).
    """
    if file_size_bytes <= 0:
        return
    conn = _get_conn()
    conn.execute(
        "UPDATE users SET bytes_downloaded=bytes_downloaded+? WHERE user_id=?",
        (file_size_bytes, user_id),
    )
    conn.commit()
