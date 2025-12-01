# -*- coding: utf-8 -*-
import asyncio, logging, callback_handlers
import warnings
import payment.stars
import payment.stars.handlers
import supports
import handlers
import spam.handlers
import supports.handlers
import game.handlers
import payment
import managers.handlers
from connect import bot

from aiogram import Dispatcher


# warnings.filterwarnings("ignore", category=SyntaxWarning)

supports.handlers.register_message_handlers(bot)
handlers.register_message_handlers(bot)
spam.handlers.register_message_handlers(bot)
payment.stars.handlers.register_message_handlers(bot)
managers.handlers.register_message_handlers(bot)

async def main() -> None:
    dispatcher = Dispatcher()
    dispatcher.include_routers(
        callback_handlers.router
    )
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот запущен")
    await dispatcher.start_polling(bot)


asyncio.run(main())