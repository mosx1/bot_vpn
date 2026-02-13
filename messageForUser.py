import utils, keyboards

from connect import bot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from enums.parse_mode import ParseMode
from enums.keyCall import KeyCall

from users.methods import get_user_by_id
from database import User

from configparser import ConfigParser

from keyboards import KeyboardForUser, get_inline_loading

from servers.methods import get_very_free_server

from network_service.controller_flask_api import get_subscription_link


def successfully_paid(id, old_message: Message | None =None, optionText="") -> Message | bool:

    conf = ConfigParser()
    conf.read('config.ini')

    user: User = get_user_by_id(id)
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="Авто вкл/выкл на iPhone", 
            callback_data='{"key": "comands_video"}'
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="Ручная настройка", 
            callback_data='{"key": "manualSettings", "id": "' + str(id) + '"}'
        ),
        InlineKeyboardButton(
            text="Сменить сервер",
            callback_data='{"key": "' + KeyCall.transfer_other_server.value + '"}'
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="Купить роутер с этим сервисом.",
            callback_data='{"key": "' + KeyCall.pay_router.value + '"}'
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="Продлить", 
            callback_data='{"key": "' + KeyCall.pollCountMonth.value + '"}'
        ),
        InlineKeyboardButton(
            text=KeyboardForUser.gift.value,
            callback_data='{"key": "' + KeyCall.pollCountMonth.value + '", "server": '+ str(get_very_free_server()) + ', "gift": true}'
        )
    )
    
    text_for_message: str = conf['MessagesTextMD'].get('successfully_subscription_automatic')

    if not old_message:
        if user.paid:
            keyboard_ref = ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard_ref.add(KeyboardButton(text=KeyboardForUser.balanceTime.value))
            keyboard_ref.add(
                KeyboardButton(text=KeyboardForUser.buy.value),
                KeyboardButton(text=KeyboardForUser.gift.value)
            )
            bot.send_message(
                id,
                "Реферальная программа",
                reply_markup=keyboard_ref,
                parse_mode= ParseMode.mdv2.value
            )
    
        if t := bot.send_photo(
                chat_id=id,
                photo=open("4rrr.jpg", "rb"),
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
            old_message,
            optionText + text_for_message.format(
                user.telegram_id,
                utils.replaceMonthOnRuText(user.exit_date),
                utils.form_text_markdownv2(
                    utils.get_server_name_by_id(user.server_id)
                ),
                id
            ),
            reply_markup=keyboard, 
            parse_mode=ParseMode.mdv2
        )


def manual_successfully_paid(id: int, old_message: Message) -> bool:
    """
        отправляет сообщение для ручной настройки
    """
    bot.edit_message_reply_markup(
        id,
        old_message.id,
        reply_markup=get_inline_loading()
    )

    conf = ConfigParser()
    conf.read('config.ini')

    caption_for_message: str = conf['MessagesTextMD'].get('successfully_subscription')

    user: User = get_user_by_id(id)

    bot.edit_message_text_or_caption(
        old_message,
        caption_for_message.format(
            get_subscription_link(id),
            utils.form_text_markdownv2(user.server_link)
        ),
        reply_markup=keyboards.get_inline_back_to_main(id), 
        parse_mode=ParseMode.mdv2
    )
