from telebot.types import InlineKeyboardMarkup
from telebot.util import quick_markup

from servers.server_list import Country, Servers
from servers.methods import get_very_free_server

from enum import Enum

from enums.keyCall import KeyCall

from utils import callBackBilder


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