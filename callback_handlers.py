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

from managers.subscription.renewal_of_subscription import renewalOfSubscription



def register_callback_handlers(bot: TeleBotMod) -> None:

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

    @bot.callback_query_handler(func=lambda call: str(call.data).startswith('{"key":'))
    def _(call: types.CallbackQuery):

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
                        '12 мес.| ' + str(conf['Price'].getint('RUB') * 12) + " руб.": {'callback_data': '{"key": "' + key + '", "server": ' + str(server_id) + ', "month": 12}'},
                        '◀️ назад': {'callback_data': '{"key": "' + KeyCall.backmanual_settings.value + '"}'}
                    },
                    row_width=2
                )
                bot.edit_message_text_or_caption(call.message, "На какой срок?", reply_markup=keyboard)
            
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
                
                bot.edit_message_text_or_caption(call.message, config.TextsMessages.giftPay.value, reply_markup=keyboard)

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

                link_payment: str = getLinkPayment(label, call_data['month'])

                keyboard: keyboards.InlineKeyboardMarkup = quick_markup(
                    {
                        'Оплата рублями': {'url': link_payment},
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

                bot.edit_message_text_or_caption(
                    call.message, 
                    "Вы выбрали сервер " + utils.get_server_name_by_id(call_data['server']) + option_text,
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

            case KeyCall.backmanual_settings.value:
                
                if call_data.get('id'):
                    id: int = call_data.get('id')
                else:
                    id: int = call.from_user.id

                successfully_paid(id, oldMessageId=call.message.id)

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

            case KeyCall.transfer_from_nid.value:

                bot.edit_message_reply_markup(
                    call.message.chat.id,
                    call.message.id,
                    reply_markup=keyboards.get_inline_loading()
                )
                user: User = get_user_by_id(call.from_user.id)
                renewalOfSubscription(user, "", get_very_free_server())
                successfully_paid(
                    user.telegram_id,
                    call.message.id,
                    "ПЕРЕНАСТРОЙТЕ ПРИЛОЖЕНИЕ!!!"
                )

            case _:

                bot.answer_callback_query(
                    callback_query_id=call.id,
                    text='Кнопка еще не настроена.'
                )