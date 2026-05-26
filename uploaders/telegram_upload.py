import os
from config import bot
from utils import fmt_size, cleanup_path, friendly_error, safe_tg_call
from uploaders.gdrive_upload import upload_to_gdrive_cancellable

def upload_file_to_telegram(file_path: str, status_msg, task_info=None):
    from locales import t
    if task_info is None:
        task_info = {}
    chat_id = status_msg.chat.id
    cid     = chat_id
    size_mb = os.path.getsize(file_path) / (1024 * 1024)

    if size_mb > 2000:
        try:
            safe_tg_call(
                bot.edit_message_text,
                t(cid, 'tg_upload_large', size=f"{size_mb:.1f}"),
                chat_id, status_msg.message_id)
        except Exception:
            pass
        upload_to_gdrive_cancellable(
            file_path, status_msg,
            task_info=task_info,
            user_id=task_info.get('user_id'),
        )
        return

    try:
        safe_tg_call(bot.edit_message_text, t(cid, 'tg_uploading'), chat_id, status_msg.message_id)
    except Exception:
        pass

    # Dynamic timeout: assume worst-case 1 MB/s upload speed, add 2-min buffer.
    # Floor of 300 s covers small files; ceiling is uncapped so 2 GB @ 1 MB/s
    # gets ~2168 s (~36 min) instead of the old hard-coded 300 s.
    _size_bytes    = os.path.getsize(file_path)
    upload_timeout = max(300, int(_size_bytes / (1 * 1024 * 1024)) + 120)

    try:
        with open(file_path, 'rb') as f:
            name = os.path.basename(file_path)
            ext  = os.path.splitext(name)[1].lower()
            if ext in ('.mp4', '.mkv', '.avi', '.mov', '.webm'):
                bot.send_video(chat_id, f, caption=name, timeout=upload_timeout)
            elif ext in ('.mp3', '.m4a', '.ogg', '.flac', '.wav'):
                bot.send_audio(chat_id, f, caption=name, timeout=upload_timeout)
            else:
                bot.send_document(chat_id, f, caption=name, timeout=upload_timeout)

        # Edit status message to show final success state
        title   = task_info.get('title', name)[:45]
        source  = task_info.get('source', 'Telegram')
        quality = task_info.get('quality', '')
        fsize   = fmt_size(os.path.getsize(file_path))

        final_text = t(cid, 'tg_upload_done',
                       title=title, size=fsize, source=source, quality=quality)
        try:
            safe_tg_call(bot.edit_message_text, final_text, chat_id, status_msg.message_id)
        except Exception:
            pass

        cleanup_path(file_path)
    except Exception as e:
        text = f"❌ {friendly_error(str(e), cid=cid)}"
        try:
            safe_tg_call(bot.edit_message_text, text, chat_id, status_msg.message_id)
        except Exception:
            safe_tg_call(bot.send_message, chat_id, text)

def upload_folder_to_telegram(folder_path: str, status_msg, task_info=None):
    from locales import t
    if task_info is None:
        task_info = {}
    chat_id = status_msg.chat.id
    cid     = chat_id
    if os.path.isfile(folder_path):
        upload_file_to_telegram(folder_path, status_msg, task_info)
        return
    files = sorted([os.path.join(folder_path, f)
                    for f in os.listdir(folder_path)
                    if os.path.isfile(os.path.join(folder_path, f))])
    bot.send_message(chat_id, t(cid, 'tg_folder_files', count=len(files)))
    for i, fp in enumerate(files, 1):
        sub = bot.send_message(chat_id, f"⬆️ {i}/{len(files)}: {os.path.basename(fp)}")
        upload_file_to_telegram(fp, sub, task_info)