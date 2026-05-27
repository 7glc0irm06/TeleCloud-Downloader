<div align="center">
  <h1>☁️ TeleCloud-Downloader</h1>
  <p><strong>Advanced, Fully Modular Asynchronous Telegram Download Manager</strong></p>

  <a href="./README_FA.md">🇮🇷 مستندات فارسی</a>
  <br>
  <a href="./QUICKSTART.md">⚡ Quick Start (Beginners)</a> · <a href="./QUICKSTART_FA.md">⚡ شروع سریع فارسی</a>
  <br>
  <a href="./SETUP.md">🛠️ Setup Guide</a> · <a href="./SETUP_FA.md">🛠️ راهنمای نصب فارسی</a>
  <br><br>

  <!-- Badges -->
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/pyTelegramBotAPI-Latest-229ED9.svg?logo=telegram&logoColor=white" alt="pyTelegramBotAPI">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/yt--dlp-Powered-FF0000.svg?logo=youtube&logoColor=white" alt="yt-dlp">
  <img src="https://img.shields.io/badge/Local%20Bot%20API-2GB%20Uploads-26A69A.svg?logo=telegram&logoColor=white" alt="Local Bot API">
  <img src="https://img.shields.io/badge/License-MIT-22C55E.svg" alt="License">
</div>

---

## 📖 Table of Contents

- [✨ Features](#-features)
- [🏗️ Architecture Overview](#-architecture-overview)
- [🛠️ Tech Stack](#-tech-stack)
- [🚀 Installation & Deployment](#-installation--deployment)
- [💬 Usage & Commands](#-usage--commands)
- [⚙️ Configuration Reference](#-configuration-reference)
- [📁 Project Structure](#-project-structure)
- [💾 Data Persistency & Volumes](#-data-persistency--volumes)
- [🔄 Updating the Bot](#-updating-the-bot)
- [🔒 Security Notes](#-security-notes)
- [🐛 Troubleshooting & FAQ](#-troubleshooting--faq)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## ✨ Features

### 🔥 Local Telegram Bot API Server — No More File Size Limits
> This is the most critical architectural feature of TeleCloud-Downloader.

Unlike standard bots that are capped by Telegram's default **20 MB download / 50 MB upload** limits, TeleCloud-Downloader runs its own **self-hosted Local Telegram Bot API Server** (`aiogram/telegram-bot-api`). This completely bypasses Telegram's cloud restrictions:

- **📦 Supports files up to 2 GB** — download and send massive video, audio, and archive files without restrictions.
- **⚡ Lightning-fast local file transfers** — In local mode, the bot reads files directly from shared local Bot API storage (`/var/lib/telegram-bot-api`) and falls back to cloud download only when needed.
- **🔒 Private & self-contained** — All API traffic stays on your own server (`http://localhost:8081`), never touching Telegram's cloud API endpoint.

---

### 🚀 Multi-Engine Downloader
- **yt-dlp Engine** — High-speed, robust downloads from YouTube, SoundCloud, X (Twitter), Instagram, and hundreds of other platforms.
- **Torrent Engine** — Direct processing and downloading of BitTorrent magnet links.
- **Direct Link Downloader** — Efficient downloads for raw HTTP/HTTPS file URLs.

### ☁️ Smart Upload Destinations
Seamlessly toggle on-the-fly between **native Telegram uploads** and **automated Google Drive** cloud uploads via Rclone.

### 🎛️ Advanced Settings Panel
- **Video Mode:** Cycle between `mp4`, `mkv`, or `default` format.
- **Audio Mode:** Cycle between `mp3`, `m4a`, `flac`, or `default` format.
- **Video Quality:** 480p / 720p / 1080p / 1440p (2K) / 2160p (4K) / Best
- **Audio Quality:** 128 kbps / 192 kbps / 320 kbps

### 📝 Smart Subtitle Embedding (Muxing)
Hard and soft subtitle embedding for English and Persian subtitles via FFmpeg, with a graceful fallback mechanism — if subtitles are unavailable, the bot downloads and sends the video without crashing.

### ⏱️ YouTube Chapters Extraction
Automatically extracts and injects native YouTube timestamp chapters into downloaded video files using FFmpeg metadata injection.

### 🌐 Bilingual UI & 🍪 Cookie Manager
Full Persian and English localization. Includes an interactive cookie manager (via `.txt` file uploads) to bypass age restrictions or access private playlists.

---

## 🏗️ Architecture Overview

TeleCloud-Downloader runs with two deployment modes:

- **Local API mode (`TELEGRAM_LOCAL=1`)**: `telegram-bot` + `telegram-bot-api`
- **Cloud API mode (`TELEGRAM_LOCAL=0`)**: `telegram-bot` only

Local API mode architecture:

```text
┌─────────────────────────────────────────────────────────────┐
│                    Docker Host (Host Network)              │
│                                                             │
│  ┌────────────────────┐    ┌─────────────────────────────┐  │
│  │  telegram-bot-api  │    │       telegram-bot          │  │
│  │  Port: 8081        │◄───│  Uses localhost Bot API     │  │
│  └────────────┬───────┘    └────────────┬────────────────┘  │
│               │                          │                   │
│               └──────────────────────────┘                   │
│      Shared local API storage: /var/lib/telegram-bot-api       │
└─────────────────────────────────────────────────────────────┘
```

**Important runtime detail:** In local mode, `bot.get_file()` can return a relative path. The bot reconstructs the absolute path under `/var/lib/telegram-bot-api/...` before reading the file, with cloud download fallback when needed.

---

## 🛠️ Tech Stack

| Component | Technology | Role |
|---|---|---|
| **Local Bot API** | `aiogram/telegram-bot-api:latest` | ⭐ Removes file size limits → supports up to **2 GB** |
| **Runtime** | Python 3.11+ | Core application language |
| **Bot Framework** | pyTelegramBotAPI | Telegram Bot API integration |
| **Download Engine** | yt-dlp | Multi-platform media downloads |
| **Media Processing** | FFmpeg | Subtitle muxing, chapters, encoding |
| **Containerization** | Docker + Docker Compose | Full service orchestration |
| **Cloud Storage** | Rclone | Google Drive upload integration |
| **Source Control** | Git + GitHub | Version-controlled deployment workflow |

---

## 🚀 Installation & Deployment

### Beginner Path (Recommended): `start.sh`

Use the one-command installer:

```bash
chmod +x start.sh
./start.sh
```

What this does:

- Collects required values (`DOWNLOADER_BOT_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `ADMIN_ID`)
- Lets you choose local API mode (`TELEGRAM_LOCAL=1` or `0`)
- Optionally configures Google Drive (`./rclone.conf`)
- Generates and runs `.start.compose.yml` for your selected mode

For full beginner flow details, see [QUICKSTART.md](./QUICKSTART.md).

### Advanced Path: Manual Docker Setup

#### 1) Prerequisites

- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose Plugin](https://docs.docker.com/compose/install/) (`docker compose` v2)
- Git

#### 2) Clone

```bash
git clone https://github.com/parsa-f/TeleCloud-Downloader.git
cd TeleCloud-Downloader
```

#### 3) Create `.env`

```env
DOWNLOADER_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_API_ID=your_api_id_from_my.telegram.org
TELEGRAM_API_HASH=your_api_hash_from_my.telegram.org
ADMIN_ID=your_numeric_telegram_user_id
TELEGRAM_LOCAL=1
```

#### 4) Prepare required host files/directories

```bash
mkdir -p downloads cookies user_configs
test -f cookies_enabled.json || printf "{}" > cookies_enabled.json
test -f rclone.conf || touch rclone.conf
```

#### 5) Launch

```bash
docker compose up -d --build
docker compose ps
```

Expected services:

- `TELEGRAM_LOCAL=1`: `telegram-bot` + `telegram-bot-api`
- `TELEGRAM_LOCAL=0`: `telegram-bot` only

Logs:

```bash
docker compose logs -f telegram-bot
docker compose logs -f telegram-bot-api
```

---

## 💬 Usage & Commands

### Authentication

Access is approval-based:

- `ADMIN_ID` always has access.
- If `REGISTRATION_OPEN=true`, new users are auto-approved on `/start`.
- If `REGISTRATION_OPEN=false`, users must send `/start` and request access; admin approves/rejects.

### Downloading Media

Send any supported URL or magnet link directly to the bot:

| Input Type | Example |
|---|---|
| YouTube Video | `https://www.youtube.com/watch?v=...` |
| YouTube Playlist | `https://www.youtube.com/playlist?list=...` |
| SoundCloud / Instagram / X | Any yt-dlp-supported URL |
| BitTorrent Magnet Link | `magnet:?xt=urn:btih:...` |
| Direct File URL | `https://example.com/largefile.mp4` |

### Settings Panel

Send `/settings` or tap the **⚙️ Settings** button to open the interactive inline panel:

| Setting | Options |
|---|---|
| **Media Mode** | 🎬 Video / 🎵 Audio |
| **Video Quality** | 480p / 720p / 1080p / 1440p / 2160p / Best |
| **Video Format** | MP4 / MKV / Default |
| **Audio Quality** | 128 kbps / 192 kbps / 320 kbps |
| **Audio Format** | MP3 / M4A / FLAC / Default |
| **Upload Destination** | 📨 Telegram / ☁️ Google Drive |
| **Subtitles** | Off / English / Persian |
| **Chapters** | On / Off |
| **Download Mode** | Auto / yt-dlp / Torrent / Direct |

### Cookie Management

To bypass age restrictions or access private content, upload a **Netscape-format** cookies `.txt` file directly to the bot chat. The cookie manager will process and store it securely.

---

## ⚙️ Configuration Reference

Runtime configuration in `config.py` reads the following `.env` variables:

| Variable | Required | Description |
|---|---|---|
| `DOWNLOADER_BOT_TOKEN` | ✅ Yes | Your Telegram Bot Token from @BotFather |
| `DRIVE_FOLDER_ID` | ⬜ Optional | Default Google Drive root folder ID for admin uploads |
| `ADMIN_ID` | ✅ Yes | Telegram numeric user ID for the bot administrator |
| `REGISTRATION_OPEN` | ⬜ Optional | `true/false` toggle for self-registration on `/start` |
| `MAX_DAILY_FILES` | ⬜ Optional | Default daily file-count quota per user |
| `MAX_DAILY_BYTES` | ⬜ Optional | Default daily byte quota per user |
| `COLAB_URL` | ⬜ Optional | Colab link shown for Drive onboarding |
| `MAX_CONCURRENT_DOWNLOADS` | ⬜ Optional | Parallel download worker limit |
| `TELEGRAM_LOCAL` | ⬜ Optional | `1/true` enables local Bot API mode; `0/false` uses cloud Bot API |

`start.sh` also collects `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` for local Bot API server deployment.

---

## 📁 Project Structure

```text
TeleCloud-Downloader/
├── Dockerfile                  # Bot container build definition
├── docker-compose.yml          # Full multi-container service orchestration
├── .env                        # (Excluded from Git) Secrets & API credentials
├── .gitignore                  # Excludes downloads/, cookies, .env, JSON DBs
├── main.py                     # Bot entry point — always runs from here
├── config.py                   # All settings, shared state, bot object
├── handlers.py                 # Message and command handlers
├── callbacks.py                # Inline keyboard callback query processing
├── menu.py                     # Telegram markup / keyboard builders
├── playlist_menu.py            # YouTube playlist-specific menus
├── dest_helpers.py             # Upload destination routing (Telegram vs Drive)
├── downloader_queue.py         # Async task queue and worker management
├── cookies.py                  # Cookie manager logic
├── utils.py                    # Shared utilities and helper functions
├── user_langs.py               # Per-user language persistence
├── downloaders/                # Download engines
│   ├── __init__.py
│   ├── youtube.py              #   yt-dlp (YouTube, social platforms)
│   ├── social.py               #   General social platform handler
│   ├── torrent.py              #   BitTorrent / magnet link engine
│   └── direct.py              #   Direct HTTP file downloader
└── uploaders/                  # Upload engines
    ├── __init__.py
    ├── telegram_upload.py      #   Local Telegram API uploader
    ├── gdrive_upload.py        #   Rclone / Google Drive uploader
    └── smart_dest.py          #   Destination routing logic
```

> ⚠️ **Important:** Never create a file named `queue.py` inside the bot folder. It conflicts with Python's standard library `queue` module. The queue module in this project is named `downloader_queue.py`.

---

## 💾 Data Persistency & Volumes

All persistent data lives **on the host machine** via Docker bind mounts, ensuring it survives container restarts and image rebuilds:

| Host Path | Container Path | Service | Contents |
|---|---|---|---|
| `./telegram-bot-api-data` | `/var/lib/telegram-bot-api` | `telegram-bot-api` | Local API server session data |
| `./downloads` | `/root/downloads` | Both containers | Shared file staging area (the 2GB transfer bridge) |
| `./cookies` | `/root/cookies` | `telegram-bot` | Netscape-format cookie files |
| `./cookies_enabled.json` | `/root/cookies_enabled.json` | `telegram-bot` | Cookie activation state |
| `./rclone.conf` | `/root/.config/rclone/rclone.conf` | `telegram-bot` | Default Google Drive rclone config file |
| `./user_configs` | `/app/user_configs` | `telegram-bot` | SQLite DB and per-user config files |
| `.` | `/app` | `telegram-bot` | **Live-mounted** bot source code |
| `./telegram-bot-api-data` | `/var/lib/telegram-bot-api` (ro) | `telegram-bot` | Read-only local API file store for direct file reads |

The two `telegram-bot-api-data` mounts are only used when Local API mode is enabled (`TELEGRAM_LOCAL=1`).

> **Tip:** To perform a clean reinstall without losing user data, rebuild only the image: `docker compose build && docker compose up -d`

---

## 🔄 Updating the Bot

The bot code is version-controlled via **Git**. The `/root/bot/` directory is mounted directly into the container as `/app`, so code changes take effect immediately after a container restart — **no image rebuild needed**.

### Standard Update Workflow

```bash
# On your local development machine:
git push origin main

# On the server:
cd /root/bot
git pull
docker restart telegram-bot
```

> ⚠️ **Do NOT** edit files directly on the server using `cat << EOF` or manual text editing. Always push changes via Git and pull them on the server to maintain a clean, reproducible state.

---

## 🔒 Security Notes

- **Access Control:** The bot enforces approval-based access control. Users are admitted through `REGISTRATION_OPEN` policy and/or admin approval.
- **Secret Management:** Keep `.env` out of version control. At minimum it contains bot token and deployment/runtime settings.
- **Local API Isolation:** The Local Telegram Bot API server only listens on `localhost:8081`. It is not exposed to the public internet.
- **Cookie Safety:** The cookie manager handles `.txt` tokens safely. Keep your cookie files secure and never expose them publicly.
- **Rclone Config:** Your `rclone.conf` contains Google account credentials. It is mounted into the container and should never be committed to Git.

---

## 🐛 Troubleshooting & FAQ

<details>
<summary><strong>🔴 The bot is not responding after deployment</strong></summary>

1. Check services with the same compose file you launched with:
   - Manual: `docker compose ps`
   - `start.sh`: `docker compose -f .start.compose.yml ps`
2. View bot logs:
   - Manual: `docker compose logs -f telegram-bot`
   - `start.sh`: `docker compose -f .start.compose.yml logs -f telegram-bot`
3. If local mode is enabled (`TELEGRAM_LOCAL=1`), also check `telegram-bot-api` logs.
4. Verify `DOWNLOADER_BOT_TOKEN` in `.env` is valid and has no extra spaces.

</details>

<details>
<summary><strong>🔴 "File too large" error or upload fails</strong></summary>

The standard Telegram Bot API caps file uploads at **50 MB**. This project runs a **self-hosted Local Telegram Bot API Server** that raises this limit to **2 GB**. If you are seeing this error:

1. Confirm the `telegram-bot-api` container is running: `docker ps | grep telegram-bot-api`
2. Check its logs: `docker logs -f telegram-bot-api`
3. Verify `TELEGRAM_LOCAL=1` is present in your `.env` file.
4. Ensure the bot is configured to point to `http://localhost:8081`.

</details>

<details>
<summary><strong>🔴 Google Drive upload fails</strong></summary>

1. Confirm `./rclone.conf` exists in the project root and is a **file**.
2. Run `docker exec telegram-bot rclone listremotes` to verify rclone sees your remote.
3. Check that your configured Drive remote has write access to the target folder.

</details>

<details>
<summary><strong>🔴 `[Errno 21] Is a directory` for `cookies_enabled.json` or `rclone.conf`</strong></summary>

Docker can create missing bind-mount targets as directories. Ensure both paths exist as files on the host:

```bash
test -f cookies_enabled.json || printf "{}" > cookies_enabled.json
test -f rclone.conf || touch rclone.conf
```

If either path is currently a directory, remove it and recreate it as a file before restarting containers.

</details>

<details>
<summary><strong>🔴 Local Bot API download fails with 404 for Telegram files</strong></summary>

In local mode, `bot.get_file()` may return a relative path (for example `videos/file_6.mp4`). The bot must reconstruct an absolute path under `/var/lib/telegram-bot-api/...` before reading.

This project already includes that guard, and it depends on this mount in `telegram-bot`:

```yaml
- ./telegram-bot-api-data:/var/lib/telegram-bot-api:ro
```

If you removed that mount, put it back and restart.

</details>

<details>
<summary><strong>🔴 Drive uploads fail because folder ID env key is ignored</strong></summary>

Use exact env key casing: `DRIVE_FOLDER_ID` (uppercase `ID`).  
Wrong casing like `DRIVE_FOLDER_iD` will not be read by runtime config.

</details>

<details>
<summary><strong>🔴 Download fails with "403 Forbidden" or age-restriction error</strong></summary>

You need to provide authentication cookies from a logged-in browser session. Export your cookies in **Netscape format** using a browser extension (e.g., "Get cookies.txt LOCALLY"), then upload the `.txt` file directly to the bot chat.

</details>

<details>
<summary><strong>🟡 How do I update the bot to a new version?</strong></summary>

```bash
# On the server:
cd /root/bot
git pull
docker restart telegram-bot
```

Your `.env`, persistent data, and volumes will not be affected.

</details>

<details>
<summary><strong>🟡 How do I stop all services?</strong></summary>

```bash
docker compose down
```

To stop and remove all associated data volumes as well:

```bash
docker compose down -v
```

</details>

<details>
<summary><strong>🟡 Why can't I name my file "queue.py"?</strong></summary>

The name `queue` conflicts with Python's built-in standard library module. Any file named `queue.py` inside the bot directory (`/app`) will shadow the standard library's `queue` module and break the application. The queue implementation in this project is named `downloader_queue.py`.

</details>

---

## 🤝 Contributing

Contributions are warmly welcome! Here's how to get involved:

1. **Fork** the repository on GitHub.
2. **Create a feature branch:** `git checkout -b feature/your-amazing-feature`
3. **Commit your changes** with clear, descriptive messages: `git commit -m "feat: add amazing feature"`
4. **Push** to your fork: `git push origin feature/your-amazing-feature`
5. **Open a Pull Request** against the `main` branch, describing what you changed and why.

### Development Guidelines

- Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code style.
- Keep changes focused — one feature or fix per PR.
- Update the relevant README section if your change affects the user-facing workflow.
- For bilingual strings, add entries to both English and Persian sections in `locales.py`.
- Never name a file `queue.py` inside the bot directory.

### Reporting Issues

Please open a [GitHub Issue](https://github.com/parsa-f/TeleCloud-Downloader/issues) with:
- A clear description of the bug or feature request.
- Steps to reproduce (for bugs).
- Relevant logs from `docker logs telegram-bot` or `docker logs telegram-bot-api`.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).





