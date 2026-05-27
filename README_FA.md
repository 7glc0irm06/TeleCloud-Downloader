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
- [⚙️ راهنمای کامل متغیرهای محیطی](#-راهنمای-کامل-متغیرهای-محیطی)
- [📁 ساختار پروژه](#-ساختار-پروژه)
- [💾 پایداری داده‌ها و ولوم‌ها](#-پایداری-دادهها-و-ولومها)
- [🔄 به‌روزرسانی ربات](#-بهروزرسانی-ربات)
- [🔒 نکات امنیتی](#-نکات-امنیتی)
- [🐛 عیب‌یابی و سوالات متداول](#-عیبیابی-و-سوالات-متداول)
- [🤝 مشارکت در توسعه](#-مشارکت-در-توسعه)
- [📄 لایسنس](#-لایسنس)

---

## ✨ ویژگی‌ها

### 🔥 سرور محلی Telegram Bot API — بدون محدودیت حجم فایل
> این مهم‌ترین ویژگی معماری TeleCloud-Downloader است.

برخلاف ربات‌های معمولی که با محدودیت پیش‌فرض تلگرام (**۲۰ مگابایت دانلود / ۵۰ مگابایت آپلود**) مواجه هستند، TeleCloud-Downloader یک **سرور محلی Telegram Bot API** (`aiogram/telegram-bot-api`) روی خود سرور اجرا می‌کند. این معماری کاملاً محدودیت‌های فضای ابری تلگرام را دور می‌زند:

- **📦 پشتیبانی از فایل‌های تا ۲ گیگابایت** — دانلود و ارسال فایل‌های بسیار بزرگ ویدیویی، صوتی و آرشیو بدون هیچ محدودیتی.
- **⚡ انتقال فایل فوری و محلی** — در حالت محلی، دستور `getFile` مسیر فیزیکی فایل روی دیسک را برمی‌گرداند. ربات از طریق **ولوم اشتراکی Docker** (`/root/downloads`) و با `shutil.copy2` فایل‌ها را بین کانتینرها منتقل می‌کند — بدون دانلود مجدد از HTTP، بدون سربار شبکه.
- **🔒 خصوصی و مستقل** — تمام ترافیک API روی سرور خودتان باقی می‌ماند (`http://localhost:8081`) و هرگز به API ابری تلگرام متصل نمی‌شود.

---

### 🚀 دانلودر چند موتوره
- **موتور yt-dlp** — دانلود پرسرعت و پایدار از یوتیوب، ساندکلاد، ایکس (توییتر)، اینستاگرام و صدها پلتفرم دیگر.
- **موتور تورنت** — پردازش مستقیم و دانلود از طریق مگنت‌لینک‌های BitTorrent.
- **دانلودر لینک مستقیم** — دانلود سریع و بهینه برای لینک‌های HTTP/HTTPS مستقیم.

### ☁️ مقاصد آپلود هوشمند
امکان جابجایی لحظه‌ای بین **آپلود مستقیم در تلگرام** و **آپلود خودکار در گوگل درایو** از طریق Rclone.

### 🎛️ پنل تنظیمات پیشرفته
- **حالت ویدیو:** جابجایی بین فرمت‌های `mp4`، `mkv` یا `default`
- **حالت صوت:** جابجایی بین `mp3`، `m4a`، `flac` یا `default`
- **کیفیت ویدیو:** 480p / 720p / 1080p / 1440p (2K) / 2160p (4K) / بهترین
- **کیفیت صدا:** 128 kbps / 192 kbps / 320 kbps

### 📝 ادغام هوشمند زیرنویس (Muxing)
پشتیبانی از چسباندن (Hard-sub) و قرار دادن (Soft-sub) زیرنویس‌های فارسی و انگلیسی از طریق FFmpeg، با سیستم جایگزین (Fallback) — در صورت نبود زیرنویس، ربات کرش نمی‌کند بلکه ویدیو را بدون زیرنویس ارسال کرده و کاربر را مطلع می‌سازد.

### ⏱️ استخراج چپترهای یوتیوب
استخراج و تزریق خودکار چپترها (Chapters) و زمان‌بندی‌های یوتیوب به داخل فایل ویدیویی با استفاده از متادیتای FFmpeg.

### 🌐 رابط کاربری دوزبانه و 🍪 مدیریت کوکی
بومی‌سازی کامل به فارسی و انگلیسی. سیستم مدیریت کوکی تعاملی (آپلود فایل `.txt`) برای دور زدن محدودیت‌های سنی یا دسترسی به محتوای خصوصی.

---

## 🏗️ معماری کلی سیستم

TeleCloud-Downloader به عنوان یک **اپلیکیشن چند کانتینری Docker** با استفاده از `docker-compose` مدیریت می‌شود. چهار کانتینر همواره در حال اجرا هستند:

```
┌─────────────────────────────────────────────────────────────┐
│               Docker Host (شبکه: Host Network)              │
│                                                             │
│  ┌────────────────────┐    ┌─────────────────────────────┐  │
│  │  telegram-bot-api  │    │       telegram-bot           │  │
│  │  (سرور API محلی)   │    │    (ربات دانلودر)           │  │
│  │  پورت: 8081        │◄───│  ارتباط از طریق localhost   │  │
│  │  aiogram/tg-bot-api│    │  parsafadaeei/telegram-bot  │  │
│  └────────────┬───────┘    └────────────┬────────────────┘  │
│               │                          │                   │
│               └──────────────────────────┘                   │
│           ولوم اشتراکی: /root/downloads                      │
│       (انتقال فایل با shutil.copy2، بدون HTTP)               │
│                                                             │
│  ┌──────────────────┐    ┌──────────────────────────────┐   │
│  │   goose-server   │    │       goose-manager          │   │
│  └──────────────────┘    └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**نکته کلیدی طراحی:** هر دو کانتینر از `network_mode: host` و ولوم مشترک `/root/downloads` استفاده می‌کنند. وقتی سرور API محلی فایلی را ذخیره می‌کند، ربات آن را از **همان مسیر فیزیکی روی دیسک** با `shutil.copy2` می‌خواند — آپلود تقریباً آنی، صرف نظر از حجم فایل.

---

## 🛠️ تکنولوژی‌ها

| کامپوننت | تکنولوژی | نقش |
|---|---|---|
| **سرور API محلی** | `aiogram/telegram-bot-api:latest` | ⭐ حذف محدودیت حجم → پشتیبانی تا **۲ گیگابایت** |
| **زبان برنامه‌نویسی** | Python 3.11+ | زبان اصلی اپلیکیشن |
| **فریمورک ربات** | pyTelegramBotAPI | یکپارچه‌سازی با Telegram Bot API |
| **موتور دانلود** | yt-dlp | دانلود از پلتفرم‌های متعدد |
| **پردازش رسانه** | FFmpeg | ادغام زیرنویس، چپتر، انکودینگ |
| **کانتینرسازی** | Docker + Docker Compose | مدیریت کامل سرویس‌ها |
| **فضای ابری** | Rclone | یکپارچه‌سازی با گوگل درایو |
| **کنترل نسخه** | Git + GitHub | جریان کار استقرار مبتنی بر نسخه |

---

## 🚀 نصب و راه‌اندازی

> **`Dockerfile` و `docker-compose.yml` در مخزن موجود هستند.** کافیست clone کنید، پیکربندی نمایید و اجرا کنید.

### مرحله ۱ — پیش‌نیازها

موارد زیر باید روی سرور شما (Ubuntu/Linux توصیه می‌شود) نصب باشند:

- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose Plugin](https://docs.docker.com/compose/install/) (`docker compose` نسخه ۲)
- Git

### مرحله ۲ — کلون کردن مخزن

```bash
git clone https://github.com/parsa-f/TeleCloud-Downloader.git
cd TeleCloud-Downloader
```

برای اجرای محلی (بدون Docker)، وابستگی‌های پایتون را با دستور زیر نصب کنید:

```bash
pip install -r requirements.txt
```

### مرحله ۳ — پیکربندی متغیرهای محیطی

یک فایل `.env` در مسیر اصلی پروژه ایجاد کنید. این فایل **از Git مستثنی شده** (از طریق `.gitignore`) و هرگز commit نمی‌شود.

```env
# ─── اطلاعات ربات تلگرام ──────────────────────────────────
DOWNLOADER_BOT_TOKEN=your_telegram_bot_token_here
BOT_PASSWORD=your_secure_access_password

# ─── سرور محلی Telegram Bot API (الزامی برای پشتیبانی از ۲ گیگابایت) ─
TELEGRAM_API_ID=your_api_id_from_my.telegram.org
TELEGRAM_API_HASH=your_api_hash_from_my.telegram.org
TELEGRAM_LOCAL=1

# ─── اختیاری ──────────────────────────────────────────────
# مسیر فایل rclone در داخل کانتینر (مقدار پیش‌فرض نمایش داده شده)
RCLONE_CONFIG_PATH=/root/.config/rclone/rclone.conf
```

> **نحوه دریافت `TELEGRAM_API_ID` و `TELEGRAM_API_HASH`:**  
> وارد [my.telegram.org](https://my.telegram.org) شوید، به بخش **API Development Tools** بروید و یک اپلیکیشن بسازید. `api_id` و `api_hash` را کپی کنید.

> **نحوه دریافت توکن ربات:**  
> [@BotFather](https://t.me/BotFather) را در تلگرام باز کنید، `/newbot` را ارسال کنید و توکن ارائه شده را کپی نمایید.

### مرحله ۴ — پیکربندی Rclone (برای گوگل درایو)

اگر قصد استفاده از آپلود به گوگل درایو را دارید، فایل `rclone.conf` را در مسیر میزبان قرار دهید: `/root/.config/rclone/rclone.conf`. فایل `docker-compose.yml` این دایرکتوری را داخل کانتینر mount می‌کند.

```bash
# اجرای پیکربندی جدید rclone:
rclone config   # سپس به گوگل درایو مجوز بدهید

# یا کپی پیکربندی موجود:
cp ~/.config/rclone/rclone.conf /root/.config/rclone/rclone.conf
```

> اگر از گوگل درایو استفاده نمی‌کنید، این مرحله را می‌توانید رد کنید. ربات فقط با آپلود تلگرام نیز کار می‌کند.

### مرحله ۵ — Build و اجرا

```bash
docker compose up -d --build
```

تأیید اجرای همه ۴ کانتینر:

```bash
docker compose ps
# یا
docker ps
```

مشاهده لاگ‌های زنده:

```bash
docker logs -f telegram-bot
docker logs -f telegram-bot-api
```

---

## 💬 نحوه استفاده و دستورات

### احراز هویت

ربات با رمز عبور محافظت شده است. در اولین استفاده، رمزی که در `BOT_PASSWORD` تنظیم کرده‌اید را برای ربات ارسال کنید:

```
your_secure_access_password
```

### دانلود رسانه

هر URL پشتیبانی‌شده یا مگنت‌لینک را مستقیماً برای ربات ارسال کنید:

| نوع ورودی | مثال |
|---|---|
| ویدیوی یوتیوب | `https://www.youtube.com/watch?v=...` |
| پلی‌لیست یوتیوب | `https://www.youtube.com/playlist?list=...` |
| SoundCloud / Instagram / X | هر URL پشتیبانی‌شده توسط yt-dlp |
| مگنت‌لینک تورنت | `magnet:?xt=urn:btih:...` |
| لینک مستقیم فایل | `https://example.com/largefile.mp4` |

### پنل تنظیمات

`/settings` را ارسال کنید یا دکمه **⚙️ تنظیمات** را لمس کنید:

| تنظیم | گزینه‌ها |
|---|---|
| **حالت رسانه** | 🎬 ویدیو / 🎵 صدا |
| **کیفیت ویدیو** | 480p / 720p / 1080p / 1440p / 2160p / بهترین |
| **فرمت ویدیو** | MP4 / MKV / پیش‌فرض |
| **کیفیت صدا** | 128 kbps / 192 kbps / 320 kbps |
| **فرمت صدا** | MP3 / M4A / FLAC / پیش‌فرض |
| **مقصد آپلود** | 📨 تلگرام / ☁️ گوگل درایو |
| **زیرنویس** | خاموش / انگلیسی / فارسی |
| **چپتر** | روشن / خاموش |
| **حالت دانلود** | خودکار / yt-dlp / تورنت / مستقیم |

### مدیریت کوکی

برای دور زدن محدودیت‌های سنی یا دسترسی به محتوای خصوصی، یک فایل `.txt` کوکی با فرمت **Netscape** مستقیماً برای ربات آپلود کنید. مدیر کوکی آن را پردازش و ذخیره می‌کند.

---

## ⚙️ راهنمای کامل متغیرهای محیطی

تمام پیکربندی از طریق فایل `.env` مدیریت می‌شود که توسط همه کانتینرها از طریق `env_file` به اشتراک گذاشته می‌شود:

| متغیر | الزامی | توضیح |
|---|---|---|
| `DOWNLOADER_BOT_TOKEN` | ✅ بله | توکن ربات تلگرام از @BotFather |
| `BOT_PASSWORD` | ✅ بله | رمز عبور برای احراز هویت کاربران |
| `TELEGRAM_API_ID` | ✅ بله | App API ID از [my.telegram.org](https://my.telegram.org) (مورد نیاز سرور API محلی) |
| `TELEGRAM_API_HASH` | ✅ بله | App API Hash از [my.telegram.org](https://my.telegram.org) (مورد نیاز سرور API محلی) |
| `TELEGRAM_LOCAL` | ✅ بله | باید `1` باشد تا حالت API محلی فعال شود |
| `RCLONE_CONFIG_PATH` | ⬜ اختیاری | مسیر فایل `rclone.conf` داخل کانتینر |

---

## 📁 ساختار پروژه

```text
TeleCloud-Downloader/
├── Dockerfile                  # تعریف build کانتینر ربات
├── docker-compose.yml          # مدیریت کامل سرویس‌های چند کانتینری
├── .env                        # (از Git مستثنی) اسرار و اطلاعات API
├── .gitignore                  # downloads/، cookies، .env و JSON DB را حذف می‌کند
├── main.py                     # نقطه ورود ربات — همیشه از اینجا اجرا می‌شود
├── config.py                   # تمام تنظیمات، وضعیت مشترک، شیء ربات
├── handlers.py                 # کنترل‌کننده پیام‌ها و دستورات
├── callbacks.py                # پردازش callback query دکمه‌های inline
├── menu.py                     # سازنده‌های منو و صفحه‌کلید تلگرام
├── playlist_menu.py            # منوهای مخصوص پلی‌لیست یوتیوب
├── dest_helpers.py             # مسیریابی مقصد آپلود (تلگرام یا درایو)
├── downloader_queue.py         # صف async وظایف و مدیریت worker
├── cookies.py                  # منطق مدیریت کوکی
├── utils.py                    # توابع کمکی و اشتراکی
├── user_langs.py               # ذخیره‌سازی زبان هر کاربر
├── downloaders/                # موتورهای دانلود
│   ├── __init__.py
│   ├── youtube.py              #   yt-dlp (یوتیوب، پلتفرم‌های اجتماعی)
│   ├── social.py               #   کنترل‌کننده پلتفرم‌های اجتماعی
│   ├── torrent.py              #   موتور BitTorrent / مگنت‌لینک
│   └── direct.py              #   دانلودر مستقیم HTTP
└── uploaders/                  # موتورهای آپلود
    ├── __init__.py
    ├── telegram_upload.py      #   آپلودر از طریق Local Telegram API
    ├── gdrive_upload.py        #   آپلودر Rclone / گوگل درایو
    └── smart_dest.py          #   منطق مسیریابی مقصد
```

> ⚠️ **مهم:** هرگز فایلی با نام `queue.py` داخل پوشه ربات ایجاد نکنید. این نام با ماژول استاندارد کتابخانه Python تداخل دارد. پیاده‌سازی صف در این پروژه `downloader_queue.py` نام دارد.

---

## 💾 پایداری داده‌ها و ولوم‌ها

تمام داده‌های پایدار **روی ماشین میزبان** از طریق bind mount های Docker ذخیره می‌شوند و از ری‌استارت کانتینر و rebuild ایمیج در امان هستند:

| مسیر میزبان | مسیر کانتینر | سرویس | محتوا |
|---|---|---|---|
| `./telegram-bot-api-data` | `/var/lib/telegram-bot-api` | `telegram-bot-api` | داده‌های session سرور API محلی |
| `./downloads` | `/root/downloads` | هر دو کانتینر | فضای مشترک فایل (پل انتقال ۲ گیگابایتی) |
| `./cookies` | `/root/cookies` | `telegram-bot` | فایل‌های کوکی با فرمت Netscape |
| `./cookies_enabled.json` | `/root/cookies_enabled.json` | `telegram-bot` | وضعیت فعال‌سازی کوکی |
| `./.config/rclone` | `/root/.config/rclone` | `telegram-bot` | اطلاعات احراز هویت گوگل درایو |
| `./bot` | `/app` | `telegram-bot` | کد منبع ربات (Live mount — مخزن Git) |

> **نکته:** برای نصب مجدد بدون از دست دادن داده‌های کاربر، فقط ایمیج را rebuild کنید: `docker compose build && docker compose up -d`

---

## 🔄 به‌روزرسانی ربات

کد ربات از طریق **Git** کنترل نسخه می‌شود. دایرکتوری `/root/bot/` مستقیماً به عنوان `/app` داخل کانتینر mount شده، بنابراین تغییرات کد بلافاصله پس از ری‌استارت کانتینر اعمال می‌شوند — **بدون نیاز به rebuild ایمیج**.

### جریان کار استاندارد به‌روزرسانی

```bash
# روی ماشین توسعه‌دهنده محلی:
git push origin main

# روی سرور:
cd /root/bot
git pull
docker restart telegram-bot
```

> ⚠️ فایل‌ها را مستقیماً روی سرور با `cat << EOF` یا ویرایشگر متن ویرایش **نکنید**. همیشه تغییرات را از طریق Git push کنید و روی سرور pull نمایید تا وضعیت تمیز و قابل بازتولید حفظ شود.

---

## 🔒 نکات امنیتی

- **کنترل دسترسی:** ربات احراز هویت اجباری با رمز عبور را اعمال می‌کند. تنها کاربرانی که `BOT_PASSWORD` صحیح را وارد کنند مجاز به استفاده هستند.
- **مدیریت اسرار:** `BOT_PASSWORD`، `DOWNLOADER_BOT_TOKEN`، `TELEGRAM_API_ID` و `TELEGRAM_API_HASH` از فایل `.env` بارگذاری می‌شوند که از کنترل نسخه مستثنی است. **هرگز فایل `.env` خود را commit نکنید.**
- **ایزوله‌سازی API محلی:** سرور Local Telegram Bot API فقط روی `localhost:8081` گوش می‌دهد و به اینترنت عمومی در معرض نیست.
- **امنیت کوکی:** مدیر کوکی توکن‌های `.txt` را به صورت امن پردازش می‌کند. فایل‌های کوکی خود را امن نگه دارید و هرگز آن‌ها را به صورت عمومی فاش نکنید.
- **پیکربندی Rclone:** `rclone.conf` شما حاوی اطلاعات احراز هویت گوگل است. داخل کانتینر mount می‌شود و هرگز نباید به Git commit شود.

---

## 🐛 عیب‌یابی و سوالات متداول

<details>
<summary><strong>🔴 ربات پس از راه‌اندازی پاسخ نمی‌دهد</strong></summary>

1. اطمینان از اجرای همه کانتینرها: `docker ps`
2. بررسی لاگ‌های ربات: `docker logs -f telegram-bot`
3. بررسی لاگ‌های سرور API محلی: `docker logs -f telegram-bot-api`
4. بررسی صحت `DOWNLOADER_BOT_TOKEN` در فایل `.env` (بدون فضای خالی اضافه).
5. تأیید وجود `TELEGRAM_API_ID`، `TELEGRAM_API_HASH` و `TELEGRAM_LOCAL=1` در فایل `.env`.

</details>

<details>
<summary><strong>🔴 خطای "فایل خیلی بزرگ است" یا آپلود ناموفق</strong></summary>

Telegram Bot API استاندارد آپلود فایل را به **۵۰ مگابایت** محدود می‌کند. این پروژه یک **سرور محلی Telegram Bot API** اجرا می‌کند که این محدودیت را به **۲ گیگابایت** افزایش می‌دهد. اگر با این خطا مواجه هستید:

1. تأیید اجرای کانتینر `telegram-bot-api`: `docker ps | grep telegram-bot-api`
2. بررسی لاگ‌های آن: `docker logs -f telegram-bot-api`
3. تأیید وجود `TELEGRAM_LOCAL=1` در فایل `.env`.
4. اطمینان از پیکربندی ربات برای اتصال به `http://localhost:8081`.

</details>

<details>
<summary><strong>🔴 آپلود گوگل درایو ناموفق است</strong></summary>

1. وجود `rclone.conf` در مسیر میزبان `/root/.config/rclone/rclone.conf` را تأیید کنید.
2. اجرا کنید: `docker exec telegram-bot rclone listremotes` تا مطمئن شوید rclone remote شما را می‌بیند.
3. تأیید دسترسی write به پوشه هدف در درایو.

</details>

<details>
<summary><strong>🔴 دانلود با خطای "403 Forbidden" یا محدودیت سنی ناموفق است</strong></summary>

باید کوکی‌های احراز هویت از یک session مرورگر وارد شده ارائه دهید. کوکی‌های خود را با فرمت **Netscape** از طریق یک افزونه مرورگر (مثلاً "Get cookies.txt LOCALLY") صادر کرده، سپس فایل `.txt` را مستقیماً برای ربات آپلود کنید.

</details>

<details>
<summary><strong>🟡 چطور ربات را به نسخه جدید به‌روزرسانی کنم؟</strong></summary>

```bash
# روی سرور:
cd /root/bot
git pull
docker restart telegram-bot
```

فایل `.env`، داده‌های پایدار و ولوم‌ها تحت تأثیر قرار نمی‌گیرند.

</details>

<details>
<summary><strong>🟡 چطور همه سرویس‌ها را متوقف کنم؟</strong></summary>

```bash
docker compose down
```

برای توقف و حذف همه ولوم‌های داده:

```bash
docker compose down -v
```

</details>

<details>
<summary><strong>🟡 چرا نمی‌توانم فایلم را "queue.py" بنامم؟</strong></summary>

نام `queue` با ماژول استاندارد کتابخانه Python تداخل دارد. هر فایلی با نام `queue.py` داخل دایرکتوری ربات (`/app`) ماژول `queue` کتابخانه استاندارد را پنهان کرده و اپلیکیشن را خراب می‌کند. پیاده‌سازی صف در این پروژه `downloader_queue.py` نام دارد.

</details>

---

## 🤝 مشارکت در توسعه

مشارکت‌ها با گرمی پذیرفته می‌شوند! نحوه مشارکت:

1. مخزن را روی GitHub **Fork** کنید.
2. یک branch ویژگی بسازید: `git checkout -b feature/your-amazing-feature`
3. تغییرات خود را با پیام‌های واضح commit کنید: `git commit -m "feat: add amazing feature"`
4. به fork خود **Push** کنید: `git push origin feature/your-amazing-feature`
5. یک **Pull Request** به برنچ `main` باز کنید و توضیح دهید چه تغییراتی داده‌اید و چرا.

### راهنمای توسعه

- از [PEP 8](https://peps.python.org/pep-0008/) برای استایل کد Python پیروی کنید.
- تغییرات را متمرکز نگه دارید — یک ویژگی یا رفع باگ در هر PR.
- اگر تغییر شما بر جریان کار کاربر تأثیر می‌گذارد، بخش مرتبط README را به‌روز کنید.
- برای رشته‌های دوزبانه، ورودی‌ها را به هر دو بخش انگلیسی و فارسی در `locales.py` اضافه کنید.
- هرگز فایلی با نام `queue.py` داخل دایرکتوری ربات نسازید.

### گزارش مشکلات

لطفاً یک [GitHub Issue](https://github.com/parsa-f/TeleCloud-Downloader/issues) با موارد زیر باز کنید:
- توضیح واضح باگ یا درخواست ویژگی.
- مراحل بازتولید (برای باگ‌ها).
- لاگ‌های مرتبط از `docker logs telegram-bot` یا `docker logs telegram-bot-api`.

---

## 📄 لایسنس

این پروژه تحت مجوز [MIT License](LICENSE) منتشر شده است.

</div>





