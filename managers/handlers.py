import utils

from telebot import TeleBot
from telebot.types import Message

from enums.comands import Comands

from servers.methods import get_info_servers, get_info_all_servers


def register_message_handlers(bot: TeleBot) -> None:

    @bot.message_handler(commands=[Comands.actionUsersCount.value])
    def _(message: Message) -> None:

        info_all_servers = get_info_all_servers()
        message_text: str = f"{info_all_servers.count} | {info_all_servers.count_pay} : Всего активных\n"

        for item in get_info_servers():
            message_text += f"{utils.bool_in_circle_for_text(item.answers)}|{item.count}|{item.count_pay}|{item.load}%: {item.name} \n"

        bot.send_message(
            message.chat.id,
            message_text
        )