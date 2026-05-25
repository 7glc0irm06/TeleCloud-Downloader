import os
import re
import subprocess
import time
import html
from pathlib import Path

from config import bot, stop_event, DRIVE_FOLDER_ID, USER_CONFIGS_DIR
from utils import build_rich_progress_card, cleanup_path, fmt_size

# ──────────────────────────────────────────────────────────────
# Per-user rclone config resolution
# ──────────────────────────────────────────────────────────────
DEFAULT_RCLONE_CONF = "/root/.config/rclone/rclone.conf"


def _user_config_path(user_id: int) -> Path:
    """Return the per-user rclone config path (may not exist)."""
    return Path(USER_CONFIGS_DIR) / f"rclone_{user_id}.conf"


def get_rclone_config_args(user_id: int | None) -> list[str]:
    """
    Return the rclone --config flag list appropriate for `user_id`.

    Priority:
      1. /app/user_configs/rclone_<user_id>.conf   (user connected their Drive)
      2. /root/.config/rclone/rclone.conf           (system-wide / admin config)

    Raises RuntimeError if neither config file exists.
    """
    if user_id is not None:
        user_conf = _user_config_path(user_id)
        if user_conf.exists():
            return ["--config", str(user_conf)]

    default_conf = Path(DEFAULT_RCLONE_CONF)
    if default_conf.exists():
        return ["--config", str(default_conf)]

    raise RuntimeError(
        "No rclone config found. "
        "Please connect your Google Drive first by running the Colab script "
        "and sending the generated rclone.conf to the bot."
    )

# ──────────────────────────────────────────────────────────────
# Source → Google Drive folder name mapping
# ──────────────────────────────────────────────────────────────
SOURCE_FOLDER_MAP = {
    'youtube':          'YouTube',
    'youtube playlist': 'YouTube',
    'soundcloud':       'SoundCloud',
    'twitter':          'Twitter',
    'x':                'Twitter',
    'instagram':        'Instagram',
    'tiktok':           'TikTok',
    'vimeo':            'Vimeo',
    'twitch':           'Twitch',
    'reddit':           'Reddit',
    'facebook':         'Facebook',
    'torrent':          'Torrent',
    'direct':           'Direct',
    'direct link':      'Direct',
    'telegram':         'Telegram',
    'ناشناس':           'Other',
    'other':            'Other',
}

def _source_to_folder(source: str) -> str:
    key = (source or '').lower().strip()
    return SOURCE_FOLDER_MAP.get(key, 'Other')

def _to_direct_download_link(link: str) -> str:
    if not link:
        return link
    m = re.search(r'/file/d/([a-zA-Z0-9_-]+)', link)
    if m:
        file_id = m.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    m2 = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', link)
    if m2:
        file_id = m2.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    if 'export=download' in link:
        return link
    return link

def _cancel_markup(cid=None):
    from telebot import types
    from locales import t
    m = types.InlineKeyboardMarkup()
    label = t(cid, 'cancel_btn') if cid else "❌ لغو"
    m.add(types.InlineKeyboardButton(label, callback_data="cancel_task"))
    return m

def parse_rclone_speed(s):
    if not s: return 0
    s = s.upper()
    mul = 1
    if 'G' in s: mul = 1024**3
    elif 'M' in s: mul = 1024**2
    elif 'K' in s: mul = 1024
    val = re.sub(r'[^\d.]', '', s)
    return float(val) * mul if val else 0

def parse_rclone_eta(s):
    if not s: return 0
    h  = re.search(r'(\d+)h', s)
    m  = re.search(r'(\d+)m', s)
    sc = re.search(r'(\d+)s', s)
    eta = 0
    if h:  eta += int(h.group(1))  * 3600
    if m:  eta += int(m.group(1))  * 60
    if sc: eta += int(sc.group(1))
    return eta

def upload_to_gdrive_cancellable(
    path: str,
    status_msg,
    folder_name=None,
    is_folder=False,
    task_info=None,
    user_id: int | None = None,
):
    from locales import t
    import config

    if task_info is None:
        task_info = {}

    chat_id = status_msg.chat.id
    cid     = chat_id
    # Prefer explicit user_id; fall back to chat_id (1:1 chats only)
    uid     = user_id if user_id is not None else chat_id
    source  = task_info.get('source', 'Other')
    quality = task_info.get('quality', '')
    title   = task_info.get('title', os.path.basename(path))

    source_folder = _source_to_folder(source)

    if folder_name:
        drive_dest = f"gdrive:BotDownloader/{source_folder}/{folder_name}"
    else:
        drive_dest = f"gdrive:BotDownloader/{source_folder}"

    if not is_folder:
        total_size = os.path.getsize(path)
    else:
        total_size = sum(
            os.path.getsize(os.path.join(d, f))
            for d, _, fs in os.walk(path) for f in fs
        )

    # ── Resolve rclone config (raises RuntimeError if none found) ──────────
    try:
        config_args = get_rclone_config_args(uid)
    except RuntimeError as cfg_err:
        try:
            bot.edit_message_text(f"❌ {cfg_err}", chat_id, status_msg.message_id)
        except Exception:
            bot.send_message(chat_id, f"❌ {cfg_err}")
        cleanup_path(path)
        return
    # ───────────────────────────────────────────────────────────────────────

    try:
        card = build_rich_progress_card(
            "☁️", title, 0, 0, total_size, 0, 0, source, quality, cid=cid)
        bot.edit_message_text(
            card, chat_id, status_msg.message_id,
            reply_markup=_cancel_markup(cid))
    except Exception:
        pass

    cmd = [
        "rclone", "move", path, drive_dest,
        "--drive-root-folder-id", DRIVE_FOLDER_ID,
        "--progress",
    ] + config_args

    config.rclone_process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding='utf-8', errors='replace')

    last_update = time.time()

    while True:
        if stop_event.is_set():
            config.rclone_process.terminate()
            config.rclone_process = None
            cleanup_path(path)
            try:
                bot.edit_message_text(
                    t(cid, 'upload_cancelled'), chat_id, status_msg.message_id)
            except Exception:
                pass
            return

        line = config.rclone_process.stdout.readline()
        if not line and config.rclone_process.poll() is not None:
            break

        if time.time() - last_update > 4:
            m_pct = re.search(r'(\d+)%', line)
            m_spd = re.search(r',\s*([\d.]+\s*[a-zA-Z]+/s)', line)
            m_eta = re.search(r'ETA\s+([0-9hms]+)', line)

            if m_pct:
                pct        = float(m_pct.group(1))
                spd_raw    = m_spd.group(1) if m_spd else ""
                eta_raw    = m_eta.group(1) if m_eta else ""
                speed      = parse_rclone_speed(spd_raw)
                eta        = parse_rclone_eta(eta_raw)
                downloaded = (pct / 100.0) * total_size

                card = build_rich_progress_card(
                    "☁️", title, pct, downloaded, total_size,
                    speed, eta, source, quality, cid=cid)
                try:
                    bot.edit_message_text(
                        card, chat_id, status_msg.message_id,
                        reply_markup=_cancel_markup(cid))
                except Exception:
                    pass
                last_update = time.time()

    ret = config.rclone_process.wait()
    config.rclone_process = None
    cleanup_path(path)

    name = os.path.basename(path)

    if ret == 0:
        try:
            bot.edit_message_text(
                t(cid, 'getting_gdrive_link'),
                chat_id, status_msg.message_id)
        except Exception:
            pass

        try:
            if is_folder:
                remote_file_path = drive_dest
            else:
                remote_file_path = drive_dest.rstrip('/') + '/' + name

            # Retrieve file ID via lsjson (faster, no timeout issues)
            direct_link = None
            raw_link    = None
            lj = subprocess.run(
                ["rclone", "lsjson", remote_file_path,
                 "--drive-root-folder-id", DRIVE_FOLDER_ID] + config_args,
                capture_output=True, text=True, timeout=30)
            if lj.returncode == 0 and lj.stdout.strip():
                import json as _json
                try:
                    items = _json.loads(lj.stdout)
                    if items and items[0].get('ID'):
                        file_id     = items[0]['ID']
                        direct_link = f"https://drive.google.com/uc?export=download&id={file_id}"
                except Exception:
                    pass
            # Fallback: rclone link
            if not direct_link:
                lr = subprocess.run(
                    ["rclone", "link", remote_file_path,
                     "--drive-root-folder-id", DRIVE_FOLDER_ID] + config_args,
                    capture_output=True, text=True, timeout=60)
                raw_link    = lr.stdout.strip() if lr.returncode == 0 else None
                direct_link = _to_direct_download_link(raw_link) if raw_link else None

            safe_title     = html.escape(title)
            folder_display = f"BotDownloader/{source_folder}" + (f"/{folder_name}" if folder_name else "")

            final_txt = t(cid, 'gdrive_upload_done',
                          title=safe_title,
                          size=fmt_size(total_size),
                          source=source,
                          quality=quality,
                          folder=html.escape(folder_display))
            if direct_link:
                final_txt += t(cid, 'gdrive_direct_link', link=direct_link)
            elif raw_link:
                final_txt += t(cid, 'gdrive_view_link', link=raw_link)
            else:
                final_txt += t(cid, 'gdrive_link_error')

            try:
                bot.edit_message_text(
                    final_txt, chat_id, status_msg.message_id,
                    parse_mode='HTML', disable_web_page_preview=True)
            except Exception:
                bot.send_message(
                    chat_id, final_txt,
                    parse_mode='HTML', disable_web_page_preview=True)

        except Exception as e:
            try:
                bot.edit_message_text(
                    t(cid, 'gdrive_upload_fallback', name=name, e=e),
                    chat_id, status_msg.message_id)
            except Exception:
                pass
    else:
        try:
            bot.edit_message_text(
                t(cid, 'gdrive_upload_error'), chat_id, status_msg.message_id)
        except Exception:
            pass

def upload_file_to_gdrive_folder(
    file_path: str,
    status_msg,
    folder_name="Telegram",
    task_info=None,
    user_id: int | None = None,
):
    if task_info is None:
        task_info = {}
    if 'source' not in task_info:
        task_info['source'] = 'Telegram'
    upload_to_gdrive_cancellable(
        file_path, status_msg,
        folder_name=folder_name,
        task_info=task_info,
        user_id=user_id,
    )
