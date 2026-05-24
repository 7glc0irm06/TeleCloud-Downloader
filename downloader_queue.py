import time
import threading

from config import (bot, stop_event, MAX_RETRIES, RETRY_DELAY)
from utils import friendly_error
import config


def download_worker():
    while True:
        task = None
        with config.queue_lock:
            if config.pending_queue:
                task = config.pending_queue.pop(0)

        if not task:
            time.sleep(1)
            continue

        config.current_task = task
        config.stop_event.clear()
        retries = task.get('_retries', 0)
        cid     = task.get('chat_id')

        try:
            _dispatch(task)
        except Exception as e:
            err = str(e)
            from locales import t
            cancel_kw = t(cid, 'cancelled_keyword') if cid else "لغو"
            if retries < MAX_RETRIES and cancel_kw not in err:
                task['_retries'] = retries + 1
                try:
                    bot.send_message(
                        cid,
                        t(cid, 'retry_error',
                          attempt=retries + 1, max=MAX_RETRIES,
                          error=friendly_error(err, cid=cid),
                          delay=RETRY_DELAY) if cid else (
                            f"⚠️ خطا در دانلود (تلاش {retries+1}/{MAX_RETRIES}):\n"
                            f"{friendly_error(err)}\n\n"
                            f"⏳ {RETRY_DELAY} ثانیه دیگر دوباره امتحان میکنم..."
                        )
                    )
                except Exception:
                    pass
                threading.Timer(RETRY_DELAY, lambda t=task: enqueue(t)).start()
            else:
                try:
                    if retries >= MAX_RETRIES:
                        bot.send_message(
                            cid,
                            t(cid, 'max_retries_error',
                              max=MAX_RETRIES,
                              error=friendly_error(err, cid=cid)) if cid else (
                                f"❌ بعد از {MAX_RETRIES} بار تلاش موفق نشدم:\n{friendly_error(err)}"
                            )
                        )
                    else:
                        bot.send_message(
                            cid,
                            t(cid, 'generic_error',
                              error=friendly_error(err, cid=cid)) if cid else (
                                f"❌ خطا:\n{friendly_error(err)}"
                            )
                        )
                except Exception:
                    pass
        finally:
            config.current_task = None


def enqueue(task):
    with config.queue_lock:
        config.pending_queue.append(task)
        return len(config.pending_queue)


def remove_from_queue(idx):
    with config.queue_lock:
        if 0 <= idx < len(config.pending_queue):
            return config.pending_queue.pop(idx)
        return None


def clear_queue():
    with config.queue_lock:
        config.pending_queue.clear()


def get_queue_items():
    with config.queue_lock:
        return list(config.pending_queue)


def _dispatch(task):
    t_type = task['type']
    if t_type == 'youtube':
        from downloaders.youtube import process_youtube_download
        process_youtube_download(task)
    elif t_type == 'youtube_playlist':
        from downloaders.youtube import process_playlist_download
        process_playlist_download(task)
    elif t_type == 'torrent':
        from downloaders.torrent import process_torrent_download
        process_torrent_download(task)
    elif t_type == 'direct':
        from downloaders.direct import process_direct_download
        process_direct_download(task)
    elif t_type == 'social':
        from downloaders.social import ytdlp_universal
        ytdlp_universal(task)
    else:
        cid = task.get('chat_id')
        from locales import t as _t
        raise ValueError(
            _t(cid, 'unknown_task_type', t=t_type) if cid else
            f"نوع task ناشناخته: {t_type}"
        )


def start_worker():
    threading.Thread(target=download_worker, daemon=True).start()
