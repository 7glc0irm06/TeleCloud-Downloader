<div align="center" dir="rtl">
  <h1>☁️ TeleCloud-Downloader</h1>
  <p><strong>ربات مدیریت دانلود پیشرفته، کاملاً ماژولار و ناهمگام (Asynchronous) تلگرام</strong></p>

  <a href="./README.md">🇺🇸 Read in English</a>
  <br>
  <a href="./QUICKSTART_FA.md">⚡ شروع سریع</a> · <a href="./QUICKSTART.md">⚡ English Quick Start</a>
  <br>
  <a href="./SETUP_FA.md">🛠️ راهنمای نصب</a> · <a href="./SETUP.md">🛠️ English Setup Guide</a>
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

<div dir="rtl">

## 📖 فهرست مطالب

- [✨ ویژگی‌ها](#-ویژگیها)
- [🏗️ معماری کلی سیستم](#-معماری-کلی-سیستم)
- [🛠️ تکنولوژی‌ها](#-تکنولوژیها)
- [🚀 نصب و راه‌اندازی](#-نصب-و-راهاندازی)
- [💬 نحوه استفاده و دستورات](#-نحوه-استفاده-و-دستورات)
- [⚙️ راهنمای متغیرهای محیطی](#-راهنمای-متغیرهای-محیطی)
- [📁 ساختار پروژه](#-ساختار-پروژه)
- [💾 پایداری داده‌ها و ولوم‌ها](#-پایداری-دادهها-و-ولومها)
- [🔒 نکات امنیتی](#-نکات-امنیتی)
- [🐛 عیب‌یابی و سوالات متداول](#-عیبیابی-و-سوالات-متداول)
- [📄 لایسنس](#-لایسنس)

---

## ✨ ویژگی‌ها

### ☁️ یکپارچه‌سازی Google Drive با Rclone
فایل‌های دانلودشده را می‌توانید با Rclone مستقیماً در Google Drive آپلود کنید و بر اساس تنظیمات، مقصد را بین Telegram و Drive تغییر دهید.

---

### 🔥 سرور محلی Telegram Bot API — بدون محدودیت حجم فایل
> این مهم‌ترین ویژگی معماری TeleCloud-Downloader است.

برخلاف ربات‌های معمولی که با محدودیت پیش‌فرض تلگرام (**۲۰ مگابایت دانلود / ۵۰ مگابایت آپلود**) مواجه هستند، TeleCloud-Downloader یک **سرور محلی Telegram Bot API** (`aiogram/telegram-bot-api`) روی خود سرور اجرا می‌کند. این معماری محدودیت‌های فضای ابری تلگرام را دور می‌زند:

- **📦 پشتیبانی از فایل‌های تا ۲ گیگابایت** — دانلود و ارسال فایل‌های بسیار بزرگ ویدیویی، صوتی و آرشیو.
- **⚡ انتقال فایل سریع در حالت محلی** — در حالت local، ربات فایل‌ها را مستقیم از مسیر اشتراکی Local Bot API (`/var/lib/telegram-bot-api`) می‌خواند و فقط در صورت نیاز به fallback از cloud download استفاده می‌کند.
- **🔒 خصوصی و مستقل** — تمام ترافیک API روی سرور خودتان باقی می‌ماند (`http://localhost:8081`) و به API ابری تلگرام متصل نمی‌شود.

---

### 🚀 دانلودر چند موتوره

#### 🌐 سایت‌های پشتیبانی‌شده (yt-dlp)
با استفاده از [yt-dlp](https://github.com/yt-dlp/yt-dlp)، ربات از **هزاران وب‌سایت** پشتیبانی می‌کند. محبوب‌ترین‌ها:

| پلتفرم | نوع محتوا |
|---|---|
| YouTube | Videos, Playlists, Shorts, Live streams |
| Instagram | Reels, Posts, Stories, IGTV |
| X (Twitter) | Videos, GIFs |
| TikTok | Videos |
| SoundCloud | Tracks, Playlists |
| Vimeo | Videos |
| Dailymotion | Videos |
| Reddit | Videos, GIFs |
| Pinterest | Videos |
| Twitch | Clips, VODs |
| Facebook | Videos, Reels |


> این فقط بخشی از قابلیت‌هاست — [yt-dlp از 1000+ سایت پشتیبانی می‌کند](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md). هر URL که با yt-dlp کار کند، اینجا هم کار می‌کند.

#### 🧲 Torrent و Magnet Link
هر **BitTorrent magnet link** (`magnet:?xt=urn:btih:...`) را مستقیم برای ربات بفرستید. موتور torrent محتوا را دانلود کرده و به Telegram یا Google Drive تحویل می‌دهد — بدون نیاز به torrent client در سمت شما.

#### 🔗 دانلودر لینک مستقیم
هر URL مستقیم HTTP/HTTPS را بفرستید و ربات همان فایل را مستقیم دانلود می‌کند — PDF، ZIP، MP4 یا هر نوع فایل دیگر.

### 🎛️ پنل تنظیمات پیشرفته
- **حالت ویدیو:** جابجایی بین فرمت‌های `mp4`، `mkv` یا `default`
- **حالت صوت:** جابجایی بین `mp3`، `m4a`، `flac` یا `default`
- **کیفیت ویدیو:** 480p / 720p / 1080p / 1440p (2K) / 2160p (4K) / بهترین
- **کیفیت صدا:** 128 kbps / 192 kbps / 320 kbps

### 📝 ادغام هوشمند زیرنویس (Muxing)
پشتیبانی از Hard-sub و Soft-sub برای زیرنویس فارسی/انگلیسی با FFmpeg. در صورت نبود زیرنویس، ربات کرش نمی‌کند و ویدیو بدون زیرنویس ارسال می‌شود.

### ⏱️ استخراج Chapter یوتیوب
استخراج و تزریق خودکار Chapterهای یوتیوب در فایل نهایی ویدیو با متادیتای FFmpeg.

### 🌐 رابط کاربری دوزبانه و 🍪 مدیریت کوکی
رابط کاربری کامل فارسی/انگلیسی. همچنین سیستم مدیریت کوکی تعاملی (آپلود فایل `.txt`) برای دسترسی به محتوای محدودشده.

---

## 🏗️ معماری کلی سیستم

TeleCloud-Downloader با دو حالت استقرار اجرا می‌شود:

- **حالت Local API (`TELEGRAM_LOCAL=1`)**: `telegram-bot` + `telegram-bot-api`
- **حالت Cloud API (`TELEGRAM_LOCAL=0`)**: فقط `telegram-bot`

معماری در حالت Local API:

```text
┌─────────────────────────────────────────────────────────────┐
│                    Docker Host (Host Network)              │
│                                                             │
│  ┌────────────────────┐    ┌─────────────────────────────┐  │
│  │  telegram-bot-api  │    │       telegram-bot          │  │
│  │  Port: 8081        │◄───│  Uses localhost Bot API     │  │
│  └────────────┬───────┘    └────────────┬────────────────┘  │
│               │                          │                   │
│               └──────────────────────────┘                   │
│      Shared local API storage: /var/lib/telegram-bot-api    │
└─────────────────────────────────────────────────────────────┘
```

**جزئیات مهم در runtime:** در حالت local ممکن است `bot.get_file()` مسیر نسبی برگرداند. ربات مسیر مطلق را زیر `/var/lib/telegram-bot-api/...` بازسازی می‌کند و در صورت نیاز fallback به cloud download دارد.

---

## 🛠️ تکنولوژی‌ها

| کامپوننت | تکنولوژی | نقش |
|---|---|---|
| **سرور API محلی** | `aiogram/telegram-bot-api:latest` | ⭐ حذف محدودیت حجم → پشتیبانی تا **۲ گیگابایت** |
| **زبان برنامه‌نویسی** | Python 3.11+ | زبان اصلی اپلیکیشن |
| **فریمورک ربات** | pyTelegramBotAPI | یکپارچه‌سازی با Telegram Bot API |
| **موتور دانلود** | yt-dlp | دانلود از پلتفرم‌های متعدد |
| **پردازش رسانه** | FFmpeg | ادغام زیرنویس، chapter، encoding |
| **کانتینرسازی** | Docker + Docker Compose | مدیریت کامل سرویس‌ها |
| **فضای ابری** | Rclone | یکپارچه‌سازی با Google Drive |
| **کنترل نسخه** | Git + GitHub | جریان کار مبتنی بر نسخه |

---

## 🚀 نصب و راه‌اندازی

راهنمای مناسب شرایط خود را انتخاب کنید:

| راهنما | مناسب برای |
|---|---|
| [⚡ QUICKSTART_FA.md](./QUICKSTART_FA.md) | راه‌اندازی اولیه روی Ubuntu/Debian با نصب‌کننده یک‌دستوری (`start.sh`) |
| [🛠️ SETUP_FA.md](./SETUP_FA.md) | راه‌اندازی دستی Docker، تنظیمات پیشرفته، اجرای محلی بدون Docker |

---

## 💬 نحوه استفاده و دستورات

### احراز دسترسی

کنترل دسترسی مبتنی بر تایید (approval) است:

- `ADMIN_ID` همیشه دسترسی دارد.
- اگر `REGISTRATION_OPEN=true` باشد، کاربران جدید در `/start` خودکار تایید می‌شوند.
- اگر `REGISTRATION_OPEN=false` باشد، کاربر باید `/start` بزند و درخواست دسترسی بدهد تا ادمین تایید/رد کند.

### دانلود رسانه

هر URL پشتیبانی‌شده یا magnet link را مستقیم برای ربات بفرستید:

| نوع ورودی | مثال |
|---|---|
| ویدیوی YouTube | `https://www.youtube.com/watch?v=...` |
| پلی‌لیست YouTube | `https://www.youtube.com/playlist?list=...` |
| SoundCloud / Instagram / X | هر URL پشتیبانی‌شده توسط yt-dlp |
| Magnet Link تورنت | `magnet:?xt=urn:btih:...` |
| لینک مستقیم فایل | `https://example.com/largefile.mp4` |

### پنل تنظیمات

`/settings` را ارسال کنید یا دکمه **⚙️ تنظیمات** را لمس کنید:

| تنظیم | گزینه‌ها |
|---|---|
| **حالت رسانه** | 🎬 ویدیو / 🎵 صدا |
| **کیفیت ویدیو** | 480p / 720p / 1080p / 1440p / 2160p / Best |
| **فرمت ویدیو** | MP4 / MKV / Default |
| **کیفیت صدا** | 128 kbps / 192 kbps / 320 kbps |
| **فرمت صدا** | MP3 / M4A / FLAC / Default |
| **مقصد آپلود** | 📨 Telegram / ☁️ Google Drive |
| **زیرنویس** | Off / English / Persian |
| **Chapter** | On / Off |
| **حالت دانلود** | Auto / yt-dlp / Torrent / Direct |

### مدیریت کوکی

برای دور زدن محدودیت‌های سنی یا دسترسی به محتوای خصوصی، فایل کوکی `.txt` با فرمت **Netscape** را مستقیم در چت ربات آپلود کنید.

---

## ⚙️ راهنمای متغیرهای محیطی

پیکربندی runtime در `config.py` این متغیرهای `.env` را می‌خواند:

| متغیر | الزامی | توضیح |
|---|---|---|
| `DOWNLOADER_BOT_TOKEN` | ✅ بله | توکن ربات Telegram از @BotFather |
| `DRIVE_FOLDER_ID` | ⬜ اختیاری | شناسه پوشه پیش‌فرض Google Drive برای آپلودهای ادمین |
| `ADMIN_ID` | ✅ بله | شناسه عددی کاربر Telegram ادمین |
| `REGISTRATION_OPEN` | ⬜ اختیاری | فعال/غیرفعال بودن self-registration در `/start` |
| `MAX_DAILY_FILES` | ⬜ اختیاری | سقف تعداد فایل روزانه پیش‌فرض هر کاربر |
| `MAX_DAILY_BYTES` | ⬜ اختیاری | سقف حجم روزانه پیش‌فرض هر کاربر |
| `COLAB_URL` | ⬜ اختیاری | لینک Colab نمایش‌داده‌شده در onboarding درایو |
| `MAX_CONCURRENT_DOWNLOADS` | ⬜ اختیاری | سقف دانلودهای همزمان |
| `TELEGRAM_LOCAL` | ⬜ اختیاری | `1/true` برای Local Bot API و `0/false` برای Cloud Bot API |

`start.sh` همچنین `TELEGRAM_API_ID` و `TELEGRAM_API_HASH` را برای استقرار Local Bot API جمع‌آوری می‌کند.

---

## 📁 ساختار پروژه

```text
TeleCloud-Downloader/
├── Dockerfile                  # تعریف build کانتینر ربات
├── docker-compose.yml          # مدیریت کامل سرویس‌های چندکانتینری
├── .env                        # (از Git مستثنی) اسرار و اطلاعات API
├── .gitignore                  # downloads/، cookies، .env و JSON DB را حذف می‌کند
├── main.py                     # نقطه ورود ربات — همیشه از اینجا اجرا می‌شود
├── config.py                   # تمام تنظیمات، وضعیت مشترک، شیء ربات
├── handlers.py                 # کنترل‌کننده پیام‌ها و دستورات
├── callbacks.py                # پردازش callback query دکمه‌های inline
├── menu.py                     # سازنده‌های منو و صفحه‌کلید Telegram
├── playlist_menu.py            # منوهای مخصوص پلی‌لیست YouTube
├── dest_helpers.py             # مسیریابی مقصد آپلود (Telegram یا Drive)
├── downloader_queue.py         # صف async وظایف و مدیریت worker
├── cookies.py                  # منطق مدیریت کوکی
├── utils.py                    # توابع کمکی و اشتراکی
├── user_langs.py               # ذخیره‌سازی زبان هر کاربر
├── downloaders/                # موتورهای دانلود
│   ├── __init__.py
│   ├── youtube.py              #   yt-dlp (YouTube، شبکه‌های اجتماعی)
│   ├── social.py               #   کنترل‌کننده پلتفرم‌های اجتماعی
│   ├── torrent.py              #   موتور BitTorrent / magnet link
│   └── direct.py              #   دانلودر مستقیم HTTP
└── uploaders/                  # موتورهای آپلود
    ├── __init__.py
    ├── telegram_upload.py      #   آپلود از طریق Local Telegram API
    ├── gdrive_upload.py        #   آپلود Rclone / Google Drive
    └── smart_dest.py          #   منطق مسیریابی مقصد
```

---

## 💾 پایداری داده‌ها و ولوم‌ها

تمام داده‌های پایدار روی ماشین میزبان با bind mount های Docker نگه‌داری می‌شوند:

| مسیر میزبان | مسیر کانتینر | سرویس | محتوا |
|---|---|---|---|
| `./telegram-bot-api-data` | `/var/lib/telegram-bot-api` | `telegram-bot-api` | داده‌های session سرور API محلی |
| `./downloads` | `/root/downloads` | هر دو کانتینر | فضای مشترک فایل (پل انتقال ۲ گیگابایتی) |
| `./cookies` | `/root/cookies` | `telegram-bot` | فایل‌های کوکی با فرمت Netscape |
| `./cookies_enabled.json` | `/root/cookies_enabled.json` | `telegram-bot` | وضعیت فعال‌سازی کوکی |
| `./rclone.conf` | `/root/.config/rclone/rclone.conf` | `telegram-bot` | فایل پیش‌فرض rclone برای Google Drive |
| `./user_configs` | `/app/user_configs` | `telegram-bot` | پایگاه‌داده SQLite و تنظیمات هر کاربر |
| `.` | `/app` | `telegram-bot` | کد منبع ربات (Live mount) |
| `./telegram-bot-api-data` | `/var/lib/telegram-bot-api` (ro) | `telegram-bot` | ذخیره‌ساز local API به‌صورت read-only برای خواندن مستقیم فایل |

دو mount مربوط به `telegram-bot-api-data` فقط وقتی استفاده می‌شوند که Local API mode فعال باشد (`TELEGRAM_LOCAL=1`).

> **نکته:** برای نصب مجدد بدون از دست دادن داده‌ها، فقط image را rebuild کنید: `docker compose build && docker compose up -d`

---

## 🔒 نکات امنیتی

- **کنترل دسترسی:** ربات از مدل تاییدمحور (approval-based) استفاده می‌کند و دسترسی‌ها با سیاست `REGISTRATION_OPEN` و تایید ادمین مدیریت می‌شوند.
- **مدیریت اسرار:** فایل `.env` را خارج از version control نگه دارید. حداقل شامل token ربات و تنظیمات deployment/runtime است.
- **ایزوله‌سازی Local API:** سرور Local Telegram Bot API فقط روی `localhost:8081` گوش می‌دهد و در معرض اینترنت عمومی نیست.
- **امنیت کوکی:** فایل‌های کوکی `.txt` را امن نگه دارید و عمومی نکنید.
- **پیکربندی Rclone:** فایل `rclone.conf` شامل اطلاعات احراز هویت Google است؛ هرگز آن را commit نکنید.

---

## 🐛 عیب‌یابی و سوالات متداول

<details>
<summary><strong>🔴 ربات بعد از راه‌اندازی پاسخ نمی‌دهد</strong></summary>

1. وضعیت سرویس‌ها را با همان compose fileی که اجرا کردید بررسی کنید:
   - حالت دستی: `docker compose ps`
   - با `start.sh`: `docker compose -f .start.compose.yml ps`
2. لاگ‌های ربات را ببینید:
   - حالت دستی: `docker compose logs -f telegram-bot`
   - با `start.sh`: `docker compose -f .start.compose.yml logs -f telegram-bot`
3. اگر Local mode فعال است (`TELEGRAM_LOCAL=1`)، لاگ `telegram-bot-api` را هم بررسی کنید.
4. صحت `DOWNLOADER_BOT_TOKEN` در `.env` را بررسی کنید (بدون فاصله اضافه).

</details>

<details>
<summary><strong>🔴 خطای "فایل خیلی بزرگ است" یا آپلود ناموفق</strong></summary>

Telegram Bot API استاندارد آپلود را به **50 MB** محدود می‌کند. این پروژه با **Local Telegram Bot API** این سقف را به **2 GB** افزایش می‌دهد. اگر خطا می‌بینید:

1. از اجرای کانتینر `telegram-bot-api` مطمئن شوید: `docker ps | grep telegram-bot-api`
2. لاگ آن را بررسی کنید: `docker logs -f telegram-bot-api`
3. وجود `TELEGRAM_LOCAL=1` در `.env` را تایید کنید.
4. تنظیم بودن اتصال ربات به `http://localhost:8081` را بررسی کنید.

</details>

<details>
<summary><strong>🔴 آپلود Google Drive ناموفق است</strong></summary>

1. بررسی کنید `./rclone.conf` در ریشه پروژه وجود دارد و **فایل** است.
2. دستور `docker exec telegram-bot rclone listremotes` را اجرا کنید تا remote قابل مشاهده باشد.
3. دسترسی write پوشه مقصد در Drive را تایید کنید.

</details>

<details>
<summary><strong>🔴 خطای `[Errno 21] Is a directory` برای `cookies_enabled.json` یا `rclone.conf`</strong></summary>

اگر فایل bind-mount وجود نداشته باشد، Docker ممکن است آن را به‌صورت directory بسازد. این دو مسیر باید فایل باشند:

```bash
test -f cookies_enabled.json || printf "{}" > cookies_enabled.json
test -f rclone.conf || touch rclone.conf
```

اگر الان directory هستند، حذفشان کنید و دوباره به‌صورت فایل بسازید، سپس سرویس‌ها را ری‌استارت کنید.

</details>

<details>
<summary><strong>🔴 دانلود فایل‌های Telegram در Local Bot API با 404 شکست می‌خورد</strong></summary>

در حالت local ممکن است `bot.get_file()` مسیر نسبی بدهد (مثل `videos/file_6.mp4`). ربات باید قبل از خواندن، مسیر مطلق زیر `/var/lib/telegram-bot-api/...` را بازسازی کند.

این پروژه guard لازم را دارد و به این mount در `telegram-bot` وابسته است:

```yaml
- ./telegram-bot-api-data:/var/lib/telegram-bot-api:ro
```

اگر این mount را حذف کرده‌اید، برگردانید و سرویس‌ها را ری‌استارت کنید.

</details>

<details>
<summary><strong>🔴 آپلود Drive شکست می‌خورد چون env key پوشه شناسایی نمی‌شود</strong></summary>

کلید env را دقیقاً با همین حروف بنویسید: `DRIVE_FOLDER_ID` (حروف بزرگ `ID`).  
حالت اشتباه مثل `DRIVE_FOLDER_iD` در runtime خوانده نمی‌شود.

</details>

<details>
<summary><strong>🔴 دانلود با خطای "403 Forbidden" یا محدودیت سنی ناموفق است</strong></summary>

کوکی احراز هویت از مرورگر لاگین‌شده لازم است. کوکی را با فرمت **Netscape** (مثلاً با افزونه "Get cookies.txt LOCALLY") خروجی بگیرید و فایل `.txt` را مستقیم برای ربات بفرستید.

</details>

---

## 📄 لایسنس

این پروژه تحت مجوز [MIT License](LICENSE) منتشر شده است.

</div>
