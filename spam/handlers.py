from telebot import types, TeleBot
from telebot.types import Message

from filters import onlyAdminChat
from spam.methods import spamMessage

from servers.server_list import Country
from servers.methods import get_server_list

from enums.spam import MessageTextRu
from enums.parse_mode import ParseMode

from users.methods import get_user_by, get_user_by_country, get_jwt_by_id

from tables import User, ServersTable

from connect import logging

from messageForUser import successfully_paid

from keyboards import get_inline_web_page



def register_message_handlers(bot: TeleBot) -> None:

    @bot.message_handler(
        commands=["spam"],
        func=onlyAdminChat()
    )
    def _(message: types.Message) -> None:
        """
            Рассылает сообщение всем пользователям
        """
        
        words = message.text.split(' ')
        count_words: int = len(words)
        
        match count_words:
            case 1:
                users: list[User] = get_user_by()
            case 2:
                servers: list[ServersTable] = get_server_list(ServersTable.name.ilike(f'%{words[1]}%'))
                users: list[User] = get_user_by(User.server_id.in_([server.id for server in servers]))
            case _:
                bot.reply_to(message, "Передано более 2х аргументов.")
                return


        current_message: types.Message = bot.reply_to(message, MessageTextRu.spam.value)

        spamMessage(message, users)
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
    

    @bot.message_handler(commands=["spamref"])
    def _(message: types.Message) -> None:

        current_message: types.Message = bot.reply_to(message, MessageTextRu.spamAction.value)
        users: list[User] = get_user_by(User.action == True)
        
        for user in users:
            try:
                bot.send_message(
                    user.telegram_id, 
                    "Вы можете пригласить нового пользователя и получить за это 1 мес\. подписки бесплатно\. Для того чтоб использовать такую возможность, отправьте вашу пригласительную ссылку другу\(для копирования достаточно нажать на ссылку\)\n\n"+
                    "Персональная ссылка:\n`https://t.me/open_vpn_sale_bot?start=" + str(user.telegram_id) + "` \n\nПоделившись ссылкой - вы помогаете проекту развиваться\.",
                    parse_mode= ParseMode.mdv2.value
                )
            except Exception as e:
                logging.error("Не удалось отправить сообщение пользователю", e)
                
        bot.edit_message_text(
            MessageTextRu.spam_completed.value,
            current_message.chat.id,
            current_message.id
        )
    
    
    @bot.message_handler(commands=["spamSUB"])
    def _(message: types.Message) -> None:

        bot.reply_to(
            message, 
            'Начата рассылка'
        )

        users: list[User] = get_user_by(User.action == True)
        
        for user in users:
            try:
                successfully_paid(
                    user.telegram_id,
                    optionText="*РАБОТА ВОССТАНОВЛЕНА, НЕОБХОДИМО ЗАНОВО НАСТРОИТЬ КОНФИГУРАЦИЮ*"
                )
            except Exception as e:
                logging.error(f"Не удалось отправить сообщение пользователю id: {user.telegram_id} name: {user.name}")

    @bot.message_handler(commands=['webapp'])
    def _(message: Message) -> None:
        
        old_message: Message = bot.reply_to(
            message, 
            'Начата рассылка'
        )

        users: list[User] = get_user_by()

        for user in users:

            token = get_jwt_by_id(user.telegram_id)
            try:
                message_web_app: Message = bot.send_message(
                    user.telegram_id,
                    'Если телеграм не работает, оформить подписку можно через веб интерфейс или воспользовавшись прокси для телеграм.',
                    reply_markup=get_inline_web_page(token)
                )
                bot.pin_chat_message(
                    message_web_app.chat.id,
                    message_web_app.id,
                    disable_notification=True
                )
            except Exception:
                pass
        bot.edit_message_text(
            'Рассылка окончена',
            old_message.chat.id,
            old_message.id
        )