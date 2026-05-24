import time
from config import bot
from downloader_queue import start_worker

import handlers
import callbacks

def main():
    start_worker()
    bot.remove_webhook()
    print("✅ Bot is running...")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            print(f"❌ Error: {e} — restarting in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    main()