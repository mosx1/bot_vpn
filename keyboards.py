import json

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from servers.server_list import Country, Servers
from servers.methods import get_very_free_server

from enum import Enum

from enums.keyCall import KeyCall

from utils import callBackBilder

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

def get_inline_subscription_period(key: str, server_id: int) -> InlineKeyboardMarkup:

    conf = ConfigParser()
    conf.read('config.ini')
    
    buttons = [
        [
            InlineKeyboardButton(
                text='1 мес.| ' + conf['Price'].get('RUB') + " руб.",
                callback_data=json.dumps(
                    {
                        "key":  key,
                        "server": server_id,
                        "month": 1
                    }
                )
            ),
            InlineKeyboardButton(
                text='3 мес.| ' + str(conf['Price'].getint('RUB') * 3) + " руб.",
                callback_data=json.dumps(
                    {
                        "key":  key,
                        "server": server_id, 
                        "month": 3
                    }
                )
            )
        ],
        [
            InlineKeyboardButton(
                text='6 мес.| ' + str(conf['Price'].getint('RUB') * 6) + " руб.",
                callback_data=json.dumps(
                    {
                        "key": key, 
                        "server": server_id, 
                        "month": 6
                    }
                )
            ),
            InlineKeyboardButton(
                text='12 мес.| ' + str(conf['Price'].getint('RUB') * 12) + " руб.",
                callback_data=json.dumps(
                    {
                        "key": key, 
                        "server": server_id, 
                        "month": 12
                    }
                )
            )
        ],
        [
            InlineKeyboardButton(
                text='◀️ назад',
                callback_data=json.dumps(
                    {
                        "key": KeyCall.backmanual_settings.value
                    }
                )
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_inline_payment_methods(
        server_id: int,
        link_yoomony: str | None = None, 
        link_crypto_bot: str | None = None,
        gift: bool = False
) -> InlineKeyboardMarkup:

    buttons = []

    if link_yoomony:
        
        buttons.append(
            [
                InlineKeyboardButton(
                    text='Оплата рублями',
                    url=link_yoomony
                )
            ]
        )
    
    if link_crypto_bot:

        buttons.append(
            [
                InlineKeyboardButton(
                    text="Оплата Crypto Bot",
                    url=link_crypto_bot
                )
            ]
        )
    
    buttons.append(
        [
            InlineKeyboardButton(
                text='<<< назад',
                callback_data=json.dumps(
                    {
                        "key": "pollCountMonth", 
                        "server": server_id, 
                        "gift": gift
                    }
                )
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_inline_qty_month(user_id: int, server_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=i,
                callback_data=json.dumps(
                    {
                        "key": "action", 
                        "id": user_id, 
                        "month": str(i),
                        "s": server_id
                    }
                )
            ) for i in range(0, 13)
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)