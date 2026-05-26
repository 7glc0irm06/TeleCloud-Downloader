#!/bin/sh
cd /root/bot

# اطمینان از وجود فایل‌های ضروری
[ ! -f cookies_enabled.json ] && echo '{}' > cookies_enabled.json
[ ! -f rclone.conf ] && cp /root/.config/rclone/rclone.conf rclone.conf

docker compose up -d
