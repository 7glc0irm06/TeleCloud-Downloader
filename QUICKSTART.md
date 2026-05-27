# TeleCloud-Downloader Quick Start (Beginners)

> Persian version: [QUICKSTART_FA.md](./QUICKSTART_FA.md)  
> Full setup guide: [SETUP.md](./SETUP.md)

This guide is for beginners who want a one-command installation flow on Ubuntu/Debian.

## Requirements

- Ubuntu/Debian server
- Internet access
- A user with `sudo` access
- Project already extracted/cloned

## Run the installer

From project root:

```bash
chmod +x start.sh
./start.sh
```

## What the script does

- Installs/checks required server tools and Docker stack
- Creates required folders/files safely
- Asks you for required bot variables:
  - `DOWNLOADER_BOT_TOKEN`
  - `BOT_PASSWORD`
  - `TELEGRAM_API_ID`
  - `TELEGRAM_API_HASH`
  - `ADMIN_ID`
- Writes safe defaults for advanced settings
- Handles Google Drive setup (`rclone.conf`) with fallback instructions
- Starts the bot with Docker Compose

## Google Drive note

If you skip Google Drive during setup, the installer still creates `./rclone.conf` as a placeholder file.  
This prevents Docker mount crashes and starts the bot in Telegram-only mode.

## Re-run behavior

You can run `./start.sh` again anytime:

- Keeps existing valid `.env` values
- Re-checks system and files
- Prompts only for missing essentials (for example, missing Drive config)

