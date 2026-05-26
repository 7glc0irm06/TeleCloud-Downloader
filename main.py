import time
import logging
from telebot import types
from config import bot, ADMIN_ID
from downloader_queue import start_worker

import handlers
import callbacks

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


def _configure_bot_commands():
    """
    Configure Telegram command menus with scopes:
    - Default scope: safe public commands only
    - Admin chat scope: includes admin-only commands
    """
    public_commands = [
        types.BotCommand('start', 'Start bot / Open main menu'),
    ]

    admin_commands = [
        types.BotCommand('adduser', 'Approve user: /adduser <id>'),
        types.BotCommand('deluser', 'Disable user: /deluser <id>'),
        types.BotCommand('setquota', 'Set quota: /setquota <id> <files> <GB>'),
        types.BotCommand('users', 'Manage users panel: /users'),
        types.BotCommand('togglereg', 'Toggle self-registration'),
        types.BotCommand('broadcast', 'Broadcast: /broadcast <message>'),
    ]

    # Everyone sees only public commands.
    bot.set_my_commands(
        public_commands,
        scope=types.BotCommandScopeDefault(),
    )

    # The admin sees both public + admin commands in their own chat menu.
    if ADMIN_ID > 0:
        bot.set_my_commands(
            public_commands + admin_commands,
            scope=types.BotCommandScopeChat(ADMIN_ID),
        )


def main():
    start_worker()
    bot.remove_webhook()
    _configure_bot_commands()
    print('Bot is running...')
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            print(f'Error: {e} - restarting in 5 seconds...')
            time.sleep(5)


if __name__ == '__main__':
    main()
