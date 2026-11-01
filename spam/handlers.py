from telebot import types, TeleBot
from telebot.types import Message

from filters import onlyAdminChat
from spam.methods import spamMessage

from servers.server_list import Country
from servers.methods import get_server_list

from enums.spam import MessageTextRu
from enums.parse_mode import ParseMode

from users.methods import get_user_by, get_user_by_country

from tables import User, ServersTable

from connect import logging

from messageForUser import successfully_paid

from subscription.messages import send_subscription_manage_message


_SUBSCRIPTION_KEYBOARD_HINT = (
    "Управление подпиской: личный кабинет, смена сервера и протокола, "
    "возобновление — кнопками ниже (запросы идут в сервис подписок kuzmos.ru/sub)."
)


def register_message_handlers(bot: TeleBot) -> None:

    @bot.message_handler(
        commands=["spam"],
        func=onlyAdminChat()
    )
    def _(message: types.Message) -> None:
        """
            Рассылает сообщение всем пользователям.
            /spam sub — к копии добавляется клавиатура подписки (нужен reply на сообщение).
            /spam <фильтр> sub — рассылка по серверам с клавиатурой.
        """

        words = message.text.split()
        attach_sub = bool(words) and words[-1].lower() == "sub"
        if attach_sub:
            words = words[:-1]

        if len(words) > 2:
            bot.reply_to(message, "Передано более 2х аргументов.")
            return

        if attach_sub and not message.reply_to_message:
            bot.reply_to(
                message,
                "Для рассылки с кнопками подписки ответьте на сообщение "
                "и укажите /spam sub или /spam <имя сервера> sub.",
            )
            return

        if len(words) == 1:
            users: list[User] = get_user_by()
        else:
            servers: list[ServersTable] = get_server_list(
                ServersTable.name.ilike(f'%{words[1]}%')
            )
            users = get_user_by(
                User.server_id.in_([server.id for server in servers])
            )

        current_message: types.Message = bot.reply_to(message, MessageTextRu.spam.value)

        spamMessage(
            message,
            users,
            attach_subscription_keyboard=attach_sub,
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
        current_message: types.Message = bot.reply_to(
            message, MessageTextRu.spamNotAction.value
        )
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
                referal_text = (
                    "Вы можете пригласить нового пользователя и получить за это "
                    "1 мес\\. подписки бесплатно\\. Для того чтоб использовать такую "
                    "возможность, отправьте вашу пригласительную ссылку другу\\(для "
                    "копирования достаточно нажать на ссылку\\)\n\n"
                    "Персональная ссылка:\n"
                    f"`https://t.me/open_vpn_sale_bot?start={user.telegram_id}` \n\n"
                    "Поделившись ссылкой \\- вы помогаете проекту развиваться\\."
                )
                send_subscription_manage_message(
                    bot,
                    user.telegram_id,
                    referal_text,
                    user=user,
                    parse_mode=ParseMode.mdv2.value,
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
                    optionText="*РАБОТА ВОССТАНОВЛЕНА, НЕОБХОДИМО ЗАНОВО НАСТРОИТЬ КОНФИГУРАЦИЮ*\n",
                )
            except Exception:
                logging.error(
                    "Не удалось отправить сообщение пользователю id: %s name: %s",
                    user.telegram_id,
                    user.name,
                )

    @bot.message_handler(commands=["spamSubBtn"], func=onlyAdminChat())
    def _(message: types.Message) -> None:
        """
        Рассылка с ответом на сообщение: текст копируется, к каждому добавляется
        клавиатура управления подпиской (vpn-webapp /sub/*).
        """
        if not message.reply_to_message:
            bot.reply_to(message, "Ответьте на сообщение, которое нужно разослать.")
            return

        current_message = bot.reply_to(message, MessageTextRu.spamAction.value)
        users: list[User] = get_user_by(User.action == True)
        spamMessage(message, users, attach_subscription_keyboard=True)
        bot.edit_message_text(
            MessageTextRu.spam_completed.value,
            current_message.chat.id,
            current_message.id,
        )

    @bot.message_handler(commands=['webapp'])
    def _(message: Message) -> None:

        old_message: Message = bot.reply_to(
            message,
            'Начата рассылка'
        )

        users: list[User] = get_user_by()

        for user in users:
            try:
                send_subscription_manage_message(
                    bot,
                    user.telegram_id,
                    "Если Telegram не работает, оформить или управлять подпиской "
                    f"можно через веб-интерфейс.\n\n{_SUBSCRIPTION_KEYBOARD_HINT}",
                    user=user,
                    pin=True,
                    disable_notification=True,
                )
            except Exception:
                pass
        bot.edit_message_text(
            'Рассылка окончена',
            old_message.chat.id,
            old_message.id
        )
