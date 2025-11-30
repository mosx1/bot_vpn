import enums.invite
import enums.keyCall
import json, config, os, utils, pytz, datetime, time, managment_user, invite, enums, keyboards

from connect import db, logging

import invite.methods

from telebot import types

from managment_user import add_user, del_user, UserList, data_user, delete_not_subscription

from filters import onlyAdminChat

from psycopg2.extras import DictCursor
                  
from servers.server_list import Servers, Country
from servers.methods import get_server_list, get_very_free_server

from yoomoneyMethods import getInfoLastPayment, getLinkPayment

from telebot.util import quick_markup
from telebot.types import WebAppInfo

from threading import Thread

from enums.comands import Comands
from enums.parse_mode import ParseMode
from enums.keyCall import KeyCall
from enums.chat_types import ChatTypes
from enums.content_types import ContentTypes

from giftUsers import genGiftCode, checkGiftCode

from messageForUser import successfully_paid, manual_successfully_paid

from tables import User

from users.methods import get_user_by_id

from sqlalchemy import func

from payment.crypto.repository.methods import crypto_pay, PayingUser, TypeOfPurchase
from payment.stars.handlers import handle_buy

from statistic.tasks import start_statistic

from configparser import ConfigParser

from network_service import controllerFastApi
from network_service.entity import NetworkServiceError

from core.telebot import TeleBotMod


def register_message_handlers(bot: TeleBotMod) -> None:
    

    def pollingInfoLastPayment(*args) -> dict:
        """
            args - label, server, day, userId, messageId
        """
        label = args[0]
        server = args[1]
        month = args[2]
        userId = args[3]
        messageId = args[4]
        try:
            userName: str = args[5]
        except Exception:
            userName = userId

        stopDateTime = datetime.datetime.now(pytz.timezone('Europe/Moscow')) + datetime.timedelta(hours=1)

        while True:

            time.sleep(3)
            currentDateTime: datetime.datetime = datetime.datetime.now(pytz.timezone('Europe/Moscow'))
            try:
                res = getInfoLastPayment(label)
            except Exception as e:
                bot.send_message(config.ADMINCHAT, str(e))
                logging.error(str(e))

            if res:

                logging.info(
                    "user_id: {}; user_name:{}; Оплата подписки {} мес. сервер {}".format(
                        userId,
                        userName,
                        month,
                        utils.get_server_name_by_id(server)
                    )
                )

                bot.edit_message_caption("Оплата получена, идет настройка конфигурации(это может занять несколько минут)...", userId, messageId)
                
                userMessage: config.AddUserMessage = add_user(userId, month, server=server)

                bot.send_message(config.ADMINCHAT,
                                "[" + utils.form_text_markdownv2(userName) + "](tg://user?id\=" + str(userId) + ") оплатил",
                                parse_mode=ParseMode.mdv2.value)
                bot.delete_message(userId, messageId)
                
                invite.methods.incrementBalance(userId, month=month)
                
                successfully_paid(userId, optionText=userMessage.value)

                return res
            
            if currentDateTime > stopDateTime:
                bot.delete_message(userId, messageId)
                return 
            


    def pollingInfoLastPaymentGift(*args) -> dict:
        """
        args - label, month, userId, messageId
        """
        label = args[0]
        month = args[1]
        userId = args[2]
        messageId = args[3]
        try:
            userName = args[5]
        except Exception:
            userName = userId

        stopDateTime = datetime.datetime.now(pytz.timezone('Europe/Moscow')) + datetime.timedelta(hours=1)

        while True:

            time.sleep(2)
            currentDateTime = datetime.datetime.now(pytz.timezone('Europe/Moscow'))
            res = getInfoLastPayment(label)

            if res or userId == config.ADMINCHAT:

                logging.info(
                    "user_id: {}; user_name:{}; Оплата подарочной подписки {} мес.".format(
                        userId,
                        userName,
                        month
                    )
                )

                hash = genGiftCode(month)

                bot.send_message(
                    config.ADMINCHAT,
                    "[{}](tg://user?id\={}) оплатил подарочную подписку".format(utils.form_text_markdownv2(userName), userId),
                    parse_mode=ParseMode.mdv2.value
                )
                bot.delete_message(userId, messageId)

                photoMessage = bot.send_photo(
                    chat_id=userId,
                    photo=open(config.FILE_URL + "image/gift.png", "rb"),
                    caption=config.TextsMessages.giftPostcard.value.format(code=hash, date=month),
                    parse_mode=ParseMode.mdv2.value
                )

                bot.reply_to(photoMessage, "Перешлите это сообщение другу в качестве подарка. Спасибо что помогаете нам делать интернет доступнее.")

                return res
            
            if currentDateTime > stopDateTime:
                bot.delete_message(userId, messageId)
                return 
            

    def add_key_admin(message: types.Message):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton(text=f'/{Comands.adminPanel.value}'),
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

    
    @bot.message_handler(commands=[config.ADMINPASSWORD], func=onlyAdminChat())
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


    @bot.callback_query_handler(func=lambda call: str(call.data).startswith('{"key":'))
    def callback_woker(call: types.CallbackQuery):

        call_data = json.loads(call.data)
        username: str = call.from_user.full_name

        logging.info("user_id: " + str(call.from_user.id) + ", user_name:" + str(username) + " нажата кнопка с ключем " + call_data['key'])

        match call_data['key']:

            case "try":
                
                conf = ConfigParser()
                conf.read(config.FILE_URL + 'config.ini')

                bot.delete_message(call.message.chat.id, call.message.id)
                oldMessage: types.Message = bot.send_photo(
                    chat_id=call.from_user.id, 
                    photo=open(config.FILE_URL + "4rrr.jpg", "rb"),
                    caption="Идет формирование конфигурации. Это может занять несколько минут..."
                )
                add_user(
                    call.from_user.id,
                    conf['BaseConfig'].getint('first_start_duration_month'),
                    name_user=utils.form_text_markdownv2(username, delete=True),
                    server=get_very_free_server()
                )
                if 'invitedId' in call_data:
                    invite.methods.addInvitedBonus(call_data['invitedId'])
                    invite.methods.writeInvited(
                        str(call.from_user.id), 
                        str(call_data['invitedId'])
                    )

                successfully_paid(
                    call.from_user.id, 
                    oldMessage.id
                )
            
            case KeyCall.sale.value:
                
                user: User = get_user_by_id(call.from_user.id)
                
                if 'back' in call_data:

                    return bot.edit_message_caption(
                        utils.form_text_markdownv2(config.TextsMessages.select_country.value),
                        call.message.chat.id,
                        call.message.id,
                        reply_markup=keyboards.get_inline_keyboard_list_countries(user.server_id),
                        parse_mode=ParseMode.mdv2.value
                    )

                bot.send_photo(
                    call.from_user.id,
                    photo = open(config.FILE_URL + "vpn_option.png", "rb"),
                    caption = utils.form_text_markdownv2(config.TextsMessages.select_country.value),
                    parse_mode=ParseMode.mdv2.value,
                    reply_markup=keyboards.get_inline_keyboard_list_countries(user.server_id)
                )

            case KeyCall.tryServers.value:

                bot.edit_message_text(
                    chat_id=call.from_user.id,
                    message_id=call.message.id,
                    text = utils.form_text_markdownv2(config.TextsMessages.select_country.value),
                    parse_mode=ParseMode.mdv2.value,
                    reply_markup=keyboards.get_inline_keyboard_list_countries_by_try(callData=call_data)
                )

            case KeyCall.pollCountMonth.value:
                
                conf = ConfigParser()
                conf.read(config.FILE_URL + 'config.ini')

                server_id: int = get_very_free_server()

                if "gift" in call_data:
                    key = "getGiftCode"
                else:
                    key = "getLinkPayment"

                keyboard = quick_markup(
                    {
                        '1 мес.| ' + conf['Price'].get('RUB') + " руб.": {'callback_data': '{"key": "' + key + '", "server": ' + str(server_id) + ', "month": 1}'},
                        '3 мес.| ' + str(conf['Price'].getint('RUB') * 3) + " руб.": {'callback_data': '{"key": "' + key + '", "server": ' + str(server_id) + ', "month": 3}'},
                        '6 мес.| ' + str(conf['Price'].getint('RUB') * 6) + " руб.": {'callback_data': '{"key": "' + key + '", "server": ' + str(server_id) + ', "month": 6}'},
                        '12 мес.| ' + str(conf['Price'].getint('RUB') * 12) + " руб.": {'callback_data': '{"key": "' + key + '", "server": ' + str(server_id) + ', "month": 12}'}
                    },
                    row_width=2
                )
                bot.edit_message_caption("На какой срок?", call.message.chat.id, call.message.id, reply_markup=keyboard)
            
            case "getGiftCode":

                data = crypto_pay.create_invoice(call_data['month'])
                crypto_pay.ids[data['invoice_id']] = PayingUser(
                    call.from_user.id,
                    call_data['month'],
                    call_data['server'],
                    call.message.id,
                    TypeOfPurchase.gift
                )

                label = (str(call.from_user.id) + 
                        str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))).replace(" ", "").replace("-","").replace("+", "").replace(".", "").replace(":", "")

                keyboard = quick_markup(
                    {
                        'Оплата рублями': {'url': getLinkPayment(label, call_data['month'])},
                        "Оплата Crypto Bot": {"url": data['mini_app_invoice_url']},
                        '<<< назад': {'callback_data': '{"key": "pollCountMonth", "server": ' + str(call_data['server']) + ', "gift": true}'}
                    },
                    row_width=1
                )
                
                bot.edit_message_caption(config.TextsMessages.giftPay.value, call.message.chat.id, call.message.id, reply_markup=keyboard)

                checkPayment = Thread(target=pollingInfoLastPaymentGift, args=(label, call_data['month'], call.from_user.id, call.message.id, call.from_user.full_name))
                checkPayment.start()

            case "getLinkPayment":
                
                conf = ConfigParser()
                conf.read(config.FILE_URL + 'config.ini')

                data = crypto_pay.create_invoice(call_data['month'])
                crypto_pay.ids[data['invoice_id']] = PayingUser(
                    call.from_user.id,
                    call_data['month'],
                    call_data['server'],
                    call.message.id,
                    TypeOfPurchase.yourself
                )


                label = (str(call.from_user.id) + 
                        str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))).replace(" ", "").replace("-","").replace("+", "").replace(".", "").replace(":", "")

                keyboard: keyboards.InlineKeyboardMarkup = quick_markup(
                    {
                        'Оплата рублями': {'url': getLinkPayment(label, call_data['month'])},
                        "Оплата Crypto Bot": {"url": data['mini_app_invoice_url']},
                        "Оплата звездами": {
                            "callback_data": '{"key": "' + enums.keyCall.KeyCall.payment_stars.name + '", "amount": ' + str(conf['Price'].getint('star') * int(call_data['month'])) + ', "server": ' + str(call_data['server']) + '}'
                        },
                        '<<< назад': {'callback_data': '{"key": "pollCountMonth", "server": ' + str(call_data['server']) + '}'}
                    },
                    row_width=1
                )
                user: User = get_user_by_id(call.from_user.id)

                option_text = ""
                if int(user.server_id) != int(call_data['server']):
                    option_text = "\n\nВнимание! После оплаты необходимо будет заново настроить VPN по инструкции, которую отправит вам бот."

                bot.edit_message_caption(
                    "Вы выбрали сервер " + utils.get_server_name_by_id(call_data['server']) + option_text, 
                    call.message.chat.id, 
                    call.message.id,
                    reply_markup=keyboard
                )

                checkPayment = Thread(target=pollingInfoLastPayment, args=(label, call_data['server'], call_data['month'], call.from_user.id, call.message.id, call.from_user.full_name))
                checkPayment.start()

            case "connect":

                key = types.InlineKeyboardMarkup()
                key.add(
                    *[
                        types.InlineKeyboardButton(
                            text=i,
                            callback_data='{"key": "action", "id": "' + str(call_data['id']) + '", "month": "' + str(i) + '", "s":' + str(call_data['serverId']) + '}'
                        ) for i in range(0, 13)
                    ],
                    types.InlineKeyboardButton(text="Назад", callback_data='{"key": "backConnectKey", "id": "' + str(call_data['id']) + '"}')
                )
                
                return bot.edit_message_reply_markup(
                    call.message.chat.id,
                    call.message.id,
                    reply_markup=key
                )
            
            case "backConnectKey":

                user: User = get_user_by_id(call_data['id'])
                bot.edit_message_reply_markup(
                    chat_id = call.message.chat.id, 
                    message_id = call.message.id, 
                    reply_markup = UserList.addButtonKeyForUsersList(user)
                )
                return
            
            case "action":

                user: User = get_user_by_id(call_data['id'])

                bot.edit_message_reply_markup(
                    chat_id = call.message.chat.id,
                    message_id= call.message.id,
                    reply_markup = keyboards.get_inline_loading()
                )

                if call.message.chat.id == config.ADMINCHAT:
                    try:
                        username = str(call.message.caption).split(": ", 1)[1]
                    except Exception:
                        username = str(call.message.text).split(" ", -2)[0]
                if "s" in call_data:
                    add_user(call_data['id'], call_data["month"], name_user=username, server=call_data['s'])
                else:
                    add_user(call_data['id'], call_data["month"], name_user=username)
                
                text_arr: list[str] = utils.form_text_markdownv2(call.message.text_or_caption).split('id:')[:-1]

                text: str = "id:".join(text_arr)

                if successfully_paid(call_data['id']):
                    text += "\n\n*Подписка активирована, сообщение пользователю отправлено*"
                else:
                    text += "\n\n*Подписка активирована, но сообщение не отправлено*"

                text += "\n\nid:" + call_data['id']

                bot.edit_message_text_or_caption(
                    call.message,
                    text,
                    parse_mode=ParseMode.mdv2,
                    reply_markup = UserList.addButtonKeyForUsersList(user)
                )

            case KeyCall.deaction.name:

                text = ""
            
                res: bool | NetworkServiceError = del_user(call_data['id'], no_message=True)

                if not isinstance(res, NetworkServiceError):

                    data_user(
                        call_data['id'],
                        call.message
                    )

                    text = "Подписка отключена"

                else:

                    text = f"{res.caption} [{res.response}]"

                return bot.answer_callback_query(
                    callback_query_id=call.id,
                    text=text,
                    show_alert=True
                )
                
            case "not_action":

                bot.delete_message(call.message.chat.id, call.message.id)
                bot.send_message(call_data['id'], "Покупка отклонена администратором")

            case "faq_video":

                bot.send_video(call.from_user.id, open(f"{config.FILE_URL}video/0809.mp4", "rb"), width=888, height=1920)

            case "comands_video":

                bot.send_video(call.from_user.id, open(f"{config.FILE_URL}video/08.mp4", "rb"), width=888, height=1920)

            case "page_client_next":
                
                managment_user.manager_users_list.next_page(call.message)

            case "page_client_back":

                managment_user.manager_users_list.back_page(call.message)

            case KeyCall.data_user.name:

                data_user(
                    call_data['id'],
                    call.message
                )

            case "option_where":

                if managment_user.manager_users_list.one_active == False:
                    managment_user.manager_users_list.one_active = True
                else:
                    managment_user.manager_users_list.one_active = False

                managment_user.manager_users_list.start = 0
                managment_user.manager_users_list.search_user(call.message)
             
            case "pppd":

                bot.send_message(call.message.chat.id, config.TextsMessages.TEXTPERSONINFO.value)

            case "termsOfUse":

                bot.send_message(call.message.chat.id, config.TextsMessages.TEXTTERMS.value)
        
            case "manualSettings":

                manual_successfully_paid(call_data['id'], call.message.id)

            case "backmanualSettings":

                successfully_paid(call_data['id'], oldMessageId=call.message.id)

            case "sendConf":

                if successfully_paid(call_data['id']):
                    bot.answer_callback_query(callback_query_id=call.id, text='Отправлено', show_alert=True)

            case enums.invite.CallbackKeys.resetToZeroBalance.value:

                invite.methods.resetToZeroBalance(call_data['userId'])
                bot.delete_message(
                    call.message.chat.id,
                    call.message.id
                )

                data_user(
                    call_data['userId'],
                    call.message
                )

                bot.answer_callback_query(
                    callback_query_id=call.id,
                    text='Баланс обнулен'
                )
            
            case enums.keyCall.KeyCall.refreshtoken.name:
                
                with db.cursor(cursor_factory=DictCursor) as cursor:
                    
                    user: User = get_user_by_id(call_data['user_id'])
                    controllerFastApi.del_users({user.telegram_id}, user.server_id)
                    link = controllerFastApi.add_vpn_user(user.telegram_id, user.server_id)
 
                    cursor.execute(
                        "UPDATE users_subscription" + 
                        "\nSET server_link='" + str(link) + "'" +
                        f"\nWHERE telegram_id={user.telegram_id}"
                    )
                    db.commit()

                bot.answer_callback_query(
                    callback_query_id=call.id,
                    text='Готово'
                )

            case enums.keyCall.KeyCall.create_cryptio_pay.name:

                data = crypto_pay.create_invoice(call_data['asset'])
                crypto_pay.ids[data['invoice_id']] = PayingUser(
                    call.from_user.id,
                    call_data['month'],
                    call_data['server'],
                    call.message.id
                )

                keyboard = quick_markup(
                    {
                        "Crypto Bot": {"web_app": data['mini_app_invoice_url']}
                    },
                    row_width=1
                )

                bot.edit_message_caption(
                    "Оплата USDT:",
                    call.message.chat.id,
                    call.message.id,
                    reply_markup=keyboard
                )

            case enums.keyCall.KeyCall.payment_stars.name:

                handle_buy(
                    call.message,
                    call_data['amount'],
                    call_data['server']
                )

            case KeyCall.list_servers_for_admin.name:

                keyboard: types.InlineKeyboardMarkup = quick_markup(
                    {
                        "Германия(самый свободный)": {"callback_data": '{"key": "connect", "id": "' + str(call_data['user_id']) + '", "serverId": ' + str(get_very_free_server(Country.deutsche)) + '}'}
                    }
                )

                keyboard.add(
                    *[
                        types.InlineKeyboardButton(
                            server.name,
                            callback_data='{"key": "connect", "id": "' + str(call_data['user_id']) + '", "serverId": ' + str(server.id) + '}'
                        ) for server in get_server_list()
                    ],
                    row_width=3
                )

                bot.edit_message_reply_markup(
                    call.message.chat.id,
                    call.message.id,
                    reply_markup=keyboard
                )
            
            case KeyCall.send_message_for_extension.name:

                bot.send_message(
                    call_data['user_id'],
                    "Продление:",
                    reply_markup=keyboards.getInlineExtend()
                )
                
                bot.answer_callback_query(
                    call.id,
                    "Отправлено"
                )
            
            case KeyCall.loading.name:

                bot.answer_callback_query(
                    callback_query_id=call.id,
                    text='Идет загрузка, ожидайте.'
                )

            case _:

                bot.answer_callback_query(
                    callback_query_id=call.id,
                    text='Кнопка еще не настроена.'
                )