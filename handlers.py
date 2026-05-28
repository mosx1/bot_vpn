
import config

from connect import db

from telebot import types
from telebot.types import InlineKeyboardButton

from managment_user import data_user

from filters import onlyAdminChat

from enums.comands import Comands
from enums.parse_mode import ParseMode
from enums.chat_types import ChatTypes

from giftUsers import checkGiftCode

from messageForUser import successfully_paid

from tables import User

from users.methods import get_user_by_id, get_jwt_by_id

from core.telebot import TeleBotMod

from configparser import ConfigParser

from keyboards import get_inline_web_page


def register_message_handlers(bot: TeleBotMod) -> None:

    conf = ConfigParser()
    conf.read('config.ini')

    def add_key_admin(message: types.Message):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton(text=f'/{Comands.actionUsersCount.value}'))
        bot.send_message(message.from_user.id, "add_key", reply_markup=keyboard)

    
    @bot.message_handler(commands=[conf['BaseConfig'].get('admin_password')], func=onlyAdminChat())
    def d(message):
        add_key_admin(message)
        # managment_user.manager_users_list = UserList(message)


    @bot.message_handler(
        commands=[Comands.start.value],
        chat_types=[ChatTypes.private.value]
    )
    def start(message: types.Message):

        user: User | None = get_user_by_id(message.from_user.id)

        keyboard = types.InlineKeyboardMarkup()

        if not user:
            arrStartMessageText = message.text.split(" ")
            if len(arrStartMessageText) == 2:
                if arrStartMessageText[1].isdigit():
                    with db.cursor() as cursor:
                        cursor.execute(
                            "SELECT EXISTS(SELECT 1 FROM users_subscription WHERE action = true AND telegram_id = " + str(arrStartMessageText[1]) + ")"
                        )
                        invited = cursor.fetchall()
                        if len(invited) > 0:
                            message.text = arrStartMessageText[1]
                elif checkGiftCode(message):
                    return successfully_paid(message.from_user.id, optionText="Подарок активирован\n")

            keyboard.add(
                InlineKeyboardButton(
                    text="Перейти к регистрации",
                    url="https://kuzmos.ru/auth/"
                )
            )
        elif user.action == False:
            token = get_jwt_by_id(user.telegram_id)
            bot.send_message(
                user.telegram_id,
                'Для управления подпиской используйте веб приложение.',
                reply_markup=get_inline_web_page(token)
            )
        elif user.action:
            successfully_paid(message.from_user.id)
            return

        bot.send_message(
            message.chat.id, 
            "*Приветствую Вас в сервисе VPN для свободного интернета без границ\.*",
            reply_markup=keyboard, 
            parse_mode=ParseMode.mdv2.value
        )

    @bot.message_handler(
        func=lambda message: message.forward_from is not None and message.chat.id == config.ADMINCHAT
    )
    def _(message: types.Message):
        data_user(message.forward_from.id)