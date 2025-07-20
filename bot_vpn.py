# -*- coding: utf-8 -*-

import payment.stars
import payment.stars.handlers
import supports
import handlers
import spam.handlers
import supports.handlers
import game.handlers
import payment

from connect import bot, storage

supports.handlers.register_message_handlers(bot)
handlers.register_message_handlers(bot)
spam.handlers.register_message_handlers(bot)
payment.stars.handlers.register_message_handlers(bot)
game.handlers.register_handlers(bot, storage)


bot.infinity_polling()