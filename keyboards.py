from typing import Union
from telebot.types import InlineKeyboardMarkup
from telebot.util import quick_markup

from servers.server_list import Servers
from servers.server_list import Country
from enums.keyCall import KeyCall

from utils import get_very_free_server

# from connect import engine

# from sqlalchemy import select
# from sqlalchemy.orm import Session


def getInlineKeyboardListCountries(callData = None, optionText: str = "", key: str = "pollCountMonth", new = None) -> InlineKeyboardMarkup:
    """
        Возвращает клавиатуру со списком стран доступных для аренды
    """
    if callData != None and "invitedId" in callData:
        optionText = ', "invitedId": ' + str(callData['invitedId'])
        key = 'try'

    if new:
        key = 'try'

    return quick_markup(
        {   
            "Самый свободный сервер(рекомендуется)": {'callback_data': '{"key": "' + key + '", "server": ' + str(get_very_free_server()) + optionText + '}'},
            "Германия": {'callback_data': '{"key": "' + key + '", "server": ' + str(get_very_free_server(Country.deutsche)) + optionText + '}'},
            "Финляндия": {'callback_data': '{"key": "' + key + '", "server": ' + str(Servers.finland1.value) + optionText + '}'},
            "Нидерланды": {'callback_data': '{"key": "' + key + '", "server": ' + str(Servers.niderlands2.value) + optionText + '}'}
        },
        row_width=1
    )


def getInlineExtend() -> InlineKeyboardMarkup:

    return quick_markup(
        {
            "Продлить": {
                'callback_data': '{"key": "sale"}'
            }
        }
    )


def get_inline_keyboard_countries() -> InlineKeyboardMarkup:
    pass