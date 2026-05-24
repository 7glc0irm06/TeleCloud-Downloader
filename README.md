<div align="center">
  <h1>☁️ TeleCloud-Downloader</h1>
  <p><strong>Advanced, Fully Modular Asynchronous Telegram Download Manager</strong></p>

  <a href="./README_FA.md">🇮🇷 مستندات فارسی</a>
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
- [🏗️ Architecture Overview](#️-architecture-overview)
- [🛠️ Tech Stack](#️-tech-stack)
- [🚀 Installation & Deployment](#-installation--deployment)
- [💬 Usage & Commands](#-usage--commands)
- [⚙️ Configuration Reference](#️-configuration-reference)
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
- **⚡ Lightning-fast local file transfers** — In local mode, `getFile` returns the physical path of the downloaded file on disk. The bot uses `shutil.copy2` via a **shared Docker volume** (`/root/downloads`) to move files between containers instantly — no HTTP re-download, no network overhead.
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

TeleCloud-Downloader is orchestrated as a **multi-container Docker application** using `docker-compose`. Four containers always run together:

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Host (Host Network)                │
│                                                             │
│  ┌────────────────────┐    ┌─────────────────────────────┐  │
│  │  telegram-bot-api  │    │       telegram-bot           │  │
│  │  (Local API Server)│    │    (Downloader Bot)          │  │
│  │  Port: 8081        │◄───│  Communicates via localhost  │  │
│  │  aiogram/tg-bot-api│    │  parsafadaeei/telegram-bot  │  │
│  └────────────┬───────┘    └────────────┬────────────────┘  │
│               │                          │                   │
│               └──────────────────────────┘                   │
│               Shared Volume: /root/downloads                 │
│         (Files transferred via shutil.copy2, not HTTP)       │
│                                                             │
│  ┌──────────────────┐    ┌──────────────────────────────┐   │
│  │   goose-server   │    │       goose-manager          │   │
│  └──────────────────┘    └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Key design choice:** Both containers share the same `network_mode: host` and the same `/root/downloads` bind mount. When the Local API Server saves a file, the bot reads it from the **exact same path on disk** using `shutil.copy2` — making uploads near-instantaneous regardless of file size.

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

> **The `Dockerfile` and `docker-compose.yml` are included in the repository.** Clone, configure, and run — that's all.

### Step 1 — Prerequisites

Ensure the following are installed on your server (Ubuntu/Linux recommended):

- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose Plugin](https://docs.docker.com/compose/install/) (`docker compose` v2)
- Git

### Step 2 — Clone the Repository

```bash
git clone https://github.com/parsa-f/TeleCloud-Downloader.git
cd TeleCloud-Downloader
```

### Step 3 — Configure Environment Variables

Create a `.env` file in the project root. This file is **excluded from Git** (via `.gitignore`) and will never be committed.

```env
# ─── Telegram Bot Credentials ─────────────────────────────
DOWNLOADER_BOT_TOKEN=your_telegram_bot_token_here
BOT_PASSWORD=your_secure_access_password

# ─── Local Telegram Bot API (Required for 2GB file support) ─
TELEGRAM_API_ID=your_api_id_from_my.telegram.org
TELEGRAM_API_HASH=your_api_hash_from_my.telegram.org
TELEGRAM_LOCAL=1

# ─── Optional ─────────────────────────────────────────────
# Path to rclone config inside the container (default shown)
RCLONE_CONFIG_PATH=/root/.config/rclone/rclone.conf
```

> **How to get `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`:**  
> Log in to [my.telegram.org](https://my.telegram.org), go to **API Development Tools**, and create an application. Copy the `api_id` and `api_hash`.

> **How to get your Bot Token:**  
> Open [@BotFather](https://t.me/BotFather) on Telegram, run `/newbot`, and copy the provided token.

### Step 4 — Configure Rclone (for Google Drive)

If you intend to use Google Drive uploads, place your `rclone.conf` at the expected host path: `/root/.config/rclone/rclone.conf`. The `docker-compose.yml` mounts this directory into the container.

```bash
# If you already have rclone configured on your machine:
rclone config   # then authorize your Google Drive remote

# Or copy an existing config:
cp ~/.config/rclone/rclone.conf /root/.config/rclone/rclone.conf
```

> If you **do not** use Google Drive, this step can be skipped. The bot will still work with Telegram-only uploads.

### Step 5 — Build & Launch

```bash
docker compose up -d --build
```

Confirm all 4 containers are running:

```bash
docker compose ps
# or
docker ps
```

View live logs:

```bash
docker logs -f telegram-bot
docker logs -f telegram-bot-api
```

---

## 💬 Usage & Commands

### Authentication

The bot is password-protected. On first use, send the password you set in `BOT_PASSWORD` to the bot:

```
your_secure_access_password
```

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

All configuration is driven by the `.env` file, which is shared by all containers via `env_file`. Below is the full reference:

| Variable | Required | Description |
|---|---|---|
| `DOWNLOADER_BOT_TOKEN` | ✅ Yes | Your Telegram Bot Token from @BotFather |
| `BOT_PASSWORD` | ✅ Yes | Password users must enter to authenticate |
| `TELEGRAM_API_ID` | ✅ Yes | App API ID from [my.telegram.org](https://my.telegram.org) (required by Local Bot API) |
| `TELEGRAM_API_HASH` | ✅ Yes | App API Hash from [my.telegram.org](https://my.telegram.org) (required by Local Bot API) |
| `TELEGRAM_LOCAL` | ✅ Yes | Must be set to `1` to enable local API mode |
| `RCLONE_CONFIG_PATH` | ⬜ Optional | Path to `rclone.conf` inside container |

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
| `./.config/rclone` | `/root/.config/rclone` | `telegram-bot` | Rclone Google Drive credentials |
| `./bot` | `/app` | `telegram-bot` | **Live-mounted** bot source code (Git repo) |

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

- **Access Control:** The bot enforces mandatory password authentication. Only users who provide the correct `BOT_PASSWORD` can interact with it.
- **Secret Management:** `BOT_PASSWORD`, `DOWNLOADER_BOT_TOKEN`, `TELEGRAM_API_ID`, and `TELEGRAM_API_HASH` are loaded from `.env`, which is excluded from version control. **Never commit your `.env` file.**
- **Local API Isolation:** The Local Telegram Bot API server only listens on `localhost:8081`. It is not exposed to the public internet.
- **Cookie Safety:** The cookie manager handles `.txt` tokens safely. Keep your cookie files secure and never expose them publicly.
- **Rclone Config:** Your `rclone.conf` contains Google account credentials. It is mounted into the container and should never be committed to Git.

---

## 🐛 Troubleshooting & FAQ

<details>
<summary><strong>🔴 The bot is not responding after deployment</strong></summary>

1. Check that all containers are running: `docker ps`
2. View bot logs for errors: `docker logs -f telegram-bot`
3. View Local API logs: `docker logs -f telegram-bot-api`
4. Verify your `DOWNLOADER_BOT_TOKEN` in `.env` is correct and has no extra spaces.
5. Confirm `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, and `TELEGRAM_LOCAL=1` are all set in `.env`.

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

1. Confirm `rclone.conf` exists at the host path `/root/.config/rclone/rclone.conf`.
2. Run `docker exec telegram-bot rclone listremotes` to verify rclone sees your remote.
3. Check that your configured Drive remote has write access to the target folder.

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
