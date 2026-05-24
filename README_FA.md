<div align="center" dir="rtl">
  <h1>☁️ TeleCloud-Downloader (دانلودر ابری تلگرام)</h1>
  <p><strong>ربات مدیریت دانلود پیشرفته، کاملاً ماژولار و ناهمگام (Asynchronous) تلگرام</strong></p>

  <a href="./README.md">🇺🇸 Read in English</a>
  <br><br>

  <!-- Badges -->
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/pyTelegramBotAPI-Latest-blue.svg?logo=telegram&logoColor=white" alt="pyTelegramBotAPI">
  <img src="https://img.shields.io/badge/Docker-Supported-2496ED.svg?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/yt--dlp-Powered-red.svg?logo=youtube&logoColor=white" alt="yt-dlp">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</div>

<div dir="rtl">

## ✨ ویژگی‌ها (Features)

- **🚀 دانلودر چندموتوره (Multi-Engine):**
  - **موتور yt-dlp:** دانلود پرسرعت و پایدار از پلتفرم‌هایی نظیر یوتیوب، ساندکلاد، ایکس (توییتر)، اینستاگرام و غیره.
  - **موتور تورنت (Torrent):** پردازش مستقیم و دانلود از طریق مگنت لینک‌های بیت‌تورنت.
  - **دانلودر لینک مستقیم:** دانلود بهینه و سریع برای فایل‌های خام.
- **☁️ مقاصد آپلود هوشمند:** امکان تغییر آنی (On-the-fly) بین آپلود مستقیم در سرورهای تلگرام و آپلود خودکار در فضای ابری گوگل درایو (از طریق Rclone).
- **🔄 چرخه پیشرفته فرمت‌های رسانه:** پنل تنظیمات کاملاً هوشمند.
  - *حالت ویدیو:* جابجایی بین فرمت‌های `mp4`، `mkv` یا `default`.
  - *حالت صوت:* جابجایی بین `mp3`، `m4a`، `flac` یا `default`.
- **🎛️ تنظیمات کیفیت مستقل:** کنترل دقیق روی فایل‌ها. چرخه کیفیت ویدیو از 480p تا 4K (2160p) و 2K (1440p). چرخه کیفیت صدا از 128kbps تا 320kbps.
- **📝 ادغام هوشمند زیرنویس (Muxing):** پشتیبانی از چسباندن (Hard-sub) و قرار دادن (Soft-sub) زیرنویس‌های فارسی و انگلیسی روی ویدیوها توسط FFmpeg. مجهز به سیستم Fallback جایگزین — در صورتی که زیرنویس یافت نشود، ربات کرش نمی‌کند بلکه ویدیو را دانلود کرده و به کاربر اطلاع می‌دهد.
- **⏱️ استخراج چپترهای یوتیوب:** استخراج و تزریق خودکار متادیتا و زمان‌بندی‌های (Chapters) یوتیوب به داخل فایل ویدیویی با استفاده از امکانات پیشرفته FFmpeg.
- **🌐 رابط کاربری دوزبانه و 🍪 مدیریت کوکی‌ها:** بومی‌سازی روان به زبان‌های فارسی و انگلیسی. دارای سیستم مدیریت کوکی تعاملی (آپلود فایل `.txt`) برای دور زدن محدودیت‌های سنی یا دانلود از پلی‌لیست‌های خصوصی.

## 🛠️ تکنولوژی‌ها و پیش‌نیازها

برای اجرای پروژه، محیط شما باید دارای پیش‌نیازهای زیر باشد:
- **پایتون (Python):** نسخه 3.11 یا بالاتر
- **کتابخانه‌های اصلی:** `pyTelegramBotAPI`, `yt-dlp`
- **پردازش رسانه:** `FFmpeg` (الزامی برای Muxing و تزریق متادیتا)
- **استقرار (Deployment):** `Docker`, `Docker-compose`
- **فضای ابری:** `Rclone` (برای اتصال به گوگل درایو)

## 🚀 نصب و راه‌اندازی (Deployment)

تله‌کلود دانلودر به گونه‌ای طراحی شده که به راحتی با داکر (Docker) مستقر شود.

### ۱. پیکربندی
یک فایل `.env` در مسیر اصلی پروژه ایجاد کرده و متغیرهای محیطی خود را تنظیم کنید:

```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_admin_id
BOT_PASSWORD=your_secure_password
RCLONE_CONFIG_PATH=/app/rclone.conf
```

### ۲. داکر کمپوز (Docker Compose)
از قالب زیر برای فایل `docker-compose.yml` استفاده کنید:

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

### ۳. بیلد و اجرا
دستورات زیر را برای کلون کردن مخزن، ساخت ایمیج و اجرای کانتینر در پس‌زمینه وارد کنید:

```bash
git clone https://github.com/yourusername/TeleCloud-Downloader.git
cd TeleCloud-Downloader
# Ensure .env and rclone.conf are set up
docker compose up -d --build
```

## ⚙️ نحوه استفاده و تنظیمات

- **پنل تنظیمات تعاملی:** ربات دارای یک پنل شیشه‌ای (Inline) تنظیمات با چیدمان شبکه‌ای (Grid) دو ستونه است. این پنل به شما اجازه می‌دهد فرمت‌ها، کیفیت‌ها و مقصد آپلود را به سادگی تغییر دهید.
- **سیستم صف ناهمگام (Asynchronous Queue):** به صورت پایه‌ای برای مدیریت کارآمد چندین ورکر (Worker) دانلود همزمان طراحی شده است. مدیر صف بدون مسدود کردن رویدادهای اصلی (Event loop)، وظایف را زمان‌بندی و اجرا می‌کند تا تجربه‌ای روان حتی در بارهای کاری سنگین ارائه دهد.

## 📁 ساختار پروژه

```text
TeleCloud-Downloader/
├── main.py                 # نقطه ورود ربات و مدیریت چرخه حیات
├── config.py               # متغیرهای محیطی و تنظیمات
├── handlers.py             # کنترل‌کننده‌های پیام‌ها و دستورات
├── callbacks.py            # پردازش کوئری‌های دکمه‌های شیشه‌ای
├── dest_helpers.py         # مسیریابی مقاصد آپلود (تلگرام یا گوگل درایو)
├── downloader_queue.py     # صف ناهمگام وظایف و مدیریت ورکرها
├── downloaders/            # موتورهای دانلود (yt-dlp, torrent, direct)
├── uploaders/              # موتورهای آپلود (Telegram API, Rclone)
└── locales.py              # دیکشنری‌های بومی‌سازی دوزبانه (En/Fa)
```

## 🔒 نکات امنیتی

- **کنترل دسترسی:** ربات از سیستم محافظت با رمز عبور پشتیبانی می‌کند. تنها کاربرانی که `BOT_PASSWORD` صحیح را در اختیار داشته باشند مجاز به استفاده هستند.
- **امنیت کوکی‌ها:** مدیر کوکی توکن‌های `.txt` را به صورت امن پردازش می‌کند. همواره اطمینان حاصل کنید که فایل‌های کوکی شما امن نگه داشته شده و به صورت عمومی فاش نشوند.

## 📄 لایسنس

این پروژه تحت مجوز [MIT License](LICENSE) منتشر شده است.

</div>
