from telebot import types, TeleBot
from telebot.util import quick_markup

from filters import onlyAdminChat
from spam.methods import spamMessage
from servers.server_list import Servers
from enums.spam import MessageTextRu
from enums.keyCall import KeyCall



def register_message_handlers(bot: TeleBot):

    @bot.message_handler(
        commands=["spam"],
        func=onlyAdminChat()
    )
    def _(message: types.Message):
        bot.reply_to(message, MessageTextRu.spam.value)
        spamMessage(
            message,
            "SELECT telegram_id FROM users_subscription"
        )
        



    @bot.message_handler(
        commands=["spamDE"], 
        func=onlyAdminChat()
    )
    def _(message: types.Message):
        spamMessage(
            message,
            "SELECT telegram_id FROM users_subscription WHERE action = True AND server_id = {}".format(Servers.deutsche.value)
        )
        bot.reply_to(message, MessageTextRu.spamDe.value)



    @bot.message_handler(
        commands=["spamNID"], 
        func=onlyAdminChat()
    )
    def _(message: types.Message):
        spamMessage(
            message,
            "SELECT telegram_id FROM users_subscription WHERE action = True AND server_id = {}".format(Servers.niderlands2.value)
        )
        bot.reply_to(message, MessageTextRu.spamNid.value)



    @bot.message_handler(
        commands=["spamNIDDE"], 
        func=onlyAdminChat()
    )
    def _(message: types.Message) -> None:
        inlineKeyboard: types.InlineKeyboardMarkup = quick_markup(
            {
                "Продлить": {"callback_data": '{"key": "' + KeyCall.sale.value + '"}'}
            }
        )
        spamMessage(
            message,
            "SELECT telegram_id FROM users_subscription WHERE action = True AND server_id = {}".format(Servers.niderlands2.value),
            inlineKeyboard
        )
        bot.reply_to(message, MessageTextRu.spamNid.value)



    @bot.message_handler(
        commands=["spamACTION"],
        func=onlyAdminChat()
    )
    def _(message: types.Message):
        spamMessage(
            message,
            "SELECT telegram_id FROM users_subscription WHERE action = True"
        )
        bot.reply_to(message, MessageTextRu.spamAction.value)



    @bot.message_handler(
        commands=["spamNOTACTION"], 
        func=onlyAdminChat()
    )
    def _(message: types.Message):
        spamMessage(
            message,
            "SELECT telegram_id FROM users_subscription WHERE action = False"
        )
        bot.reply_to(message, MessageTextRu.spamNotAction.value)