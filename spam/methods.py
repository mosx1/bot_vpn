from connect import bot, logging, db
from psycopg2.extras import DictCursor
from telebot import types



def spamMessage(message: types.Message, execute: str, inlineKeyboard: types.InlineKeyboardButton | None = None) -> None:
    with db.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute(execute)
        for item in cursor.fetchall():
            try:
                bot.copy_message(
                    chat_id=item["telegram_id"],
                    from_chat_id=message.reply_to_message.chat.id,
                    message_id=message.reply_to_message.id,
                    disable_notification=False,
                    reply_markup=inlineKeyboard
                )
            except Exception:
                logging.error("Не удалось отправить spam сообщение пользователю")