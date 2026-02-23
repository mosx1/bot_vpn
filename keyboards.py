import utils

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.util import quick_markup

from servers.server_list import Country
from servers.methods import get_very_free_server

from enum import Enum

from enums.keyCall import KeyCall, ReduceTime

from tables import User

from configparser import ConfigParser



class KeyboardForUser(Enum):
    
    balanceTime: str = "Дата окончания подписки"
    gift: str = "Подарить"
    buy: str = "Продлить"


def get_inline_keyboard_list_countries_by_try(callData = None, optionText: str = "") -> InlineKeyboardMarkup:
    """
        Возвращает клавиатуру со списком стран доступных для аренды для новых пользователей
    """
    if callData != None and "invitedId" in callData:
        optionText = ', "invitedId": ' + str(callData['invitedId'])

    return quick_markup(
        {   
            "Самый свободный сервер(рекомендуется)": {
                'callback_data': '{"key": "try", "server": ' + str(get_very_free_server()) + optionText + '}'
            },
            "Германия": {
                'callback_data': '{"key": "try", "server": ' + str(get_very_free_server(Country.deutsche)) + optionText + '}'
            }
        },
        row_width=1
    )


def get_inline_keyboard_list_countries(current_server_id: int) -> InlineKeyboardMarkup:
    """
        Возвращает клавиатуру со списком стран доступных для аренды для старых пользователей
    """

    return quick_markup(
        {   
            "Текущая локация(рекомендуется)": {
                'callback_data': '{"key": "' + KeyCall.pollCountMonth.value + '", "server": ' + str(current_server_id) + '}'
            },
            "Германия": {
                'callback_data': '{"key": "' + KeyCall.pollCountMonth.value + '", "server": ' + str(get_very_free_server(Country.deutsche)) + '}'
            }
        },
        row_width=1
    )
    


def getInlineExtend(value: str = "Продлить") -> InlineKeyboardMarkup:
    return quick_markup({value: {'callback_data': '{"key": "' + KeyCall.pollCountMonth.value + '"}'}})


def get_inline_loading() -> InlineKeyboardMarkup:
    return quick_markup({"Загрузка...": {"callback_data": '{"key": "' + KeyCall.loading.name + '"}'}})

def get_inline_transfer_for_nid() -> InlineKeyboardMarkup:
    return quick_markup({"Перейти на Немецкие сервера": {"callback_data": '{"key": "' + KeyCall.transfer_from_nid.value + '"}'}})

def get_inline_back_to_main(user_id: int | str) -> InlineKeyboardMarkup:
    return quick_markup(
        {
            "Смена ключа на роутере": {"callback_data": utils.callBackBilder(KeyCall.get_settings_vpn_router)},
            "<<<Назад": {"callback_data": '{"key": "backmanualSettings", "id": "' + str(user_id) +'"}'}
        },
        row_width=1
    )

def get_inline_for_users_list(user: User | None = None, a: int = 0, buttonNav: list = None, textKeyWhere: str = None) -> InlineKeyboardMarkup:

    config = ConfigParser()
    config.read('config.ini')

    keyboard_offer_one = InlineKeyboardMarkup()

    if user:
        if user.action:

            inlineKeyConnect = InlineKeyboardButton(
                    text="+",
                    callback_data='{"key": "connect", "id": ' + str(user.telegram_id) + ', "serverId": ' + str(user.server_id) + '}'
                )

            keyboard_offer_one.add(
                inlineKeyConnect,
                InlineKeyboardButton(
                    text="-",
                    callback_data=utils.callBackBilder(
                        ReduceTime.timing,
                        id=user.telegram_id
                    )
                ),
                InlineKeyboardButton(
                    text="Отключить", 
                    callback_data='{"key": "deaction", "id": "' + str(user.telegram_id) + '"}'
                ),
                InlineKeyboardButton(
                    text="Данные", 
                    callback_data='{"key": "data_user", "id": "' + str(user.telegram_id) + '"}'
                ),
                InlineKeyboardButton(
                    text="Отправить конфиг", 
                    callback_data='{"key": "sendConf", "id": "' + str(user.telegram_id) + '"}'
                )
            )
            
        else:

            keyboard_offer_one.add(
                InlineKeyboardButton(
                    text="Выбрать сервер", 
                    callback_data='{"key": "' + KeyCall.list_servers_for_admin.name + '", "user_id": ' + str(user.telegram_id) + '}'
                ),
                InlineKeyboardButton(
                    text="Данные", 
                    callback_data='{"key": "data_user", "id": "' + str(user.telegram_id) + '"}'
                ),
                InlineKeyboardButton(
                    text="Отправить кнопку продления",
                    callback_data='{"key": "' + KeyCall.send_message_for_extension.name + '", "user_id": "' + str(user.telegram_id) + '"}'
                ),
                row_width=2
            )
    if a == config['BaseConfig'].getint('count_page') - 1:
        keyboard_offer_one.row(*buttonNav)
        keyboard_offer_one.add(InlineKeyboardButton(text=textKeyWhere, callback_data='{"key": "option_where"}'))
    return keyboard_offer_one


def get_inline_for_full_user_info(user: User):

    keyboard: InlineKeyboardMarkup = get_inline_for_users_list(user)

    keyboard.add(
        InlineKeyboardButton(
            text = "Обнулить баланс",
            callback_data = utils.callBackBilder(
                KeyCall.reset_to_zero_balance,
                userId = id
            )
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text=KeyCall.refreshtoken.value,
            callback_data=utils.callBackBilder(
                KeyCall.refreshtoken,
                user_id = user.telegram_id
            )
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="Отправить счет",
            callback_data=utils.callBackBilder(
                KeyCall.send_sale_invoice,
                user_id = user.telegram_id
            )
        )
    )