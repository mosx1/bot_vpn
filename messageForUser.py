import config, utils

from connect import bot, db
from telebot import types
from telebot.util import quick_markup

from psycopg2.extras import DictCursor

from enums.parse_mode import ParseMode
from enums.keyCall import KeyCall

from users.methods import get_user_by_id
from tables import User



def periodSubscription(call: types.CallbackQuery, call_data: dict):
    
    keyboard: types.InlineKeyboardMarkup = quick_markup(
                {
                    '1 мес.| ' + str(config.PRICE) + " руб.": {'callback_data': '{"key": "getLinkPayment", "server": ' + str(call_data['server']) + ', "month": 1}'},
                    '3 мес.| ' + str(config.PRICE * 3) + " руб.": {'callback_data': '{"key": "getLinkPayment", "server": ' + str(call_data['server']) + ', "month": 3}'},
                    '6 мес.| ' + str(config.PRICE * 6) + " руб.": {'callback_data': '{"key": "getLinkPayment", "server": ' + str(call_data['server']) + ', "month": 6}'},
                    '12 мес.| ' + str(config.PRICE * 12) + " руб.": {'callback_data': '{"key": "getLinkPayment", "server": ' + str(call_data['server']) + ', "month": 12}'},
                    '<<< назад': {'callback_data': '{"key": "sale", "back": 1}'}
                },
                row_width=2
            )
    bot.edit_message_caption("На какой срок?", call.message.chat.id, call.message.id, reply_markup=keyboard)



def successfully_paid(id, oldMessageId=None, optionText="") -> bool:

    user: User = get_user_by_id(id)
    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            text="Завершить настройку", 
            url='https://kuzmos.ru/mobile?link={}'.format(
                str(user.server_link).replace('#', '&name=')
            )
        )
    )
    keyboard.add(
        types.InlineKeyboardButton(
            text="Ручная настройка(если ничего не подключается)", 
            callback_data='{"key": "manualSettings", "id": "' + str(id) + '"}'
        )
    )
    keyboard.add(
        types.InlineKeyboardButton(
            text="Авто вкл/выкл на iPhone", 
            callback_data='{"key": "comands_video"}'
        )
    )
    keyboard.add(
        types.InlineKeyboardButton(
            text="Продлить", 
            callback_data='{"key": "sale"}'
        ),
        types.InlineKeyboardButton(
            text=config.KeyboardForUser.gift.value,
            callback_data='{"key": "' + KeyCall.pollCountMonth.value + '", "server": '+ str(config.DEFAULTSERVER) + ', "gift": true}')
    )
    
    if not oldMessageId:
        if user.paid:
            keyboard_ref = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard_ref.add(types.KeyboardButton(text=config.KeyboardForUser.refProgram.value))
            keyboard_ref.add(types.KeyboardButton(text=config.KeyboardForUser.balanceTime.value))
            keyboard_ref.add(
                types.KeyboardButton(text=config.KeyboardForUser.buy.value),
                types.KeyboardButton(text=config.KeyboardForUser.gift.value)
            )
            bot.send_message(
                id,
                "Реферальная программа",
                reply_markup=keyboard_ref,
                parse_mode= ParseMode.mdv2.value
            )
    
        if bot.send_photo(
                chat_id=id,
                photo=open(config.FILE_URL + "4rrr.jpg", "rb"),
                caption=optionText + config.TextsMessages.successfullySubscriptionAutomatic.value.format(
                    id,
                    utils.replaceMonthOnRuText(user.exit_date),
                    utils.get_server_name_by_id(user.server_id)
                ),
                reply_markup=keyboard, 
                parse_mode=ParseMode.mdv2.value
            ):
            return True
        else:
            return False
    else:
        return bot.edit_message_caption(
            chat_id=id, 
            message_id=oldMessageId,
            caption=optionText + config.TextsMessages.successfullySubscriptionAutomatic.value.format(
                id,
                utils.replaceMonthOnRuText(user.exit_date),
                utils.get_server_name_by_id(user.server_id)
            ),
            reply_markup=keyboard, 
            parse_mode=ParseMode.mdv2.value
        )


def manual_successfully_paid(id, old_message_id) -> bool:

    user: User = get_user_by_id(id)

    keyboard: types.InlineKeyboardMarkup = quick_markup(
        {
            "Как подключить ПК": {"url": "https://drive.google.com/file/d/1mSATyhbzILNiMJxnkHMnKZWj_h6LpKIF/view?usp=sharing"},
            "Как подключить Android/iOS/MacOS": {"callback_data": '{"key": "home_key_faq"}'},
            "<<<Назад": {"callback_data": '{"key": "backmanualSettings", "id": "' + str(id) +'"}'}
        },
        row_width=1
    )

    return bot.edit_message_caption(
        chat_id=id, 
        message_id=old_message_id,
        caption=config.TextsMessages.successfullySubscription.value.format(
        utils.form_text_markdownv2(user.server_link),
        utils.replaceMonthOnRuText(user.exit_date)),
        reply_markup=keyboard, 
        parse_mode=ParseMode.mdv2.value
    )