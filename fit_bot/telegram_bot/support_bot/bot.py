import time
from .loader import bot
from . import handlers


def start_support_bot():
    bot.send_message(58790442, f'Бот запущен! Можете нажать /start')
    bot.infinity_polling()
    # bot.infinity_polling(restart_on_change=True)
    bot.send_message(58790442, f'Бот Выключен!')

