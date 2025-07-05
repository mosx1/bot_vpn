from connect import db, logging, engine

from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, text

from enums.invite import CallbackKeys
from servers.server_list import Country, Servers
from enums.logs import TypeLogs

from psycopg2.extras import DictCursor, DictRow

from tables import User, ServersTable

from enum import Enum



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
                if delete == True:
                    message_text = str(message_text).replace(escaped_characters, " ")
                else:
                    message_text = str(message_text).replace(escaped_characters, "\\" + escaped_characters)
    except TypeError:
        return temp
    return message_text


#получает адрес сервера по ид
def getUrlByIdServer(serverId: str) -> str:
    with db.cursor() as cursor:
        cursor.execute("SELECT links FROM servers WHERE id = " + str(serverId))
        curData = cursor.fetchone()
        if curData:
            return curData[0]
        


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
    with db.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute("SELECT hash FROM securityhashs")
        dataCur = cursor.fetchone()
        return dataCur['hash']
    


def get_very_free_server(country: Country | None = None) -> int:
    """
        Возвращает менее загруженный сервер по стране
        Если страна не передана - ищет по всем странам
    """
    with Session(engine) as session:
        query = (
            select(
                func.count().label('count'),
                ServersTable.id
            )
            .select_from(ServersTable)
            .join(
                User,
                and_(
                    User.server_id == ServersTable.id,
                    User.action == True
                ), 
                isouter=True
            )
        )
        
        if country:
            query = query.filter(ServersTable.country == country.value)
        else:
            query = query.filter(ServersTable.id != Servers.niderlands2.value)

        query = (
            query
            .group_by(ServersTable.id)
            .order_by(text('count ASC'))
            .limit(1)
        )
        result = session.execute(query).one()
       
        return result.id
        

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