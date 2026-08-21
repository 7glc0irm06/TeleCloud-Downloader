#!/bin/sh
set -e

# ── Start Local Telegram Bot API Server (enables 2GB uploads) ──
API_ID="${TELEGRAM_API_ID:-0}"
API_HASH="${TELEGRAM_API_HASH:-00000000000000000000000000000000}"

mkdir -p /var/lib/telegram-bot-api /root/downloads /root/storage /root/.config/rclone
# empty rclone config placeholder (gdrive path is disabled, but keep file present)
if [ ! -f /root/.config/rclone/rclone.conf ]; then
  printf '[gdrive]\ntype = drive\n' > /root/.config/rclone/rclone.conf
fi

echo "[railway] starting telegram-bot-api on 0.0.0.0:8081 (local mode)"
/usr/local/bin/telegram-bot-api \
  --local \
  --api-id "$API_ID" \
  --api-hash "$API_HASH" \
  --http-port 8081 \
  --dir /var/lib/telegram-bot-api \
  --log /var/lib/telegram-bot-api/bot-api.log \
  &

sleep 4

# ── Wait for Postgres (if DATABASE_URL is set) ──
if [ -n "$DATABASE_URL" ]; then
  echo "[railway] waiting for Postgres..."
  for i in $(seq 1 30); do
    if python3 -c "import psycopg2,os; psycopg2.connect(os.environ['DATABASE_URL'], connect_timeout=2).close(); print('ok')" 2>/dev/null; then
      echo "[railway] Postgres is up"
      break
    fi
    sleep 2
  done
fi

echo "[railway] starting bot"
exec python3 main.py
