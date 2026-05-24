import json
import os

from config import USER_LANGS_FILE

# In-memory cache to avoid repeated disk reads
_cache: dict = {}
_loaded = False


def _load():
    global _loaded
    if _loaded:
        return
    _loaded = True
    if os.path.exists(USER_LANGS_FILE):
        try:
            with open(USER_LANGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for k, v in data.items():
                _cache[int(k)] = v
        except Exception:
            pass


def _save():
    try:
        with open(USER_LANGS_FILE, 'w', encoding='utf-8') as f:
            json.dump({str(k): v for k, v in _cache.items()}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_lang(cid: int) -> str:
    """Return the user's language code ('fa' or 'en'). Defaults to 'fa'."""
    _load()
    return _cache.get(cid, 'fa')


def has_lang(cid: int) -> bool:
    """Return True if the user has already chosen a language."""
    _load()
    return cid in _cache


def set_lang(cid: int, lang: str):
    """Persist the user's language choice."""
    _load()
    _cache[cid] = lang
    _save()
