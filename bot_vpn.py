# -*- coding: utf-8 -*-
import logging
import warnings
import time
import payment.stars
import payment.stars.handlers
import supports
import handlers
import spam.handlers
import supports.handlers
import game.handlers
import payment
import managers.handlers
import callback_handlers
import threads
from connect import bot, storage

bot.remove_webhook()

warnings.filterwarnings("ignore", category=SyntaxWarning)
callback_handlers.register_callback_handlers(bot)
spam.handlers.register_message_handlers(bot)
supports.handlers.register_message_handlers(bot)
handlers.register_message_handlers(bot)
payment.stars.handlers.register_message_handlers(bot)
game.handlers.register_handlers(bot, storage)
managers.handlers.register_message_handlers(bot)

print('БОТ ЗАПУЩЕН')

while True:
    try:
        bot.infinity_polling()
    except Exception as e:
        logging.error(e)
        time.sleep(5)