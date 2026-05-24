import os
import re
import glob
import time
import threading
import yt_dlp

from config import bot, stop_event, DOWNLOAD_DIR, cache_lock, url_cache
from cookies import active_cookies_file
from utils import (check_disk_space, get_free_space, cleanup_path,
                   fmt_size, build_rich_progress_card, friendly_error)
from uploaders.smart_dest import smart_dest

def _cancel_markup(cid=None):
    from telebot import types
    from locales import t
    m = types.InlineKeyboardMarkup()
    label = t(cid, 'cancel_btn') if cid else "❌ لغو"
    m.add(types.InlineKeyboardButton(label, callback_data="cancel_task"))
    return m


def get_format_sizes(url: str) -> dict:
    sizes = {}
    cf    = active_cookies_file(url)
    opts  = {
        'quiet': True,
        'skip_download': True,
        'js_runtimes': {'node': {}},
    }
    if cf: opts['cookiefile'] = cf
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])
        for h in (1080, 720, 480):
            vf = next((f for f in reversed(formats) if f.get('height') == h and f.get('ext') == 'mp4'), None)
            af = next((f for f in reversed(formats) if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and f.get('ext') == 'm4a'), None)
            if vf:
                vs       = vf.get('filesize') or vf.get('filesize_approx') or 0
                as_      = (af.get('filesize') or af.get('filesize_approx') or 0) if af else 0
                sizes[h] = vs + as_
        bf = next((f for f in reversed(formats) if f.get('vcodec') != 'none' and f.get('acodec') != 'none'), None)
        if bf: sizes['best'] = bf.get('filesize') or bf.get('filesize_approx') or 0
        af = next((f for f in reversed(formats) if f.get('acodec') != 'none' and f.get('vcodec') == 'none'), None)
        if af: sizes['audio'] = af.get('filesize') or af.get('filesize_approx') or 0
    except Exception:
        pass
    return sizes


def _build_ydl_opts(task: dict, folder: str, hook) -> dict:
    """
    Dynamically build yt-dlp options from the task's user settings.
    Covers: audio mode, video format, subtitles, and chapter embedding.
    """
    from locales import t
    cid = task['chat_id']

    audio_only    = task.get('audio_only', False)
    audio_codec   = task.get('audio_format', 'mp3')    # mp3 | m4a | flac | default
    audio_quality = task.get('audio_quality', 'default')  # 320 | 128 | default
    video_fmt     = task.get('video_format', 'mp4')    # mp4 | mkv | default
    subtitle_lang = task.get('subtitle', 'off')        # en | fa | off
    embed_chapters = task.get('chapters', False)

    postprocessors = []

    if audio_only:
        # ── Task 3: Always use FFmpegExtractAudio for audio downloads ──
        pp = {'key': 'FFmpegExtractAudio'}
        if audio_codec != 'default':
            pp['preferredcodec'] = audio_codec
        else:
            pp['preferredcodec'] = 'mp3'  # yt-dlp requires a codec value
        if audio_quality != 'default':
            pp['preferredquality'] = audio_quality
        postprocessors.append(pp)

    # ── Task 5: Chapter / metadata embedding ──────────────────────────────
    # NOTE: FFmpegMetadata MUST be appended AFTER subtitle PPs so it runs
    # last and picks up the fully-muxed file (including embedded sub tracks).
    # It is intentionally moved to *after* the subtitle block below.

    # ── Task 4: Subtitle embedding ─────────────────────────────
    #
    # Root-cause fix: YouTube only serves subtitles as .vtt (WebVTT).
    # Embedding raw .vtt into .mp4 produces garbage "ISO Media" data tracks
    # because FFmpeg cannot recognise the codec. The correct pipeline is:
    #
    #   FFmpegSubtitlesConvertor (vtt → srt)
    #       → FFmpegEmbedSubtitle  (srt → mov_text inside .mp4 / ass inside .mkv)
    #
    # `subtitlesformat` is intentionally left unset so yt-dlp downloads
    # whatever the source offers (vtt/json3); the Convertor PP then
    # normalises everything to SRT before the embed step.
    subtitle_opts = {}
    if subtitle_lang != 'off' and not audio_only:
        subtitle_opts = {
            'writesubtitles':      True,
            'writeautomaticsub':   True,   # fall back to auto-generated subs
            'subtitleslangs':      [subtitle_lang, f'{subtitle_lang}-*'],
            # DO NOT set subtitlesformat here – let yt-dlp grab whatever
            # the source offers, then the Convertor PP handles normalisation.
            'ignoreerrors':        True,
        }
        # 1. Convert downloaded subtitle (vtt/json3/…) → srt
        postprocessors.append({
            'key':  'FFmpegSubtitlesConvertor',
            'format': 'srt',
        })
        # 2. Embed the normalised srt into the container
        #    FFmpeg will automatically re-encode srt → mov_text for .mp4
        #    and srt → ass/subrip for .mkv — both display correctly.
        postprocessors.append({'key': 'FFmpegEmbedSubtitle', 'already_have_subtitle': False})

    # ── Task 5 (continued): Append Metadata PP last ───────────────────────
    if embed_chapters and not audio_only:
        postprocessors.append({'key': 'FFmpegMetadata', 'add_chapters': True})

    # ── Task 1: Video container format ────────────────────────
    merge_fmt = video_fmt if video_fmt != 'default' else 'mp4'

    # Subtitles embed best in mp4 and mkv — warn if format is incompatible
    # (No automatic re-mux: just catch and warn per user preference)
    if subtitle_lang != 'off' and not audio_only and merge_fmt not in ('mp4', 'mkv'):
        merge_fmt = 'mp4'  # silently coerce to mp4 so FFmpegEmbedSubtitle has a chance

    ydl_opts = {
        'format':              task['format'],
        'outtmpl':             os.path.join(folder, '%(title)s.%(ext)s'),
        'progress_hooks':      [hook],
        'noplaylist':          True,
        'merge_output_format': merge_fmt,
        'postprocessors':      postprocessors,
        'quiet':               True,
        'no_warnings':         True,
        'js_runtimes':         {'node': {}},
        'windowsfilenames':    True,
        'concurrent_fragment_downloads': 4,
        'throttledratelimit':           100000,
    }

    if embed_chapters and not audio_only:
        ydl_opts['embedchapters'] = True

    ydl_opts.update(subtitle_opts)

    cf = active_cookies_file(task.get('url', ''))
    if cf:
        ydl_opts['cookiefile'] = cf

    return ydl_opts


def _check_subtitle_embedded(folder: str, subtitle_lang: str) -> bool:
    """
    Return True if yt-dlp successfully downloaded a subtitle file for this video.
    We detect this by looking for any .srt / .vtt / .ass file in the folder.
    If none found, the subtitle was not available → show warning to user.
    """
    patterns = [
        os.path.join(folder, f'*.{subtitle_lang}.srt'),
        os.path.join(folder, f'*.{subtitle_lang}.vtt'),
        os.path.join(folder, f'*.{subtitle_lang}.ass'),
        os.path.join(folder, f'*.{subtitle_lang}.ssa'),
        # Some extractors write without the lang prefix
        os.path.join(folder, '*.srt'),
        os.path.join(folder, '*.vtt'),
    ]
    for pat in patterns:
        if glob.glob(pat):
            return True
    return False


def process_youtube_download(task):
    from config import tg_upload_mode
    from locales import t
    chat_id = task['chat_id']
    cid     = chat_id
    dest    = task.get('dest') or ('tg' if chat_id in tg_upload_mode else 'gd')

    if not check_disk_space():
        bot.send_message(chat_id, t(cid, 'disk_no_space', free=get_free_space()))
        return

    audio_only    = task.get('audio_only', False)
    subtitle_lang = task.get('subtitle', 'off')
    title_kw      = task.get('title', 'video')

    # Build quality label for the progress card
    if audio_only:
        fmt_key  = task.get('audio_format', 'mp3')
        q_prefix = fmt_key.upper() if fmt_key != 'default' else 'MP3'
        aq       = task.get('audio_quality', 'default')
        quality_label = f"🎵 {q_prefix}" + (f" {aq}k" if aq != 'default' else '')
    else:
        quality_label = 'video'

    msg      = bot.send_message(chat_id, t(cid, 'connecting_youtube'), reply_markup=_cancel_markup(cid))
    last_upd = [time.time()]

    def my_hook(d):
        if stop_event.is_set(): raise Exception(t(cid, 'cancelled_keyword'))
        if d['status'] == 'downloading' and time.time() - last_upd[0] > 3:
            pct   = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            speed = d.get('speed', 0) or 0
            eta   = d.get('eta', 0) or 0
            pct_f = (pct / total * 100) if total else 0
            actual_title = d.get('info_dict', {}).get('title', title_kw)
            task['actual_title'] = actual_title
            card = build_rich_progress_card("⬇️", actual_title, pct_f, pct, total, speed, eta, "YouTube", quality_label, cid=cid)
            try: bot.edit_message_text(card, chat_id, msg.message_id, reply_markup=_cancel_markup(cid))
            except Exception: pass
            last_upd[0] = time.time()

    safe_title = re.sub(r'[\\/*?:"<>|]', '_', title_kw)[:50]
    folder     = os.path.join(DOWNLOAD_DIR, safe_title)
    os.makedirs(folder, exist_ok=True)

    ydl_opts  = _build_ydl_opts(task, folder, my_hook)
    file_path = None
    subtitle_warning = ''

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info     = ydl.extract_info(task['url'], download=True)
            expected = ydl.prepare_filename(info)
            base     = os.path.splitext(expected)[0]

            # For audio: yt-dlp changes the extension after FFmpegExtractAudio
            candidates = glob.glob(base + '.*')
            file_path  = max(candidates, key=os.path.getmtime) if candidates else None
            if not file_path:
                files     = sorted(glob.glob(os.path.join(folder, '*')), key=os.path.getmtime)
                file_path = files[-1] if files else None
            if not file_path:
                raise Exception(t(cid, 'file_not_found_err'))

        # ── Task 4 fallback: check if subtitle was actually found ──
        if subtitle_lang != 'off' and not audio_only:
            if not _check_subtitle_embedded(folder, subtitle_lang):
                subtitle_warning = t(cid, 'subtitle_not_found_warn')

        try: bot.edit_message_text(t(cid, 'processing_file'), chat_id, msg.message_id)
        except Exception: pass

        final_title = task.get('actual_title', title_kw)
        task_info   = {
            'title':    final_title,
            'source':   'YouTube',
            'quality':  quality_label,
            'extra_msg': subtitle_warning,  # appended by smart_dest / upload completion
        }
        smart_dest(file_path, msg, dest, folder_name=safe_title, task_info=task_info)
        cleanup_path(folder)

    except Exception as e:
        import traceback; print("FULL ERROR:", traceback.format_exc(), flush=True)
        if file_path: cleanup_path(file_path)
        cleanup_path(folder)
        _handle_yt_error(e, chat_id, msg, cid)


def fetch_playlist_entries(url: str, cf=None) -> tuple:
    opts = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': True,
        'js_runtimes': {'node': {}},
    }
    if cf: opts['cookiefile'] = cf
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return list(info.get('entries', [])), info.get('title', 'playlist')


def process_playlist_download(task):
    from config import tg_upload_mode
    from locales import t
    chat_id    = task['chat_id']
    cid        = chat_id
    dest       = task.get('dest') or ('tg' if chat_id in tg_upload_mode else 'gd')
    url        = task['url']
    audio_only = task.get('audio_only', False)
    fmt        = task.get('format', 'bestvideo+bestaudio/best')
    indices    = task.get('indices', None)

    if not check_disk_space():
        bot.send_message(chat_id, t(cid, 'disk_no_space', free=get_free_space()))
        return

    msg = bot.send_message(chat_id, t(cid, 'fetching_playlist'), reply_markup=_cancel_markup(cid))
    cf  = active_cookies_file(url)

    try:
        entries, pl_title = fetch_playlist_entries(url, cf)
        if indices is not None: entries = [e for i, e in enumerate(entries, 1) if i in indices]
        pl_title = re.sub(r'[\\/*?:"<>|]', '_', pl_title)[:40]
        total    = len(entries)
    except Exception as e:
        import traceback; print("FULL ERROR:", traceback.format_exc(), flush=True)
        try: bot.edit_message_text(f"❌ {friendly_error(str(e), cid=cid)}", chat_id, msg.message_id)
        except Exception: pass
        return

    folder    = os.path.join(DOWNLOAD_DIR, pl_title)
    os.makedirs(folder, exist_ok=True)
    completed = [0]
    errors    = [0]
    lock      = threading.Lock()
    semaphore = threading.Semaphore(2)

    if audio_only:
        audio_codec   = task.get('audio_format', 'mp3')
        audio_quality = task.get('audio_quality', 'default')
        q_prefix      = audio_codec.upper() if audio_codec != 'default' else 'MP3'
        quality_label = f"🎵 {q_prefix}"
    else:
        quality_label = 'video'

    task_info_base = {'source': 'YouTube Playlist', 'quality': quality_label}

    def process_one(entry, idx):
        if stop_event.is_set(): return
        with semaphore:
            if stop_event.is_set(): return
            entry_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry['id']}"

            # Build per-entry opts (reuse task settings for audio codec/quality)
            postprocessors = []
            if audio_only:
                pp = {'key': 'FFmpegExtractAudio', 'preferredcodec': audio_codec if audio_codec != 'default' else 'mp3'}
                if audio_quality != 'default':
                    pp['preferredquality'] = audio_quality
                postprocessors.append(pp)

            video_fmt  = task.get('video_format', 'mp4')
            merge_fmt  = video_fmt if video_fmt != 'default' else 'mp4'
            embed_chap = task.get('chapters', False)
            if embed_chap and not audio_only:
                postprocessors.append({'key': 'FFmpegMetadata', 'add_chapters': True})

            ydl_opts = {
                'format':              fmt,
                'outtmpl':             os.path.join(folder, f"{idx:03d}_%(title)s.%(ext)s"),
                'merge_output_format': merge_fmt,
                'quiet':               True,
                'no_warnings':         True,
                'js_runtimes':         {'node': {}},
                'windowsfilenames':    True,
                'concurrent_fragment_downloads': 4,
                'throttledratelimit':           100000,
                'postprocessors':      postprocessors,
            }
            if embed_chap and not audio_only:
                ydl_opts['embedchapters'] = True
            if cf: ydl_opts['cookiefile'] = cf

            fp = None
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    dl_info   = ydl.extract_info(entry_url, download=True)
                    expected  = ydl.prepare_filename(dl_info)
                    base      = os.path.splitext(expected)[0]
                    candidates = glob.glob(base + '.*')
                    fp        = max(candidates, key=os.path.getmtime) if candidates else None

                if fp and not stop_event.is_set():
                    sub = bot.send_message(chat_id, t(cid, 'uploading_item', idx=idx, total=total, name=os.path.basename(fp)))
                    item_info = task_info_base.copy()
                    item_info['title'] = os.path.basename(fp)
                    smart_dest(fp, sub, dest, folder_name=pl_title, task_info=item_info)
                with lock: completed[0] += 1
            except Exception:
                if fp: cleanup_path(fp)
                with lock:
                    errors[0]    += 1
                    completed[0] += 1

            with lock: done = completed[0]
            from utils import make_progress_bar
            try:
                bar = make_progress_bar(done / total * 100)
                bot.edit_message_text(
                    f"📋 {pl_title}\n{bar} {done}/{total}\n✅ {done - errors[0]}  ❌ {errors[0]}",
                    chat_id, msg.message_id, reply_markup=_cancel_markup(cid))
            except Exception: pass

    threads = [threading.Thread(target=process_one, args=(e, i)) for i, e in enumerate(entries, 1)]
    for th in threads: th.start()
    for th in threads: th.join()

    try: bot.edit_message_text(
        t(cid, 'playlist_done', title=pl_title, ok=total - errors[0], total=total),
        chat_id, msg.message_id)
    except Exception: pass


def _handle_yt_error(e, chat_id, msg, cid=None):
    from locales import t
    err = str(e)
    cancel_kw = t(cid, 'cancelled_keyword') if cid else "لغو"
    if cancel_kw in err:
        try: bot.edit_message_text(t(cid, 'download_cancelled') if cid else "🚫 دانلود لغو شد.", chat_id, msg.message_id)
        except Exception: pass
    else:
        text = f"❌ {friendly_error(err, cid=cid)}"
        try: bot.edit_message_text(text, chat_id, msg.message_id)
        except Exception: bot.send_message(chat_id, text)