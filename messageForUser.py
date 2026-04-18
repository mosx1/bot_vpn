import utils, keyboards, jwt

from connect import bot, engine, logging, conf
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from enums.parse_mode import ParseMode
from enums.keyCall import KeyCall
# from protocols import Protocol

from users.methods import get_user_by_id, get_jwt_by_id

from tables import User, SecurityHashs

from keyboards import KeyboardForUser, get_inline_loading, get_inline_web_page

from servers.methods import get_very_free_server, get_url_mtproto, get_server_by_id

from sqlalchemy import select
from sqlalchemy.orm import Session

def successfully_paid(id, old_message: Message | None =None, optionText="") -> Message | bool:

    user: User = get_user_by_id(id)
    token = get_jwt_by_id(user.telegram_id)
    # server = get_server_by_id(user.server_id)
    #if user.protocol == Protocol.amneziawg.value or server.panel_xray != 0:
    message_web_app = bot.send_message(
        id,
        'Для управления подпиской используйте веб приложение.',
        reply_markup=get_inline_web_page(token)
    )
    return bot.pin_chat_message(
        message_web_app.chat.id,
        message_web_app.id,
        disable_notification=True
    )

    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            text="Прокси для ТГ",
            url=get_url_mtproto(user.server_id),
            style="primary"
        ),
        InlineKeyboardButton(
            text="Авто вкл/выкл на iPhone", 
            callback_data='{"key": "comands_video"}'
        )
    )

    current_server = get_server_by_id(user.server_id)
    button_manual_settings = InlineKeyboardButton(
        text="Ручная настройка", 
        callback_data='{"key": "manualSettings", "id": "' + str(id) + '"}'
    )
    if current_server.is_wl:
        keyboard.add(button_manual_settings)
    else:
        keyboard.add(
            button_manual_settings,
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
            callback_data='{"key": "' + KeyCall.poll_count_month_gift.value + '", "server": '+ str(get_very_free_server()) + '}'
        )
    )
    
    text_for_message: str = conf['MessagesTextMD'].get('successfully_subscription_automatic')
    
    if not old_message:
        message_web_app: Message = bot.send_message(
            id,
            'Если телеграм не работает, оформить подписку можно через веб интерфейс или воспользовавшись прокси для телеграм.',
            reply_markup=get_inline_web_page(token)
        )
        bot.pin_chat_message(
            message_web_app.chat.id,
            message_web_app.id,
            disable_notification=True
        )
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
        
        with open("static/logo_big.jpeg", "rb") as logo_big:
            if t := bot.send_photo(
                    chat_id=id,
                    photo=logo_big,
                    caption=optionText + text_for_message.format(
                        token,
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
                token,
                utils.replaceMonthOnRuText(user.exit_date),
                utils.form_text_markdownv2(
                    utils.get_server_name_by_id(user.server_id)
                ),
                id
            ),
            reply_markup=keyboard, 
            parse_mode=ParseMode.mdv2
        )


def manual_successfully_paid(id: int, old_message: Message) -> None:
    """
        отправляет сообщение для ручной настройки
    """
    bot.edit_message_reply_markup(
        id,
        old_message.id,
        reply_markup=get_inline_loading()
    )
    caption_for_message: str = conf['MessagesTextMD'].get('successfully_subscription')
    user: User = get_user_by_id(id)
    with Session(engine) as session:
        hash_code = session.execute(
            select(SecurityHashs).limit(1)
        ).scalar()
    if not hash_code:
        bot.send_message(
            conf['Telegram'].getint('admin_chat'),
            f"Не удалось получить hash_code для пользователя id: {id}"
        )
        logging.error(f"Не удалось получить hash_code для пользователя id: {id}")
        return
    token: str = jwt.encode(
        {"telegram_id": id},
        hash_code.hash, 
        algorithm=conf['JWT'].get('algoritm')
    )
    bot.edit_message_text_or_caption(
        old_message,
        caption_for_message.format(
            f"https://kuzmos.ru/sub?jwt={token}",
            utils.form_text_markdownv2(user.server_link)
        ),
        reply_markup=keyboards.get_inline_back_to_main(id), 
        parse_mode=ParseMode.mdv2
    )
