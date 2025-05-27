# -*- coding: utf-8 -*-

import supports
import handlers
import spam.handlers
import supports.handlers
# import payment.stars.handlers

from connect import bot

# payment.stars.handlers.register_message_handlers(bot)
supports.handlers.register_message_handlers(bot)
handlers.register_message_handlers(bot)
spam.handlers.register_message_handlers(bot)


bot.infinity_polling()

