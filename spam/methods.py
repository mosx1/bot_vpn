from connect import bot, logging, db
from psycopg2.extras import DictCursor
from telebot import types

from tables import User


def spamMessage(message: types.Message, users: set[User], inlineKeyboard: types.InlineKeyboardButton | None = None) -> None:

    for user in users:
        try:
            bot.copy_message(
                chat_id=user.telegram_id,
                from_chat_id=message.reply_to_message.chat.id,
                message_id=message.reply_to_message.id,
                disable_notification=False,
                reply_markup=inlineKeyboard
            )
        except Exception:
            logging.error("Не удалось отправить spam сообщение пользователю")