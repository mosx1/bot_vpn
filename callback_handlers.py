import enums.invite
import enums.keyCall
import json, config, utils, pytz, datetime, managment_user, invite, enums, keyboards, asyncio

from connect import AsyncSession, logging, bot

import invite.methods

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from managment_user import add_user, del_user, UserList, data_user, delete_not_subscription

from filters import onlyAdminChat
                  
from servers.server_list import Servers, Country
from servers.methods import get_server_list, get_very_free_server

from yoomoneyMethods import getInfoLastPayment, getLinkPayment

from threading import Thread

from enums.comands import Comands
from enums.parse_mode import ParseMode
from enums.keyCall import KeyCall
from enums.chat_types import ChatTypes

from giftUsers import genGiftCode, checkGiftCode

from messageForUser import successfully_paid, manual_successfully_paid

from tables import User

from users.methods import get_user_by_id

from sqlalchemy import text as sqltext

from payment.crypto.repository.methods import crypto_pay, PayingUser, TypeOfPurchase
from payment.stars.handlers import handle_buy

from configparser import ConfigParser

from network_service import controllerFastApi
from network_service.entity import NetworkServiceError

from core.aiogram import TeleBotMod

from managers.subscription.renewal_of_subscription import renewalOfSubscription

router = Router()

async def polling_info_last_payment(label, server, month, user_id, message_id, user_name: str | None = None) -> dict:
    """
        args - label, server, day, userId, messageId
    """
    userId = user_id
    messageId = message_id
    
    if user_name:
        userName: str = user_name
    else:
        userName = userId

    conf = ConfigParser()
    conf.read('config.ini')

    stopDateTime = datetime.datetime.now(pytz.timezone('Europe/Moscow')) + datetime.timedelta(hours=1)

    while True:
        
        res = None

        await asyncio.sleep(3)

        currentDateTime: datetime.datetime = datetime.datetime.now(pytz.timezone('Europe/Moscow'))

        try:
            res: dict = getInfoLastPayment(label)
        except Exception as e:
            await bot.send_message(conf['Telegram'].get('admin_chat'), str(e))
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

            await bot.edit_message_caption(
                "Оплата получена, идет настройка конфигурации(это может занять несколько минут)...", 
                userId,
                messageId
            )
            
            userMessage: config.AddUserMessage = add_user(userId, month, server=server)

            await bot.send_message(
                config.ADMINCHAT,
                "[" + utils.form_text_markdownv2(userName) + "](tg://user?id\=" + str(userId) + ") оплатил",
                parse_mode=ParseMode.mdv2.value
            )
            await bot.delete_message(userId, messageId)
            
            invite.methods.incrementBalance(userId, month=month)
            
            successfully_paid(userId, optionText=userMessage.value)

            return res
        
        if currentDateTime > stopDateTime:
            await bot.delete_message(userId, messageId)
            return 
        
        
async def polling_info_last_payment_gift(label, month, user_id, message_id, user_name: str | None = None) -> dict:

    userId = user_id
    messageId = message_id
    if user_name:
        userName = user_name
    else:
        userName = userId

    conf = ConfigParser()
    conf.read('config.ini')
    admin_chat_id = conf['Telegram'].get('admin_chat')

    stopDateTime = datetime.datetime.now(pytz.timezone('Europe/Moscow')) + datetime.timedelta(hours=1)

    while True:

        res = None

        asyncio.sleep(2)
        
        currentDateTime = datetime.datetime.now(pytz.timezone('Europe/Moscow'))
        res = getInfoLastPayment(label)

        if res or userId == admin_chat_id:

            logging.info(
                "user_id: {}; user_name:{}; Оплата подарочной подписки {} мес.".format(
                    userId,
                    userName,
                    month
                )
            )

            hash = genGiftCode(month)

            await bot.send_message(
                admin_chat_id,
                "[{}](tg://user?id\={}) оплатил подарочную подписку".format(utils.form_text_markdownv2(userName), userId),
                parse_mode=ParseMode.mdv2.value
            )
            await bot.delete_message(userId, messageId)

            photoMessage: Message = await bot.send_photo(
                chat_id=userId,
                photo=open(config.FILE_URL + "image/gift.png", "rb"),
                caption=config.TextsMessages.giftPostcard.value.format(code=hash, date=month),
                parse_mode=ParseMode.mdv2.value
            )

            await photoMessage.reply("Перешлите это сообщение другу в качестве подарка. Спасибо что помогаете нам делать интернет доступнее.")

            return res
        
        if currentDateTime > stopDateTime:
            await bot.delete_message(userId, messageId)
            return 

@router.callback_query(F.data.startswith('{"key":'))
async def _(call: CallbackQuery):

    call_data = json.loads(call.data)
    username: str = call.from_user.full_name

    logging.info("user_id: " + str(call.from_user.id) + ", user_name:" + str(username) + " нажата кнопка с ключем " + call_data['key'])
    
    match call_data['key']:

        case "try":
            
            conf = ConfigParser()
            conf.read(config.FILE_URL + 'config.ini')

            await bot.delete_message(call.message.chat.id, call.message.id)
            oldMessage: Message = await bot.send_photo(
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

                return await bot.edit_message_caption(
                    utils.form_text_markdownv2(config.TextsMessages.select_country.value),
                    call.message.chat.id,
                    call.message.id,
                    reply_markup=keyboards.get_inline_keyboard_list_countries(user.server_id),
                    parse_mode=ParseMode.mdv2.value
                )

            await bot.send_photo(
                call.from_user.id,
                photo = open(config.FILE_URL + "vpn_option.png", "rb"),
                caption = utils.form_text_markdownv2(config.TextsMessages.select_country.value),
                parse_mode=ParseMode.mdv2.value,
                reply_markup=keyboards.get_inline_keyboard_list_countries(user.server_id)
            )

        case KeyCall.tryServers.value:

            await bot.edit_message_text(
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

            bot.edit_message_text_or_caption(
                call.message, 
                "На какой срок?", 
                reply_markup=keyboards.get_inline_subscription_period(key, server_id)
            )
        
        case "getGiftCode":

            data = crypto_pay.create_invoice(call_data['month'])
            crypto_pay.ids[data['invoice_id']] = PayingUser(
                call.from_user.id,
                call_data['month'],
                call_data['server'],
                call.message.id,
                TypeOfPurchase.gift
            )

            label = (str(call.from_user.id) + str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))).replace(" ", "").replace("-","").replace("+", "").replace(".", "").replace(":", "")
            
            bot.edit_message_text_or_caption(
                call.message, 
                config.TextsMessages.giftPay.value, 
                reply_markup=keyboards.get_inline_payment_methods(
                    call_data['server'],
                    getLinkPayment(label, call_data['month']),
                    data['mini_app_invoice_url'],
                    True
                )
            )

            asyncio.create_task(
                polling_info_last_payment_gift(
                    label, 
                    call_data['month'],
                    call.from_user.id,
                    call.message.id,
                    call.from_user.full_name
                )
            )

        case "getLinkPayment":
            
            conf = ConfigParser()
            conf.read(config.FILE_URL + 'config.ini')
            
            user: User = get_user_by_id(call.from_user.id)
            
            if user.action:
                server_id = user.server_id
            else:
                server_id = get_very_free_server()

            data = crypto_pay.create_invoice(call_data['month'])
            crypto_pay.ids[data['invoice_id']] = PayingUser(
                call.from_user.id,
                call_data['month'],
                server_id,
                call.message.id,
                TypeOfPurchase.yourself
            )


            label = (str(call.from_user.id) + str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))).replace(" ", "").replace("-","").replace("+", "").replace(".", "").replace(":", "")
            

            option_text = ""
            if int(user.server_id) != int(call_data['server']):
                option_text = "\n\nВнимание! После оплаты необходимо будет заново настроить VPN по инструкции, которую отправит вам бот."

            await bot.edit_message_text_or_caption(
                call.message, 
                "Оплата рублями временно не принимается. В место этого используйте оплату звездами." + option_text,
                reply_markup=keyboards.get_inline_payment_methods(
                    call_data['server'],
                    getLinkPayment(label, call_data['month']),
                    data['mini_app_invoice_url'],
                    True
                )
            )

            asyncio.create_task(
                polling_info_last_payment(
                    label, 
                    call_data['month'],
                    call.from_user.id,
                    call.message.id,
                    call.from_user.full_name
                )
            )

        case "connect":
            
            return await bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.id,
                reply_markup=keyboards.get_inline_qty_month(
                    call_data['id'],
                    call_data['serverId']
                )
            )
        
        case "backConnectKey":

            user: User = get_user_by_id(call_data['id'])
            await bot.edit_message_reply_markup(
                chat_id = call.message.chat.id, 
                message_id = call.message.id, 
                reply_markup = UserList.addButtonKeyForUsersList(user)
            )
            return
        
        case "action":

            user: User = get_user_by_id(call_data['id'])

            await bot.edit_message_reply_markup(
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

            await bot.edit_message_text_or_caption(
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

            return await bot.answer_callback_query(
                callback_query_id=call.id,
                text=text,
                show_alert=True
            )
            
        case "not_action":

            await bot.delete_message(call.message.chat.id, call.message.id)
            await bot.send_message(call_data['id'], "Покупка отклонена администратором")

        case "faq_video":

            await bot.send_video(call.from_user.id, open(f"{config.FILE_URL}video/0809.mp4", "rb"), width=888, height=1920)

        case "comands_video":

            await bot.send_video(call.from_user.id, open(f"{config.FILE_URL}video/08.mp4", "rb"), width=888, height=1920)

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

            await bot.send_message(call.message.chat.id, config.TextsMessages.TEXTPERSONINFO.value)

        case "termsOfUse":

            await bot.send_message(call.message.chat.id, config.TextsMessages.TEXTTERMS.value)
    
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
            await bot.delete_message(
                call.message.chat.id,
                call.message.id
            )

            data_user(
                call_data['userId'],
                call.message
            )

            await bot.answer_callback_query(
                callback_query_id=call.id,
                text='Баланс обнулен'
            )
        
        case enums.keyCall.KeyCall.refreshtoken.name:
            
            async with AsyncSession() as session:
                
                user: User = get_user_by_id(call_data['user_id'])
                controllerFastApi.del_users({user.telegram_id}, user.server_id)
                link = controllerFastApi.add_vpn_user(user.telegram_id, user.server_id)

                session.execute(
                    sqltext(
                        "UPDATE users_subscription" + 
                        "\nSET server_link='" + str(link) + "'" +
                        f"\nWHERE telegram_id={user.telegram_id}"
                    )
                )
                session.commit()

            await bot.answer_callback_query(
                callback_query_id=call.id,
                text='Готово'
            )

        case enums.keyCall.KeyCall.payment_stars.name:

            handle_buy(
                call.message,
                call_data['amount'],
                call_data['server']
            )

        case KeyCall.list_servers_for_admin.name:
            pass
            # keyboard: InlineKeyboardMarkup = quick_markup(
            #     {
            #         "Германия(самый свободный)": {"callback_data": '{"key": "connect", "id": "' + str(call_data['user_id']) + '", "serverId": ' + str(get_very_free_server(Country.deutsche)) + '}'}
            #     }
            # )

            # keyboard.add(
            #     *[
            #         InlineKeyboardButton(
            #             server.name,
            #             callback_data='{"key": "connect", "id": "' + str(call_data['user_id']) + '", "serverId": ' + str(server.id) + '}'
            #         ) for server in get_server_list()
            #     ],
            #     row_width=3
            # )

            # bot.edit_message_reply_markup(
            #     call.message.chat.id,
            #     call.message.id,
            #     reply_markup=keyboard
            # )
        
        case KeyCall.send_message_for_extension.name:

            await bot.send_message(
                call_data['user_id'],
                "Продление:",
                reply_markup=keyboards.getInlineExtend()
            )
            
            await bot.answer_callback_query(
                call.id,
                "Отправлено"
            )
        
        case KeyCall.loading.name:

            await bot.answer_callback_query(
                callback_query_id=call.id,
                text='Идет загрузка, ожидайте.'
            )

        case KeyCall.transfer_from_nid.value:

            await bot.edit_message_reply_markup(
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

            await bot.answer_callback_query(
                callback_query_id=call.id,
                text='Кнопка еще не настроена.'
            )