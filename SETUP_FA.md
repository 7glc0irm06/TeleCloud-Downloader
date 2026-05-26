<div dir="rtl">

# راهنمای راه‌اندازی TeleCloud-Downloader

> نسخه انگلیسی: [SETUP.md](./SETUP.md)
> مستند اصلی: [README_FA.md](./README_FA.md)

## نمای کلی

این راهنما روش راه‌اندازی TeleCloud-Downloader را در حالت production (Docker) و اجرای محلی (بدون Docker) توضیح می‌دهد.

## راه‌اندازی با Docker (پیشنهادی)

### 1. پیش‌نیازها

- Docker Engine
- Docker Compose v2 (`docker compose`)
- Git

### 2. کلون مخزن

```bash
git clone https://github.com/parsa-f/TeleCloud-Downloader.git
cd TeleCloud-Downloader
```

### 3. ساخت فایل‌های لازم روی هاست قبل از اجرای اولیه

این فایل‌ها باید قبل از `docker compose up` روی هاست به صورت فایل وجود داشته باشند:

```bash
touch cookies_enabled.json
touch rclone.conf
```

بررسی:

```bash
ls -la
```

### 4. تنظیم `.env`

حداقل متغیرهای لازم:

```env
DOWNLOADER_BOT_TOKEN=...
BOT_PASSWORD=...
TELEGRAM_API_ID=...
TELEGRAM_API_HASH=...
TELEGRAM_LOCAL=1
ADMIN_ID=123456789
```

### 5. اجرا

```bash
docker compose up -d --build
docker compose ps
```

## اجرای محلی (بدون Docker)

### 1. پیش‌نیازها

- Python 3.11+
- `ffmpeg`
- `aria2c`
- `rclone`
- دسترسی به Local Telegram Bot API روی `http://localhost:8081`

### 2. نصب وابستگی‌های پایتون

```bash
pip install pyTelegramBotAPI yt-dlp requests
```

### 3. اجرا

```bash
python3 main.py
```

## باگ‌های عمومی احتمالی

### Local Bot API مسیر فایل را نسبی برمی‌گرداند (نه مطلق)

در حالت استفاده از Local Telegram Bot API self-hosted (`aiogram/telegram-bot-api`)، ممکن است `bot.get_file()` به‌جای مسیر مطلق کامل، یک مسیر نسبی مثل `videos/file_6.mp4` برگرداند، نه مسیر کامل `/var/lib/telegram-bot-api/<token>/videos/file_6.mp4`.

اگر `bot.download_file()` را با همین مسیر نسبی صدا بزنید، درخواست به سرورهای cloud تلگرام می‌رود و چون فایل فقط روی سرور لوکال شما وجود دارد، پاسخ HTTP 404 می‌گیرید.

راه‌حل:

پوشه `telegram-bot-api-data` را به صورت read-only داخل کانتینر ربات mount کنید:

```yaml
- ./telegram-bot-api-data:/var/lib/telegram-bot-api:ro
```

قبل از خواندن فایل، مسیر مطلق را در کد بازسازی کنید:

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

این guard را برای همه call siteهای `bot.get_file()` اعمال کنید؛ نه فقط handler اصلی فایل، بلکه مسیرهای آپلود cookie و آپلود `rclone.conf` را هم شامل شود.

نکته مهم دیگر: `cookies_enabled.json` و `rclone.conf` باید قبل از `docker compose up` روی هاست به شکل فایل وجود داشته باشند. اگر نباشند، Docker ممکن است آن‌ها را به صورت دایرکتوری خالی بسازد و در زمان اجرا خطای `[Errno 21] Is a directory` ایجاد شود. قبل از بالا آوردن کانتینرها همیشه با `ls -la` بررسی کنید.

</div>
