
import config, os, utils, managment_user, keyboards

from connect import db, logging

from telebot import types

from managment_user import UserList, data_user, delete_not_subscription

from filters import onlyAdminChat

from psycopg2.extras import DictCursor
                  
from servers.server_list import Servers
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

from users.methods import get_user_by_id

from sqlalchemy import func

from statistic.tasks import start_statistic


from network_service import controllerFastApi

from core.telebot import TeleBotMod

from configparser import ConfigParser


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
    def _(message: types.Message) -> None:
        treadCheckUsersSubscription = Thread(target=delete_not_subscription)
        treadCheckUsersSubscription.start()

    
    @bot.message_handler(commands=[conf['BaseConfig'].get('admin_password')], func=onlyAdminChat())
    def d(message):
        add_key_admin(message)
        managment_user.manager_users_list = UserList(message)
    
    @bot.message_handler(commands=['te'], func=onlyAdminChat())
    def _(message: types.Message):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton('test', web_app=WebAppInfo('https://gidcolor.ru')))
        bot.send_message(message.chat.id, 'test',reply_markup=keyboard)
        
        # with Session(engine) as session:
        #     user = select(User).filter(User.telegram_id == message.from_user.id)
        #     data: User | None = session.scalar(user)
        #     print(data.server_link)
            


    @bot.message_handler(commands=[Comands.restart.value], func=onlyAdminChat())
    def restart(message):
        os.system("systemctl restart bot_vpn.service")


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

        with db.cursor() as cursor:
            cursor.execute("DELETE FROM users_subscription WHERE telegram_id = " + str(message.from_user.id))
            db.commit()


    @bot.message_handler(commands=["log", "лог"], func=onlyAdminChat())
    def _(message: types.Message):

        bot.send_document(message.chat.id, document=open(config.FILE_URL + "logs.txt","rb"))


    @bot.message_handler(
        commands=[Comands.start.value],
        chat_types=[ChatTypes.private.value]
    )
    def start(message: types.Message):

        jsonIdInvited = ""

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
                            jsonIdInvited: str = ', "invitedId": ' + str(arrStartMessageText[1])
                            message.text = arrStartMessageText[1]
                elif checkGiftCode(message):
                    return successfully_paid(message.from_user.id, optionText="Подарок активирован\n")
            # else:

            #     bot.send_message(message.chat.id, "Привет! Давай сыграем в крестики-нолики. Используй /game чтобы начать игру.")
            #     return
            
            keyboard.add(types.InlineKeyboardButton(text="Попробовать", callback_data='{"key": "try"' + jsonIdInvited + '}'))
            keyboard.add(types.InlineKeyboardButton(text="Политика по обработке персональных данных", callback_data='{"key": "pppd"}'))
            keyboard.add(types.InlineKeyboardButton(text="Условия использования", callback_data='{"key": "termsOfUse"}'))
            option_text = "\n\n_Нажимая кнопку \"Попробовать\", Вы соглашаетесь с политикой обработки персональных данных и условиями использования сервиса\._" 
        
        elif user.action == False:
            keyboard.add(
                types.InlineKeyboardButton(
                    text="Возобновить", 
                    callback_data='{"key": "' + KeyCall.pollCountMonth.value + '"}'
                )
            )
            option_text = ""
        elif user.action:
            successfully_paid(message.from_user.id)
            return
        
        bot.send_message(
            message.chat.id, 
            "*Приветствую Вас в сервисе VPN для свободного интернета без границ\.*" + option_text,
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
                keyboards.KeyboardForUser.gift.value: {'callback_data': '{"key": "' + KeyCall.pollCountMonth.value + '", "server": '+ str(get_very_free_server()) + ', "gift": true}'}
            },
            row_width=1
        )

        with db.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT telegram_id FROM users_subscription")
            for item in cursor.fetchall():
                try:
                    bot.send_photo(
                        chat_id=item,
                        photo=open(config.FILE_URL + "image/gift.png", "rb"),
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
                keyboards.KeyboardForUser.gift.value: {'callback_data': '{"key": "' + KeyCall.pollCountMonth.value + '", "server": '+ str(get_very_free_server()) + ', "gift": true}'}
            },
            row_width=1
        )
        bot.send_photo(
            chat_id=message.from_user.id,
            photo = open(config.FILE_URL + "vpn_option.png", "rb"),
            caption="Для оформления подарка нажмите кнопку ниже",
            reply_markup=key
        )


    @bot.message_handler(commands=[Comands.statistic.value], func=onlyAdminChat())
    def _(message: types.Message) -> None:
        start_statistic()


    @bot.message_handler(commands=[Comands.resubusa.value])
    def _(message: types.Message):
        bot.send_message(config.ADMINCHAT, "выполняется процесс...")
        with db.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT telegram_id, name FROM users_subscription WHERE action = True" +
                            " AND server_id = " + str(Servers.niderlands.value))
            users = cursor.fetchall()
            for i in users:
                link = controllerFastApi.add_vpn_user(i['telegram_id'], Servers.niderlands2.value)
    
                cursor.execute("UPDATE users_subscription" + 
                            "\nSET server_link='" + link +
                            "\n, server_id = " + str(Servers.niderlands2.value) +
                            ", protocol=" + str(config.DEFAULTPROTOCOL) + 
                            "'\n WHERE telegram_id=" + str(i['telegram_id']))
            db.commit()
            for i in users:
                try:
                    successfully_paid(i['telegram_id'], optionText="НЕОБХОДИМО ОБНОВИТЬ КОНФИГУРАЦИЮ\. СТАРАЯ КОНФИГУРАЦИЯ БОЛЬШЕ НЕ РАБОТАЕТ\.")
                except Exception as e:
                    bot.send_message(
                        config.ADMINCHAT, 
                        "error sendmessage [" + str(i['name']) + "](tg://user?id\=" + str(i['telegram_id']) + ") " + utils.form_text_markdownv2(str(e)),
                        parse_mode=ParseMode.mdv2.value)
        bot.send_message(config.ADMINCHAT, "commit")



    @bot.message_handler(
        func=lambda message: message.forward_from is not None and onlyAdminChat()
    )
    def _(message: types.Message):
        data_user(message.forward_from.id)