from connect import bot
from telebot.types import Message

from users.methods import get_user_by_id

from tables import User

from subscription.messages import send_subscription_manage_message

def successfully_paid(id, old_message: Message | None =None, optionText="") -> Message | bool:

    user: User = get_user_by_id(id)
    message_web_app = send_subscription_manage_message(
        bot,
        id,
        optionText
        + "Управление подпиской — кнопками ниже "
        "(смена сервера, протокола, возобновление выполняются через сервис подписок).",
        user=user,
        pin=True,
    )
    return message_web_app