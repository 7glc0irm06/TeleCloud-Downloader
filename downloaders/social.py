import os
import glob
import time
from urllib.parse import urlparse
import yt_dlp

import db
from config import bot, DOWNLOAD_DIR, ADMIN_ID
from cookies import active_cookies_file
from utils import check_disk_space, get_free_space, cleanup_path, build_rich_progress_card, friendly_error
from uploaders.smart_dest import smart_dest

def _cancel_markup(cid=None):
    from telebot import types
    from locales import t
    m = types.InlineKeyboardMarkup()
    label = t(cid, 'cancel_btn') if cid else "❌ لغو"
    m.add(types.InlineKeyboardButton(label, callback_data="cancel_task"))
    return m

def _is_ytdlp_url(url: str) -> bool:
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'js_runtimes': {'node': {}}}) as ydl:
            for ie_cls in ydl._ies.values():
                try:
                    if ie_cls.suitable(url) and ie_cls.IE_NAME not in ('generic', 'Generic'):
                        return True
                except Exception:
                    continue
    except Exception:
        pass
    return False

def ytdlp_universal(task):
    from locales import t
    from config import tg_upload_mode
    chat_id = task['chat_id']
    cid     = chat_id
    dest    = task.get('dest') or ('tg' if chat_id in tg_upload_mode else 'gd')
    url     = task['url']

    if not check_disk_space():
        bot.send_message(chat_id, t(cid, 'disk_no_space', free=get_free_space()))
        return

    audio_only    = task.get('audio_only', False) or task.get('format', '') == 'bestaudio/best'
    audio_codec   = task.get('audio_format', 'mp3')      # mp3 | m4a | flac | default
    audio_quality = task.get('audio_quality', 'default')  # 320 | 128 | default
    video_fmt     = task.get('video_format', 'mp4')       # mp4 | mkv | default
    embed_chapters = task.get('chapters', False)

    domain        = urlparse(url).netloc.replace('www.', '').split('.')[0].capitalize()
    quality_label = f"🎵 {audio_codec.upper() if audio_codec != 'default' else 'MP3'}" if audio_only else 'video'

    msg      = bot.send_message(chat_id, t(cid, 'social_preparing', domain=domain), reply_markup=_cancel_markup(cid))
    task['_msg_id'] = msg.message_id  # lets cancel_task find this task by its progress message
    last_upd = [time.time()]

    def hook(d):
        if task['_stop'].is_set(): raise Exception(t(cid, 'social_cancelled'))
        if d['status'] == 'downloading' and time.time() - last_upd[0] > 3:
            pct   = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            speed = d.get('speed', 0) or 0
            eta   = d.get('eta', 0) or 0
            pct_f = pct / total * 100 if total else 0
            actual_title = d.get('info_dict', {}).get('title', f"{domain} Media")
            task['actual_title'] = actual_title
            card = build_rich_progress_card("⬇️", actual_title, pct_f, pct, total, speed, eta, domain, quality_label, cid=cid)
            try: bot.edit_message_text(card, chat_id, msg.message_id, reply_markup=_cancel_markup(cid))
            except Exception: pass
            last_upd[0] = time.time()

    folder = os.path.join(DOWNLOAD_DIR, domain)
    os.makedirs(folder, exist_ok=True)
    cf = active_cookies_file(url)

    # ── Build postprocessors dynamically ──────────────────────
    postprocessors = []
    if audio_only:
        # Task 3: Always extract audio via FFmpeg (never raw stream)
        pp = {'key': 'FFmpegExtractAudio', 'preferredcodec': audio_codec if audio_codec != 'default' else 'mp3'}
        if audio_quality != 'default':
            pp['preferredquality'] = audio_quality
        postprocessors.append(pp)

    if embed_chapters and not audio_only:
        postprocessors.append({'key': 'FFmpegMetadata', 'add_chapters': True})

    merge_fmt = video_fmt if video_fmt != 'default' else 'mp4'

    ydl_opts = {
        'format':              task.get('format', 'bestvideo+bestaudio/best'),
        'outtmpl':             os.path.join(folder, '%(title)s.%(ext)s'),
        'merge_output_format': merge_fmt,
        'progress_hooks':      [hook],
        'quiet':               True,
        'no_warnings':         True,
        'js_runtimes':         {'node': {}},
        'windowsfilenames':    True,
        'noplaylist':          True,
        'nocheckcertificate':  True,
        'format_sort':         ['res', 'ext:mp4:m4a'],
        'postprocessors':      postprocessors,
        'http_headers': {
            'User-Agent':      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept':          'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        },
        'extractor_args': {
            'twitter': {'api': ['graphql']},
        },
    }
    if embed_chapters and not audio_only:
        ydl_opts['embedchapters'] = True
    if cf: ydl_opts['cookiefile'] = cf


    fp = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info      = ydl.extract_info(url, download=True)
            expected  = ydl.prepare_filename(info)
            base      = os.path.splitext(expected)[0]
            candidates = glob.glob(base + '.*')
            fp        = max(candidates, key=os.path.getmtime) if candidates else None
            if not fp:
                files = sorted(glob.glob(os.path.join(folder, '*')), key=os.path.getmtime)
                fp    = files[-1] if files else None
            if not fp: raise Exception(t(cid, 'file_not_found_err'))

        try: bot.edit_message_text(t(cid, 'social_upload_preparing'), chat_id, msg.message_id)
        except Exception: pass

        final_title = task.get('actual_title', f"{domain} Media")
        task_info = {'title': final_title, 'source': domain, 'quality': quality_label}

        # ── Byte quota accounting ──────────────────────────────
        if cid != ADMIN_ID:
            real_size = os.path.getsize(fp) if os.path.isfile(fp) else 0
            db.record_download_bytes(cid, real_size)

        smart_dest(fp, msg, dest, folder_name=None, task_info=task_info)
        cleanup_path(folder)

    except Exception as e:
        if fp: cleanup_path(fp)
        cleanup_path(folder)
        err = str(e)
        cancel_kw = t(cid, 'social_cancelled')
        if cancel_kw in err or t(cid, 'cancelled_keyword') in err:
            try: bot.edit_message_text(t(cid, 'download_cancelled'), chat_id, msg.message_id)
            except Exception: pass
        else:
            text = f"❌ {friendly_error(err, cid=cid)}"
            try: bot.edit_message_text(text, chat_id, msg.message_id)
            except Exception: bot.send_message(chat_id, text)
            bot.send_message(chat_id, f"DEBUG ERROR:\n{err[:500]}")