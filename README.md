<div align="center">
  <h1>☁️ TeleCloud-Downloader</h1>
  <p><strong>Advanced, Fully Modular Asynchronous Telegram Download Manager</strong></p>

  <a href="./README_FA.md">🇮🇷 فارسی</a>
  <br><br>

  <!-- Badges -->
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/pyTelegramBotAPI-Latest-blue.svg?logo=telegram&logoColor=white" alt="pyTelegramBotAPI">
  <img src="https://img.shields.io/badge/Docker-Supported-2496ED.svg?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/yt--dlp-Powered-red.svg?logo=youtube&logoColor=white" alt="yt-dlp">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</div>

## ✨ Features

- **🚀 Multi-Engine Downloader:** 
  - **yt-dlp Engine:** High-speed, robust downloads from platforms like YouTube, SoundCloud, X (Twitter), Instagram, and more.
  - **Torrent Engine:** Direct processing and downloading of BitTorrent magnet links.
  - **Direct Link Downloader:** Efficient and fast downloads for raw file URLs.
- **☁️ Smart Upload Destinations:** Seamlessly toggle on-the-fly between native Telegram uploads and automated Google Drive cloud uploads via Rclone.
- **🔄 Advanced Media Format Cycle:** Fully context-aware settings panel.
  - *Video mode:* Cycle seamlessly between `mp4`, `mkv`, or `default`.
  - *Audio mode:* Cycle between `mp3`, `m4a`, `flac`, or `default`.
- **🎛️ Independent Quality Settings:** Granular control over your media. Video quality ranges from 480p up to 4K (2160p) & 2K (1440p). Audio quality ranges from 128kbps to 320kbps.
- **📝 Smart Subtitle Embedding (Muxing):** Supports hard and soft embedding of English and Persian subtitles directly into videos via FFmpeg. Features an automatic robust fallback mechanism—if subtitles are missing, it gracefully downloads the video and notifies you instead of crashing.
- **⏱️ YouTube Chapters Extraction:** Automatically extracts and embeds native YouTube timestamp chapters into the downloaded video file using advanced FFmpeg metadata injection.
- **🌐 Bilingual UI & 🍪 Active Cookie Manager:** Smooth Persian and English localization. Includes an interactive cookie manager (via `.txt` file uploads) to bypass age restrictions or download from private playlists.

## 🛠️ Tech Stack & Prerequisites

Before deploying, ensure your environment meets the following requirements:
- **Python:** 3.11 or higher
- **Core Libraries:** `pyTelegramBotAPI`, `yt-dlp`
- **Media Processing:** `FFmpeg` (Required for muxing and metadata injection)
- **Deployment:** `Docker`, `Docker-compose`
- **Cloud Storage:** `Rclone` (For Google Drive integration)

## 🚀 Installation & Deployment

TeleCloud-Downloader is designed to be easily deployed using Docker.

### 1. Configuration
Create a `.env` file in the root directory and configure your environment variables:

```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_admin_id
BOT_PASSWORD=your_secure_password
RCLONE_CONFIG_PATH=/app/rclone.conf
```

### 2. Docker Compose
Use the following `docker-compose.yml` template to define your service:

```yaml
version: '3.8'

services:
  telecloud-bot:
    build: .
    container_name: telecloud_downloader
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./downloads:/app/downloads
      - ./rclone.conf:/app/rclone.conf:ro
```

### 3. Build & Run
Run these commands to clone the repository, build the image, and start the container in detached mode:

```bash
git clone https://github.com/yourusername/TeleCloud-Downloader.git
cd TeleCloud-Downloader
# Ensure .env and rclone.conf are set up
docker compose up -d --build
```

## ⚙️ Configuration & Usage

- **Interactive Settings Panel:** The bot features a dynamic 2-column grid inline settings panel. This allows you to easily toggle formats, qualities, and upload destinations.
- **Asynchronous Queue System:** Built from the ground up to handle concurrent download workers efficiently. The queue manager schedules and executes tasks without blocking the main event loop, ensuring a smooth experience even under heavy load.

## 📁 Project Structure

```text
TeleCloud-Downloader/
├── main.py                 # Bot entry point and lifecycle manager
├── config.py               # Environment variables and configuration
├── handlers.py             # Message and command handlers
├── callbacks.py            # Inline keyboard callback query processing
├── dest_helpers.py         # Upload destination routing (Telegram vs Drive)
├── downloader_queue.py     # Asynchronous task queue and worker management
├── downloaders/            # Download engines (yt-dlp, torrent, direct)
├── uploaders/              # Upload engines (Telegram API, Rclone)
└── locales.py              # Bilingual (En/Fa) localization dictionaries
```

## 🔒 Security Notes

- **Access Control:** The bot implements mandatory password protection. Only authorized users with the correct `BOT_PASSWORD` can interact with it.
- **Cookie Safety:** The cookie manager handles `.txt` tokens safely. Always ensure your cookie files are kept secure and are never exposed publicly.

## 📄 License

This project is licensed under the [MIT License](LICENSE).
