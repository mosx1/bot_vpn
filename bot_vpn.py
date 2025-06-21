# -*- coding: utf-8 -*-

import payment.stars
import payment.stars.handlers
import supports
import handlers
import spam.handlers
import supports.handlers
# import payment.stars.handlers
import payment

from connect import bot

# payment.stars.handlers.register_message_handlers(bot)
supports.handlers.register_message_handlers(bot)
handlers.register_message_handlers(bot)
spam.handlers.register_message_handlers(bot)
payment.stars.handlers.register_message_handlers(bot)


bot.infinity_polling()