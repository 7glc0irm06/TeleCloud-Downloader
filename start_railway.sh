#!/bin/sh
set -e

# ── Start Local Telegram Bot API Server (enables 2GB uploads) ──
# Reads API_ID / API_HASH from env (my.telegram.org). Falls back to public
# values if not provided (bot-api can run without them for local mode).
API_ID="${TELEGRAM_API_ID:-0}"
API_HASH="${TELEGRAM_API_HASH:-00000000000000000000000000000000}"

mkdir -p /var/lib/telegram-bot-api /root/downloads

echo "[railway] starting telegram-bot-api on 0.0.0.0:8081 (local mode)"
telegram-bot-api \
  --local \
  --api-id "$API_ID" \
  --api-hash "$API_HASH" \
  --http-port 8081 \
  --dir /var/lib/telegram-bot-api \
  --log /var/lib/telegram-bot-api/bot-api.log \
  &

# give the API server a moment to bind
sleep 4

echo "[railway] starting bot"
exec python3 main.py
