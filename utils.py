from connect import logging, engine

from sqlalchemy.orm import Session
from sqlalchemy import select

from enums.logs import TypeLogs
from enums.content_types import ContentTypes

from tables import User, ServersTable, SecurityHashs

from enum import Enum

from telebot.types import Message



def replaceMonthOnRuText(datetime_exit) -> str:
    
    """принимает дату в формате как в БД
    и отдает строку с понятной человеку датой
    без времени"""

    arr = ['янв.',
                'фев.',
                'март.',
                'апр.',
                'мая',
                'июн.',
                'июл.',
                'авг.',
                'сен.',
                'окт.',
                'ноя.',
                'дек.'
                ]
    arrDate = str(datetime_exit).split("-")
    moth = arr[int(arrDate[1]) - 1]
    return form_text_markdownv2(str(arrDate[2]).split(" ")[0] + " " + str(moth) + " " + str(arrDate[0]))



def form_text_markdownv2(message_text: str, delete=None):

    """Преобразование строки в формат MarkdownV2"""
    
    temp = message_text
    try:
        for escaped_characters in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
            if escaped_characters in message_text:
                if delete:
                    message_text = str(message_text).replace(escaped_characters, " ")
                else:
                    message_text = str(message_text).replace(escaped_characters, "\\" + escaped_characters)
    except TypeError:
        return temp
    return message_text


#получает адрес сервера по ид
def getUrlByIdServer(serverId: str) -> str:
    with Session(engine) as session:
        query = select(ServersTable).where(ServersTable.id == serverId)
        server: ServersTable | None = session.execute(query).scalar()
        return server.links
        


def callBackBilder(callBackKey: Enum, **kwargs):
    
    """
        Формирует callback_data для InlineButton
    """

    itemsText = ""

    for property,value in kwargs.items():
        if isinstance(value, str):
            value = '"{}"'.format(value)
            
        itemsText += ',"{}": {}'.format(property, value)

    return '{"key": "' + callBackKey.value + '"' + itemsText + '}'



def get_token() -> str:
    with Session(engine) as session:
        query = select(SecurityHashs)
        security_hash: SecurityHashs | None = session.execute(query).scalar()
        return security_hash.hash
    

def write_log(type: TypeLogs, user: User, text: str) -> None:

    text = "user_id: " + str(user.telegram_id) + ", user_name:" + str(user.name) + ", " + text

    match type:
        case TypeLogs.info:
            logging.info(text)
        case TypeLogs.error:
            logging.error(text)


def get_server_name_by_id(server_id: int) -> str:
    
    query = select(ServersTable).filter(ServersTable.id == server_id)

    with Session(engine) as session:
        data: ServersTable | None = session.execute(query).scalar()
        if data:
            return data.name
        return "Неизвестное наименование сервера"
    

def get_list_values_from_enum(data: Enum) -> list:
    return [item.value for item in data]


def get_message_text_or_caption(message: Message) -> str | None:
    if message.content_type == ContentTypes.text.value:
        return message.text
    return message.caption