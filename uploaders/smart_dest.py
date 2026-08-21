import os
from config import bot
from utils import get_file_size, fmt_size

def smart_dest(file_path: str, status_msg, dest: str = None, folder_name: str = None, task_info: dict = None):
    """
    Send the file to the correct destination.
    dest='tg'  → Telegram (auto-redirects to Drive if size > 2GB)
    dest='gd'  → Google Drive
    dest=None  → reads from user's upload toggle
    """
    from locales import t
    from config import tg_upload_mode
    from uploaders.telegram_upload import upload_file_to_telegram
    from uploaders.gdrive_upload import upload_to_gdrive_cancellable

    chat_id = status_msg.chat.id
    cid     = chat_id
    if task_info is None:
        task_info = {}

    if dest is None:
        dest = 'tg'

    size = get_file_size(file_path)

    # Local Bot API allows up to 2GB; if a single file is larger, notify and skip gdrive.
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
    else:
        # gdrive path disabled: fall back to telegram
        upload_file_to_telegram(file_path, status_msg, task_info)