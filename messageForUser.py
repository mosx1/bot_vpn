import config, utils

from connect import bot
from telebot import types
from telebot.util import quick_markup

from enums.parse_mode import ParseMode
from enums.keyCall import KeyCall

from users.methods import get_user_by_id
from tables import User

from configparser import ConfigParser

from keyboards import KeyboardForUser, get_inline_loading

from servers.methods import get_very_free_server

from network_service.controller_flask_api import get_subscription_link


def successfully_paid(id, oldMessageId=None, optionText="") -> bool:

    conf = ConfigParser()
    conf.read(config.FILE_URL + 'config.ini')

    user: User = get_user_by_id(id)
    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            text="Авто вкл/выкл на iPhone", 
            callback_data='{"key": "comands_video"}'
        )
    )
    keyboard.add(
        types.InlineKeyboardButton(
            text="Ручная настройка", 
            callback_data='{"key": "manualSettings", "id": "' + str(id) + '"}'
        )
    )
    keyboard.add(
        types.InlineKeyboardButton(
            text="Продлить", 
            callback_data='{"key": "' + KeyCall.pollCountMonth.value + '"}'
        ),
        types.InlineKeyboardButton(
            text=KeyboardForUser.gift.value,
            callback_data='{"key": "' + KeyCall.pollCountMonth.value + '", "server": '+ str(get_very_free_server()) + ', "gift": true}'
        )
    )
    
    text_for_message: str = conf['MessagesTextMD'].get('successfully_subscription_automatic')

    if not oldMessageId:
        if user.paid:
            keyboard_ref = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard_ref.add(types.KeyboardButton(text=KeyboardForUser.balanceTime.value))
            keyboard_ref.add(
                types.KeyboardButton(text=KeyboardForUser.buy.value),
                types.KeyboardButton(text=KeyboardForUser.gift.value)
            )
            bot.send_message(
                id,
                "Реферальная программа",
                reply_markup=keyboard_ref,
                parse_mode= ParseMode.mdv2.value
            )
    
        if t := bot.send_photo(
                chat_id=id,
                photo=open(config.FILE_URL + "4rrr.jpg", "rb"),
                caption=optionText + text_for_message.format(
                    user.telegram_id,
                    utils.replaceMonthOnRuText(user.exit_date),
                    utils.form_text_markdownv2(
                        utils.get_server_name_by_id(user.server_id)
                    ),
                    id
                ),
                reply_markup=keyboard, 
                parse_mode=ParseMode.mdv2.value
            ):

            return True
        else:
            return False
    else:
        return bot.edit_message_text_or_caption(
            chat_id=id, 
            message_id=oldMessageId,
            caption=optionText + text_for_message.format(
                user.telegram_id,
                utils.replaceMonthOnRuText(user.exit_date),
                utils.form_text_markdownv2(
                    utils.get_server_name_by_id(user.server_id)
                ),
                id
            ),
            reply_markup=keyboard, 
            parse_mode=ParseMode.mdv2.value
        )
    


def manual_successfully_paid(id: int, old_message_id: int) -> bool:
    """
        отправляет сообщение для ручной настройки
    """
    bot.edit_message_reply_markup(
        id,
        old_message_id,
        reply_markup=get_inline_loading()
    )

    conf = ConfigParser()
    conf.read(config.FILE_URL + 'config.ini')

    caption_for_message: str = conf['MessagesTextMD'].get('successfully_subscription')

    user: User = get_user_by_id(id)

    keyboard: types.InlineKeyboardMarkup = quick_markup(
        {
            "<<<Назад": {"callback_data": '{"key": "backmanualSettings", "id": "' + str(id) +'"}'}
        },
        row_width=1
    )

    try:
        bot.edit_message_caption(
            chat_id=id, 
            message_id=old_message_id,
            caption=caption_for_message.format(
                get_subscription_link(id),
                utils.form_text_markdownv2(user.server_link)
            ),
            reply_markup=keyboard, 
            parse_mode=ParseMode.mdv2.value
        )
    except Exception as e :
        bot.send_message(
            id,
            user.server_link
        )