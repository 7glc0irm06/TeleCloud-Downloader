import os
from config import bot
from utils import get_file_size, fmt_size


def smart_dest(file_path: str, status_msg, dest: str = None, folder_name: str = None, task_info: dict = None):
    """
    Send the file to the correct destination.
    dest='tg'      → Telegram (max 2GB via Local Bot API)
    dest='s3'      → Railway Bucket (S3-compatible), public link
    dest='github'  → user's own GitHub repo (per-user token), raw link
    dest='gd'      → disabled (kept for compat, falls back to tg)
    dest=None      → defaults to 'tg'
    """
    from locales import t
    from config import tg_upload_mode
    from uploaders.telegram_upload import upload_file_to_telegram
    from uploaders.s3_upload import upload_to_s3
    from uploaders.github_upload import upload_to_github

    chat_id = status_msg.chat.id
    cid = chat_id
    if task_info is None:
        task_info = {}

    if dest is None:
        dest = 'tg'

    size = get_file_size(file_path)

    # Telegram hard limit is 2GB (Local Bot API). Notify and stop for larger files.
    if size > 2000 * 1024 * 1024 and dest == 'tg':
        try:
            bot.edit_message_text(
                t(cid, 'smart_dest_large', size=fmt_size(size)),
                chat_id, status_msg.message_id
            )
        except Exception:
            pass
        return

    if dest == 'tg':
        upload_file_to_telegram(file_path, status_msg, task_info)
        return

    if dest == 's3':
        url = upload_to_s3(file_path, chat_id, status_msg)
        _reply_link(status_msg, url, "S3/Railway", cid)
        return

    if dest == 'github':
        url = upload_to_github(file_path, chat_id, status_msg)
        _reply_link(status_msg, url, "GitHub", cid)
        return

    # gd / unknown → fall back to telegram
    upload_file_to_telegram(file_path, status_msg, task_info)


def _reply_link(status_msg, url: str | None, label: str, cid: int):
    from locales import t
    if url:
        try:
            bot.edit_message_text(
                f"{label} link:\n{url}",
                cid, status_msg.message_id
            )
        except Exception:
            pass
    else:
        try:
            bot.edit_message_text(
                t(cid, 'upload_failed_toast'),
                cid, status_msg.message_id
            )
        except Exception:
            pass
