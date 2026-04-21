
from sqlalchemy.orm import Session
import config, os, utils, managment_user, keyboards

from connect import db, logging, engine

from telebot import types
from telebot.types import InlineKeyboardButton, Message

from managment_user import UserList, data_user, delete_not_subscription

from filters import onlyAdminChat

from psycopg2.extras import DictCursor

from servers.methods import get_very_free_server

from telebot.util import quick_markup
from telebot.types import WebAppInfo

from threading import Thread

from enums.comands import Comands
from enums.parse_mode import ParseMode
from enums.keyCall import KeyCall
from enums.chat_types import ChatTypes

from giftUsers import checkGiftCode

from messageForUser import successfully_paid

from tables import User

from users.methods import get_user_by_id, get_jwt_by_id

from sqlalchemy import func, delete

from statistic.tasks import start_statistic

from core.telebot import TeleBotMod

from configparser import ConfigParser

from keyboards import get_inline_web_page


def register_message_handlers(bot: TeleBotMod) -> None:

    conf = ConfigParser()
    conf.read('config.ini')

    def add_key_admin(message: types.Message):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton(text=f'/{conf['BaseConfig'].get('admin_password')}'),
                    types.KeyboardButton(text=f'/{Comands.actionUsersCount.value}'))
        keyboard.add(
            types.KeyboardButton(text=f'/{Comands.statistic.value}'),
            types.KeyboardButton(text=f'/{Comands.checkSubscription.value}')
        )
        bot.send_message(message.from_user.id, "add_key", reply_markup=keyboard)

    @bot.message_handler(commands=[Comands.checkSubscription.value], func=onlyAdminChat())
    def _(message: Message) -> None:
        treadCheckUsersSubscription = Thread(target=delete_not_subscription)
        treadCheckUsersSubscription.start()

    
    @bot.message_handler(commands=[conf['BaseConfig'].get('admin_password')], func=onlyAdminChat())
    def d(message):
        add_key_admin(message)
        managment_user.manager_users_list = UserList(message)
    
    @bot.message_handler(commands=['te'], func=onlyAdminChat())
    def _(message: Message):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton('test', web_app=WebAppInfo('https://gidcolor.ru')))
        bot.send_message(message.chat.id, 'test',reply_markup=keyboard)
        
        # with Session(engine) as session:
        #     user = select(User).filter(User.telegram_id == message.from_user.id)
        #     data: User | None = session.scalar(user)
        #     print(data.server_link)


    @bot.message_handler(
            commands=["поиск", "найти", "search"], 
            func=onlyAdminChat()
    )
    def _(message) -> None:

        add_key_admin(message)

        text: str = ' '.join(str(message.text).split(' ')[1:])

        managment_user.manager_users_list = UserList(
            message,
            func.concat(User.telegram_id, User.name).ilike(f'%{text}%')
        )


    @bot.message_handler(commands=["del"], func=onlyAdminChat())
    def _(message: types.Message):

        """Удаляет текущего пользователя. Для теста"""

        with Session(engine) as session:
            session.execute(delete(User).where(User.telegram_id == message.from_user.id))
            session.commit()


    @bot.message_handler(commands=["log", "лог"], func=onlyAdminChat())
    def _(message: types.Message):

        bot.send_document(message.chat.id, document=open("logs.txt","rb"))


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
            

    @bot.message_handler(commands=["status_bot"], func=onlyAdminChat())
    def oss(message):
        bot.send_message(message.chat.id, str(os.system("systemctl status bot_vpn.service")))
    

    @bot.message_handler(commands=["gift"])
    def _(message: types.Message):

        key = quick_markup(
            {
                keyboards.KeyboardForUser.gift.value: {'callback_data': '{"key": "' + KeyCall.poll_count_month_gift.value + '", "server": '+ str(get_very_free_server()) + '}'}
            },
            row_width=1
        )

        with db.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT telegram_id FROM users_subscription")
            for item in cursor.fetchall():
                try:
                    bot.send_photo(
                        chat_id=item,
                        photo=open("static/logo_big.jpeg", "rb"),
                        caption=config.TextsMessages.giftSpamCaption.value,
                        reply_markup=key
                    )
                except Exception:
                    logging.error("Не удалось отправить spam сообщение пользователю")
            
            
    @bot.message_handler(
        func=lambda message: message.text == keyboards.KeyboardForUser.balanceTime.value
    )
    def _(message: types.Message) -> None:

        user: User = get_user_by_id(message.from_user.id)
        bot.reply_to(
            message,
            "Подписка оканчивается: " + utils.replaceMonthOnRuText(user.exit_date),
            reply_markup=keyboards.getInlineExtend(),
            parse_mode=ParseMode.mdv2.value
        )


    @bot.message_handler(func=lambda message: message.text == keyboards.KeyboardForUser.gift.value)
    def _(message: types.Message):
        key = quick_markup(
            {
                keyboards.KeyboardForUser.gift.value: {'callback_data': '{"key": "' + KeyCall.poll_count_month_gift.value + '", "server": '+ str(get_very_free_server()) + '}'}
            },
            row_width=1
        )
        bot.send_photo(
            chat_id=message.from_user.id,
            photo = open("static/logo_option.jpg", "rb"),
            caption="Для оформления подарка нажмите кнопку ниже",
            reply_markup=key
        )


    @bot.message_handler(commands=[Comands.statistic.value], func=onlyAdminChat())
    def _(message: types.Message) -> None:
        start_statistic()

    @bot.message_handler(
        func=lambda message: message.forward_from is not None and message.chat.id == config.ADMINCHAT
    )
    def _(message: types.Message):
        data_user(message.forward_from.id)