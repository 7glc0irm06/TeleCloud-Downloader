# TeleCloud-Downloader Quick Start (Beginners)

> Persian version: [QUICKSTART_FA.md](./QUICKSTART_FA.md)  
> Full setup guide: [SETUP.md](./SETUP.md)

This guide is for beginners who want a one-command setup on Ubuntu/Debian.

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

## What `start.sh` does

- Installs/checks required tools and Docker stack
- Creates required folders/files safely
- Collects required bot settings (`DOWNLOADER_BOT_TOKEN`, `BOT_PASSWORD`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `ADMIN_ID`)
- Supports re-setup mode to review/edit existing `.env` values
- Lets you choose Local Bot API mode and Google Drive mode
- Shows a summary and asks confirmation before launch
- Starts containers with an auto-generated runtime compose file

## Deployment Modes

### 1) Full Mode (Local API + Drive)

- `TELEGRAM_LOCAL=1`
- Local `telegram-bot-api` service enabled
- Supports uploads up to 2GB
- `rclone.conf` configured for Drive uploads

### 2) No Drive Mode (Local API only)

- `TELEGRAM_LOCAL=1`
- Local `telegram-bot-api` service enabled
- Supports uploads up to 2GB
- Drive disabled; bot works with Telegram-only delivery
- Installer still ensures `./rclone.conf` exists as a file placeholder

### 3) Simple Mode (No Local API, No Drive)

- `TELEGRAM_LOCAL=0`
- Local `telegram-bot-api` service skipped
- Telegram cloud API mode (20MB limit applies)
- Drive disabled; Telegram-only workflow

## Re-run Behavior

You can run `./start.sh` again anytime:

- If `.env` is complete, it asks:
  - `1) Review / edit existing values`
  - `2) Keep existing values and continue`
- If you choose continue, previously answered optional modes are reused
- Required safety files are always enforced:
  - `cookies_enabled.json` must be a file containing `{}`
  - `rclone.conf` must be a file (placeholder is created when Drive is disabled)
