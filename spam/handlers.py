from telebot import types, TeleBot
from telebot.util import quick_markup

from filters import onlyAdminChat
from spam.methods import spamMessage

from servers.server_list import Country

from enums.spam import MessageTextRu
from enums.keyCall import KeyCall

from users.methods import get_user_by, get_user_by_country

from tables import User



def register_message_handlers(bot: TeleBot) -> None:

    @bot.message_handler(
        commands=["spam"],
        func=onlyAdminChat()
    )
    def _(message: types.Message) -> None:
        """
            Рассылает сообщение всем пользователям
        """
        current_message: types.Message = bot.reply_to(message, MessageTextRu.spam.value)
        print(get_user_by())
        spamMessage(
            message,
            get_user_by()
        )
        bot.edit_message_text(
            MessageTextRu.spam_completed.value,
            current_message.chat.id,
            current_message.id
        )


    @bot.message_handler(
        commands=["spamDE"], 
        func=onlyAdminChat()
    )
    def _(message: types.Message) -> None:
        """
            Рассылает сообщение пользователям локации Германия
        """
        current_message: types.Message = bot.reply_to(message, MessageTextRu.spamDe.value)

        spamMessage(
            message,
            get_user_by_country(Country.deutsche)
        )
        bot.edit_message_text(
            MessageTextRu.spam_completed.value,
            current_message.chat.id,
            current_message.id
        )


    @bot.message_handler(
        commands=["spamNID"], 
        func=onlyAdminChat()
    )
    def _(message: types.Message) -> None:
        """
            Рассылает сообщение пользователям локации Нидерланды
        """
        current_message: types.Message = bot.reply_to(message, MessageTextRu.spamNid.value)
        spamMessage(
            message,
            get_user_by_country(Country.niderlands)
        )
        bot.edit_message_text(
            MessageTextRu.spam_completed.value,
            current_message.chat.id,
            current_message.id
        )


    @bot.message_handler(
        commands=["spamNIDDE"], 
        func=onlyAdminChat()
    )
    def _(message: types.Message) -> None:

        current_message: types.Message = bot.reply_to(message, MessageTextRu.spamNid.value)

        inlineKeyboard: types.InlineKeyboardMarkup = quick_markup(
            {
                "Продлить": {"callback_data": '{"key": "' + KeyCall.sale.value + '"}'}
            }
        )
        spamMessage(
            message,
            get_user_by_country(
                Country.niderlands, 
                User.action == True
            ),
            inlineKeyboard
        )
        
        bot.edit_message_text(
            MessageTextRu.spam_completed.value,
            current_message.chat.id,
            current_message.id
        )


    @bot.message_handler(
        commands=["spamACTION"],
        func=onlyAdminChat()
    )
    def _(message: types.Message) -> None:
        """
            Рассылает сообщение активным пользователям
        """
        current_message: types.Message = bot.reply_to(message, MessageTextRu.spamAction.value)
        spamMessage(
            message,
            get_user_by(User.action == True)
        )
        bot.edit_message_text(
            MessageTextRu.spam_completed.value,
            current_message.chat.id,
            current_message.id
        )



    @bot.message_handler(
        commands=["spamNOTACTION"], 
        func=onlyAdminChat()
    )
    def _(message: types.Message) -> None:
        """
            Рассылает сообщение неактивным пользователям
        """
        current_message: types.Message = bot.reply_to(message, MessageTextRu.spamNotAction.value)
        spamMessage(
            message,
            get_user_by(User.action == False)
        )
        bot.edit_message_text(
            MessageTextRu.spam_completed.value,
            current_message.chat.id,
            current_message.id
        )