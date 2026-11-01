from connect import bot, logging
from telebot import types

from keyboards import get_inline_web_page
from tables import User
from users.methods import get_jwt_by_id


def spamMessage(
    message: types.Message,
    users: set[User] | list[User],
    inlineKeyboard: types.InlineKeyboardMarkup | None = None,
    *,
    attach_subscription_keyboard: bool = False,
) -> None:
    """
    Копирует сообщение администратора пользователям.

    attach_subscription_keyboard — у каждого получателя своя клавиатура
    (WebApp/URL с JWT и callback на /sub/* vpn-webapp).
    """
    if not message.reply_to_message:
        logging.error("spamMessage: нет reply_to_message")
        return

    for user in users:
        reply_markup = inlineKeyboard
        if attach_subscription_keyboard:
            reply_markup = get_inline_web_page(get_jwt_by_id(user.telegram_id), user)
        try:
            bot.copy_message(
                chat_id=user.telegram_id,
                from_chat_id=message.reply_to_message.chat.id,
                message_id=message.reply_to_message.id,
                disable_notification=False,
                reply_markup=reply_markup,
            )
        except Exception:
            logging.error(
                "Не удалось отправить spam сообщение пользователю %s",
                user.telegram_id,
            )