<div dir="rtl">

# راهنمای نصب TeleCloud-Downloader

> نسخه انگلیسی: [SETUP.md](./SETUP.md)
> مستند اصلی: [README_FA.md](./README_FA.md)

## نمای کلی

این راهنما روش استقرار و اجرای TeleCloud-Downloader را در حالت production (Docker) و حالت محلی (بدون Docker) توضیح می‌دهد.

## راه‌اندازی با Docker (پیشنهادی)

### 1. پیش‌نیازها

- Docker Engine
- Docker Compose v2 (`docker compose`)
- Git

### 2. Clone

```bash
git clone https://github.com/parsa-f/TeleCloud-Downloader.git
cd TeleCloud-Downloader
```

### 3. ساخت فایل‌های لازم روی هاست قبل از اجرای اول

این فایل‌ها باید قبل از `docker compose up` روی هاست به‌صورت فایل وجود داشته باشند:

```bash
touch cookies_enabled.json
touch rclone.conf
```

بررسی:

```bash
ls -la
```

### 4. پیکربندی `.env`

حداقل مقادیر:

```env
DOWNLOADER_BOT_TOKEN=...
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

### اختیاری: اسکریپت شروع سریع (مناسب مبتدی‌ها)

اگر روی سرور Ubuntu/Debian Linux استقرار می‌دهید و نصب مرحله‌به‌مرحله یک‌بار مصرف می‌خواهید، از `start.sh` استفاده کنید:

```bash
chmod +x start.sh
./start.sh
```

اسکریپت `start.sh` چه کار می‌کند:

- context پروژه را بررسی و مسیرها/فایل‌های ضروری را اعتبارسنجی می‌کند
- وابستگی‌های سرور را نصب/بررسی می‌کند (`git`, `curl`, `unzip`, Docker, Docker Compose)
- متغیرهای ضروری `.env` را می‌پرسد (token، API ID/hash، admin ID)
- مقدارهای امن پیش‌فرض برای تنظیمات پیشرفته قرار می‌دهد
- راه‌اندازی Google Drive (`rclone.conf`) را با مسیر جایگزین Colab راهبری می‌کند
- اگر Drive رد شود، وجود فایل placeholder برای `./rclone.conf` را اجباری می‌کند (برای جلوگیری از خطای mount شدن دایرکتوری در Docker)
- کانتینرها را build و start می‌کند و وضعیت سرویس را نمایش می‌دهد

نکته مهم:

- این نصب‌کننده برای سرورهای Ubuntu/Debian Linux طراحی شده است.
- آن را از ریشه پروژه اجرا کنید (پروژه باید از قبل extract شده باشد).
- اگر Drive را رد کنید، ربات همچنان در حالت Telegram-only بالا می‌آید.

## اجرای محلی (بدون Docker)

### 1. پیش‌نیازها

- Python 3.11+
- `ffmpeg`
- `aria2c`
- `rclone`
- دسترسی به Local Telegram Bot API server روی `http://localhost:8081`

### 2. نصب وابستگی‌های پایتون

```bash
pip install -r requirements.txt
```

### 3. اجرا

```bash
python3 main.py
```

## باگ‌های عمومی احتمالی

### Local Bot API مسیر فایل را نسبی برمی‌گرداند (نه مطلق)

در زمان استفاده از Local Telegram Bot API self-hosted (`aiogram/telegram-bot-api`)، ممکن است `bot.get_file()` به‌جای مسیر مطلق کامل `/var/lib/telegram-bot-api/<token>/videos/file_6.mp4` یک مسیر نسبی مثل `videos/file_6.mp4` برگرداند.

اگر `bot.download_file()` را با همین مسیر نسبی صدا بزنید، درخواست به cloud Telegram servers می‌رود و چون فایل فقط روی سرور local شما وجود دارد، HTTP 404 دریافت می‌کنید.

راه‌حل:

`telegram-bot-api-data` را به صورت read-only داخل کانتینر ربات mount کنید:

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

این guard باید روی همه call siteهای `bot.get_file()` اعمال شود؛ نه فقط handler اصلی فایل، بلکه آپلود cookie و آپلود `rclone.conf` را هم شامل شود.

همچنین توجه کنید: `cookies_enabled.json` و `rclone.conf` باید قبل از `docker compose up` روی هاست به‌صورت فایل وجود داشته باشند. اگر فایل نباشند، Docker ممکن است آن‌ها را به شکل دایرکتوری خالی بسازد و در زمان اجرا خطای `[Errno 21] Is a directory` ایجاد شود. قبل از بالا آوردن کانتینرها همیشه با `ls -la` بررسی کنید.

</div>
