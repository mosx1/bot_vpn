from connect import bot
from telebot.types import Message

from users.methods import get_user_by_id, get_jwt_by_id

from tables import User

from keyboards import get_inline_web_page

def successfully_paid(id, old_message: Message | None =None, optionText="") -> Message | bool:

    user: User = get_user_by_id(id)
    token = get_jwt_by_id(user.telegram_id)

    message_web_app = bot.send_message(
        id,
        'Для управления подпиской используйте веб приложение.',
        reply_markup=get_inline_web_page(token)
    )
    return bot.pin_chat_message(
        message_web_app.chat.id,
        message_web_app.id,
        disable_notification=True
    )