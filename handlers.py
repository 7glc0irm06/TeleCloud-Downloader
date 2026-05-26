import os
import html
from pathlib import Path
from downloader_queue import enqueue as _raw_enqueue
import re
import threading
import yt_dlp
from telebot import types
from urllib.parse import urlparse

import config
from config import (bot, cache_lock, url_cache,
                    user_state, ADMIN_ID, REGISTRATION_OPEN,
                    USER_CONFIGS_DIR)

import db
from cookies import (active_cookies_file, save_cookie_data,
                     cookie_exists, is_cookie_enabled,
                     get_cookie_path, _cookies_state, _save_cookies_state)
from utils import clean_url, get_free_space, fmt_size, friendly_error
from menu import main_menu_markup, cookie_list_markup, cancel_markup
from dest_helpers import (get_dest, should_ask_dest, get_quality,
                          get_quality_label, is_audio_mode, get_audio_mode_label,
                          get_audio_format, get_audio_quality, get_video_format,
                          get_subtitle, get_chapters)
from downloaders.youtube import get_format_sizes
from uploaders.gdrive_upload import upload_file_to_gdrive_folder
from downloaders.social import _is_ytdlp_url
from locales import t
from user_langs import get_lang, has_lang, set_lang


# =============================================================
# Quota-aware enqueue wrapper
# =============================================================
def enqueue(task: dict):
    """
    Wrap _raw_enqueue with a quota check.
    - Admin always bypasses.
    - For regular users: call db.check_and_update_quota.
      If denied, send an error to the chat and do NOT enqueue.
    The file_size_bytes estimate is 0 at enqueue time; the real
    size accounting happens inside the downloader after download.
    """
    cid = task.get('chat_id')
    if cid == ADMIN_ID:
        return _raw_enqueue(task)

    allowed, reason = db.check_and_update_quota(cid, file_size_bytes=0)
    if not allowed:
        try:
            bot.send_message(cid, reason)
        except Exception:
            pass
        return None
    return _raw_enqueue(task)


YT_FMT_MAP = {
    '1080': ('bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best', False),
    '720':  ('bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best',  False),
    '480':  ('bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best',  False),
    'best': ('bestvideo+bestaudio/best', False),
}

YT_LABELS = {
    '1080': '1080p', '720': '720p', '480': '480p',
    'best': '⭐ بهترین',
}

# Tracks pending join requests to avoid duplicate admin notifications
_pending_join_requests: set = set()


# =============================================================
# /start
# =============================================================
@bot.message_handler(commands=['start'])
def start(message):
    cid = message.chat.id

    # Language picker first
    if not has_lang(cid):
        mk = types.InlineKeyboardMarkup()
        mk.row(
            types.InlineKeyboardButton("English", callback_data="lang|en"),
            types.InlineKeyboardButton("فارسی",   callback_data="lang|fa"),
        )
        bot.send_message(cid, t(cid, 'lang_select'), reply_markup=mk)
        return

    # Admin always has full access
    if cid == ADMIN_ID:
        db.add_user(cid, approved=True)
        user_state[cid] = None
        bot.send_message(cid, t(cid, 'bot_ready'), reply_markup=main_menu_markup(cid))
        return

    # Ensure user row exists
    db.add_user(cid, approved=REGISTRATION_OPEN)

    if db.is_approved(cid):
        user_state[cid] = None
        bot.send_message(cid, t(cid, 'bot_ready'), reply_markup=main_menu_markup(cid))
        return

    # Registration closed — show join-request button
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(
        t(cid, 'btn_request_access'),
        callback_data="joinreq|request",
    ))
    bot.send_message(cid, t(cid, 'registration_closed'), reply_markup=mk)


# =============================================================
# Admin command: /adduser <id>
# =============================================================
@bot.message_handler(commands=['adduser'])
def cmd_adduser(message):
    cid = message.chat.id
    if cid != ADMIN_ID:
        bot.reply_to(message, t(cid, 'admin_only'))
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, t(cid, 'admin_adduser_usage'))
        return
    try:
        uid = int(parts[1])
    except ValueError:
        bot.reply_to(message, t(cid, 'admin_adduser_usage'))
        return
    db.approve_user(uid)
    bot.reply_to(message, t(cid, 'admin_adduser_done', user_id=uid))
    # Notify the newly approved user
    try:
        bot.send_message(uid, t(uid, 'join_approved_user_notify'),
                         reply_markup=main_menu_markup(uid))
    except Exception:
        pass


# =============================================================
# Admin command: /deluser <id>
# =============================================================
@bot.message_handler(commands=['deluser'])
def cmd_deluser(message):
    cid = message.chat.id
    if cid != ADMIN_ID:
        bot.reply_to(message, t(cid, 'admin_only'))
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, t(cid, 'admin_deluser_usage'))
        return
    try:
        uid = int(parts[1])
    except ValueError:
        bot.reply_to(message, t(cid, 'admin_deluser_usage'))
        return
    db.delete_user(uid)
    bot.reply_to(message, t(cid, 'admin_deluser_done', user_id=uid))


# =============================================================
# Admin command: /setquota <id> <files> <GB>
# =============================================================
@bot.message_handler(commands=['setquota'])
def cmd_setquota(message):
    cid = message.chat.id
    if cid != ADMIN_ID:
        bot.reply_to(message, t(cid, 'admin_only'))
        return
    parts = message.text.split()
    if len(parts) < 4:
        bot.reply_to(message, t(cid, 'admin_setquota_usage'))
        return
    try:
        uid   = int(parts[1])
        files = int(parts[2])
        gb    = float(parts[3])
    except ValueError:
        bot.reply_to(message, t(cid, 'admin_setquota_usage'))
        return
    bytes_ = int(gb * 1024 ** 3)
    db.set_custom_quota(uid, files, bytes_)
    bot.reply_to(message, t(cid, 'admin_setquota_done',
                             user_id=uid, files=files, gb=gb))


# =============================================================
# Admin command: /togglereg
# =============================================================
@bot.message_handler(commands=['togglereg'])
def cmd_togglereg(message):
    cid = message.chat.id
    if cid != ADMIN_ID:
        bot.reply_to(message, t(cid, 'admin_only'))
        return
    config.REGISTRATION_OPEN = not config.REGISTRATION_OPEN
    status_key = 'admin_togglereg_open' if config.REGISTRATION_OPEN else 'admin_togglereg_closed'
    bot.reply_to(message,
                 t(cid, 'admin_togglereg_done', status=t(cid, status_key)))


# =============================================================
# Admin command: /broadcast <message>
# =============================================================
@bot.message_handler(commands=['broadcast'])
def cmd_broadcast(message):
    cid  = message.chat.id
    if cid != ADMIN_ID:
        bot.reply_to(message, t(cid, 'admin_only'))
        return
    text = message.text.partition(' ')[2].strip()
    if not text:
        bot.reply_to(message, t(cid, 'admin_broadcast_usage'))
        return
    users = db.get_all_approved_users()
    sent  = 0
    for uid in users:
        try:
            bot.send_message(uid, text)
            sent += 1
        except Exception:
            pass
    bot.reply_to(message, t(cid, 'admin_broadcast_done', count=sent))



# =============================================================
# Incoming files (cookies, upload to drive)
# =============================================================
@bot.message_handler(content_types=['document', 'video', 'audio', 'photo', 'voice', 'video_note'])
def handle_incoming_files(message):
    cid   = message.chat.id
    state = user_state.get(cid)

    if cid != ADMIN_ID and not db.is_approved(cid):
        bot.reply_to(message, t(cid, 'not_approved'))
        return

    # ── rclone.conf upload — multi-tenant Google Drive setup ──────────────
    if (
        message.content_type == 'document'
        and message.document.file_name == 'rclone.conf'
    ):
        _handle_rclone_conf_upload(message, cid)
        return
    # ─────────────────────────────────────────────────────────────────────

    if message.content_type == 'document' and message.document.file_name.endswith('.txt'):
        fname = message.document.file_name
        if state == 'await_cookie_file' or 'cookie' in fname.lower():
            try:
                info = bot.get_file(message.document.file_id)
                data = bot.download_file(info.file_path)
                base = os.path.splitext(fname)[0].lower()
                base = re.sub(r'[^a-zA-Z0-9_\-]', '_', base)
                if base in ('cookies', 'cookie', 'cookies_txt', ''):
                    with cache_lock:
                        url_cache[(cid, 'pending_cookie')] = data
                    user_state[cid] = 'await_cookie_name'
                    bot.reply_to(message, t(cid, 'cookie_received_ask_name'))
                else:
                    save_cookie_data(base, data)
                    user_state[cid] = None
                    bot.reply_to(message, t(cid, 'cookie_saved', name=base),
                                 reply_markup=main_menu_markup(cid))
            except Exception as e:
                bot.reply_to(message, t(cid, 'cookie_error', e=e))
            return

    if state == 'await_cookie_file':
        bot.reply_to(message, t(cid, 'cookie_need_txt'))
        return

    from config import DOWNLOAD_DIR
    status_msg = bot.reply_to(message, t(cid, 'receiving_file'))
    try:
        if message.content_type == 'document':
            fid, fname = message.document.file_id, message.document.file_name
        elif message.content_type == 'video':
            fid, fname = message.video.file_id, f"video_{message.video.file_id}.mp4"
        elif message.content_type == 'audio':
            fid = message.audio.file_id
            fname = getattr(message.audio, 'file_name', f"audio_{fid}.mp3")
        elif message.content_type == 'photo':
            fid, fname = message.photo[-1].file_id, f"photo_{message.photo[-1].file_id}.jpg"
        elif message.content_type == 'voice':
            fid, fname = message.voice.file_id, f"voice_{message.voice.file_id}.ogg"
        elif message.content_type == 'video_note':
            fid, fname = message.video_note.file_id, f"vidnote_{message.video_note.file_id}.mp4"
        else:
            bot.edit_message_text(t(cid, 'unsupported_type'), cid, status_msg.message_id)
            return

        info = bot.get_file(fid)
        file_path = info.file_path
        if file_path.startswith('/'):
            import shutil
            fp = os.path.join(DOWNLOAD_DIR, fname)
            shutil.copy2(file_path, fp)
        else:
            data = bot.download_file(file_path)
            fp   = os.path.join(DOWNLOAD_DIR, fname)
            with open(fp, 'wb') as f:
                f.write(data)
        upload_file_to_gdrive_folder(
            fp, status_msg, "FilesFromTel",
            user_id=message.from_user.id,
        )

    except Exception as e:
        text = f"❌ {friendly_error(str(e), cid=cid)}"
        try:
            bot.edit_message_text(text, cid, status_msg.message_id)
        except Exception:
            bot.send_message(cid, text)


# =============================================================
# rclone.conf handler — multi-tenant Google Drive onboarding
# =============================================================
def _handle_rclone_conf_upload(message, cid: int) -> None:
    """
    Persist a user-supplied rclone.conf to:
        /app/user_configs/rclone_<user_id>.conf

    The file is validated to contain the bare minimum rclone remote
    declaration before it is saved, so garbage files are rejected early.
    A Persian success message is sent on success; a descriptive error
    message is sent on any failure.
    """
    status_msg = bot.reply_to(message, "⏳ در حال پردازش فایل rclone.conf…")

    try:
        # Download the file from Telegram / local bot-api server
        file_info = bot.get_file(message.document.file_id)
        file_path = file_info.file_path

        if file_path.startswith('/'):
            # Local Bot-API server — file already on shared volume
            import shutil
            raw_data = Path(file_path).read_bytes()
        else:
            # Cloud Telegram servers
            raw_data = bot.download_file(file_path)

        conf_text = raw_data.decode('utf-8', errors='replace')

        # ── Basic sanity check ────────────────────────────────────────────
        if '[gdrive]' not in conf_text or 'type = drive' not in conf_text:
            bot.edit_message_text(
                "❌ فایل ارسالی معتبر نیست.\n"
                "لطفاً فایل <code>rclone.conf</code> را که از اسکریپت Colab دریافت کردید ارسال کنید.",
                cid,
                status_msg.message_id,
                parse_mode='HTML',
            )
            return

        # ── Persist ───────────────────────────────────────────────────────
        dest = os.path.join(USER_CONFIGS_DIR, f"rclone_{cid}.conf")
        with open(dest, 'w', encoding='utf-8') as f:
            f.write(conf_text)

        bot.edit_message_text(
            "✅ درایو شما با موفقیت متصل شد!\n"
            "فایل‌های شما از این به بعد در پوشه <b>TeleCloud-Downloads</b> ذخیره می‌شوند.",
            cid,
            status_msg.message_id,
            parse_mode='HTML',
        )

    except Exception as exc:
        try:
            bot.edit_message_text(
                f"❌ خطا در پردازش فایل: <code>{html.escape(str(exc))}</code>",
                cid,
                status_msg.message_id,
                parse_mode='HTML',
            )
        except Exception:
            bot.send_message(cid, f"❌ خطا: {exc}")


# =============================================================
# Main text message handler
# =============================================================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    cid   = message.chat.id
    text  = message.text.strip() if message.text else ""
    state = user_state.get(cid)

    # Auth gate (admins bypass, approved users pass, others are blocked)
    if cid != ADMIN_ID and not db.is_approved(cid):
        # Allow the language selection to pass through as a callback, not here
        bot.send_message(cid, t(cid, 'not_approved'))
        return

    if isinstance(state, str) and state.startswith('await_cookie_rename|'):
        old_name = state.split('|')[1]
        new_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', text).lower()
        if not new_name:
            bot.send_message(cid, t(cid, 'cookie_invalid_name'))
            return
        try:
            os.rename(get_cookie_path(old_name), get_cookie_path(new_name))
            st = _cookies_state()
            st[new_name] = st.pop(old_name, True)
            _save_cookies_state(st)
            user_state[cid] = None
            bot.send_message(cid, t(cid, 'cookie_rename_done', new_name=new_name),
                             reply_markup=main_menu_markup(cid))
        except Exception as e:
            bot.send_message(cid, t(cid, 'cookie_error', e=e))
        return

    if state == 'await_cookie_name':
        name = re.sub(r'[^a-zA-Z0-9_\-]', '_', text).lower()
        if not name:
            bot.send_message(cid, t(cid, 'cookie_invalid_name'))
            return
        with cache_lock:
            pending = url_cache.get((cid, 'pending_cookie'))
        if pending:
            save_cookie_data(name, pending if isinstance(pending, bytes) else pending.encode('utf-8'))
            with cache_lock:
                url_cache.pop((cid, 'pending_cookie'), None)
            user_state[cid] = None
            bot.send_message(cid, t(cid, 'cookie_saved', name=name), reply_markup=main_menu_markup(cid))
        else:
            bot.send_message(cid, t(cid, 'cookie_data_not_found'))
            user_state[cid] = None
        return

    if state == 'await_cookie_text':
        if "# Netscape" in text or "\t" in text:
            with cache_lock:
                url_cache[(cid, 'pending_cookie')] = text.encode('utf-8')
            user_state[cid] = 'await_cookie_name'
            bot.send_message(cid, t(cid, 'cookie_text_received'))
        else:
            bot.send_message(cid, t(cid, 'cookie_invalid_format'))
        return

    if isinstance(state, str) and state.startswith('await_playlist_count|'):
        _handle_playlist_count(cid, text, state)
        return

    if _handle_menu(cid, text, message):
        return

    if text.startswith(("http://", "https://")):
        text = clean_url(text)

    _handle_url(message, cid, text, state)


# =============================================================
# Menu dispatcher
# =============================================================
def _handle_menu(cid, text, message) -> bool:
    # Collect both FA and EN button labels so either language works
    if text in (t(cid, 'btn_settings'), "تنظیمات ⚙️", "Settings ⚙️"):
        from menu import settings_inline_markup
        user_state[cid] = None
        bot.send_message(cid, t(cid, 'settings_panel_title'),
                         reply_markup=settings_inline_markup(cid))
        return True

    # ── Profile button ────────────────────────────────────────
    if text in (t(cid, 'btn_profile'), "👤 پروفایل من", "👤 My Profile"):
        _send_profile_stats(cid)
        return True

    if text in (t(cid, 'btn_ytdlp'), "🔽 دانلود با yt-dlp", "🔽 Download with yt-dlp"):
        user_state[cid] = 'ytdlp'
        bot.send_message(cid, t(cid, 'ytdlp_activated'))
        return True

    if text in (t(cid, 'btn_torrent'), "🧲 دانلود تورنت", "🧲 Download Torrent"):
        user_state[cid] = 'torrent'
        bot.send_message(cid, t(cid, 'ask_magnet'))
        return True

    if text in (t(cid, 'btn_direct'), "🌐 دانلود لینک مستقیم", "🌐 Direct Link Download"):
        user_state[cid] = 'direct'
        bot.send_message(cid, t(cid, 'ask_direct'))
        return True

    if text in (t(cid, 'btn_cookie'), "🍪 مدیریت کوکی", "🍪 Cookie Manager"):
        user_state[cid] = None
        bot.send_message(cid, t(cid, 'cookie_manage'), reply_markup=cookie_list_markup(cid))
        return True

    if text in (t(cid, 'btn_queue'), "📊 وضعیت صف", "📊 Queue Status"):
        from downloader_queue import get_queue_items
        q_items = get_queue_items()
        with config.current_tasks_lock:
            active_tasks = list(config.current_tasks.values())
        lines   = []
        unknown = t(cid, 'queue_unknown')
        if active_tasks:
            for act in active_tasks:
                a_title = act.get('title') or act.get('url', unknown)
                lines.append(t(cid, 'queue_running', type=act['type'], title=a_title))
        else:
            lines.append(t(cid, 'queue_nothing_running'))
        if not q_items:
            lines.append(t(cid, 'queue_empty'))
            bot.send_message(cid, "\n".join(lines) + f"\n\n💾 {get_free_space()}")
        else:
            lines.append(t(cid, 'queue_waiting', count=len(q_items)))
            for i, item in enumerate(q_items):
                i_title = item.get('title') or item.get('url', unknown)
                lines.append(f"{i+1}. {item['type']} | {i_title}")
            markup = types.InlineKeyboardMarkup(row_width=5)
            btns = [types.InlineKeyboardButton(f"❌ {i+1}", callback_data=f"qrm|{i}") for i in range(len(q_items))]
            markup.add(*btns)
            markup.row(types.InlineKeyboardButton(t(cid, 'queue_clear_btn'), callback_data="qclear"))
            markup.row(types.InlineKeyboardButton(t(cid, 'queue_refresh_btn'), callback_data="qrefresh"))
            bot.send_message(cid, "\n".join(lines) + f"\n\n💾 {get_free_space()}", reply_markup=markup)
        return True

    if text in (t(cid, 'btn_cancel'), "❌ لغو عملیات فعلی", "❌ Cancel Current Task"):
        with config.current_tasks_lock:
            # Collect all tasks that belong to this user (multiple possible
            # if MAX_CONCURRENT_DOWNLOADS > 1 and this user queued several).
            my_tasks = [tk for tk in config.current_tasks.values()
                        if tk.get('chat_id') == cid]
        if my_tasks or config.rclone_process:
            for tk in my_tasks:
                tk['_stop'].set()
            if config.rclone_process:
                config.stop_event.set()  # rclone checks the global event
                try:
                    config.rclone_process.terminate()
                except Exception:
                    pass
            bot.send_message(cid, t(cid, 'cancel_requested'))
        else:
            bot.send_message(cid, t(cid, 'cancel_nothing'))
        return True

    if text in (t(cid, 'btn_help'), "ℹ️ راهنما", "ℹ️ Help"):
        bot.send_message(cid, t(cid, 'help_text'), reply_markup=main_menu_markup(cid))
        return True

    if text in (t(cid, 'btn_change_lang'), "تغییر زبان 🌐", "Change Language 🌐"):
        mk = types.InlineKeyboardMarkup()
        mk.row(
            types.InlineKeyboardButton("English", callback_data="lang|en"),
            types.InlineKeyboardButton("فارسی",   callback_data="lang|fa"),
        )
        bot.send_message(cid, t(cid, 'lang_select'), reply_markup=mk)
        return True

    return False


# =============================================================
# Link detection and routing
# =============================================================
def _handle_url(message, cid, text, state):
    cur = state
    if cur == 'ytdlp':
        if "youtube.com" in text or "youtu.be" in text:
            cur = 'youtube'
        elif text.startswith("magnet:?"):
            cur = 'torrent'
        elif text.startswith(("http://", "https://")):
            cur = 'social'
        else:
            bot.reply_to(message, t(cid, 'invalid_link'))
            return
    elif cur is None:
        if "youtube.com" in text or "youtu.be" in text:
            cur = 'youtube'
        elif text.startswith("magnet:?"):
            cur = 'torrent'
        elif text.startswith(("http://", "https://")):
            cur = 'social' if _is_ytdlp_url(text) else 'direct'
        else:
            bot.reply_to(message, t(cid, 'unknown_link'),
                         reply_markup=main_menu_markup(cid))
            return

    if cur == 'youtube':
        _handle_youtube_link(message, cid, text)
    elif cur == 'torrent':
        _handle_torrent_link(message, cid, text)
    elif cur == 'direct':
        _handle_direct_link(message, cid, text)
    elif cur == 'social':
        _handle_social_link(message, cid, text)


def _handle_youtube_link(message, cid, text):
    if "youtube.com" not in text and "youtu.be" not in text:
        bot.reply_to(message, t(cid, 'not_youtube'))
        return
    msg = bot.reply_to(message, t(cid, 'checking_link'))
    key = (cid, msg.message_id)
    with cache_lock:
        url_cache[key] = text
    opts = {'extract_flat': True, 'playlistend': 5, 'quiet': True, 'js_runtimes': {'node': {}}}
    cf   = active_cookies_file(text)
    if cf:
        opts['cookiefile'] = cf
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(text, download=False)

        unknown = t(cid, 'unknown_title')

        if 'entries' in info:
            count  = len(list(info['entries']))
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton(
                    t(cid, 'yt_playlist_label', count=count),
                    callback_data=f"yt|pl|{msg.message_id}"),
                types.InlineKeyboardButton(
                    t(cid, 'yt_playlist_mp3'),
                    callback_data=f"yt|pl_audio|{msg.message_id}"),
            )
            bot.edit_message_text(
                t(cid, 'yt_playlist_info', title=info.get('title', unknown), count=count),
                cid, msg.message_id, reply_markup=markup)
        else:
            audio   = is_audio_mode(cid)
            quality = 'manual' if audio else get_quality(cid)
            title   = info.get('title', unknown)
            dur     = info.get('duration', 0)
            m, s    = divmod(dur, 60)
            s_str   = f"{s:02d}"

            if audio:
                fmt, audio_only = 'bestaudio/best', True
                dest = get_dest(cid)
                if should_ask_dest(cid):
                    dest_mk = types.InlineKeyboardMarkup()
                    dest_mk.row(
                        types.InlineKeyboardButton(t(cid, 'btn_tg'), callback_data=f"ytd|audio|tg|{msg.message_id}"),
                        types.InlineKeyboardButton(t(cid, 'btn_gd'), callback_data=f"ytd|audio|gd|{msg.message_id}"),
                    )
                    bot.edit_message_text(
                        t(cid, 'yt_audio_dest_msg', title=title, m=m, s=s_str),
                        cid, msg.message_id, reply_markup=dest_mk)
                else:
                    enqueue({
                        'type': 'youtube', 'url': text, 'format': fmt,
                        'chat_id': cid, 'audio_only': True,
                        'dest': dest, 'title': title,
                        'audio_format':  get_audio_format(cid),
                        'audio_quality': get_audio_quality(cid),
                        'video_format':  get_video_format(cid),
                        'subtitle':      get_subtitle(cid),
                        'chapters':      get_chapters(cid),
                    })
                    pos = len(config.pending_queue)
                    bot.edit_message_text(
                        t(cid, 'yt_queued',
                          title=title, quality='🎵 MP3',
                          dest_icon='📱' if dest == 'tg' else '☁️',
                          pos=pos),
                        cid, msg.message_id)

            elif quality != 'manual':
                fmt, audio_only = YT_FMT_MAP[quality]
                dest = get_dest(cid)
                yt_label = YT_LABELS.get(quality, quality)
                if should_ask_dest(cid):
                    dest_mk = types.InlineKeyboardMarkup()
                    dest_mk.row(
                        types.InlineKeyboardButton(t(cid, 'btn_tg'), callback_data=f"ytd|{quality}|tg|{msg.message_id}"),
                        types.InlineKeyboardButton(t(cid, 'btn_gd'), callback_data=f"ytd|{quality}|gd|{msg.message_id}"),
                    )
                    bot.edit_message_text(
                        t(cid, 'yt_quality_dest_msg', title=title, m=m, s=s_str, quality=yt_label),
                        cid, msg.message_id, reply_markup=dest_mk)
                else:
                    enqueue({
                        'type': 'youtube', 'url': text, 'format': fmt,
                        'chat_id': cid, 'audio_only': audio_only,
                        'dest': dest, 'title': title,
                        'audio_format':  get_audio_format(cid),
                        'audio_quality': get_audio_quality(cid),
                        'video_format':  get_video_format(cid),
                        'subtitle':      get_subtitle(cid),
                        'chapters':      get_chapters(cid),
                    })
                    pos = len(config.pending_queue)
                    bot.edit_message_text(
                        t(cid, 'yt_queued',
                          title=title, quality=yt_label,
                          dest_icon='📱' if dest == 'tg' else '☁️',
                          pos=pos),
                        cid, msg.message_id)

            else:
                bot.edit_message_text(t(cid, 'fetching_quality'), cid, msg.message_id)
                sizes = get_format_sizes(text)

                def sz(k):
                    b = sizes.get(k, 0)
                    return f" ({fmt_size(b)})" if b else ""

                markup = types.InlineKeyboardMarkup()
                markup.row(
                    types.InlineKeyboardButton(f"1080p{sz(1080)}", callback_data=f"yt|1080|{msg.message_id}"),
                    types.InlineKeyboardButton(f"720p{sz(720)}",   callback_data=f"yt|720|{msg.message_id}"),
                    types.InlineKeyboardButton(f"480p{sz(480)}",   callback_data=f"yt|480|{msg.message_id}"),
                )
                markup.row(
                    types.InlineKeyboardButton(
                        f"{t(cid, 'best_quality')}{sz('best')}",
                        callback_data=f"yt|best|{msg.message_id}"),
                )
                bot.edit_message_text(
                    t(cid, 'select_quality', title=title, m=m, s=s_str),
                    cid, msg.message_id, reply_markup=markup)

    except Exception as e:
        bot.edit_message_text(f"❌ {friendly_error(str(e), cid=cid)}", cid, msg.message_id)


def _handle_torrent_link(message, cid, text):
    if not text.startswith("magnet:?"):
        bot.reply_to(message, t(cid, 'not_magnet'))
        return
    key = (cid, message.message_id)
    with cache_lock:
        url_cache[key] = text
    if not should_ask_dest(cid):
        enqueue({'type': 'torrent', 'url': text, 'chat_id': cid,
                 'dest': get_dest(cid)})
        dest_icon = '📱' if cid in config.tg_upload_mode else '☁️'
        bot.reply_to(message, t(cid, 'torrent_queued', dest_icon=dest_icon))
    else:
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton(t(cid, 'btn_tg'), callback_data=f"tr|tg|{message.message_id}"),
            types.InlineKeyboardButton(t(cid, 'btn_gd'), callback_data=f"tr|gd|{message.message_id}"),
        )
        bot.reply_to(message, t(cid, 'select_dest'), reply_markup=markup)


def _handle_direct_link(message, cid, text):
    key = (cid, message.message_id)
    with cache_lock:
        url_cache[key] = text
    if not should_ask_dest(cid):
        enqueue({'type': 'direct', 'url': text, 'chat_id': cid,
                 'dest': get_dest(cid)})
        dest_icon = '📱' if cid in config.tg_upload_mode else '☁️'
        bot.reply_to(message, t(cid, 'direct_queued', dest_icon=dest_icon))
    else:
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton(t(cid, 'btn_tg'), callback_data=f"dl|tg|{message.message_id}"),
            types.InlineKeyboardButton(t(cid, 'btn_gd'), callback_data=f"dl|gd|{message.message_id}"),
        )
        bot.reply_to(message, t(cid, 'select_dest'), reply_markup=markup)


def _handle_social_link(message, cid, text):
    domain = urlparse(text).netloc.replace('www.', '')
    msg    = bot.reply_to(message, t(cid, 'fetching_info', domain=domain))
    key    = (cid, msg.message_id)
    with cache_lock:
        url_cache[key] = text

    quality = get_quality(cid)
    audio   = is_audio_mode(cid)

    if audio:
        dest = get_dest(cid)
        if should_ask_dest(cid):
            dest_mk = types.InlineKeyboardMarkup()
            dest_mk.row(
                types.InlineKeyboardButton(t(cid, 'btn_tg'),
                    callback_data=f"scd|a|bestaudio/best|tg|{msg.message_id}"),
                types.InlineKeyboardButton(t(cid, 'btn_gd'),
                    callback_data=f"scd|a|bestaudio/best|gd|{msg.message_id}"),
            )
            try:
                bot.edit_message_text(
                    t(cid, 'social_audio_dest_msg', domain=domain),
                    cid, msg.message_id, reply_markup=dest_mk)
            except Exception:
                pass
        else:
            enqueue({
                'type': 'social', 'chat_id': cid, 'url': text,
                'dest': dest, 'format': 'bestaudio/best',
                'audio_only':    True,
                'audio_format':  get_audio_format(cid),
                'audio_quality': get_audio_quality(cid),
                'video_format':  get_video_format(cid),
                'subtitle':      get_subtitle(cid),
                'chapters':      get_chapters(cid),
            })
            try:
                bot.edit_message_text(
                    t(cid, 'social_queued',
                      domain=domain,
                      dest_icon='📱' if dest == 'tg' else '☁️'),
                    cid, msg.message_id)
            except Exception:
                pass
        return

    if quality != 'manual':
        dest = get_dest(cid)
        fmt = 'bestvideo+bestaudio/best' if quality == 'best' else f'bestvideo[height<={quality}]+bestaudio/best'
        if should_ask_dest(cid):
            dest_mk = types.InlineKeyboardMarkup()
            dest_mk.row(
                types.InlineKeyboardButton(t(cid, 'btn_tg'),
                    callback_data=f"scd|v|{fmt}|tg|{msg.message_id}"),
                types.InlineKeyboardButton(t(cid, 'btn_gd'),
                    callback_data=f"scd|v|{fmt}|gd|{msg.message_id}"),
            )
            try:
                bot.edit_message_text(
                    t(cid, 'social_quality_dest_msg', domain=domain, quality=quality),
                    cid, msg.message_id, reply_markup=dest_mk)
            except Exception:
                pass
        else:
            enqueue({
                'type': 'social', 'chat_id': cid, 'url': text,
                'dest': dest, 'format': fmt,
                'audio_format':  get_audio_format(cid),
                'audio_quality': get_audio_quality(cid),
                'video_format':  get_video_format(cid),
                'subtitle':      get_subtitle(cid),
                'chapters':      get_chapters(cid),
            })
            try:
                bot.edit_message_text(
                    t(cid, 'social_quality_queued',
                      domain=domain, quality=quality,
                      dest_icon='📱' if dest == 'tg' else '☁️'),
                    cid, msg.message_id)
            except Exception:
                pass
        return

    def fetch_social_formats():
        cf   = active_cookies_file(text)
        opts = {'quiet': True, 'skip_download': True, 'noplaylist': True, 'js_runtimes': {'node': {}}}
        if cf:
            opts['cookiefile'] = cf
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(text, download=False)
            title   = info.get('title', domain)[:40]
            formats = info.get('formats', [])
            seen_h     = set()
            video_fmts = []
            for f in reversed(formats):
                h = f.get('height')
                if not h or h in seen_h:
                    continue
                is_merged = (f.get('acodec') not in ('none', None) and
                             f.get('vcodec') not in ('none', None))
                if is_merged:
                    seen_h.add(h)
                    size = f.get('filesize') or f.get('filesize_approx') or 0
                    video_fmts.append((h, f['format_id'], size))
            if not video_fmts:
                for f in reversed(formats):
                    h = f.get('height')
                    if h and f.get('vcodec') not in ('none', None) and h not in seen_h:
                        seen_h.add(h)
                        size = f.get('filesize') or f.get('filesize_approx') or 0
                        video_fmts.append((h, f['format_id'], size))
            video_fmts.sort(key=lambda x: x[0], reverse=True)
            mid      = msg.message_id
            ask_dest = should_ask_dest(cid)
            prefix   = "sca" if not ask_dest else "scq"
            markup   = types.InlineKeyboardMarkup(row_width=2)
            btns     = []
            for h, fid, size in video_fmts[:4]:
                sz_str = f" ({fmt_size(size)})" if size else ""
                btns.append(types.InlineKeyboardButton(
                    f"📹 {h}p{sz_str}", callback_data=f"{prefix}|v|{fid}|{mid}"))
            if btns:
                markup.add(*btns)
            if not video_fmts:
                markup.add(types.InlineKeyboardButton(
                    t(cid, 'best_quality_btn'),
                    callback_data=f"{prefix}|b|best|{mid}"))
            try:
                bot.edit_message_text(
                    t(cid, 'social_select_quality', title=title),
                    cid, msg.message_id, reply_markup=markup)
            except Exception:
                pass
        except Exception as e:
            try:
                bot.edit_message_text(f"❌ {friendly_error(str(e), cid=cid)}", cid, msg.message_id)
            except Exception:
                pass

    threading.Thread(target=fetch_social_formats, daemon=True).start()


# =============================================================
# Playlist custom count
# =============================================================
def _handle_playlist_count(cid, text, state):
    parts   = state.split('|')
    mid     = int(parts[1])
    audio   = parts[2] == '1'
    quality = parts[3] if len(parts) > 3 else 'best'
    key     = (cid, mid)
    with cache_lock:
        url = url_cache.get(key)
    if not url:
        bot.send_message(cid, t(cid, 'playlist_link_expired'))
        user_state[cid] = None
        return
    try:
        count = int(text.strip())
        if count < 1:
            raise ValueError()
    except Exception:
        bot.send_message(cid, t(cid, 'playlist_invalid_count'))
        return
    user_state[cid] = None
    PL_FMT_MAP = {
        "1080": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best",
        "720":  "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best",
        "480":  "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best",
        "best": "bestvideo+bestaudio/best",
        "audio": "bestaudio/best",
    }
    if not should_ask_dest(cid):
        dest = get_dest(cid)
        fmt  = PL_FMT_MAP.get(quality, "bestvideo+bestaudio/best")
        if audio:
            fmt = "bestaudio/best"
        enqueue({
            'type': 'youtube_playlist', 'url': url, 'chat_id': cid,
            'end': count, 'audio_only': audio, 'format': fmt, 'dest': dest,
        })
        bot.send_message(
            cid,
            t(cid, 'playlist_queued',
              count=count,
              dest_icon='📱' if dest == 'tg' else '☁️'))
    else:
        media = t(cid, 'playlist_media_audio') if audio else t(cid, 'playlist_media_video', quality=quality)
        dest_mk = types.InlineKeyboardMarkup()
        dest_mk.row(
            types.InlineKeyboardButton(t(cid, 'btn_tg'),
                callback_data=f"pld|{count}|tg|{mid}|{'1' if audio else '0'}|{quality}"),
            types.InlineKeyboardButton(t(cid, 'btn_gd'),
                callback_data=f"pld|{count}|gd|{mid}|{'1' if audio else '0'}|{quality}"),
        )
        bot.send_message(
            cid,
            t(cid, 'playlist_dest_msg', media=media, count=count),
            reply_markup=dest_mk)


# =============================================================
# Profile stats helper
# =============================================================
def _send_profile_stats(cid: int) -> None:
    """Send the user their daily usage stats from the DB."""
    from config import MAX_DAILY_FILES, MAX_DAILY_BYTES

    row = db.get_user(cid)
    if row is None:
        # Edge case: user not in DB yet (shouldn't happen after /start but be safe)
        db.add_user(cid, approved=db.is_approved(cid))
        row = db.get_user(cid)

    files_used  = row['files_downloaded']  if row else 0
    bytes_used  = row['bytes_downloaded']   if row else 0
    max_files   = (row['custom_quota_files']
                   if row and row['custom_quota_files'] is not None
                   else MAX_DAILY_FILES)
    max_bytes   = (row['custom_quota_bytes']
                   if row and row['custom_quota_bytes'] is not None
                   else MAX_DAILY_BYTES)

    used_gb = bytes_used  / (1024 ** 3)
    max_gb  = max_bytes   / (1024 ** 3)

    bot.send_message(
        cid,
        t(cid, 'profile_stats',
          files=files_used, max_files=max_files,
          used_gb=used_gb,  max_gb=max_gb),
    )