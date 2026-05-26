import time
import threading
import logging
from concurrent.futures import ThreadPoolExecutor

from config import bot, MAX_RETRIES, RETRY_DELAY, MAX_CONCURRENT_DOWNLOADS
from utils import friendly_error
import config

logger = logging.getLogger(__name__)

# The single shared executor; initialised by start_worker().
_executor: ThreadPoolExecutor | None = None


# =============================================================
# Internal: execute one task inside a pool worker thread
# =============================================================
def _run_task(task: dict) -> None:
    """
    Execute a single download task.

    Lifecycle
    ---------
    1. Register the task in config.current_tasks so cancel/status
       queries can find it.
    2. Dispatch to the appropriate downloader.
    3. On failure, retry up to MAX_RETRIES times (with RETRY_DELAY
       seconds between attempts) unless the user explicitly cancelled.
    4. Always deregister from config.current_tasks in the finally block.
    """
    cid     = task.get('chat_id')
    retries = task.get('_retries', 0)

    # Use the task object's identity as a unique key.
    # id(task) is stable for the entire lifetime of this call because
    # _run_task holds a reference on its stack, preventing GC/reuse.
    _task_id = id(task)

    # Register as an active task so status queries and cancellation can find it
    with config.current_tasks_lock:
        config.current_tasks[_task_id] = task

    try:
        _dispatch(task)

    except Exception as e:
        err       = str(e)
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
            # Re-enqueue after delay (the dispatcher will inject a fresh _stop)
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
        # Always deregister, even if the task was retried
        with config.current_tasks_lock:
            config.current_tasks.pop(_task_id, None)


# =============================================================
# Internal: dispatcher thread — feeds tasks into the pool
# =============================================================
def _dispatcher() -> None:
    """
    Single lightweight thread that pops tasks from pending_queue and
    submits them to the ThreadPoolExecutor.

    Sleeping 0.5 s when the queue is empty keeps CPU usage negligible
    while still reacting to new tasks within half a second.

    A fresh threading.Event is injected into every task here so that:
      • Retried tasks always start with a clean (unset) stop signal.
      • The event is available to the downloader closures via task['_stop'].
    """
    while True:
        task = None
        with config.queue_lock:
            if config.pending_queue:
                task = config.pending_queue.pop(0)

        if task is None:
            time.sleep(0.5)
            continue

        # Inject a FRESH per-task cancellation event (always overwrite so
        # retried tasks are not pre-cancelled from the previous attempt).
        task['_stop'] = threading.Event()

        _executor.submit(_run_task, task)


# =============================================================
# Public queue helpers (unchanged API)
# =============================================================
def enqueue(task: dict) -> int:
    with config.queue_lock:
        config.pending_queue.append(task)
        return len(config.pending_queue)


def remove_from_queue(idx: int):
    with config.queue_lock:
        if 0 <= idx < len(config.pending_queue):
            return config.pending_queue.pop(idx)
        return None


def clear_queue() -> None:
    with config.queue_lock:
        config.pending_queue.clear()


def get_queue_items() -> list:
    with config.queue_lock:
        return list(config.pending_queue)


# =============================================================
# Internal: route a task to the correct downloader
# =============================================================
def _dispatch(task: dict) -> None:
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


# =============================================================
# Start the worker pool and dispatcher
# =============================================================
def start_worker() -> None:
    """
    Create the ThreadPoolExecutor and launch the dispatcher thread.
    MAX_CONCURRENT_DOWNLOADS (env: MAX_CONCURRENT_DOWNLOADS, default 2)
    controls how many downloads can run simultaneously.
    """
    global _executor
    _executor = ThreadPoolExecutor(
        max_workers=MAX_CONCURRENT_DOWNLOADS,
        thread_name_prefix='dl_worker',
    )
    threading.Thread(
        target=_dispatcher,
        daemon=True,
        name='dl_dispatcher',
    ).start()
    logger.info("Download pool started (max_workers=%d)", MAX_CONCURRENT_DOWNLOADS)
