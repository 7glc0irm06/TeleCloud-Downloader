# TeleCloud-Downloader Setup Guide

> Persian version: [SETUP_FA.md](./SETUP_FA.md)
> Main docs: [README.md](./README.md)

## Overview

This guide explains how to deploy and run TeleCloud-Downloader in production (Docker) and locally (non-Docker).

## Docker Setup (Recommended)

### 1. Prerequisites

- Docker Engine
- Docker Compose v2 (`docker compose`)
- Git

### 2. Clone

```bash
git clone https://github.com/parsa-f/TeleCloud-Downloader.git
cd TeleCloud-Downloader
```

### 3. Create required host files before first run

These files must exist as files on host before `docker compose up`:

```bash
touch cookies_enabled.json
touch rclone.conf
```

Verify:

```bash
ls -la
```

### 4. Configure `.env`

At minimum:

```env
DOWNLOADER_BOT_TOKEN=...
BOT_PASSWORD=...
TELEGRAM_API_ID=...
TELEGRAM_API_HASH=...
TELEGRAM_LOCAL=1
ADMIN_ID=123456789
```

### 5. Start

```bash
docker compose up -d --build
docker compose ps
```

### Optional: Quick Start Script (Beginner-Friendly)

If you are deploying on an Ubuntu/Debian Linux server and want a guided one-time installer, use `start.sh`:

```bash
chmod +x start.sh
./start.sh
```

What `start.sh` does:

- Checks project context and validates required paths/files
- Installs/checks server dependencies (`git`, `curl`, `unzip`, Docker, Docker Compose)
- Prompts for required `.env` variables (token, password, API ID/hash, admin ID)
- Fills safe defaults for advanced settings
- Guides Google Drive setup (`rclone.conf`) with Colab fallback instructions
- Enforces `./rclone.conf` placeholder file if Drive setup is skipped (prevents Docker directory-mount crash)
- Builds and starts containers, then shows service status

Important:

- This installer is intended for Ubuntu/Debian Linux servers.
- Run it from the project root directory (already extracted).
- If Drive is skipped, the bot still starts in Telegram-only mode.

## Local Run (Non-Docker)

### 1. Prerequisites

- Python 3.11+
- `ffmpeg`
- `aria2c`
- `rclone`
- Local Telegram Bot API server reachable at `http://localhost:8081`

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Run

```bash
python3 main.py
```

## General Potential Bugs

### Local Bot API returns relative file paths (not absolute)

When using a self-hosted local Telegram Bot API server (`aiogram/telegram-bot-api`), `bot.get_file()` may return a relative path such as `videos/file_6.mp4` instead of the full absolute path `/var/lib/telegram-bot-api/<token>/videos/file_6.mp4`.

Calling `bot.download_file()` with this relative path will hit the cloud Telegram servers, which return HTTP 404 because the file only exists on your local server.

Fix:

Mount `telegram-bot-api-data` into the bot container (read-only):

```yaml
- ./telegram-bot-api-data:/var/lib/telegram-bot-api:ro
```

Reconstruct the absolute path in code before reading the file:

```python
import os
from glob import glob

LOCAL_API_ROOT = "/var/lib/telegram-bot-api"
if not file_path.startswith('/'):
    token_dirs = glob(os.path.join(LOCAL_API_ROOT, "*:*"))
    if token_dirs:
        file_path = os.path.join(token_dirs[0], file_path)
if file_path.startswith('/'):
    with open(file_path, 'rb') as f:
        data = f.read()
else:
    data = bot.download_file(file_path)  # fallback for cloud API
```

Apply this guard to every `bot.get_file()` call site in your codebase, not only the main file handler, but also cookie uploads and `rclone.conf` uploads.

Also watch out for: `cookies_enabled.json` and `rclone.conf` must exist as files on the host before `docker compose up`. If they are missing, Docker can create them as empty directories, causing `[Errno 21] Is a directory` errors at runtime. Always verify with `ls -la` before starting containers.
