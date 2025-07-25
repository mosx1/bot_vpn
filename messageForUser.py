import config, utils

from connect import bot
from telebot import types
from telebot.util import quick_markup

from enums.parse_mode import ParseMode
from enums.keyCall import KeyCall

from users.methods import get_user_by_id
from tables import User

from configparser import ConfigParser

from keyboards import KeyboardForUser


def periodSubscription(call: types.CallbackQuery, call_data: dict):

    conf = ConfigParser()
    conf.read(config.FILE_URL + 'config.ini')
    
    keyboard: types.InlineKeyboardMarkup = quick_markup(
                {
                    '1 мес.| ' + conf['Price'].get('RUB') + " руб.": {'callback_data': '{"key": "getLinkPayment", "server": ' + str(call_data['server']) + ', "month": 1}'},
                    '3 мес.| ' + str(conf['Price'].getint('RUB') * 3) + " руб.": {'callback_data': '{"key": "getLinkPayment", "server": ' + str(call_data['server']) + ', "month": 3}'},
                    '6 мес.| ' + str(conf['Price'].getint('RUB') * 6) + " руб.": {'callback_data': '{"key": "getLinkPayment", "server": ' + str(call_data['server']) + ', "month": 6}'},
                    '12 мес.| ' + str(conf['Price'].getint('RUB') * 12) + " руб.": {'callback_data': '{"key": "getLinkPayment", "server": ' + str(call_data['server']) + ', "month": 12}'},
                    '<<< назад': {'callback_data': '{"key": "sale", "back": 1}'}
                },
                row_width=2
            )
    bot.edit_message_caption("На какой срок?", call.message.chat.id, call.message.id, reply_markup=keyboard)



def successfully_paid(id, oldMessageId=None, optionText="") -> bool:

    user: User = get_user_by_id(id)
    keyboard = types.InlineKeyboardMarkup()

    # keyboard.add(
    #     types.InlineKeyboardButton(
    #         text="Завершить настройку", 
    #         url='https://kuzmos.ru/mobile?link={}'.format(
    #             str(user.server_link).replace('#', '&name=')
    #         )
    #     )
    # )
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
            text=KeyboardForUser.gift.value,
            callback_data='{"key": "' + KeyCall.pollCountMonth.value + '", "server": '+ str(utils.get_very_free_server()) + ', "gift": true}')
    )
    
    if not oldMessageId:
        if user.paid:
            keyboard_ref = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard_ref.add(types.KeyboardButton(text=KeyboardForUser.refProgram.value))
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
    
        if bot.send_photo(
                chat_id=id,
                photo=open(config.FILE_URL + "4rrr.jpg", "rb"),
                caption=optionText + config.TextsMessages.successfullySubscriptionAutomatic.value.format(
                    str(user.server_link).replace('#', '&name='),
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
        return bot.edit_message_caption(
            chat_id=id, 
            message_id=oldMessageId,
            caption=optionText + config.TextsMessages.successfullySubscriptionAutomatic.value.format(
                str(user.server_link).replace('#', '&name='),
                utils.replaceMonthOnRuText(user.exit_date),
                utils.form_text_markdownv2(
                    utils.get_server_name_by_id(user.server_id)
                ),
                id
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