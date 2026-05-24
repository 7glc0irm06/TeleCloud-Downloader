import os
import json
import re
from urllib.parse import urlparse

from config import COOKIES_DIR, COOKIES_STATE

# =============================================================
# Reading and writing cookie state
# =============================================================
def _cookies_state() -> dict:
    try:
        with open(COOKIES_STATE) as f:
            return json.load(f)
    except Exception:
        return {}

def _save_cookies_state(state: dict):
    with open(COOKIES_STATE, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# =============================================================
# Cookie operations
# =============================================================
def get_cookie_path(name: str) -> str:
    return os.path.join(COOKIES_DIR, f"{name}.txt")

def cookie_exists(name: str) -> bool:
    p = get_cookie_path(name)
    return os.path.exists(p) and os.path.getsize(p) > 0

def is_cookie_enabled(name: str) -> bool:
    return _cookies_state().get(name, True)

def set_cookie_enabled(name: str, val: bool):
    state = _cookies_state()
    state[name] = val
    _save_cookies_state(state)

def delete_cookie(name: str):
    p = get_cookie_path(name)
    if os.path.exists(p):
        os.remove(p)
    state = _cookies_state()
    state.pop(name, None)
    _save_cookies_state(state)

def save_cookie_data(name: str, data: bytes):
    with open(get_cookie_path(name), 'wb') as f:
        f.write(data)
    state = _cookies_state()
    state[name] = True
    _save_cookies_state(state)

def list_cookies() -> list:
    state  = _cookies_state()
    result = []
    for fname in sorted(os.listdir(COOKIES_DIR)):
        if not fname.endswith('.txt'):
            continue
        name    = fname[:-4]
        path    = get_cookie_path(name)
        enabled = state.get(name, True)
        size    = os.path.getsize(path)
        result.append({'name': name, 'path': path, 'enabled': enabled, 'size': size})
    return result

def active_cookies_file(url: str = '') -> str:
    """Return the appropriate cookie file for the given URL."""
    if url:
        try:
            domain  = urlparse(url).netloc.lower()
            domain  = re.sub(r'^www\.', '', domain).split('.')[0]
            aliases = {'x': ['x', 'twitter'], 'twitter': ['twitter', 'x']}
            checks  = aliases.get(domain, [domain])
            for name in checks:
                if cookie_exists(name) and is_cookie_enabled(name):
                    return get_cookie_path(name)
        except Exception:
            pass
    if cookie_exists('default') and is_cookie_enabled('default'):
        return get_cookie_path('default')
    return None
