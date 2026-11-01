import enums.keyCall
import json, config, utils, managment_user, invite, enums, keyboards

from connect import logging

import invite.methods

from telebot import types

from managment_user import data_user
                  
from servers.server_list import Country
from servers.methods import get_server_list, get_very_free_server, get_server_by_id

from telebot.util import quick_markup

from enums.parse_mode import ParseMode
from enums.keyCall import KeyCall, ReduceTime

from messageForUser import successfully_paid

from tables import User, ServersTable

from users.methods import get_user_by_id, get_jwt_by_id, reduce_time_by

from payment.crypto.repository.methods import crypto_pay, PayingUser
from payment.stars.handlers import handle_buy

from configparser import ConfigParser

from core.telebot import TeleBotMod

from network_service import vpn_webapp_api
from network_service.vpn_webapp_api import VpnWebappApiError
from keyboards import get_inline_web_page
from subscription.messages import format_subscription_expire_line


def _run_vpn_webapp_action(
    bot: TeleBotMod,
    call: types.CallbackQuery,
    action,
    progress_text: str,
) -> None:
    user: User | None = get_user_by_id(call.from_user.id)
    if not user:
        bot.answer_callback_query(call.id, "Сначала пройдите регистрацию на сайте.")
        return

    bot.answer_callback_query(call.id, progress_text)
    try:
        result = action(call.from_user.id)
    except VpnWebappApiError as error:
        bot.send_message(call.from_user.id, str(error))
        return

    token = get_jwt_by_id(call.from_user.id)
    user = get_user_by_id(call.from_user.id)
    bot.send_message(
        call.from_user.id,
        result.message,
        reply_markup=get_inline_web_page(token, user),
    )


def register_callback_handlers(bot: TeleBotMod) -> None:

    @bot.callback_query_handler(func=lambda call: call.data and isinstance(call.data, str) and call.data.startswith('{"key":'))
    def _(call: types.CallbackQuery):

        call_data = json.loads(call.data)
        username: str = call.from_user.full_name

        conf = ConfigParser()
        conf.read('config.ini')

        logging.info("user_id: " + str(call.from_user.id) + ", user_name:" + str(username) + " нажата кнопка с ключем " + call_data['key'])
        
        match call_data['key']:
            
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
                    photo = open("static/logo_option.jpg", "rb"),
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
                
                curr_user: User = get_user_by_id(call.from_user.id)
                coefficient = 1
                server: ServersTable = get_server_by_id(curr_user.server_id)
                if server.is_wl:
                    coefficient = 2

                bot.edit_message_text_or_caption(
                    call.message, 
                    "На какой срок?", 
                    reply_markup=keyboards.get_inline_for_count_month(
                        KeyCall.get_link_payment, 
                        curr_user.server_id,
                        coefficient
                    )
                )
            
            case KeyCall.poll_count_month_gift.value:
                
                bot.edit_message_text_or_caption(
                    call.message, 
                    "На какой срок?", 
                    reply_markup=keyboards.get_inline_for_count_month(
                        KeyCall.get_gift_code, 
                        call_data['server']
                    )
                )

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
            
            case ReduceTime.timing.value:

                key = types.InlineKeyboardMarkup()
                key.add(
                    *[
                        types.InlineKeyboardButton(
                            text=i,
                            callback_data=utils.callBackBilder(
                                ReduceTime.commit,
                                id=call_data['id'],
                                month=i
                            )
                        ) for i in range(0, 13)
                    ],
                    types.InlineKeyboardButton(text="Назад", callback_data='{"key": "backConnectKey", "id": "' + str(call_data['id']) + '"}')
                )
                
                return bot.edit_message_reply_markup(
                    call.message.chat.id,
                    call.message.id,
                    reply_markup=key
                )
            
            case ReduceTime.commit.value:
                
                user: User = get_user_by_id(call_data['id'])
                reduce_time_by(user, call_data['month'])
                user: User = get_user_by_id(call_data['id'])
                bot.send_message(
                    user.telegram_id,
                    f"Дата окончания подписки изменена\: {utils.replaceMonthOnRuText(user.exit_date)}",
                    parse_mode=ParseMode.mdv2.value
                )
                bot.edit_message_reply_markup(
                    chat_id = call.message.chat.id, 
                    message_id = call.message.id, 
                    reply_markup = keyboards.get_inline_for_users_list(user)
                )
                return
            
            case "backConnectKey":

                user: User = get_user_by_id(call_data['id'])
                bot.edit_message_reply_markup(
                    chat_id = call.message.chat.id, 
                    message_id = call.message.id, 
                    reply_markup = keyboards.get_inline_for_users_list(user)
                )
                return
                
            case "not_action":

                bot.delete_message(call.message.chat.id, call.message.id)
                bot.send_message(call_data['id'], "Покупка отклонена администратором")

            case "faq_video":

                bot.send_video(call.from_user.id, open("video/0809.mp4", "rb"), width=888, height=1920)

            case "comands_video":

                bot.send_video(call.from_user.id, open("video/08.mp4", "rb"), width=888, height=1920)

            case "page_client_next":
                
                managment_user.manager_users_list.next_page(call.message)

            case "page_client_back":

                managment_user.manager_users_list.back_page(call.message)

            case KeyCall.data_user.value:

                data_user(
                    call_data['id'],
                    call.message
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

            case KeyCall.transfer_other_server.value:
                _run_vpn_webapp_action(
                    bot,
                    call,
                    vpn_webapp_api.transfer_other_server,
                    "Обновляем подписку на сервере…",
                )
                return

            case KeyCall.transfer_protocol.value:
                _run_vpn_webapp_action(
                    bot,
                    call,
                    vpn_webapp_api.transfer_protocol,
                    "Меняем протокол…",
                )
                return

            case KeyCall.resume_subscription.value:
                _run_vpn_webapp_action(
                    bot,
                    call,
                    vpn_webapp_api.resume_subscription,
                    "Возобновляем подписку…",
                )
                return

            case KeyCall.subscription_info.value:
                user = get_user_by_id(call.from_user.id)
                if not user:
                    bot.answer_callback_query(call.id, "Сначала пройдите регистрацию на сайте.")
                    return
                bot.answer_callback_query(call.id, "Запрашиваем данные…")
                try:
                    info = vpn_webapp_api.get_subscription_info(call.from_user.id)
                except VpnWebappApiError as error:
                    bot.send_message(call.from_user.id, str(error))
                    return
                lines = [format_subscription_expire_line(info.get("expire_timestamp"))]
                if info.get("has_subscription_body"):
                    lines.append("Конфигурация для приложения доступна в подписке.")
                else:
                    lines.append(
                        "Конфигурация в подписке пока пуста — "
                        "возобновите доступ или обновите сервер кнопками ниже."
                    )
                token = get_jwt_by_id(call.from_user.id)
                bot.send_message(
                    call.from_user.id,
                    "\n".join(lines),
                    reply_markup=get_inline_web_page(token, user),
                )
                return

            case _:

                bot.answer_callback_query(
                    callback_query_id=call.id,
                    text='Кнопка еще не настроена.'
                )